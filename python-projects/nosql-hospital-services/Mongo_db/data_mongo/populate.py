#!/usr/bin/env python3
import csv
import os
import json
import requests

BASE_URL = "http://localhost:8003"

#Populate all users 
def load_users():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "users.csv")
    with open(csv_path) as fd:
        # Read CSV file
        users_csv = csv.DictReader(fd)
        for user in users_csv:
            # Convert active/inactive into boolean
            user["active"] = user["active"] == "True"
            # Check if the user already exist
            resp = requests.get(BASE_URL + f"/users/{user['user_id']}")
            if resp.ok:
                print(f"User already exists, skipping: {user['user_id']}")
                continue
            # Post user to the API as a json and check the response.
            x = requests.post(BASE_URL + "/users", json=user)

            if not x.ok:
                print(f"Failed to post user: {user['user_id']} -> {x.status_code} {x.text}")
            else:
                print(f"User uploaded: {user['user_id']}")

#Populate all patients 
def load_patients():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "patients.csv")
    with open(csv_path) as fd:
        patients_csv = csv.DictReader(fd)
        for p in patients_csv:
            # We convert into appropriate types (int, bool, dict, list)
            p["age"] = int(p["age"])
            p["active"] = p["active"] == "True"
            p["name"] = {"first": p["name_first"], "last": p["name_last"]}
            # After assign the name dict, we remove the old name fields. 
            del p["name_first"]
            del p["name_last"]

            p["contact"] = {
                "phone": p["phone"],
                "email": p["email"],
                "address": p["address"],
            }
            del p["phone"]
            del p["email"]
            del p["address"]

            #We convert a string into a python list and to a python dictionary with json.loads.
            p["allergies"] = json.loads(p["allergies"])
            p["medical_records"] = json.loads(p["medical_records"])
            #Check if the patient already exist
            resp = requests.get(BASE_URL + f"/patients/{p['patient_id']}")
            if resp.ok:
                print(f"Patient already exists, skipping: {p['patient_id']}")
                continue
           
            # Post a patient to the API as a json and check the response.
            x = requests.post(BASE_URL + "/patients", json=p)

            if not x.ok:
                print(f"Failed to post patient: {p['patient_id']} -> {x.status_code} {x.text}")
            else:
                print(f"Patient uploaded: {p['patient_id']}")


def main():
    print("Uploading users...")
    load_users()
    print("Uploading patients...")
    load_patients()


if __name__ == "__main__":
    main()
