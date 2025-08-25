# MULTI-DRIVER: CRUD Console Library  

A flexible and extensible library for working with different file formats (currently **CSV** and **JSON**) through the console.  
This project allows you to easily perform **CRUD operations** (Create, Read, Update, Delete) on supported file formats and is designed to be extended for future file types such as XML, YAML, or databases.  

---

## 🚀 Features  
- **Multi-driver support**: Work with multiple file formats via dedicated drivers.  
- **CRUD operations**: Create, Read, Update, and Delete records from CSV and JSON files.  
- **Driver hierarchy**: Organized structure with `DriverRegistry`, `DriverManager`, and specific file drivers.  
- **Extensible design**: Add new drivers for other file formats with minimal effort.  
- **Console-based interaction**: Perform file manipulation using Java.  

---

## 🏗️ Architecture Overview  

The project follows a clear, hierarchical design:  

- **DriverRegistry**  
  - Stores and manages available drivers.  
  - Provides registration and lookup of file drivers.  

- **DriverManager**  
  - Handles connectivity between the user and drivers.  
  - Responsible for setting and releasing driver connections.  

- **Drivers (CSVDriver, JSONDriver, …)**  
  - Perform actual file operations.  
  - Each driver implements CRUD logic tailored to its file format.  

---

## 📂 Supported Drivers  
- **CSV Driver**: Manipulate CSV files row by row.  
- **JSON Driver**: Work with structured JSON data.  

(✅ More drivers like XML, YAML, or SQL can be added easily.)  


