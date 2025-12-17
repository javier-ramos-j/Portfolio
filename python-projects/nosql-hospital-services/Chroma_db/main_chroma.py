import json
import requests

from urllib.parse import urljoin

BASE_URL = "http://localhost:8005"
KNOWLEDGE_ENDPOINT = "knowledge"
QUERY_ENDPOINT = "query"



def upload_documents(file_path):
    endpoint = urljoin(BASE_URL, KNOWLEDGE_ENDPOINT)
    try:
        contents = []
        data = {}
        with open(file_path, 'r') as file:
            documents = json.load(file)
            for doc in documents:
                contents.append(doc["content"])
            data["contents"] = contents
            response = requests.post(endpoint, json=data)
        if response.status_code == 200:
            print("Document uploaded successfully.")
        else:
            print(f"Failed to upload documents:\nStatus code: {response.status_code}\n Details: {response.json()}")
    except FileNotFoundError:
        print("File not found. Please check the path and try again.")

def get_documents():
    endpoint = urljoin(BASE_URL, KNOWLEDGE_ENDPOINT)
    response = requests.get(endpoint)
    if response.status_code == 200:
        documents = response.json()
        print(f"{len(documents)} documents retrieved successfully:")
        for doc in documents:
            id = doc["id"]
            content = doc["content"]
            print(f"{id}: {content}")
            print("-" * 80)
    else:
        print(f"Failed to get documents.\nStatus code: {response.status_code}\n Details: {response.json()}")

def get_document(doc_id):
    endpoint = urljoin(BASE_URL, KNOWLEDGE_ENDPOINT)
    response = requests.get(f"{endpoint}/{doc_id}")
    if response.status_code == 200:
        document = response.json()
        id = document["id"]
        content = document["content"]
        print(f"ID:{id}\nContent:{content}")
        print("-" * 80)
    elif response.status_code == 404:
        print("Document not found.")
    else:
        print(f"Failed to get document.\nStatus code: {response.status_code}\n Details: {response.json()}")

def chat_query(query):
    endpoint = urljoin(BASE_URL, QUERY_ENDPOINT)
    response = requests.post(endpoint, json={'query': query})
    if response.status_code == 200:
        answer = response.json().get('answer')
        print(f"Chatbot response:\n {answer}")
    else:
        print(f"Failed to get chat response.\nStatus code: {response.status_code}\n Details: {response.json()}")
        
def mostrar_menu():
    print("\n" + "-" * 80)
    print("         API CLIENT")
    print("=" * 80)
    print("\nOPCIONES:")
    print("  1) Upload JSON documents")
    print("  2) See all documents")
    print("  3) Search document by ID")
    print("  4) Make a query to the chatbot")
    print("  0) Exit")
    print("-" * 80)


def main():
    print(f"Contecting to: {BASE_URL}")

    while True:
        mostrar_menu()
        opcion = input("\nSelect an option (0-4)): ").strip()
        
        if opcion == '1':
            print("\nUPLOADING DOCUMENTS")
            upload_documents("Document/info.json")
        elif opcion == '2':
            print("\nLIST ALL DOCUMENTS")
            get_documents()
        
        elif opcion == '3':
            print("\nSEARCH DOCUMENT BY ID")
            doc_id = input("Document ID: ").strip()
            if doc_id:
                get_document(doc_id)
            else:
                print("You must provide a valid ID.")
        
        elif opcion == '4':
            print("\nASK THE CHATBOT")
            query = input("Your question: ").strip()
            if query:
                chat_query(query)
            else:
                print("The question cannot be empty.")
        
        elif opcion == '0':
            print("\nExiting..")
            break
        
        else:
            print("\nInvalid option. Please select a number between 0 and 4.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()

