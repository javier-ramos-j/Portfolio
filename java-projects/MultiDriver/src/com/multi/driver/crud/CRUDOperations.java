package com.multi.driver.crud;


/**
 * This interface is implemented in specific files drivers, ensuring they implement
 * create, read, and update. Delete is not in this interface, as it differs from driver
 * to driver.
 */
public interface CRUDOperations{
	boolean create(String ... content);
	boolean read(String field, String record);
	boolean update(String fieldToMatch, String valueToMatch, String newValue);
}
