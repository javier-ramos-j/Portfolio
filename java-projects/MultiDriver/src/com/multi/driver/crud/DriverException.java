package com.multi.driver.crud;

import java.io.IOException;

/**
 * 
 */


@SuppressWarnings("all")
public class DriverException extends IOException {

	public int errorCode;
	
	public DriverException() {
		
	}

	public DriverException(String message) {
		super(message);
	}

	public DriverException(Throwable cause) {
		super(cause);
	}

	public DriverException(String message, Throwable cause) {
		super(message, cause);
	}
	
	public DriverException(String message, Throwable cause, int errorCode) {
		super(message, cause);
		this.errorCode = errorCode;
	}
	
	public int getErrorCode() {
		return this.errorCode;
	}

}
