import datetime
import json
import pydgraph
import csv

#Schema deefinition: this part is the base of our dgraph model, we defined properties nodes, nodes
# and the relationship between them :D
#Furtheremore, we defined the necessary indexes based on our queries
def set_schema(client):
    schema = """
        type PATIENT {
            name
            last_name
            age
            genre
            patient_id
            allergies
            height
            weight
            telephone
            email
            assigned_to
            has_diagnosis
            follows_treatment
            receives_medication
            has_vital_sign
            has_visitor
        }

        type DOCTOR {
            doctor_id
            name
            last_name
            specialty
            email
            license_id
            applies_treatment
        }

        type DIAGNOSIS {
            disease_name
            icd10_code
            diagnosis_id
        }

        type TREATMENT {
            treatment_name
            start_date
            end_date
            contains_medication
            common_for_diagnosis
        }

        type MEDICATION {
            trade_name
            dosage
            frequency
            medication_id
        }

        type VITALSIGNREADING {
            type
            value
            timestamp
        }

        type VISITOR {
            visitor_name
            arrival_time
            exit_time
        }

        patient_id: string @index(exact) .
        doctor_id: string @index(exact) .

        name: string @index(term) .
        last_name: string @index(term) .

        age: int @index(int) .
        genre: string .
        allergies: string .
        height: float .
        weight: float .
        telephone: string .
        email: string .

        specialty: string .
        license_id: string @index(exact) .

        disease_name: string @index(term) .
        icd10_code: string @index(exact) .
        diagnosis_id: string @index(exact) .

        treatment_name: string @index(term) .
        start_date: datetime .
        end_date: datetime .
        treatment_id: string @index(exact) .

        trade_name: string @index(term) .
        dosage: string .
        frequency: string .
        medication_id: string @index(exact) .

        type: string .
        value: float .
        timestamp: datetime @index(day) .

        visitor_name: string .
        arrival_time: datetime @index(day) .
        exit_time: datetime @index(day) .

        # Relationships

        assigned_to: uid .                        
        has_diagnosis: uid @reverse @count .      
        follows_treatment: uid @reverse @count .  
        receives_medication: uid .                
        contains_medication: uid .                
        common_for_diagnosis: uid .               
        applies_treatment: uid .                  
        has_vital_sign: uid .                     
        has_visitor: uid .                        
    """
    return client.alter(pydgraph.Operation(schema=schema))

#Data loadind function 
def create_data(client):
    #First, we load the base catalogs 
    print("Loading base catalogs (doctors, diagnoses, medications, etc)...") #these are our nodes on the diagram 
    doctors_map = load_doctors(client, "data/doctors.csv")
    diagnoses_map = load_diagnoses(client, "data/diagnoses.csv")
    medications_map = load_medications(client, "data/medications.csv")
    treatments_map = load_treatments(client, "data/treatments.csv", diagnoses_map, medications_map) #Treatments depends on diagnoses and medications
    patients_map = load_patients(client, "data/patients.csv", doctors_map) #Patients 
    load_vital_signs(client, "data/vital_signs.csv", patients_map)
    load_visitors(client, "data/visitors.csv", patients_map)

    print("Loading relationships...") #these have the explicit relationship on the csv 
    load_doctor_treatments(client, "data/doctor_treatments.csv", doctors_map, treatments_map)
    load_patient_diagnoses(client, "data/patient_diagnoses.csv", patients_map, diagnoses_map)
    load_patient_medications(client, "data/patient_medications.csv", patients_map, medications_map)
    load_patient_treatments(client, "data/patient_treatments.csv", patients_map, treatments_map)

    print("Hospital data loaded successfully :D!")
    print("Now, you can navegate through our system...")
#----

#---From here we can see our loaders :) ----
#Loaders are functions responsable for reading the csv files and transforming in functional nodes.

#We decided to keep each loader separate because it makes the project 
#easier to read, mantain, and debug.

#Each function performs 3 basic tasks:
# - Read its specific csv file.
# - Transform each row into a dictionary following the dgraph format (including type and attributes).
# - Insert data through mutation and, when needed, return an ID -> UID map that is used to build relationships
# between nodes in other loaders.

#the general structure of the loaders are defined in the patient loader example.

def load_doctors(client, file_path):
    txn = client.txn()
    try:
        data_list = []
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                doctor_data = {
                    "dgraph.type": "DOCTOR",
                    "doctor_id": row["doctor_id"],
                    "name": row["name"],
                    "last_name": row["last_name"],
                    "specialty": row["specialty"],
                    "email": row["email"],
                    "license_id": row["license_id"],
                }
                data_list.append(doctor_data)

        txn.mutate(set_obj=data_list)
        txn.commit()
        return get_uid_map(client, "doctor_id", [d["doctor_id"] for d in data_list])
    finally:
        txn.discard()

def load_patients(client, file_path, doctors_map):
    #loads patient information from csv file and links each patient to their primary doctor
    txn = client.txn() # list that hold all patients nodes before sending them to dgraph
    try:
        data_list = []

        with open(file_path, newline="", encoding="utf-8") as f: #open the patients csv file safely
            reader = csv.DictReader(f) #use dictreader so each row is a dict with column names as keys
            for row in reader:
                #build the patient node with the dgraph structure and attributes
                patient_data = {
                    "dgraph.type": "PATIENT",
                    "patient_id": row["patient_id"],
                    "name": row["name"],
                    "last_name": row["last_name"],
                    "genre": row["genre"],
                    "age": int(row["age"]) if row["age"] else None,
                    "telephone": row["telephone"],
                    "email": row["email"],
                    "allergies": row["allergies"],
                }
                #try to link the patient with their primary doctor using the doctors_map
                doc_id = row.get("primary_doctor_id") #read the doctor id form the csv row
                if doc_id and doc_id in doctors_map: # chheck that the doctor ID exists in the preloaded map
                    patient_data["assigned_to"] = {"uid": doctors_map[doc_id]} #create the edge assigned_to using the corresponding doctor UID from Dgraph

                data_list.append(patient_data) #add this patient noode to the list to be inserted

        txn.mutate(set_obj=data_list) #send all patient nodes in a single mutation to dgraph
        txn.commit() #commit the transaction to makes changes persistent

        #build and return a map: patient_id -> uid, with this part other loader can create relationships to these patients.
        return get_uid_map(client, "patient_id", [p["patient_id"] for p in data_list])

    finally:
        txn.discard() #close/discard the transaction to free resources 


def load_diagnoses(client, file_path):
    txn = client.txn()
    try:
        data_list = []

        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                diag_data = {
                    "dgraph.type": "DIAGNOSIS",
                    "disease_name": row["disease_name"],
                    "icd10_code": row["icd10_code"],
                    "diagnosis_id": row["diagnosis_id"],
                }
                data_list.append(diag_data)

        txn.mutate(set_obj=data_list)
        txn.commit()

        return get_uid_map(client, "diagnosis_id", [d["diagnosis_id"] for d in data_list])

    finally:
        txn.discard()

def load_treatments(client, file_path, diagnoses_map, medications_map):
    txn = client.txn()
    try:
        data_list = []
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                treatment = {
                    "dgraph.type": "TREATMENT",
                    "treatment_id": row["treatment_id"],
                    "treatment_name": row["treatment_name"],
                    "start_date": row["start_date"],
                    "end_date": row["end_date"],
                }

                dxid = row.get("diagnosis_id")
                if dxid and dxid in diagnoses_map:
                    treatment["common_for_diagnosis"] = {"uid": diagnoses_map[dxid]}

                mid = row.get("medication_id")
                if mid and mid in medications_map:
                    treatment["contains_medication"] = {"uid": medications_map[mid]}

                data_list.append(treatment)

        txn.mutate(set_obj=data_list)
        txn.commit()

        return get_uid_map(client, "treatment_id",[t["treatment_id"] for t in data_list])
    finally:
        txn.discard()

def load_patient_treatments(client, file_path, patients_map, treatments_map):
    txn = client.txn()
    try:
        mutations = []
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row["patient_id"]
                tid = row["treatment_id"]

                if pid not in patients_map or tid not in treatments_map:
                    continue

                mutations.append({
                    "uid": patients_map[pid],
                    "follows_treatment": {"uid": treatments_map[tid]}
                })

        if mutations:
            txn.mutate(set_obj=mutations)
            txn.commit()

    finally:
        txn.discard()


def load_doctor_treatments(client, file_path, doctors_map, treatments_map):
    txn = client.txn()
    try:
        mutations = []
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                did = row["doctor_id"]
                tid = row["treatment_id"]

                if did not in doctors_map or tid not in treatments_map:
                    continue

                mutations.append({
                    "uid": doctors_map[did],
                    "applies_treatment": {"uid": treatments_map[tid]}
                })

        if mutations:
            txn.mutate(set_obj=mutations)
            txn.commit()

    finally:
        txn.discard()

def load_medications(client, file_path):
    txn = client.txn()
    try:
        data_list = []

        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                med_data = {
                    "dgraph.type": "MEDICATION",
                    "medication_id": row["medication_id"],
                    "trade_name": row["trade_name"],
                    "dosage": row["dosage"],
                    "frequency": row["frequency"],
                }
                data_list.append(med_data)

        txn.mutate(set_obj=data_list)
        txn.commit()

        return get_uid_map(client, "medication_id", [m["medication_id"] for m in data_list])

    finally:
        txn.discard()


def load_patient_diagnoses(client, file_path, patients_map, diagnoses_map):
    txn = client.txn()
    try:
        mutations = []

        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row["patient_id"]
                dxid = row["diagnosis_id"]

                if pid not in patients_map or dxid not in diagnoses_map:
                    continue

                patient_uid = patients_map[pid]
                diag_uid = diagnoses_map[dxid]

                m = {
                    "uid": patient_uid,
                    "has_diagnosis": {"uid": diag_uid},
                }
                mutations.append(m)

        if mutations:
            txn.mutate(set_obj=mutations)
            txn.commit()

    finally:
        txn.discard()


def load_patient_medications(client, file_path, patients_map, medications_map):
    txn = client.txn()
    try:
        mutations = []

        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row["patient_id"]
                mid = row["medication_id"]

                if pid not in patients_map or mid not in medications_map:
                    continue

                patient_uid = patients_map[pid]
                med_uid = medications_map[mid]

                m = {
                    "uid": patient_uid,
                    "receives_medication": {"uid": med_uid},
                }
                mutations.append(m)

        if mutations:
            txn.mutate(set_obj=mutations)
            txn.commit()

    finally:
        txn.discard()


def load_vital_signs(client, file_path, patients_map):
    txn = client.txn()
    try:
        data_list = []

        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row["patient_id"]
                if pid not in patients_map:
                    continue

                vs_data = {
                    "dgraph.type": "VITALSIGNREADING",
                    "reading_id": row["reading_id"],
                    "type": row["type"],
                    "value": float(row["value"]),
                    "unit": row["unit"],
                    "timestamp": row["timestamp"],
                }

                patient_uid = patients_map[pid]

                patient_node = {
                    "uid": patient_uid,
                    "has_vital_sign": vs_data,
                }
                data_list.append(patient_node)

        if data_list:
            txn.mutate(set_obj=data_list)
            txn.commit()

    finally:
        txn.discard()


def load_visitors(client, file_path, patients_map):
    txn = client.txn()
    try:
        data_list = []

        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row["patient_id"]
                if pid not in patients_map:
                    continue

                visitor_data = {
                    "dgraph.type": "VISITOR",
                    "visitor_id": row["visitor_id"],
                    "visitor_name": row["visitor_name"],
                    "arrival_time": row["arrival_time"],
                    "exit_time": row["exit_time"],
                }

                patient_uid = patients_map[pid]

                patient_node = {
                    "uid": patient_uid,
                    "has_visitor": visitor_data,
                }
                data_list.append(patient_node)

        if data_list:
            txn.mutate(set_obj=data_list)
            txn.commit()

    finally:
        txn.discard()
#------ Loaders end here

#-- Utiliities :D --- 
# This section contains helper functions that support the main loader and query operations :)

#After inserting nodes in Dgrapg, this functions retrieves the automatically 
#generated UIDs for a given attribute (such as patient_id). 
#It returns a python dictionary mapping CSV_ID -> Dgraph UID :)
def get_uid_map(client, field, values):
    mapping = {}
    txn = client.txn(read_only=True)
    try:
        for val in set(values):
            q = f'{{ q(func: eq({field}, "{val}")) {{ uid }} }}'
            res = txn.query(q)
            json_res = json.loads(res.json)
            if json_res.get("q"):
                mapping[val] = json_res["q"][0]["uid"]
    finally:
        txn.discard()
    return mapping

#A helper for executinng read-only dgraoph queries, prints the results in a clean JSON format.
#keeps the query functions simple
def run_readonly_query(client, query, variables=None):
    txn = client.txn(read_only=True)
    try:
        res = txn.query(query, variables=variables)
        data = json.loads(res.json)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    finally:
        txn.discard()
#--- Utilities end here

#From here we can see our queries definition ---

#1 - only search a patient with their ID 
def q1_search_patient_by_id(client):
    patient_id = input("Patient ID (e.g. P001): ").strip()
    query = """
    query q($pid: string) {
      patients(func: eq(patient_id, $pid)) {
        uid
        patient_id
        name
        last_name
        age
        genre
        telephone
        email
      }
    }
    """
    run_readonly_query(client, query, {"$pid": patient_id})

#2 - We can also search a patient knowing a part of their name 
def q2_search_patients_by_name(client):
    term = input("Name (e.g. 'Sofia'): ").strip()
    query = """
    query q($t: string) {
      patients(func: type(PATIENT)) @filter(
        anyofterms(name, $t) OR anyofterms(last_name, $t)
      ) {
        uid
        patient_id
        name
        last_name
        age
      }
    }
    """
    run_readonly_query(client, query, {"$t": term})

# 3 - Filter patients by a minimun age. EX: 20 years, 
# the  querie returns all patients with an age greather than or equal to 20
def q3_filter_patients_by_min_age(client):
    age_str = input("Minimum age: ").strip()
    try:
        min_age = int(age_str)
    except ValueError:
        print("Invalid age.")
        return

    query = """
    query q($a: int) {
      patients(func: ge(age, $a)) {
        patient_id
        name
        last_name
        age
      }
    }
    """
    run_readonly_query(client, query, {"$a": str(min_age)})

# 4 - The query returns all patients that have the same disease  
def q4_patients_with_disease(client):
    disease = input("Disease name (e.g. 'Hypertension' or 'Type 3 Diabetes'): ").strip()
    query = """
    query q($d: string) {
      diagnosis(func: anyofterms(disease_name, $d)) {
        disease_name
        icd10_code
        ~has_diagnosis {
          patient_id
          name
          last_name
          age
        }
      }
    }
    """
    run_readonly_query(client, query, {"$d": disease})

# 5 - The query returns all patients who share the same disease and use an age range
# in this query we used pagination to handle large amounts of data
def q5_patients_by_disease_and_age_paginated(client):
    disease = input("Disease name (e.g. 'Hypertension'): ").strip()
    age_str = input("Minimum age: ").strip()
    page_str = input("Page number (starting at 1): ").strip()

    try:
        min_age = int(age_str)
        page = max(1, int(page_str))
    except ValueError:
        print("Invalid number.")
        return

    first = 50
    offset = (page - 1) * first

    query = """
    query q($d: string, $a: int) {
      var(func: anyofterms(disease_name, $d)) {
        DX as ~has_diagnosis
      }

      patients(func: uid(DX), first: %d, offset: %d) @filter(ge(age, $a)) {
        patient_id
        name
        last_name
        age
      }
    }
    """ % (first, offset)

    run_readonly_query(client, query, {"$d": disease, "$a": str(min_age)})

# 6 - Returns all tratments that are applied by a specific doctor
def q6_treatments_by_doctor(client):
    lic = input("Doctor license_id (e.g. DOC-100): ").strip()
    query = """
    query q($lic: string) {
      doctors(func: eq(license_id, $lic)) {
        name
        last_name
        specialty
        license_id
        applies_treatment {
          treatment_name
          start_date
          end_date
          common_for_diagnosis {
            disease_name
            icd10_code
          }
        }
      }
    }
    """
    run_readonly_query(client, query, {"$lic": lic})

# 7 - Returns all medications that have a specific patient 
def q7_patient_medications(client):
    pid = input("Patient ID (e.g. P001): ").strip()
    query = """
    query q($pid: string) {
      patients(func: eq(patient_id, $pid)) {
        patient_id
        name
        last_name
        receives_medication {
          trade_name
          dosage
          frequency
        }
      }
    }
    """
    run_readonly_query(client, query, {"$pid": pid})

# 8 - Returns the specified number of recent vital signs readings for a patient
def q8_recent_vital_signs(client):
    pid = input("Patient ID (e.g. P001): ").strip()
    n_str = input("How many readings? (e.g. 3): ").strip()
    try:
        n = int(n_str)
    except ValueError:
        print("Invalid number.")
        return

    query = """
    query q($pid: string) {
      patients(func: eq(patient_id, $pid)) {
        patient_id
        name
        last_name
        has_vital_sign(orderdesc: timestamp, first: %d) {
          type
          value
          timestamp
        }
      }
    }
    """ % n

    run_readonly_query(client, query, {"$pid": pid})

# 9 - Returns vital sign readings for a specific patient within a given time range
#     Ex: all readings from a specific week. We need to provide the start date
#     (Monday) and the end date (Sunday) of that period
def q9_vital_signs_by_timerange(client):
    pid = input("Patient ID (e.g. P001): ").strip()
    start = input("Start date (YYYY-MM-DDTHH:MM:SSZ): ").strip()
    end = input("End date (YYYY-MM-DDTHH:MM:SSZ): ").strip()

    query = """
    query q($pid: string, $s: string, $e: string) {
      patients(func: eq(patient_id, $pid)) {
        patient_id
        name
        last_name
        has_vital_sign @filter(ge(timestamp, $s) AND le(timestamp, $e)) {
          type
          value
          timestamp
        }
      }
    }
    """

    run_readonly_query(client, query, {"$pid": pid, "$s": start, "$e": end})

# 10 - Returns the  count of all patients who have the same disease
def q10_count_patients_by_disease(client):
    query = """
    {
      d(func: type(DIAGNOSIS)) {
        disease_name
        icd10_code
        num_patients: count(~has_diagnosis)
      }
    }
    """
    run_readonly_query(client, query)

# 11 - Returns all visitors for a specific patient
def q11_show_visitors_of_patient(client):
    pid = input("Patient ID (e.g. P001): ").strip()

    query = """
    query q($pid: string) {
      patients(func: eq(patient_id, $pid)) {
        patient_id
        name
        last_name
        has_visitor {
          uid
          visitor_name
          arrival_time
          exit_time
        }
      }
    }
    """
    run_readonly_query(client, query, {"$pid": pid})

# 12 - This query helps us search for a specific doctor by their ID, name, or license ID
def q12_search_doctors(client):
    term = input("Doctor ID, license_id or name: ").strip()

    query = """
    query q($q: string) {
      doctors(func: type(DOCTOR)) @filter(
        eq(doctor_id, $q) OR
        eq(license_id, $q) OR
        anyofterms(name, $q) OR
        anyofterms(last_name, $q)
      ) {
        uid
        doctor_id
        license_id
        name
        last_name
        specialty
        email
      }
    }
    """
    run_readonly_query(client, query, {"$q": term})

# 13 - Returns all visitors for a specific patient within a given datetime range.
# This query filters visitors based on their arrival time.
def q13_visitors_by_timerange(client):
    pid = input("Patient ID (e.g. P001): ").strip()
    start = input("Start datetime (YYYY-MM-DDTHH:MM:SSZ): ").strip()
    end = input("End   datetime (YYYY-MM-DDTHH:MM:SSZ): ").strip()

    query = """
    query q($pid: string, $s: string, $e: string) {
      patients(func: eq(patient_id, $pid)) {
        patient_id
        name
        has_visitor @filter(ge(arrival_time, $s) AND le(arrival_time, $e)) {
          visitor_name
          arrival_time
          exit_time
        }
      }
    }
    """
    run_readonly_query(client, query, {"$pid": pid, "$s": start, "$e": end})