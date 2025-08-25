package com.multi.driver.crud;

/**
 * FileFormat enum is in charge of assigning a file format to each driver,
 * useful for creating specific drivers,
 */


public enum FileFormat {
	CSV, JSON, OTHER;
	
	public static FileFormat determineFormat(String source) {
	    if (source.toLowerCase().endsWith(".json")) {
	        return FileFormat.JSON;
	    } else if (source.toLowerCase().endsWith(".csv")) {
	        return FileFormat.CSV;
	    } else {
	        return FileFormat.OTHER;
	    }
	}
}
