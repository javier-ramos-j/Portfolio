# Dgraph Hospital Services

The first steps before running our dgraph model. :D

## Required 
Ensure you have a running Dgraph instance
```bash
docker run --name dgraph -d -p 8080:8080 -p 9080:9080 dgraph/standalone
```
Make sure that you are in the correct folder (windows)
```bash
cd DgraphDB
```

## Optional: Start Ratel for UI  
If you want to visualize or delete data from Dgraph 
```bash
 docker run -it -p 8000:8000 dgraph/ratel
```

## Setup a python virtual env with python dgraph installed:

### Install and activate virtual venv (windows):
```bash
python3 -m pip install virtualenv
python3 -m venv ./venv
.\venv\Scripts\Activate.ps1
```

### Install project python requirements:
```bash
pip install -r requirements.txt
```
## Run the app
```bash
py main_Dgraph.py
```

## CHROMA_DB

Docker run needs the container to be running
```
docker run -d -v ./chroma-data:/data -p 8001:8000 --name chromadb chromadb/chroma
cd examples
python chromadb_docker.py 
```
### To run the API service
```
python -m uvicorn app:app --reload
python -m uvicorn Chroma_db.app:app --reload
```
## MONGO_DB

# Install project python requirements
pip install -r requirements.txt

### To run the API service
```
python -m uvicorn main:app --reload
```

### To load data
Ensure you have a running mongodb instance
i.e.:
```
docker run --name mongodb -d -p 27017:27017 mongo
```
Once your API service is running (see step above), run the populate script
```
cd data/
python populate.py
```

## CASSANDRA_DB
# Cassandra 

The present database has the following nodes:

- Device: keep track of the details of each medical device used in the hospital.
- Patient: keep track of the personal information of a patient.
- Visitor: keep track of the entering and leaving times of visitors in the hospital.
- Vital Signs: keep track of only the specific measures of a patient.

The tables to be created to meet the needs of the project are: patient, vital_signs_by_patient, visitors_by_patient, device, and device_by_patient. 

## Data Loading 📊

The application now supports loading data from CSV files located in the `data_cas/` folder. The following files are expected:

- `patient.csv`: Patient information (patient_id, name_first, last_name, phone, address)
- `vital_signs_by_patient.csv`: Vital signs readings (patient_id, reading_time, blood_pressure, oxygen_set, temperature, pulse_rate, respiratory_rate)
- `visitors_by_patient.csv`: Visitor records (patient_id, visit_date, name, surname, relationship)
- `device.csv`: Medical device information (device_id, model, type, status)
- `device_by_patient.csv`: Device assignments to patients (patient_id, device_id, assigned_on, returned_on)

You can also generate sample random data through the application menu. 

## As for Partition Keys and Clustering Keys 🗝️: 

- ***Patient***: patient_id and name as primary key. Hospitals have several records, thus querying via an id is more useful than using a name. This table is required in case of only requiring personal data of the patient, no medical-related information by any means. 

- ***Vital_signs_by_patient***: patient_id is used as the partition key and reading_time as the clustering key, because it is necessary to obtain information by patient while also being able to filter or sort the data by time. This table is separated from the patient table because vital signs are time-series data that can grow significantly and require frequent updates and queries based on temporal patterns. Keeping this information separate improves query performance and scalability, preventing the patient table from becoming overloaded with continuously changing measurements. 

- ***Visitors_by_patient***: patient_id as partition key and visit_date as clustering key, as browsing visitors’ records can be performed easily via patient_id (as it is unique) and visit_date (for range). 

- ***Device***: device_id is the partition key because hospitals assign unique identifiers to each device, allowing fast and direct access. This table stores detailed information about each monitoring or medical device linked to patients. It is kept separate from other tables to isolate device-specific attributes, ensuring efficient management and flexibility when devices are reassigned or replaced. 

- ***Device_by_patient***: Devices can be reassigned to different patients at a time; unlike” patient” that stores only personal data of a patient and “device” that stores only details of the device, this table acts like a link between both.  

 

## As for each query 🔎, 

- ***Access to vital signs by patient***: this is achieved by table “vital_signs_by_patient”. Most recent details about vital_signs for each patient can be found using the clustering key “reading_time”. Plus, average metrics can be performed on each patient using this table, as it covers all metrics. 
- ***Get device information by patient***: this can be done by querying on “devices”. 
- ***Get patient information***: use the “patient” table. 
- ***Get visitors records***:Access to the visitors registers can be done using “visitors_by_patient”. 