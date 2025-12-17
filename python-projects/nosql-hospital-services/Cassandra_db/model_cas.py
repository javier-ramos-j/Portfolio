
#!/usr/bin/env python3
"""
model-cas.py
authors: Andrea Lizeth Arevalos Solis, Sofia Vanessa Noyola Fonseca, Francisco Javier Ramos Jimenez
date: 02/12/2025
description: schema creation, CSV data loading, batch inserts and basic SELECT helpers.
Special thanks to the provided laboratory code for Cassandra, and professor Leobardo Ruiz,
as this code worked as a guide to produce this activity.
"""

import csv # Handle CSV file reading
import datetime # Handle datetime fields
import logging # Used to write on a file all logs, so that tracing is easier 
import os # Used to handle file paths
import uuid # Improtant! Used to match UUID to other DBs (otherwise, it crashes).
from typing import List, Tuple # used for notation (not that important)

# Cassandra tools to work with
from cassandra.cluster import Cluster 
from cassandra.util import uuid_from_time, datetime_from_uuid1
from cassandra.query import BatchStatement

# Set logger
log = logging.getLogger()
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
log.addHandler(handler)

CREATE_KEYSPACE = """
    CREATE KEYSPACE IF NOT EXISTS {}
    WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': {} }}
"""

################### CREATE TABLES STATEMENT #######################

# Patient table, with fields patient_id, name, surname, phone, and address.
CREATE_PATIENT_TABLE = """
    CREATE TABLE IF NOT EXISTS patient (
        patient_id UUID,
        name TEXT,
        surname TEXT,
        phone TEXT,
        address TEXT,
        PRIMARY KEY (patient_id)
    )
"""

# vital_signs_by_patient table with fields patient_id, reading_time, blood_pressure, oxygen_set, temp
# pulse_rate and respiratory_rate
CREATE_VITAL_SIGNS_BY_PATIENT_TABLE = """
    CREATE TABLE IF NOT EXISTS vital_signs_by_patient (
        patient_id UUID,
        reading_time TIMEUUID,
        blood_pressure TEXT,
        oxygen_set FLOAT,
        temperature FLOAT,
        pulse_rate TEXT,
        respiratory_rate TEXT,
        PRIMARY KEY ((patient_id), reading_time)
    ) WITH CLUSTERING ORDER BY (reading_time DESC)
"""

# visitors_by_patient with fields patient_id, visit_date, name, surname and relationship
CREATE_VISITORS_BY_PATIENT_TABLE = """
    CREATE TABLE IF NOT EXISTS visitors_by_patient (
        patient_id UUID,
        visit_date TIMEUUID,
        name TEXT,
        surname TEXT,
        relationship TEXT,
        PRIMARY KEY ((patient_id), visit_date)
    ) WITH CLUSTERING ORDER BY (visit_date DESC)
"""

# device table with fields device_id, model, type and status
CREATE_DEVICE_TABLE = """
    CREATE TABLE IF NOT EXISTS device (
        device_id UUID,
        model TEXT,
        type TEXT,
        status TEXT,
        PRIMARY KEY (device_id)
    )
"""

# device_by_patient with fields patient:if, device_id, assigned_on and returned_on
CREATE_DEVICE_BY_PATIENT_TABLE = """
    CREATE TABLE IF NOT EXISTS device_by_patient (
        patient_id UUID,
        device_id UUID,
        assigned_on TIMEUUID,
        returned_on TIMEUUID,
        PRIMARY KEY ((patient_id), device_id)
    ) WITH CLUSTERING ORDER BY (device_id ASC)
"""

########################## QUERY STATEMENTS ###########################

# Q1 - Get patient info
SELECT_PATIENT_BY_ID = """
    SELECT patient_id, name, surname, phone, address
    FROM patient
    WHERE patient_id = ?
"""

# Q2 - Get vital signs for a patient (all)
SELECT_VITALS_BY_PATIENT = """
    SELECT patient_id, toDate(reading_time) as reading_time_readable, blood_pressure, oxygen_set, temperature, pulse_rate, respiratory_rate
    FROM vital_signs_by_patient
    WHERE patient_id = ?
"""

# Q3 - Get vital signs by time range
SELECT_VITALS_BY_PATIENT_DATE_RANGE = """
    SELECT patient_id, toDate(reading_time) as reading_time_readable, blood_pressure, oxygen_set, temperature, pulse_rate, respiratory_rate
    FROM vital_signs_by_patient
    WHERE patient_id = ? AND reading_time >= minTimeuuid(?) AND reading_time <= maxTimeuuid(?)
"""

# Q4 - Get visitors for a patient
SELECT_VISITORS_BY_PATIENT = """
    SELECT patient_id, toDate(visit_date) as visit_date_readable, name, surname, relationship
    FROM visitors_by_patient
    WHERE patient_id = ?
"""

# Q5 - Get devices assigned to a patient
SELECT_DEVICES_BY_PATIENT = """
    SELECT patient_id, device_id, toDate(assigned_on) as assigned_on_readable, toDate(returned_on) as returned_on_readable
    FROM device_by_patient
    WHERE patient_id = ?
"""

# Q6 - Get device info by id
SELECT_DEVICE_BY_ID = """
    SELECT device_id, model, type, status
    FROM device
    WHERE device_id = ?
"""

################## DATA CONTAINERS ###################

# Containers for loaded CSV data
PATIENTS = []
VITAL_SIGNS = []
VISITORS = []
DEVICES = []
DEVICE_BY_PATIENT = []

"""
Get date range is a function used for queries that depend on datetime objects
Args:
    start_date: str
    end_date = str
Returns:
    Tuple[datetime.datetime, datetime.datetime]
"""
def get_date_range(start_date: str = "", end_date: str = "") -> Tuple[datetime.datetime, datetime.datetime]:
    # In case none were given, default to last 30 days
    if start_date == "" and end_date == "":
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=30)
    # If end_date was not given, set it as start_date + 30 days
    elif end_date == "":
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = start_date + datetime.timedelta(days=30)
    # If start_date was not given, set it as end_date - 30 days
    elif start_date == "":
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        start_date = end_date - datetime.timedelta(days=30)
    # If both wer egiven, set it to that range
    else:
        start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start_date, end_date

"""
Get the path to the data_cas folder using absolute path,
so our code does not produce errors with file paths (like in previous laboratories)
Returns:
    str: Path to data_cas folder
"""
def get_data_folder() -> str:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'data_cas')

"""
Load patients from CSV file
Args:
    None
Returns:
    List[Tuple]: List of patient tuples (patient_id, name, surname, phone, address)
"""
def load_patients_from_csv() -> List[Tuple]:
    # patients[] stores all patients found in the CSV, then it will upload them to the table
    patients = []
    data_folder = get_data_folder()
    csv_path = os.path.join(data_folder, 'patient.csv')
    
    try:
        # Important note: we use utf-8 as our fields have accents, otherwise... error.
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                """
                Convert patient_id (P001, P002, etc.) to UUID for consistency.

                This necessity rose after handling the patient_id as an int and as a string,
                so uuid had to be implemented.
                Because our patients ids have to match those of MongoDB and Dgraph, it is needed
                to use UUID for the following reasons:
                    - Generate the uuid based on specific criteria (hash function)
                    - Avoid duplicates.
                    - And most importantly, synchronize with other tables!
                UUID5 allows this, and will ensure that for tables (like visitors_by_patient),
                the same field will be generated.

                On the other hands, NAMESPACE_DNS is a suggestion. It is the most ommon way of
                transforming strings to UUIDs.
                """
                patient_id = uuid.uuid5(uuid.NAMESPACE_DNS, row['patient_id'])
                
                # For each patient, we create append a tuple with the corresponding rows
                patients.append((
                    patient_id,
                    row['name_first'],
                    row['last_name'],
                    row['phone'],
                    row['address']
                ))
        log.info(f"Loaded {len(patients)} patients from {csv_path}")
    except Exception as e:
        log.error(f"Error loading patients from CSV: {e}")
    
    return patients

"""
Load vital signs from CSV file
Args:
    None
Returns:
    List[Tuple]: List of vital signs tuples
"""
def load_vital_signs_from_csv() -> List[Tuple]:
    # vitals has the same purpose as the ppatients array in load_patient() function, but adapted to vital signs.
    vitals = []
    data_folder = get_data_folder()
    csv_path = os.path.join(data_folder, 'vital_signs_by_patient.csv')
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vitals.append((
                    uuid.UUID(row['patient_id']),
                    uuid.UUID(row['reading_time']),
                    row['blood_pressure'],
                    float(row['oxygen_set']),
                    float(row['temperature']),
                    row['pulse_rate'],
                    row['respiratory_rate']
                ))
        log.info(f"Loaded {len(vitals)} vital signs from {csv_path}")
    except Exception as e:
        log.error(f"Error loading vital signs from CSV: {e}")
    
    return vitals

"""
Load visitors from CSV file
Args:
    None
Returns:
    List[Tuple]: List of visitors tuples
"""
def load_visitors_from_csv() -> List[Tuple]:
    # visitors is used to store a tuple for each row of in visitors_by_patient.csv
    visitors = []
    data_folder = get_data_folder()
    csv_path = os.path.join(data_folder, 'visitors_by_patient.csv')
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                visitors.append((
                    uuid.UUID(row['patient_id']),
                    uuid.UUID(row['visit_date']),
                    row['name'],
                    row['surname'],
                    row['relationship']
                ))
        log.info(f"Loaded {len(visitors)} visitors from {csv_path}")
    except Exception as e:
        log.error(f"Error loading visitors from CSV: {e}")
    
    return visitors

"""
Load devices from CSV file
Args:
    None
Returns:
    List[Tuple]: List of devices tuples
"""
def load_devices_from_csv() -> List[Tuple]:
    # devices stores a tuple for each device in device.csv
    devices = []
    data_folder = get_data_folder()
    csv_path = os.path.join(data_folder, 'device.csv')
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                devices.append((
                    uuid.UUID(row['device_id']),
                    row['model'],
                    row['type'],
                    row['status']
                ))
        log.info(f"Loaded {len(devices)} devices from {csv_path}")
    except Exception as e:
        log.error(f"Error loading devices from CSV: {e}")
    
    return devices

"""
Load device assignments from CSV file
Args:
    None
Returns:
    List[Tuple]: List of device_by_patient tuples
"""
def load_device_by_patient_from_csv() -> List[Tuple]:
    # assignments stores tuples for each device_by_patient row
    assignments = []
    data_folder = get_data_folder()
    csv_path = os.path.join(data_folder, 'device_by_patient.csv')
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                assignments.append((
                    uuid.UUID(row['patient_id']),
                    uuid.UUID(row['device_id']),
                    uuid.UUID(row['assigned_on']),
                    uuid.UUID(row['returned_on'])
                ))
        log.info(f"Loaded {len(assignments)} device assignments from {csv_path}")
    except Exception as e:
        log.error(f"Error loading device assignments from CSV: {e}")
    
    return assignments

"""
Execute inserts in batches.
Args:
    session: 
    stmt: string
    data: List[tuple]
"""
def execute_batch(session, stmt, data: List[tuple]):
    if not data:
        return

    for i in range(0, len(data), 25):
        # Batch statement will group multiple statement of Cssandra in a single call
        batch = BatchStatement()
        chunk = data[i : i + 25]
        for item in chunk:
            batch.add(stmt, item)
        session.execute(batch)

"""
Load data from CSV files and insert into Cassandra.
Args:
    session:
"""
def bulk_insert_from_csv(session):
    # Load all data from CSV files
    log.info("Loading data from CSV files...")
    patients_data = load_patients_from_csv()
    vitals_data = load_vital_signs_from_csv()
    visitors_data = load_visitors_from_csv()
    devices_data = load_devices_from_csv()
    device_by_patient_data = load_device_by_patient_from_csv()

    # Prepare insert statements
    insert_patient_stmt = session.prepare(
        "INSERT INTO patient (patient_id, name, surname, phone, address) VALUES (?, ?, ?, ?, ?)"
    )
    insert_vitals_stmt = session.prepare(
        "INSERT INTO vital_signs_by_patient (patient_id, reading_time, blood_pressure, oxygen_set, temperature, pulse_rate, respiratory_rate) VALUES (?, ?, ?, ?, ?, ?, ?)"
    )
    insert_visitor_stmt = session.prepare(
        "INSERT INTO visitors_by_patient (patient_id, visit_date, name, surname, relationship) VALUES (?, ?, ?, ?, ?)"
    )
    insert_device_stmt = session.prepare(
        "INSERT INTO device (device_id, model, type, status) VALUES (?, ?, ?, ?)"
    )
    insert_device_by_patient_stmt = session.prepare(
        "INSERT INTO device_by_patient (patient_id, device_id, assigned_on, returned_on) VALUES (?, ?, ?, ?)"
    )

    # Insert patients
    log.info(f"Inserting {len(patients_data)} patients...")
    PATIENTS.extend(patients_data)
    execute_batch(session, insert_patient_stmt, patients_data)

    # Insert devices
    log.info(f"Inserting {len(devices_data)} devices...")
    DEVICES.extend(devices_data)
    execute_batch(session, insert_device_stmt, devices_data)

    # Insert vital signs
    log.info(f"Inserting {len(vitals_data)} vital signs...")
    VITAL_SIGNS.extend(vitals_data)
    execute_batch(session, insert_vitals_stmt, vitals_data)

    # Insert visitors
    log.info(f"Inserting {len(visitors_data)} visitors...")
    VISITORS.extend(visitors_data)
    execute_batch(session, insert_visitor_stmt, visitors_data)

    # Insert device assignments
    log.info(f"Inserting {len(device_by_patient_data)} device assignments...")
    DEVICE_BY_PATIENT.extend(device_by_patient_data)
    execute_batch(session, insert_device_by_patient_stmt, device_by_patient_data)

    log.info("Bulk insert from CSV completed.")

######################### SCHEMA CREATION HELPERS #########################

"""
Create cassandra Keyspace for the hospital
Args:
    session:
    keyspace: str
    replication_factor: int = 1
"""
def create_keyspace(session, keyspace: str, replication_factor: int = 1):
    log.info(f"Creating keyspace: {keyspace} (rf={replication_factor})")
    session.execute(CREATE_KEYSPACE.format(keyspace, replication_factor))

"""
Create schema
Args:
    session: 
"""
def create_schema(session):
    log.info("Creating hospital schema...")
    session.execute(CREATE_PATIENT_TABLE)
    session.execute(CREATE_VITAL_SIGNS_BY_PATIENT_TABLE)
    session.execute(CREATE_VISITORS_BY_PATIENT_TABLE)
    session.execute(CREATE_DEVICE_TABLE)
    session.execute(CREATE_DEVICE_BY_PATIENT_TABLE)
    log.info("Schema creation complete.")

######################### QUERY HELPERS #########################

"""
First query: get patient by id
Args:
    session:
    patient_id: uuid.UUID
"""
def get_patient_by_id(session, patient_id: uuid.UUID):
    log.info(f"Retrieving patient {patient_id}")
    """
    session.prepare returns an statement, ready to use for multiple queries
    [patient_id] fills the ? in the statement
    """
    stmt = session.prepare(SELECT_PATIENT_BY_ID)
    rows = session.execute(stmt, [patient_id])
    for r in rows:
        print(r)

"""
Second query:  get vitals by patient
Args:
    session:
    patient_id: uuid.UUID
"""
def get_vitals_by_patient(session, patient_id: uuid.UUID):
    log.info(f"Retrieving vitals for {patient_id}")
    stmt = session.prepare(SELECT_VITALS_BY_PATIENT)
    rows = session.execute(stmt, [patient_id])
    for r in rows:
        print(r)

"""
Third query: get vitals by patient date range
Args:
    session:
    patient_id: uuid.UUID
    start_date: string
    end_date: string
"""
def get_vitals_by_patient_date_range(session, patient_id: uuid.UUID, start_date: str, end_date: str):
    log.info(f"Retrieving vitals for {patient_id} between {start_date} and {end_date}")
    start_dt, end_dt = get_date_range(start_date, end_date)
    stmt = session.prepare(SELECT_VITALS_BY_PATIENT_DATE_RANGE)
    rows = session.execute(stmt, [patient_id, start_dt, end_dt])
    for r in rows:
        print(r)


"""
Fourth query:  get visitors by patient
Args:
    session:
    patient_id: uuid.UUID
"""
def get_visitors_by_patient(session, patient_id: uuid.UUID):
    log.info(f"Retrieving visitors for {patient_id}")
    stmt = session.prepare(SELECT_VISITORS_BY_PATIENT)
    rows = session.execute(stmt, [patient_id])
    for r in rows:
        print(r)

"""
Fifth query: get devices by patient
Args:
    session:
    patient_id: uuid.UUID
"""
def get_devices_by_patient(session, patient_id: uuid.UUID):
    log.info(f"Retrieving devices for {patient_id}")
    stmt = session.prepare(SELECT_DEVICES_BY_PATIENT)
    rows = session.execute(stmt, [patient_id])
    for r in rows:
        print(r)

"""
Sixth query: get devices by id
Args:
    session:
    device_id: uuid.UUID
"""
def get_device_by_id(session, device_id: uuid.UUID):
    log.info(f"Retrieving device {device_id}")
    stmt = session.prepare(SELECT_DEVICE_BY_ID)
    rows = session.execute(stmt, [device_id])
    for r in rows:
        print(r)

"""
Insert a new visitor record for a patient
Args:
    session:
    patient_id: uuid.UUID 
    name: str 
    surname: str
    relationship: str 
    visit_date: datetime.datetime
Returns:
    bool: True if insertion successful, False otherwise
"""
def insert_visitor(session, patient_id: uuid.UUID, name: str, surname: str, 
                   relationship: str, visit_date: datetime.datetime = None):
    try:
        # If no visit_date provided, use current time
        if visit_date is None:
            visit_date = datetime.datetime.utcnow()
        
        # Convert datetime to TIMEUUID for consistency with the table schema
        visit_timeuuid = uuid_from_time(visit_date)
        
        log.info(f"Inserting visitor {name} {surname} for patient {patient_id}")
        
        # Prepare the insert statement
        insert_stmt = session.prepare(
            """
            INSERT INTO visitors_by_patient 
            (patient_id, visit_date, name, surname, relationship) 
            VALUES (?, ?, ?, ?, ?)
            """
        )
        
        # Execute the insert
        session.execute(insert_stmt, [patient_id, visit_timeuuid, name, surname, relationship])
        
        log.info(f"Successfully inserted visitor record for {name} {surname}")
        return True
        
    except Exception as e:
        log.error(f"Error inserting visitor: {e}")
        return False