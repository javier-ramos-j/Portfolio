#!/usr/bin/env python3
import falcon.asgi
from pymongo import MongoClient
import logging

from Mongo_db.resources_mongo import PatientsResource, PatientResource
from Mongo_db.resources_mongo import UsersResource, UserResource
from Mongo_db.resources_mongo import PatientsFilteredResource, DiagnosisCountResource, PatientLatestLabsResource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoggingMiddleware:
    async def process_request(self, req, resp):
        logger.info(f"[REQUEST] {req.method} {req.uri}")

    async def process_response(self, req, resp, resource, req_succeeded):
        logger.info(f"[RESPONSE] {resp.status} {req.method} {req.uri}")


# Initialize MongoDB client and database 
client = MongoClient("mongodb://localhost:8002/")
db = client.medical_api   


# Create the indexes for users
db.users.create_index([("email", 1)], unique=True)
db.users.create_index([("name", "text")])

# Create the indexes for patients
db.patients.create_index([("patient_id", 1)], unique=True)
db.patients.create_index([("primary_doctor_id", 1)])
db.patients.create_index([("age", 1)])
db.patients.create_index([("medical_records.medications.name", 1)])
db.patients.create_index([("medical_records.diagnosis", 1), ("age", 1)])
db.patients.create_index([
   ("name.first", "text"),
   ("name.last", "text"),
   ("medical_records.diagnosis", "text")
])

# Create a Falcon application with a middleware that is going to logg every request and response. 
app = falcon.asgi.App(middleware=[LoggingMiddleware()])

# Create the resources that are going to handle the requests (endpoints), with the db conection. 
patients_resource = PatientsResource(db)
patient_resource = PatientResource(db)
users_resource = UsersResource(db)
user_resource = UserResource(db)
patients_filtered_resource = PatientsFilteredResource(db)
diagnosis_count_resource = DiagnosisCountResource(db)
patient_latest_labs_resource = PatientLatestLabsResource(db)

# Connect the specific urls with their resources (classes that handle the requests).
app.add_route("/patients/filtered", patients_filtered_resource)
app.add_route("/patients/diagnosis-count", diagnosis_count_resource)
app.add_route("/patients/{patient_id}/labs/latest", patient_latest_labs_resource)
app.add_route("/patients", patients_resource)
app.add_route("/patients/{patient_id}", patient_resource)
app.add_route("/users", users_resource)
app.add_route("/users/{user_id}", user_resource)
app.add_route("/patients/all", patients_resource) 


