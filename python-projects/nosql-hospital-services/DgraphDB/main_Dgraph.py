import os
import pydgraph
import DgraphDB.model as model

DGRAPH_URI = os.getenv("DGRAPH_URI", "localhost:9080")

def create_client_stub():
    return pydgraph.DgraphClientStub(DGRAPH_URI)

def create_client(client_stub):
    return pydgraph.DgraphClient(client_stub)

def close_client_stub(client_stub):
    client_stub.close()


def print_menu():
    print("\n")
    print("      HOSPITAL DATABASE :D   ")
    mm_options = {
        1: "Load data",
        2: "Search patient by ID",
        3: "Search patients by name",
        4: "Filter patients by minimum age",
        5: "Patients with a given disease",
        6: "Patients by disease and age (paginated)",
        7: "Treatments applied by a doctor (and associated diseases)",
        8: "Medications of a patient",
        9: "Recent vital sign readings of a patient",
        10: "Vital signs by time range",
        11: "Count patients per disease",
        12: "Show all visitors of a patient",
        13: "Seacrh doctors by ID/Name",
        14: "Visitors by timerange",
        0: "Exit",
    }
    for key in sorted(mm_options.keys()):
        print(f"{key} -- {mm_options[key]}")

def main():
    client_stub = create_client_stub()
    client = create_client(client_stub)

    try:
        model.set_schema(client)
        print("Schema set correctly :D")
    except Exception as e:
        print(f"Could not connect to Dgraph or set schema: {e}")

    try:
        while True:
            print_menu()
            try:
                option = int(input("Choose an option: ").strip())
            except ValueError:
                print("Please enter a valid number.")
                continue

            if option == 1:
                model.create_data(client)

            elif option == 2:
                model.q1_search_patient_by_id(client)

            elif option == 3:
                model.q2_search_patients_by_name(client)

            elif option == 4:
                model.q3_filter_patients_by_min_age(client)

            elif option == 5:
                model.q4_patients_with_disease(client)

            elif option == 6:
                model.q5_patients_by_disease_and_age_paginated(client)

            elif option == 7:
                model.q6_treatments_by_doctor(client)

            elif option == 8:
                model.q7_patient_medications(client)

            elif option == 9:
                model.q8_recent_vital_signs(client)

            elif option == 10:
                model.q9_vital_signs_by_timerange(client)

            elif option == 11:
                model.q10_count_patients_by_disease(client)

            elif option == 12:
                model.q11_show_visitors_of_patient(client)
            elif option == 13:
                model.q12_search_doctors(client)
            elif option  == 14:
                model.q13_visitors_by_timerange(client)
            elif option == 0:
                print("Bye! :D ")
                break

            else:
                print("Invalid option. Try again.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        close_client_stub(client_stub)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Fatal Error: {}".format(e))
