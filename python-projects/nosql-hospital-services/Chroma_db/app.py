import os
import json
import hashlib
import logging
import falcon.asgi
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from transformers import pipeline


"""
SETUP: Start ChromaDB Docker before running this app:
docker run -d -v ./chroma-data:/data -p 8001:8000 --name chromadb chromadb/chroma

Then just run: uvicorn app:app --reload
"""
logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
logging.getLogger('chromadb').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)



# Initialize ChromaDB
DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DIR, 'data')
client = chromadb.HttpClient(host="localhost",port=8001,settings=Settings(allow_reset=True, anonymized_telemetry=False))
collection = client.get_or_create_collection(name="api_healthcare")

# Initialize Sentence Transformer model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load the model once at the application start
model_name = "gpt2"
generator = pipeline("text-generation", model=model_name)



def generate_id(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

class QueryResource:
    async def on_post(self, req, resp):
        """
        Handle POST requests to answer queries
        """
        try:
            raw_json = await req.bounded_stream.read()
            request_data = json.loads(raw_json)

            # Extract query
            query = request_data.get("query", "")
            if not query:
                raise ValueError("Query cannot be empty.")

            # Generate query embedding
            query_embedding = model.encode(query)

            # Retrieve relevant documents from ChromaDB
            results = collection.query(query_embeddings=[query_embedding], n_results=2)

            # Extract documents
            documents = results["documents"][0]

            # Combine documents into a context
            context = " ".join(documents)

             # Validate context before passing to the QA pipeline
            if not context.strip():
                context = ""

            input_text = f"Context: {context}\n\nGive me the doctor information with one phrase.\n"
            # Generate response using QA pipeline
            response = generator(input_text, max_new_tokens=70, num_return_sequences=1, truncation=True)

            # Extract the generated answer
            generated_response = "No answer found."
            if response:
                generated_response = response[0]["generated_text"]

            # Return the response
            resp.media = {
                "query": query,
                "context": context,
                "answer": generated_response,
            }
            resp.status = falcon.HTTP_200
        except Exception as e:
            resp.media = {"error": str(e)}
            resp.status = falcon.HTTP_400

class KnowledgeResource:
    async def on_post(self, req, resp):
        """
        Handle POST requests to upload new documents
        """
        try:
            raw_json = await req.bounded_stream.read()
            request_data = json.loads(raw_json)

            contents = request_data["contents"]
            doc_ids = []
            to_remove_idx = []

            # Generate document ids, check for duplication
            for i in range(len(contents)):
                doc_id = generate_id(contents[i])
                results = collection.get(ids=[doc_id])
                if not results or len(results["documents"]) == 0:
                    doc_ids.append(doc_id)
                else:
                    print(f"Document already exists, ignoring doc id:{doc_id}")
                    to_remove_idx.append(i)

            # Remove indexes of documents that already exist to avoid duplication
            for idx in sorted(to_remove_idx, reverse=True):
                del contents[idx]
    
            # Upload documents
            if len(contents) > 0:
                embeddings = model.encode(contents)
                collection.add(ids=doc_ids, documents=contents, embeddings=embeddings)
            resp.status = falcon.HTTP_200
        except Exception as e:
            resp.media = {"error": str(e)}
            resp.status = falcon.HTTP_400

    async def on_get(self, req, resp):
        """
        Handle GET requests for a all documents
        """
        try:
            response = []
            knowledge = collection.get()
            # Return the documents
            ids  = knowledge["ids"]
            contents = knowledge["documents"]
            for i in range(len(ids)):
                response.append({
                    "id": ids[i],
                    "content": contents[i],
                })

            resp.media = response
            resp.status = falcon.HTTP_200
        except Exception as e:
            resp.media = {"error": str(e)}
            resp.status = falcon.HTTP_400

class SingleKnowledgeResource:
    async def on_get(self, req, resp, id):
        """
        Handle GET requests for a specific document by ID.
        """
        try:
            # Query the database for the document using the provided ID
            results = collection.get(ids=[id])
            if not results or len(results["documents"]) == 0:
                raise ValueError("Document not found.")

            # Return the document
            content = results["documents"][0]
            resp.media = {"id": id, "content": content}
            resp.status = falcon.HTTP_200

        except ValueError as e:
            resp.media = {"error": str(e)}
            resp.status = falcon.HTTP_404
        except Exception as e:
            resp.media = {"error": str(e)}
            resp.status = falcon.HTTP_400

# Initialize Falcon app
app = falcon.asgi.App()
app.add_route("/query", QueryResource())
app.add_route("/knowledge", KnowledgeResource())
app.add_route("/knowledge/{id}", SingleKnowledgeResource())
