#!/usr/bin/env python3
import argparse
import logging
import os
import requests
import Mongo_db.data_mongo.eraseAll as eraseAll


# Create and configure loggers that write to separate files.
def setup_logger(name, filename):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(filename)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger

# Setup loggers for users and patients
users_log = setup_logger("users", "users.log")
patients_log = setup_logger("patients", "patients.log")

# API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8003")
# Assignation of the endpoints for users and patients
USERS_API_URL = f"{API_BASE_URL}/users"
PATIENTS_API_URL = f"{API_BASE_URL}/patients"


def print_user_patient(obj, indent=0):
    # Recursive function to print nested dictionaries and lists. 
    prefix = " " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            print(f"{prefix}{k}:")
            print_user_patient(v, indent + 4)

    elif isinstance(obj, list):
        for item in obj:
            print(f"{prefix}-")
            print_user_patient(item, indent + 4)

    else:
        print(f"{prefix}{obj}")

    if indent == 0:
        print("=" * 50)

# Print all users
def list_users():
    users_log.info("Requesting list of all users")
    response = requests.get(USERS_API_URL)
    # If we were able to get the users
    if response.ok:
        users = response.json()
        users_log.info(f"Successfully retrieved {len(users)} users")
        print(f"\nFinded {len(users)} users:\n")
        for u in users:
            print_user_patient(u)
    else:
        users_log.error(f"Failed to retrieve users: {response.status_code} - {response.text}") 
        print(f"Error: {response.status_code} - {response.text}")

# Get users by their user id.
def get_user_by_id(uid):
    users_log.info(f"Requesting user by ID: {uid}")
    response = requests.get(f"{USERS_API_URL}/{uid}")
    #Case that the user exists.
    if response.ok:
        users_log.info(f"Successfully retrieved user by ID: {uid}")
        print("\nUser found:\n")
        # Print the user information that was found.
        print_user_patient(response.json())
    else:
        users_log.error(f"Failed to retrieve user by ID {uid}: {response.status_code} - {response.text}")
        print(f"Error: {response.status_code} - {response.text}")

#Update user information
def update_user(uid):
    users_log.info(f"Requesting update for user ID: {uid}")
    url = f"{USERS_API_URL}/{uid}"
    old = requests.get(url)
    if not old.ok:
        users_log.error(f"User not found for update: {uid}")
        print("User not found.")
        return
    # Get the old user information as a JSON object.
    old = old.json()
    users_log.info(f"Current user data for update: {old}")
    print("\n Current user:")
    print_user_patient(old)

    print("\nEnter new values, click enter to keep current information:\n")

    fields = [
        "user_id",
        "name",
        "role",
        "specialty",
        "email",
        "password_hash",
        "active",
        "created_at",
    ]

    new = {}
    for f in fields:
        # Get new value..
        cur = old.get(f)
        val = input(f"  {f} (actual: {cur}): ")
        # If the value is blank, we keep the old one.
        if val == "":
            new[f] = cur
        else:
            # Convert active into boolean.
            if f == "active":
                new[f] = (val.lower() == "true")
            else:
                new[f] = val
    # Send the update request with the new information in JSON format.
    users_log.info(f"Sending update request for user ID: {uid} with data: {new}")
    response = requests.put(url, json=new)

    if response.ok:
        users_log.info(f"Successfully updated user ID: {uid}")
        print("\nUser updated:\n")
        print_user_patient(response.json())
    else:
        users_log.error(f"Failed to update user ID {uid}: {response.status_code} - {response.text}")
        print(f"Error: {response.status_code} - {response.text}")

# Delete a user by their user id.
def delete_user(uid):
    users_log.info(f"Requesting deletion of user ID: {uid}")
    print(f"\nAre you sure you want to delete user {uid}? (y/n): ", end="")
    confirm = input().strip().lower()
    
    if confirm in ['y', 'yes']:
        # Make a delete request to the api and save the response
        response = requests.delete(f"{USERS_API_URL}/{uid}")
        if response.ok:
            users_log.info(f"Successfully deleted user ID: {uid}")
            print(f"User {uid} deleted.")
        else:
            users_log.error(f"Failed to delete user ID {uid}: {response.status_code} - {response.text}")
            print(f"Error: {response.status_code} - {response.text}")

        return
    users_log.info(f"User deletion cancelled for user ID: {uid}")
    print("Operation cancelled.")
    return
   
# Print patients-----------------------------------------------------------------
def list_patients(diagnosis=None, min_age=None, max_age=None):
    patients_log.info("Requesting list of patients")
    params = {}
    # Cases were user provided filters.
    if diagnosis:
        params["diagnosis"] = diagnosis
    if min_age is not None:
        params["min_age"] = min_age
    if max_age is not None:
        params["max_age"] = max_age
   
   # Make the get request with the filters as parameters.
    response = requests.get(PATIENTS_API_URL, params=params)

    if response.ok:
        patients_log.info(f"Successfully retrieved {len(response.json())} patients")
        patients = response.json()
        print(f"\nFinded {len(patients)} patients:\n")
        for p in patients:
            print_user_patient(p)
    else:
        patients_log.error(f"Failed to retrieve patients: {response.status_code} - {response.text}")
        print(f"Error: {response.status_code} - {response.text}")

# Get patients by patient_id
def get_patient_by_id(pid):
    patients_log.info(f"Requesting patient by ID: {pid}")
    # Make a get request to the api with the patient id.
    response = requests.get(f"{PATIENTS_API_URL}/{pid}")
    if response.ok:
        patients_log.info(f"Successfully retrieved patient by ID: {pid}")
        print("\nPatient found:\n")
        print_user_patient(response.json())
    else:
        patients_log.error(f"Failed to retrieve patient by ID {pid}: {response.status_code} - {response.text}")
        print(f"Error: {response.status_code} - {response.text}")

def find_patients_by_doctor(doctor_id):
    patients_log.info(f"Requesting patients by doctor ID: {doctor_id}")
    params = {"primary_doctor_id": doctor_id}
    response = requests.get(PATIENTS_API_URL, params=params)
    
    if response.ok:
        patients_log.info(f"Successfully retrieved patients by doctor ID: {doctor_id}")
        patients = response.json()
        print(f"\nFound {len(patients)} patients:\n")
        for p in patients:
            print_user_patient(p)
    else:
        patients_log.error(f"Failed to retrieve patients by doctor ID {doctor_id}: {response.status_code} - {response.text}")
        print(f"Error: {response.status_code} - {response.text}")

def find_patients_by_medication(medication):
    patients_log.info(f"Requesting patients by medication: {medication}")
    params = {"medication": medication}
    response = requests.get(PATIENTS_API_URL, params=params)
    
    if response.ok:
        patients_log.info(f"Successfully retrieved patients by medication: {medication}")
        patients = response.json()
        print(f"\nFound {len(patients)} patients:\n")
        for p in patients:
            print_user_patient(p)
    else:
        patients_log.error(f"Failed to retrieve patients by medication {medication}: {response.status_code} - {response.text}")
        print(f"Error: {response.status_code} - {response.text}")

def search_patients_text(query):
    patients_log.info(f"Requesting patients by text search: {query}")
    params = {"q": query}
    response = requests.get(PATIENTS_API_URL, params=params)
    
    if response.ok:
        patients_log.info(f"Successfully retrieved patients by text search: {query}")
        patients = response.json()
        print(f"\nFound {len(patients)} patients:\n")
        for p in patients:
            print_user_patient(p)
    else:
        patients_log.error(f"Failed to retrieve patients by text search {query}: {response.status_code} - {response.text}")
        print(f"Error: {response.status_code} - {response.text}")





# Update a patient
def update_patient(pid):
    patients_log.info(f"Requesting update for patient ID: {pid}")
    url = f"{PATIENTS_API_URL}/{pid}"
    # Get the old user information as a JSON object.
    old = requests.get(url)
    if not old.ok:
        patients_log.error(f"Patient not found for update: {pid}")
        print("Error: Patient not found.")
        return

    old = old.json()
    print("\nCurrent patient:")
    print_user_patient(old)

    print("\nEnter new values, click enter to keep current information:\n")

    simple_fields = [
        "patient_id",
        "gender",
        "age",
        "primary_doctor_id",
        "created_at",
        "updated_at",
        "active"
    ]

    new = {}
   
    for f in simple_fields:
        cur = old.get(f)
        val = input(f"  {f} (actual: {cur}): ")

        if val == "":
            new[f] = cur
        else:
            if f == "age":
                new[f] = int(val)
            elif f == "active":
                new[f] = (val.lower() == "true")
            else:
                new[f] = val
    # Handle nested fields separately
    print("\nName:")
    new["name"] = {
        "first": input(f"  first (actual: {old['name']['first']}): ") or old["name"]["first"],
        "last": input(f"  last (actual: {old['name']['last']}): ") or old["name"]["last"]
    }
    print("\nContact:")
    new["contact"] = {
        "phone": input(f"  phone (actual: {old['contact']['phone']}): ") or old["contact"]["phone"],
        "email": input(f"  email (actual: {old['contact']['email']}): ") or old["contact"]["email"],
        "address": input(f"  address (actual: {old['contact']['address']}): ") or old["contact"]["address"],
    }
    print("\nAllergies (comma separated):")
    allergies = input(f"  (actual: {old['allergies']}): ")
    new["allergies"] = allergies.split(",") if allergies else old["allergies"]

    print("\nMedical records (keeping current records)")
    new["medical_records"] = old["medical_records"]
    # Send the update request with the new information in JSON format.
    response = requests.put(url, json=new)
    if response.ok:
        patients_log.info(f"Successfully updated patient ID: {pid}")
        print("\n Patient updated:\n")
        print_user_patient(response.json())
    else:
        patients_log.error(f"Failed to update patient ID {pid}: {response.status_code} - {response.text}")
        print(f"Error: {response.status_code} - {response.text}")

# Delete a patient
def delete_patient(pid):
    patients_log.info(f"Requesting deletion of patient ID: {pid}")
    print(f"\nAre you sure you want to delete patient {pid}? (y/n): ", end="")
    confirm = input().strip().lower()
    
    if confirm in ['y', 'yes']:
        # Making a delete request to the api and saving the response.
        response = requests.delete(f"{PATIENTS_API_URL}/{pid}")
        if response.ok:
            patients_log.info(f"Successfully deleted patient ID: {pid}")
            print(f"Patient {pid} deleted successfully.")
        else:
            patients_log.error(f"Failed to delete patient ID {pid}: {response.status_code} - {response.text}")
            print(f"Error: {response.status_code} - {response.text}")
        return
    
    patients_log.info(f"Patient deletion cancelled for patient ID: {pid}")
    print("Operation cancelled.")
    return

# Pipelines / Aggregations ------------------------------------------------------
#vFilter patients with advanced criteria as diagnosis and age range
def patients_filtered(diagnosis=None, min_age=None, max_age=None, skip=0, limit=50):
    patients_log.info("Requesting filtered patients")
    params = {}
    if diagnosis:
        params["diagnosis"] = diagnosis
    if min_age is not None:
        params["min_age"] = min_age
    if max_age is not None:
        params["max_age"] = max_age
    params["skip"] = skip
    params["limit"] = limit
    # Endpoint that executes the filtered pipeline
    url = f"{API_BASE_URL}/patients/filtered"
    # Make the get request with the filters as parameters.
    response = requests.get(url, params=params)
    
    if response.ok:
        patients_log.info("Successfully retrieved filtered patients")
        results = response.json()
        print(f"\nFinded {len(results)} patients:\n")
        for r in results:
            print_user_patient(r)
    else:
        patients_log.error(f"Failed to retrieve filtered patients: {response.status_code} - {response.text}")
        print(f"Error: {response.status_code} - {response.text}")

# Count the amount of diagnoses
def diagnosis_count():
    patients_log.info("Requesting diagnosis count")
    # Endpoint that executes the count pipeline
    url = f"{API_BASE_URL}/patients/diagnosis-count"
    response = requests.get(url)
    
    if response.ok:
        patients_log.info("Successfully retrieved diagnosis count")
        results = response.json()
        print(f"\nDiagnosis count (Total: {len(results)}):\n")
        #Align output in columns
        print(f"{'Diagnosis':<40} {'Total':>10}")
        print("=" * 52)
        for r in results:
            print(f"{r['diagnosis']:<40} {r['total']:>10}")
        print("=" * 52)
    else:
        patients_log.error(f"Failed to retrieve diagnosis count: {response.status_code} - {response.text}")
        print(f"Error: {response.status_code} - {response.text}")

# Pipline latest patients labs 
def patient_latest_labs(patient_id, limit=5):
    patients_log.info(f"Requesting latest labs for patient ID: {patient_id}")
    # Endpoint that executes the latest labs pipeline
    url = f"{API_BASE_URL}/patients/{patient_id}/labs/latest"
    params = {"limit": limit}
    response = requests.get(url, params=params)
    if response.ok:
        patients_log.info(f"Successfully retrieved latest labs for patient ID: {patient_id}")
        print(f"\nLast {limit} laboratory results:\n")
        print_user_patient(response.json())
    else:
        patients_log.error(f"Failed to retrieve latest labs for patient ID {patient_id}: {response.status_code} - {response.text}")
        print(f"Error: {response.status_code} - {response.text}")

#Menu---------------------------------------------------------------------------
def show_menu():
    
    print("\n" + "=" * 70)
    print(" MEDICAL API - CLIENT MENU")
    print("=" * 70)
    print("\nUSERS:")
    print("  1. List all users")
    print("  2. Find user by ID")
    print("  3. Update user")
    print("  4. Delete user")
    
    print("\n PATIENTS:")
    print("  5. List all patients")
    print("  6. Find patients with filters")
    print("  7. Find patient by ID")
    print("  8. Find patients by doctor ID")  
    print("  9. Find patients by medication")  
    print("  10. Search patients by name/diagnosis") 
    print("  11. Update patient")
    print("  12. Delete patient")
    
    print("\nPIPELINES / AGGREGATIONS:")
    print("  13. Advanced search (filtered)")
    print("  14. Diagnosis count")
    print("  15. Latest labs of a patient")
    print("  16. Delete all data")
    
    print("\n  0. Exit")
    print("=" * 70)


# MAIN------------------------------------------------------------------------------------------------
def main():
    while True:
        show_menu()
        option = input("\nSelect an option: ").strip()

        try:
            if option == "0":
                print("\nGoodbye!")
                break
            
            elif option == "1":
                list_users()
            
            elif option == "2":
                uid = input("Insert user_id: ").strip()
                get_user_by_id(uid)
            
            elif option == "3":
                uid = input("Insert user_id: ").strip()
                update_user(uid)
            
            elif option == "4":
                uid = input("Insert user_id: ").strip()
                delete_user(uid)
            
            elif option == "5":
                list_patients()
            
            elif option == "6":
                print("\nFilters (leave blank to skip):")
                diagnosis = input("  Diagnosis: ").strip() or None
                min_age_str = input("  Minimum age: ").strip()
                max_age_str = input("  Maximum age: ").strip()
                
                min_age = int(min_age_str) if min_age_str else None
                max_age = int(max_age_str) if max_age_str else None
                
                list_patients(diagnosis, min_age, max_age)
            
            elif option == "7":
                pid = input("Insert patient_id: ").strip()
                get_patient_by_id(pid)
            elif option == "8":
                doctor_id = input("Insert doctor ID: ").strip()
                find_patients_by_doctor(doctor_id)

            elif option == "9":
                medication = input("Insert medication name: ").strip()
                find_patients_by_medication(medication)

            elif option == "10":
                query = input("Insert search term (name or diagnosis): ").strip()
                search_patients_text(query)

            elif option == "11":
                pid = input("Insert patient_id: ").strip()
                update_patient(pid)
            
            elif option == "12":
                pid = input("Insert patient_id: ").strip()
                delete_patient(pid)
            
            elif option == "13":
                print("\nFilters for advanced search (leave blank to skip):")
                diagnosis = input("  Diagnosis: ").strip() or None
                min_age_str = input("  Minimum age: ").strip()
                max_age_str = input("  Maximum age: ").strip()
                skip_str = input("  Skip (default 0): ").strip()
                limit_str = input("  Limit (default 50): ").strip()
                
                min_age = int(min_age_str) if min_age_str else None
                max_age = int(max_age_str) if max_age_str else None
                skip = int(skip_str) if skip_str else 0
                limit = int(limit_str) if limit_str else 50
                
                patients_filtered(diagnosis, min_age, max_age, skip, limit)
            
            elif option == "14":
                diagnosis_count()
            
            elif option == "15":
                pid = input("Insert patient_id: ").strip()
                limit_str = input("Limit of results (default 5): ").strip()
                limit = int(limit_str) if limit_str else 5
                patient_latest_labs(pid, limit)
            elif option == "16":
                response = input("Are you sure you want to delete all data in the MongoDB database? (y/n) ").strip()
                if response == "y":
                   eraseAll.erase_data()
                else:
                    print("Returning without deleting data..")
            else:
                print("\nInvalid option, try again.")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

        input("\nPress Enter to continue...")
    return


if __name__ == "__main__":
    main()