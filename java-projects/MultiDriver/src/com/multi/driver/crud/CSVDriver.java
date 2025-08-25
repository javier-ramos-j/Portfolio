package com.multi.driver.crud;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

// A driver for managing CSV files, implementing basic CRUD operations.

public class CSVDriver extends DriverManager<List<String[]>>{


    public CSVDriver() {
    }

    // Constructor that sets the source file and format to CSV.

    public CSVDriver(String source) {
        super(source, FileFormat.CSV);
    }

    // Sets the connection source and ensures the format is CSV.
    public void setConnection(String source) {
        super.setConnection(source, FileFormat.CSV);
    }

    // Removes invisible characters (control characters) from a string.
    private static String removeInvisibleCharacters(String input) {
        return input.replaceAll("[\\p{C}]", ""); // Removes control characters
    }

    // Gets the index of a field in the header row.

    private int getFieldIndex(String fieldName) throws DriverException {
        String[] header = this.getHeader();
        for (int i = 0; i < header.length; i++) {
            if (removeInvisibleCharacters(header[i]).equals(removeInvisibleCharacters(fieldName))) {
                return i;
            }
        }
        throw new DriverException("Field not found: " + fieldName);
    }

    // Adds a new row to the CSV table.

    @Override
    public boolean create(String... content) {
        List<String[]> table = this.getTable();
        // Ensure the content matches the column count
        if (content.length == table.get(0).length) {
            // Avoid duplicate primary keys
            if (table.stream().anyMatch(row -> row[0].equals(content[0]))) return false;
            table.add(content);
            updateAndWrite(table);
            return true;
        } else {
            System.err.println(DriverExceptionsCodes.NUM);
            return false;
        }
    }

    //Reads a record from the CSV table based on a field and value.

    @Override
    public boolean read(String field, String record) {
        try {
            int indexField = getFieldIndex(field);
            List<String[]> table = this.getTable();

            // Search for the record and display it
            table.stream()
                .filter(row -> row[0].equals(record)) //Filters all rows that equal record
                .findFirst() //Stops when finding the first element to satisfy the filter condition
                .ifPresentOrElse( //If present, executes a Consumer
                    row -> {
                        System.out.println("Row found: " + Arrays.toString(row));
                        System.out.println("Field " + field + ": " + row[indexField]);
                    }, //If not present, execute a Runnable (receives nothing, return nothing)
                    () -> System.err.println("Record not found: " + record)
                );
            return true;
        } catch (DriverException e) {
            System.err.println("Error reading record: " + e.getMessage());
            return false;
        }
    }

    // Updates a field in a record that matches a specific value.

    @Override
    public boolean update(String fieldToMatch, String valueToMatch, String newValue) {
        try {
            int indexField = getFieldIndex(fieldToMatch);
            List<String[]> table = this.getTable();

            boolean updated = table.stream()
                .filter(row -> row[indexField].equals(valueToMatch))
                .peek(row -> row[indexField] = newValue)
                .findFirst()
                .isPresent();

            if (updated) {
                updateAndWrite(table);
                System.out.println("Updated record with field: \"" + fieldToMatch + "\", to new value: \"" + newValue + "\"");
                return true;
            } else {
                throw new DriverException("Record not found for update.");
            }
        } catch (DriverException e) {
            System.err.println("Error updating record: " + e.getMessage());
            return false;
        }
    }

    //Deletes a record that matches a specific value in the primary key column.
    public void delete(String recordToMatch) {
        try {
            List<String[]> table = this.getTable();
            boolean removed = table.removeIf(row -> row[0].equals(recordToMatch));

            if (removed) {
                updateAndWrite(table);
                System.out.println("Record deleted: " + recordToMatch);
            } else {
                throw new DriverException("Record not found: " + recordToMatch);
            }
        } catch (DriverException e) {
            System.err.println("Error deleting record: " + e.getMessage());
        }
    }

    //Writes the table data back to the CSV file.

    @Override
    protected void write() {
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(this.source))) {
            this.getTable().stream()
                .map(row -> String.join(",", row))
                .forEach(line -> {
                    try {
                        writer.write(line);
                        writer.newLine();
                    } catch (IOException e) {
                        throw new UncheckedIOException(e);
                    }
                });
        } catch (IOException e) {
            System.err.println("Error writing to file: " + e.getMessage());
        }
    }

    /**
     * Reads data from the CSV file and parses it into a table.
     * csvReader.lines() creates a Stream<String>, therefore, it is
     * unnecessary to declare it like csvReader.stream() or others.
     */
    @Override
    protected List<String[]> retrieveData(FileFormat format) throws DriverException {
        List<String[]> data = new ArrayList<>();
        try (BufferedReader csvReader = new BufferedReader(new FileReader(this.source))) {
            csvReader.lines()
                     .map(line -> line.split(","))
                     .forEach(data::add);
        } catch (IOException e) {
            throw new DriverException("Error reading CSV file: " + e.getMessage());
        }
        return data;
    }

    //Retrieves the header row of the CSV table.
    public String[] getHeader() {
        try {
            return getTable().get(0);
        } catch (Exception e) {
            System.err.println(DriverExceptionsCodes.TABLE);
            return null;
        }
    }

    //Creates a copy of the current driver with a new source file.

    @Override
    protected DriverManager<List<String[]>> cloneDriver(String newSource) {
        CSVDriver newDriver = new CSVDriver();
        newDriver.source = newSource;
        newDriver.format = this.format;
        DriverFactory.DRIVERS.put(newSource, this.getTable());
        return newDriver;
    }

    //Converts the table to a string representation.

    @Override
    public String toString() {
        StringBuilder message = new StringBuilder();
        List<String[]> table = this.getTable();
        table.forEach(row -> message.append(String.join(", ", row)).append('\n'));
        return message.toString();
    }

    /**
     * Compares this driver to another object for equality.
     * if it is a driver of the same format, checks if they have the same
     * content.
     */
    @Override
    public boolean equals(Object o) {
        if (!(o instanceof CSVDriver)) return false;
        CSVDriver comparison = (CSVDriver) o;
        if (!this.format.equals(comparison.format)) return false;
        List<String[]> thisData = this.getTable();
        List<String[]> thatData = comparison.getTable();
        if (thisData == null && thatData == null) return true;
        if (thisData == null || thatData == null) return false;
        if (thisData.size() != thatData.size()) return false;

        for (int i = 0; i < thisData.size(); ++i) {
            String[] thisRow = thisData.get(i);
            String[] thatRow = thatData.get(i);
            if (thisRow.length != thatRow.length) return false;
            for (int j = 0; j < thisRow.length; ++j)
                if (!thisRow[j].equals(thatRow[j])) return false;
        }
        return true;
    }
}

