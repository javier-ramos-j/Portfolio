#!/usr/bin/env python3
"""
app-cas.py
authors: Andrea Lizeth Arevalos Solis, Sofia Vanessa Noyola Fonseca, Francisco Javier Ramos Jimenez
date: 12/02/2025
description: Interactive application for hospital patient management using Cassandra NoSQL database.
"""

import logging
import os
from cassandra.cluster import Cluster

import Cassandra_db.model_cas as model_cas

# Set logger
log = logging.getLogger()
log.setLevel(logging.INFO)
handler = logging.FileHandler('hospital.log')
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

# Read env vars related to Cassandra App
CLUSTER_IPS = os.getenv('CASSANDRA_CLUSTER_IPS', '127.0.0.1')
KEYSPACE = os.getenv('CASSANDRA_KEYSPACE', 'hospital')
REPLICATION_FACTOR = int(os.getenv('CASSANDRA_REPLICATION_FACTOR', '1'))

"""
Display the main menu options.
"""
def print_menu():
    menu_options = {
        0: "Load data from CSV files",
        1: "Show all patients",
        2: "Show vital signs for a patient",
        3: "Show vital signs by date range for a patient",
        4: "Show visitors for a patient",
        5: "Show devices for a patient",
        6: "Show all devices",
        7: "Register a new visitor",
        8: "Exit"
    }
    for key in menu_options.keys():
        print(f"{key} -- {menu_options[key]}")

"""
Main application loop for hospital patient management.
"""
def main():
    log.info("Connecting to Cassandra Cluster")
    try:
        cluster = Cluster(CLUSTER_IPS.split(','))
        session = cluster.connect()
        log.info("Successfully connected to Cluster")
    except Exception as e:
        log.error(f"Failed to connect to Cassandra cluster: {e}")
        print(f"Error connecting to Cassandra: {e}")
        return

    try:
        # Initialize keyspace and schema
        model_cas.create_keyspace(session, KEYSPACE, REPLICATION_FACTOR)
        session.set_keyspace(KEYSPACE)
        model_cas.create_schema(session)
        log.info(f"Keyspace '{KEYSPACE}' ready")

        # Main menu loop
        while True:
            print("\n" + "="*60)
            print_menu()
            try:
                option = int(input('\nEnter your choice: ').strip())
            except ValueError:
                print("Please enter a valid number.")
                continue

            if option == 0:
                print("\nLoading data from CSV files...")
                model_cas.bulk_insert_from_csv(session)
                print("Data loaded successfully from CSV files!")
                log.info("Data loaded from CSV files")

            elif option == 1:
                print(f"\nAll Patients:")
                if model_cas.PATIENTS:
                    for patient_id, name, surname, phone, address in model_cas.PATIENTS:
                        print(f"  {name} {surname} (ID: {patient_id})")
                        print(f"    Phone: {phone}")
                        print(f"    Address: {address}\n")
                else:
                    print("  No patients available. Please load data first.")

            elif option == 2:
                if not model_cas.PATIENTS:
                    print("  No patients available. Please load data first.")
                else:
                    print("\nAvailable patients:")
                    for idx, (patient_id, name, surname, _, _) in enumerate(model_cas.PATIENTS):
                        print(f"  [{idx}] {name} {surname}")
                    try:
                        choice = int(input('\nSelect patient by index: ').strip())
                        if 0 <= choice < len(model_cas.PATIENTS):
                            patient_id = model_cas.PATIENTS[choice][0]
                            print(f"\nVital Signs for {model_cas.PATIENTS[choice][1]} {model_cas.PATIENTS[choice][2]}:")
                            model_cas.get_vitals_by_patient(session, patient_id)
                        else:
                            print("Invalid selection.")
                    except (ValueError, IndexError):
                        print("Please enter a valid number.")

            elif option == 3:
                if not model_cas.PATIENTS:
                    print("  No patients available. Please load data first.")
                else:
                    print("\nAvailable patients:")
                    for idx, (patient_id, name, surname, _, _) in enumerate(model_cas.PATIENTS):
                        print(f"  [{idx}] {name} {surname}")
                    try:
                        choice = int(input('\nSelect patient by index: ').strip())
                        if 0 <= choice < len(model_cas.PATIENTS):
                            patient_id = model_cas.PATIENTS[choice][0]
                            start_date = input('Enter start date (YYYY-MM-DD) or press Enter for default: ').strip()
                            end_date = input('Enter end date (YYYY-MM-DD) or press Enter for default: ').strip()
                            print(f"\nVital Signs by Date Range:")
                            model_cas.get_vitals_by_patient_date_range(session, patient_id, start_date, end_date)
                        else:
                            print("Invalid selection.")
                    except (ValueError, IndexError):
                        print("Please enter a valid number.")

            elif option == 4:
                if not model_cas.PATIENTS:
                    print("  No patients available. Please load data first.")
                else:
                    print("\nAvailable patients:")
                    for idx, (patient_id, name, surname, _, _) in enumerate(model_cas.PATIENTS):
                        print(f"  [{idx}] {name} {surname}")
                    try:
                        choice = int(input('\nSelect patient by index: ').strip())
                        if 0 <= choice < len(model_cas.PATIENTS):
                            patient_id = model_cas.PATIENTS[choice][0]
                            print(f"\nVisitors:")
                            model_cas.get_visitors_by_patient(session, patient_id)
                        else:
                            print("Invalid selection.")
                    except (ValueError, IndexError):
                        print("Please enter a valid number.")

            elif option == 5:
                if not model_cas.PATIENTS:
                    print("  No patients available. Please load data first.")
                else:
                    print("\nAvailable patients:")
                    for idx, (patient_id, name, surname, _, _) in enumerate(model_cas.PATIENTS):
                        print(f"  [{idx}] {name} {surname}")
                    try:
                        choice = int(input('\nSelect patient by index: ').strip())
                        if 0 <= choice < len(model_cas.PATIENTS):
                            patient_id = model_cas.PATIENTS[choice][0]
                            print(f"\nDevices Assigned:")
                            model_cas.get_devices_by_patient(session, patient_id)
                        else:
                            print("Invalid selection.")
                    except (ValueError, IndexError):
                        print("Please enter a valid number.")

            elif option == 6:
                print(f"\nAll Devices:")
                if model_cas.DEVICES:
                    for device_id, model, dtype, status in model_cas.DEVICES:
                        print(f"  {model} ({dtype})")
                        print(f"    ID: {device_id}")
                        print(f"    Status: {status}\n")
                else:
                    print("  No devices available. Please load data first.")
            elif option == 7:
                try:
                    print("\n" + "="*60)
                    print("REGISTER NEW VISITOR")
                    print("="*60)
                    
                    # Show available patients
                    print("\nAvailable patients:")
                    for idx, (patient_id, name, surname, _, _) in enumerate(model_cas.PATIENTS):
                        print(f"  [{idx}] {name} {surname}")
                    
                    
                    # Select patient
                    choice = int(input('\nSelect patient by index: ').strip())
                    if 0 <= choice < len(model_cas.PATIENTS):
                        patient_id = model_cas.PATIENTS[choice][0]
                        patient_name = f"{model_cas.PATIENTS[choice][1]} {model_cas.PATIENTS[choice][2]}"
                        
                        print(f"\nRegistering visitor for: {patient_name}")
                        print("-" * 60)
                        
                        # Get visitor information
                        visitor_name = input('Enter visitor first name: ').strip()
                        if not visitor_name:
                            print("Error: First name cannot be empty.")
                            continue
                        
                        visitor_surname = input('Enter visitor last name: ').strip()
                        if not visitor_surname:
                            print("Error: Last name cannot be empty.")
                            continue
                        
                        relationship = input('Enter relationship: ').strip()
                        
                        # Confirm before inserting
                        print(f"\n{'='*60}")
                        print("CONFIRM VISITOR REGISTRATION")
                        print(f"{'='*60}")
                        print(f"Patient: {patient_name}")
                        print(f"Visitor: {visitor_name} {visitor_surname}")
                        print(f"Relationship: {relationship}")
                        print(f"Visit Date: Current date/time")
                        
                        success = model_cas.insert_visitor(
                            session=session,
                            patient_id=patient_id,
                            name=visitor_name,
                            surname=visitor_surname,
                            relationship=relationship
                        )
                            
                        if success:
                            print("\nVISITOR REGISTERED SUCCESSFULLY!")
                            log.info(f"Nurse registered visitor: {visitor_name} {visitor_surname} for patient {patient_id}")
                        else:
                            print("\nFAILED TO REGISTER VISITOR.")
                    else:
                        print("Invalid patient selection.")
                except Exception as e:
                    print(f"An error occurred: {e}")
                    log.error(f"Error in visitor registration: {e}")

            elif option == 8:
                print("Exiting hospital application...")
                log.info("Application terminated by user")
                break

            else:
                print("Invalid option. Please try again.")

    except Exception as e:
        log.error(f"Application error: {e}")
        print(f"An error occurred: {e}")
    finally:
        session.shutdown()
        cluster.shutdown()
        log.info("Cassandra connection closed")
        return 0


if __name__ == '__main__':
    main()