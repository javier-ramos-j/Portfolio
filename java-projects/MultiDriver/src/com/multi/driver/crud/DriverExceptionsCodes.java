package com.multi.driver.crud;

/**
 * DriverExceptionCodes is useful for printing error messages when similar
 * circumstances occur in different drivers or in different methods within
 * a driver.
 */

public enum DriverExceptionsCodes {

	PATH("Check correct path"),
	NUM("Check correct number of field"),
	FIELDS("Check if field exists"),
	RECORD("Check if record exists"),
	TABLE("No such table found"),
	FILE("Invalid file to perform actions"),
	OTHER("Check on specific requirements to solve this issue");
	
	private String message;
	
	private DriverExceptionsCodes(String message) {
		this.message = message;
	}
	
	@Override
	public String toString() {
		return this.message;
	}
}
