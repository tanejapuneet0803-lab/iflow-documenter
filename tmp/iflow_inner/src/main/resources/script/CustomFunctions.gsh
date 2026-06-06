import java.util.UUID;
import com.sap.it.api.mapping.MappingContext;
import java.text.DateFormat;
import java.text.SimpleDateFormat;

def String getPropertyValue(String property, MappingContext context){
  return context.getProperty(property);
}

def String getHeaderValue(String header, MappingContext context){
  return context.getHeader(header);
}

def String generateGUID(String input){
  return UUID.randomUUID().toString();
}

def String convertUUIDtoID(String UUID){
  return UUID.replaceAll("-", "").toUpperCase();
}

def String convertIDtoUUID(String ID){
  ID = ID.toLowerCase();
  return ID.substring(0,8) + '-' + ID.substring(8,12) + '-' + ID.substring(12,16) + '-' + ID.substring(16,20) + '-' + ID.substring(20,32);
}

def String actualDateTime(String input){
  DateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'");
  Date date = new Date();
  return dateFormat.format(date);
}

def String substring(int startIndex, int endIndex, String input){
	String returnValue = "";
	if(input != null && startIndex <= endIndex && startIndex >= 0){
		if(startIndex == 0 && endIndex <= input.length()){
			returnValue = input.substring(startIndex, endIndex);
		}else if(startIndex == 0 && endIndex > input.length()){
			returnValue = input; 
		}
	}
	return returnValue;
}

