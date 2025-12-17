#!/usr/bin/env python3
import socket
import sys
import os
import logging
import threading
import time
import subprocess
import DgraphDB.main_Dgraph as main_Dgraph
import Mongo_db.client_mongo as client
import uvicorn
import Chroma_db.main_chroma as main_chroma
import Cassandra_db.app_cas as app_cas
from Mongo_db.main_mongo import app
from Chroma_db.app import app as chroma_app


# The logs will be saved at "hospital.log" because it was implemented at Cassandra code
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)

logger.handlers = []
file_handler = logging.FileHandler("hospital.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger = logging.getLogger(__name__)


def print_main_menu():
    print("\n" + "=" * 80)
    print(" " * 20 + "Healthcare Data Integration Platform")
    print("=" * 80)
    print("\nSelect the database system to use:")
    print("\n  1) Patient and user information (MongoDB)")
    print("  2) Hospital relationships (Dgraph)")
    print("  3) Knowledge System and Chatbot(ChromaDB)")
    print("  4) Vital Signs and Devices Management (Cassandra)")
    print("  0) Exit System")
    print("\n" + "=" * 80)


def run_mongodb():
    logger.info("Starting MongoDB API server (Falcon)")
    print("\n" + "-" * 80)
    print("MONGODB - PATIENT AND USER INFORMATION")
    print("-" * 80)
    
    initial_dir = os.getcwd()
    
    try:
        if os.path.exists('Mongo_db'):
            os.chdir('Mongo_db')
        
        def is_port_in_use(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
              return s.connect_ex(("127.0.0.1", port)) == 0

        def run_server():
            port = 8003
            if is_port_in_use(port):
                print(f" Uvicorn is already running on port {port}.")
                return
        
        #If the port is not in use, run the nex code
            uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        print("Starting server...")
        time.sleep(3)
        if os.path.exists('data_mongo/populate.py'):
            respuesta = input("Do you want to populate the data? (y/n): ").strip().lower()
            
            if respuesta == 'y':
                print("\nPopulating data...")
                print("-" * 80)
                
                result = subprocess.run([sys.executable, 'data_mongo/populate.py'], capture_output=True,text=True)
 
                if result.returncode == 0:
                    print("Data loaded successfully\n")
                    logger.info("Populate executed successfully")
                else:
                    print("Warning: populate.py finished with errors")
                    if result.stderr:
                        print(f"Error: {result.stderr}")
                    logger.warning(f"Populate finished with code: {result.returncode}")

                
                print("-" * 80)
                input("\nPress Enter to continue...")
            client.main()

    except Exception as e:
        print(f"\nError executing MongoDB: {e}")
        logger.error(f"Error MongoDB: {e}")
    finally:
        print("\n\nClosing MongoDB...")
        os.chdir(initial_dir)
        time.sleep(1)


def run_dgraph():
    logger.info("Initializing Dgraph")
    print("DGRAPH - Hospital Relationships\n" + "-" * 80)
    print("-" * 80)
    
    initial_dir = os.getcwd()
    
    try:
        if os.path.exists('DgraphDB'):
            os.chdir('DgraphDB')
        #Execute Dgraph main
        main_Dgraph.main()
    except Exception as e:
        print(f"\nError executing Dgraph: {e}")
        logger.error(f"Error Dgraph: {e}")
    finally:
        # Go to the initial direction
        os.chdir(initial_dir)


def run_chromadb():
    logger.info("Initializing Chromadb")
    print("\n" + "-" * 80)
    print("CHROMADB - CHATBOT AND KNOWLEADGE SYSTEM")
    print("-" * 80)
    
    initial_dir = os.getcwd()
    
    try:
        if os.path.exists('Chroma_db'):
            os.chdir('Chroma_db')

        print("Chroma opening...\n")
        
        def is_port_in_use(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
              return s.connect_ex(("127.0.0.1", port)) == 0

        def run_server():
            port = 8005
            if is_port_in_use(port):
                print(f" Uvicorn is already running on port {port}.")
                return
        
        #If the port is not in use, run the nex code
            uvicorn.run(chroma_app, host="0.0.0.0", port=port, log_level="warning")

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        print("Waiting Uvicorn to start...")
        time.sleep(3)

        print("\nUvicorn running correctly")
        print("-" * 80)

        main_chroma.main()
        
    except Exception as e:
        print(f"\nError executing ChromaDB {e}")
        logger.error(f"Error ChromaDB: {e}")
    finally:
        print("\n\nClosing ChromaDB...")
        os.chdir(initial_dir)
        time.sleep(1)

def run_cassandra():
    logger.info("Initializing Cassandra")
    print("\n" + "-" * 80)
    print("CASSANDRA - Vital Signs and Devices Management")
    print("-" * 80)
    
    initial_dir = os.getcwd()
    
    try:
        if os.path.exists('Cassandra_db'):
            os.chdir('Cassandra_db')

        app_cas.main()
        
    except Exception as e:
        print(f"\nError executing Cassandra: {e}")
        logger.error(f"Error Cassandra: {e}")
    finally:
        # Go back to initial directory (main menu)
        os.chdir(initial_dir)


def main():
    logger.info("System Hospital initialized")
    
    # get current work directory and save it
    initial_dir = os.getcwd()
    
    try:
        while True:
            # Assure we are in the initial directory
            os.chdir(initial_dir)
            
            print_main_menu()
            
            try:
                option = input("\nPut your option: ").strip()
                
                if option == '1':
                    run_mongodb()
                
                elif option == '2':
                    run_dgraph()
                
                elif option == '3':
                    run_chromadb()
                
                elif option == '4':
                    run_cassandra()
                
                elif option == '0':
                    print("\n" + "=" * 80)
                    print("Leaving main app...")
                    logger.info("System close by user")
                    break
                
                else:
                    print("\nInvalidid option")
                
            except ValueError:
                print("\nError: Insert a valid number.")
            except Exception as e:
                print(f"\nError: {e}")
                logger.error(f"Error: {e}")
    
    except Exception as e:
        print(f"\nError: {e}")
        logger.critical(f"Error: {e}")
    
    finally:
        os.chdir(initial_dir)
        logger.info("System ended")


if __name__ == "__main__":
    main()
