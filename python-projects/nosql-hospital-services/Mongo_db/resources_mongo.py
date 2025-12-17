#!/usr/bin/env python3
import falcon
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import traceback

# Creation of pipelines 
# Filter patients
def pipeline_filter_patients(diagnosis=None, min_age=None, max_age=None, skip=0, limit=50):
    match = {}

    if diagnosis:
        match["medical_records.diagnosis"] = diagnosis

    if min_age is not None or max_age is not None:
        match["age"] = {}
        if min_age is not None:
            # Using greater equal than or equal operator
            match["age"]["$gte"] = min_age
        if max_age is not None:
            # Using less equal than or equal operator
            match["age"]["$lte"] = max_age
 
    pipeline = []

    if match:
        pipeline.append({"$match": match})

    pipeline.append({
        "$project": {
            "patient_id": 1,
            "name": 1,
            "age": 1,
            "latest_record": {"$arrayElemAt": ["$medical_records", -1]}
        }
    })

    pipeline.append({"$sort": {"latest_record.date": -1}})
    pipeline.append({"$skip": skip})
    pipeline.append({"$limit": limit})

    return pipeline

# Pipeline count diagnosis
def pipeline_count_by_diagnosis():
    #Using unwind to separate the medical records
    #Grouping medical records by diagnosis and sum them, then print the total in ascendant way
    pipeline = [
        {"$unwind": "$medical_records"},
        {"$group": {
            "_id": "$medical_records.diagnosis",
            "total": {"$sum": 1}
        }},
        {"$sort": {"total": -1}}
    ]
    return pipeline

#Pipeline the latest lab
def pipeline_latest_lab_results(patient_id, limit=5):
    # Getting the latest lab results for a specific patient

    pipeline = [
        {"$match": {"patient_id": patient_id}},
        {"$project": {
            "name": 1,
            "latest_lab_results": {
                "$slice": ["$medical_records.lab_results", -limit]
            }
        }}
    ]
    return pipeline

#Classes---------------------------------------------------------
class PatientsResource:
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        query = {}
        diagnosis = req.get_param('diagnosis')
        min_age = req.get_param_as_int('min_age')
        max_age = req.get_param_as_int('max_age')

        text_query = req.get_param('q')

        if text_query:
            # Text search has priority over other filters
            #Using meta to get the text score and sort by it
            cursor = self.db.patients.find(
                {"$text": {"$search": text_query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})])
        else:
            if diagnosis:
                query["medical_records.diagnosis"] = diagnosis
            if min_age is not None or max_age is not None:
                query["age"] = {}
                if min_age is not None:
                    query["age"]["$gte"] = min_age
                if max_age is not None:
                    query["age"]["$lte"] = max_age

            #Search by doctor id
            doctor_id = req.get_param('primary_doctor_id')
            if doctor_id:
                query["primary_doctor_id"] = doctor_id

            #Search by medication name
            medication = req.get_param('medication')
            if medication:
                query["medical_records.medications.name"] = medication

            #Seacrh by name or diagnosis
            if text_query:
                cursor = self.db.patients.find(
                    {"$text": {"$search": text_query}},
                    {"score": {"$meta": "textScore"}}
                ).sort([("score", {"$meta": "textScore"})])
            else:
                cursor = self.db.patients.find(query)
        
        patients = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            patients.append(doc)

        resp.media = patients
        resp.status = falcon.HTTP_200

    async def on_post(self, req, resp):
        try:
            data = await req.get_media()
            result = self.db.patients.insert_one(data)
            data["_id"] = str(result.inserted_id)

            resp.media = data
            resp.status = falcon.HTTP_201
        except Exception as e:   
            if isinstance(e, DuplicateKeyError):
                resp.status = falcon.HTTP_409
                resp.media = {"error": "Patient already exists (duplicate key)"}
            else:
                print(f"ERROR in PatientsResource.on_post: {e}")
                print(traceback.format_exc())
                raise
        
    async def on_delete(self,req, resp):
        self.db.patients.delete_many({})
        resp.status = falcon.HTTP_200
        resp.media = {"status": "all patients deleted"}


class PatientResource:
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp, patient_id):
        doc = self.db.patients.find_one({"patient_id": patient_id})

        if not doc:
            resp.status = falcon.HTTP_404
            return

        doc["_id"] = str(doc["_id"])
        resp.media = doc
        resp.status = falcon.HTTP_200

    async def on_put(self, req, resp, patient_id):
        try:
            data = await req.get_media()
            data = validate_data(data, patient_types)

            result = self.db.patients.update_one(
                {"patient_id": patient_id},
                {"$set": data}
            )

            if result.matched_count == 0:
                resp.status = falcon.HTTP_404
                return

            updated = self.db.patients.find_one({"patient_id": patient_id})
            updated["_id"] = str(updated["_id"])

            resp.media = updated
            resp.status = falcon.HTTP_200
        except Exception as e:
            print(f"ERROR in PatientResource.on_put: {e}")
            print(traceback.format_exc())
            raise

    async def on_delete(self, req, resp, patient_id):
        deleted = self.db.patients.delete_one({"patient_id": patient_id})

        if deleted.deleted_count == 0:
            resp.status = falcon.HTTP_404
            return

        resp.media = {"message": "Patient deleted"}
        resp.status = falcon.HTTP_200


class UsersResource:
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        email = req.get_param('email')
        text_query = req.get_param('q')
        
        #Search by email
        if email:
            doc = self.db.users.find_one({"email": email})
            if not doc:
                resp.status = falcon.HTTP_404
                resp.media = {"error": "User not found"}
                return
            doc["_id"] = str(doc["_id"])
            resp.media = doc
            resp.status = falcon.HTTP_200
            return
        
        # Search by user name 
        if text_query:
            cursor = self.db.users.find(
                {"$text": {"$search": text_query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})])
        else:
            # List all users
            cursor = self.db.users.find({}) 
        
        users = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            users.append(doc)

        resp.media = users
        resp.status = falcon.HTTP_200

    async def on_post(self, req, resp):
        try:
            data = await req.get_media()
            result = self.db.users.insert_one(data)
            data["_id"] = str(result.inserted_id)

            resp.media = data
            resp.status = falcon.HTTP_201
        except Exception as e:
            if isinstance(e, DuplicateKeyError):
                resp.status = falcon.HTTP_409
                resp.media = {"error": "User already exists (duplicate key)"}
            else:
                print(f"ERROR in UsersResource.on_post: {e}")
                print(traceback.format_exc())
                raise
    async def on_delete(self, req, resp):
        self.db.users.delete_many({})
        resp.status = falcon.HTTP_200
        resp.media = {"status": "all users deleted"}

class UserResource:
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp, user_id):
        doc = self.db.users.find_one({"user_id": user_id})

        if not doc:
            resp.status = falcon.HTTP_404
            return

        doc["_id"] = str(doc["_id"])
        resp.media = doc
        resp.status = falcon.HTTP_200

    async def on_put(self, req, resp, user_id):
        try:
            data = await req.get_media()
            data = validate_data(data, user_types)

            result = self.db.users.update_one(
                {"user_id": user_id},
                {"$set": data}
            )

            if result.matched_count == 0:
                resp.status = falcon.HTTP_404
                return

            updated = self.db.users.find_one({"user_id": user_id})
            updated["_id"] = str(updated["_id"])

            resp.media = updated
            resp.status = falcon.HTTP_200
        except Exception as e:
            print(f"Error in UserResource.on_put: {e}")
            print(traceback.format_exc())
            raise

    async def on_delete(self, req, resp, user_id):
        deleted = self.db.users.delete_one({"user_id": user_id})

        if deleted.deleted_count == 0:
            resp.status = falcon.HTTP_404
            return

        resp.media = {"message": "User deleted"}
        resp.status = falcon.HTTP_200


class PatientsFilteredResource:
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        diagnosis = req.get_param("diagnosis")
        min_age = req.get_param_as_int("min_age")
        max_age = req.get_param_as_int("max_age")
        skip = req.get_param_as_int("skip") or 0
        limit = req.get_param_as_int("limit") or 50

        pipeline = pipeline_filter_patients(diagnosis, min_age, max_age, skip, limit)
        cursor = self.db.patients.aggregate(pipeline)

        results = []
        for doc in cursor:
            doc["_id"] = str(doc.get("_id", ""))
            results.append(doc)

        resp.media = results
        resp.status = falcon.HTTP_200


class DiagnosisCountResource:
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp):
        pipeline = pipeline_count_by_diagnosis()
        cursor = self.db.patients.aggregate(pipeline)

        results = []
        for doc in cursor:
            results.append({
                "diagnosis": doc["_id"],
                "total": doc["total"]
            })

        resp.media = results
        resp.status = falcon.HTTP_200


class PatientLatestLabsResource:
    def __init__(self, db):
        self.db = db

    async def on_get(self, req, resp, patient_id):
        limit = req.get_param_as_int("limit") or 5

        pipeline = pipeline_latest_lab_results(patient_id, limit)
        cursor = list(self.db.patients.aggregate(pipeline))

        if not cursor:
            resp.status = falcon.HTTP_404
            resp.media = {"error": "Patient not found"}
            return

        result = cursor[0]
        result["_id"] = str(result.get("_id", ""))

        resp.media = result
        resp.status = falcon.HTTP_200

# Schemas--------------------------------------------------------------
user_types = {
    "user_id": str,
    "name": str,
    "role": str,          
    "specialty": str,
    "email": str,
    "password_hash": str,
    "active": bool,
    "created_at": str
}

patient_types = {
    "patient_id": str,
    "name": {
        "first": str,
        "last": str
    },
    "gender": str,
    "age": int,
    "contact": {
        "phone": str,
        "email": str,
        "address": str
    },
    "allergies": [str],
    "primary_doctor_id": str,
    "medical_records": [{
        "record_id": str,
        "date": str,
        "diagnosis": str,
        "diagnosis_code": str,
        "doctor_id": str,
        "notes": str,
        "medications": [{
            "med_id": str,
            "name": str,
            "dose": str,
            "frequency": str
        }],
        "lab_results": [{
            "test": str,
            "result": float,
            "unit": str,
            "date": str
        }]
    }],
    "created_at": str,
    "updated_at": str,
    "active": bool
}

def validate_data(data, schema, path="root"):
    #For each field inn the schema, we check if it exists in the data and if its type is correct.
    for field, expected in schema.items():
        full_path = f"{path}.{field}"

        if field not in data:
            raise falcon.HTTPBadRequest(description=f"{full_path} is required.")

        value = data[field]

        # Validate dates
        if field in ["date", "created_at", "updated_at"]:
            if not isinstance(value, str):
                raise falcon.HTTPBadRequest( description=f"{full_path} must be a ISO string.")
            try:
                #Try to replace Z with +00:00 to make it compatible with fromisoformat
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except:
                raise falcon.HTTPBadRequest(description=f"{full_path} must be a valid ISO date.")
            continue

        # Validate simple types (str, int, bool, float)
        if isinstance(expected, type):
            try:
                if expected == bool:
                    data[field] = str(value).lower() in ['true'] \
                        if isinstance(value, str) else bool(value)
                else:
                    data[field] = expected(value)
            except:
                raise falcon.HTTPBadRequest(description=f"{full_path} must be {expected.__name__}.")
            continue

        # Validate dictionaries
        if isinstance(expected, dict):
            if not isinstance(value, dict):
                raise falcon.HTTPBadRequest(description=f"{full_path} must be an object.")
            validate_data(value, expected, full_path)
            continue

        # Validate lists
        if isinstance(expected, list):
            if not isinstance(value, list):
                raise falcon.HTTPBadRequest(description=f"{full_path} must be an array.")

            item_schema = expected[0] if expected else None

            for idx, item in enumerate(value):
                item_path = f"{full_path}[{idx}]"

                if isinstance(item_schema, dict):
                    if not isinstance(item, dict):
                        raise falcon.HTTPBadRequest(description=f"{item_path} must be an object.")
                    validate_data(item, item_schema, item_path)

                elif isinstance(item_schema, type):
                    try:
                        if item_schema == bool:
                            value[idx] = str(item).lower() in ['true']
                        else:
                            value[idx] = item_schema(item)
                    except:
                        raise falcon.HTTPBadRequest(description=f"{item_path} must be {item_schema.__name__}.")

            continue

    return data
