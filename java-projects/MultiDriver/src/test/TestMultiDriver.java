package test;

import java.util.Arrays;

import com.multi.driver.crud.CSVDriver;
import com.multi.driver.crud.DriverFactory;
import com.multi.driver.crud.JSONDriver;

public class TestMultiDriver {

	public static void main(String[] args) {
		//CSV
		CSVDriver csvDriver1 = new CSVDriver();
		CSVDriver csvDriver2 = new CSVDriver("C:\\Users\\Javier\\OneDrive\\Documentos\\ITESO\\Trabajos ITESO\\Software_y_Tecnologias_de_Desarrollo\\Programacion_Orientada_a_Objetos\\csv_example_copy.csv");
		CSVDriver csvDriver3 = new CSVDriver("C:\\Users\\Javier\\OneDrive\\Documentos\\ITESO\\Trabajos ITESO\\Software_y_Tecnologias_de_Desarrollo\\Programacion_Orientada_a_Objetos\\csv_example_copy.csv");
		csvDriver1.setConnection("C:\\Users\\Javier\\OneDrive\\Documentos\\ITESO\\Trabajos ITESO\\Software_y_Tecnologias_de_Desarrollo\\Programacion_Orientada_a_Objetos\\csv_example.csv");
		System.out.println(csvDriver2.equals(csvDriver1));
		System.out.println(csvDriver1);
		csvDriver1.create("4", "Juan", "Ramirez", "Colombia");
		System.out.println(csvDriver1);
		csvDriver1.read("Surname", "4");
		System.out.println("Header: " + Arrays.toString(csvDriver1.getHeader()));
		csvDriver1.update("Name", "Juan", "Jose");
		System.out.println(csvDriver1);
		csvDriver1.delete("4");
		System.out.println(csvDriver1);
		
		//JSON
		JSONDriver jsonDriver1 = new JSONDriver();
		jsonDriver1.setConnection("C:\\Users\\Javier\\OneDrive\\Documentos\\ITESO\\Trabajos ITESO\\Software_y_Tecnologias_de_Desarrollo\\Programacion_Orientada_a_Objetos\\json_test.json");
		System.out.println(jsonDriver1);
		jsonDriver1.create("city:New Orleans","name:Louis","age:60");
		System.out.println(jsonDriver1);
		jsonDriver1.create("city:Miami","name:Clark","age:40");
		jsonDriver1.update("city", "Atlanta", "Dallas");
		System.out.println(jsonDriver1);
		jsonDriver1.read("city", "Boston");
		System.out.println(jsonDriver1);
		jsonDriver1.delete("city:Dallas","name:Clark","age:40");
		jsonDriver1.delete("city:New Orleans","name:Louis","age:60");
		System.out.println(jsonDriver1);
		
		
		//Close drivers
		System.out.println(DriverFactory.getNumberOfDrivers());
		csvDriver1.closeConnection();
		System.out.println(DriverFactory.getNumberOfDrivers());
		csvDriver2.closeConnection();
		System.out.println(DriverFactory.getNumberOfDrivers());
		jsonDriver1.closeConnection();
		System.out.println(DriverFactory.getNumberOfDrivers());
	}
	
}
