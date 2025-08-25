package com.multi.driver.crud;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.json.JSONObject;


//Functional interface defined in JSONDriver, used to manipulate JSON data

public interface JSONObjectCreator {
	default JSONObject process(String... contentArray){
		JSONObject record = new JSONObject();
        List<String> errors = new ArrayList<>();

        // Parse each "key:value" pair from the input array
        Arrays.stream(contentArray)
                .map(pair -> pair.split(":", 2)) // Split each string into key and value
                .forEach(keyAndValues -> {
                    if (keyAndValues.length != 2) {
                        // Collect errors for malformed inputs
                        errors.add("Wrong arguments introduced: " + Arrays.toString(keyAndValues));
                    } else {
                        // Add key-value pairs to the record
                        record.put(keyAndValues[0].trim(), keyAndValues[1].trim());
                    }
                });

        // If there are errors, print them and return null
        if (!errors.isEmpty()) {
            errors.forEach(System.err::println);
            return null;
        }

        return record; // Return the created JSONObject
	}
}
