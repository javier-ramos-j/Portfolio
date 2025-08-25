package com.multi.driver.crud;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.function.BiPredicate;

import org.json.JSONArray;
import org.json.JSONObject;

//A driver for managing SON files, implementing basic CRUD operations.

public class JSONDriver extends DriverManager<JSONArray> implements JSONObjectCreator {

    // Predicate to check if two JSONObjects have the same structure (keys)
    private final BiPredicate<JSONObject, JSONObject> recordSimilarToHeader = (o1, o2) -> o1.keySet().equals(o2.keySet());

    // Default constructor
    public JSONDriver() {}

    // Constructor with source file
    public JSONDriver(String source) {
        super(source, FileFormat.JSON);
    }

    // Method to set the data source
    public void setConnection(String source) {
        super.setConnection(source, FileFormat.JSON);
    }

    @Override
    public boolean create(String... content) {
        if (this.source == null) {
            System.err.println("Source is not initialized.");
            return false;
        }

        JSONObject record = process(content); // Create a JSONObject from input
        if (record == null) {
            System.err.println("Failed to process content.");
            return false;
        }

        JSONArray table = this.getTable();
        if (table.isEmpty()) {
            System.err.println("Table is empty or not initialized.");
            return false;
        }

        JSONObject header = table.getJSONObject(0); // First row serves as the header
        if (!recordSimilarToHeader.test(header, record)) {
            System.err.println("Record structure does not match the header.");
            System.err.println(DriverExceptionsCodes.NUM); // Additional error context
            return false;
        }

        // Check for duplicate records
        for (int i = 0; i < table.length(); ++i) {
            JSONObject row = table.getJSONObject(i);
            if (row.similar(record)) {
                System.err.println("Duplicate record detected. Skipping insertion.");
                return false;
            }
        }

        table.put(record); // Add the new record to the table
        updateAndWrite(table); // Write the updated table to the file
        return true;
    }

    @Override
    public boolean read(String field, String value) {
        if (!isSourceInitialized() || !isTableInitialized()) return false;

        JSONObject header = getHeader();
        if (!header.has(field)) {
            System.err.println(DriverExceptionsCodes.FIELDS);
            return false;
        }

        JSONArray table = this.getTable();
        // Search for rows with matching field and value
        for (int i = 0; i < table.length(); i++) {
            JSONObject row = table.getJSONObject(i);
            if (row.has(field) && row.getString(field).equals(value)) {
                System.out.println("Record found: " + row);
                return true;
            }
        }
        return false;
    }

    @Override
    public boolean update(String fieldToMatch, String valueToMatch, String newValue) {
        if (!isSourceInitialized() || !isTableInitialized()) return false;

        JSONArray table = this.getTable();
        // Find and update the matching row
        for (int i = 0; i < table.length(); i++) {
            JSONObject row = table.getJSONObject(i);
            if (row.has(fieldToMatch) && row.getString(fieldToMatch).equals(valueToMatch)) {
                row.put(fieldToMatch, newValue); // Update the value
                updateAndWrite(table); // Write the updated table to the file
                return true;
            }
        }
        return false;
    }

    public void delete(String... content) {
        if (!isSourceInitialized() || !isTableInitialized()) return;

        JSONObject recordToMatch = process(content); // Create a JSONObject from input
        if (recordToMatch == null) return;

        JSONArray table = this.getTable();
        // Find and remove the matching record
        for (int i = 0; i < table.length(); ++i) {
            if (table.getJSONObject(i).similar(recordToMatch)) {
                table.remove(i);
                updateAndWrite(table); // Write the updated table to the file
                System.out.println("Record successfully deleted.");
                return;
            }
        }

        System.err.println("No matching record found to delete.");
    }

    @Override
    protected void write() {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(super.source))) {
            writer.write(this.getTable().toString(4)); // Pretty-print JSON
        } catch (IOException e) {
            System.err.println("Error writing to file: " + e.getMessage());
        }
    }

    @Override
    public String toString() {
        JSONArray table = this.getTable();
        StringBuilder message = new StringBuilder();
        // Convert each row to a string and append to the message
        for (int i = 0; i < table.length(); i++) {
            message.append(table.getJSONObject(i).toString()).append('\n');
        }
        return message.toString();
    }

    @Override
    protected JSONArray retrieveData(FileFormat format) {
        JSONArray data = new JSONArray();
        try (BufferedReader jsonReader = new BufferedReader(new FileReader(this.source))) {
            StringBuilder jsonContent = new StringBuilder();
            String line;
            // Read the entire JSON file
            while ((line = jsonReader.readLine()) != null) {
                jsonContent.append(line);
            }
            data = new JSONArray(jsonContent.toString()); // Parse JSON data
        } catch (IOException e) {
            System.err.println("Error reading file: " + e.getMessage());
        }
        return data;
    }

    public JSONObject getHeader() {
        if (isTableInitialized()) {
            return getTable().getJSONObject(0); // First row is the header
        } else {
            System.err.println(DriverExceptionsCodes.TABLE);
            return null;
        }
    }

    @Override
    protected DriverManager<JSONArray> cloneDriver(String newSource) {
        JSONDriver newDriver = new JSONDriver();
        newDriver.source = newSource;
        newDriver.format = this.format;
        DriverFactory.DRIVERS.put(newSource, this.getTable());
        return newDriver;
    }

    @Override
    @SuppressWarnings("unchecked")
    public boolean equals(Object o) {
        if (!(o instanceof DriverManager<?>)) return false;
        DriverManager<JSONArray> comparison = (DriverManager<JSONArray>) o;
        if (!this.format.equals(comparison.format)) return false;
        JSONArray thisData = this.getTable();
        JSONArray thatData = comparison.getTable();
        if (thisData == null && thatData == null) return true;
        if (thisData == null || thatData == null) return false;
        if (thisData.length() != thatData.length()) return false;
        if (thisData.getClass().equals(thatData.getClass()))
            for (int i = 0; i < thisData.length(); ++i)
                if (!thisData.getJSONObject(i).equals(thatData.getJSONObject(i))) return false;
        return false;
    }

    // Utility methods for reusable validations
    private boolean isSourceInitialized() {
        if (this.source == null) {
            System.err.println("Source is not initialized.");
            return false;
        }
        return true;
    }

    private boolean isTableInitialized() {
        if (this.getTable().isEmpty()) {
            System.err.println("Table is empty or not initialized.");
            return false;
        }
        return true;
    }
}


