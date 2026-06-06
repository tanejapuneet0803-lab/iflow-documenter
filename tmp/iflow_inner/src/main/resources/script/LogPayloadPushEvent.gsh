import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;

def Message processData(Message message) {
	
	// Initialize Loop Counter and set property
	Integer loopCounter = 0;
	message.setProperty("loopCounter", loopCounter);
	
	// Logging
	def pmap = message.getProperties();
	String enableLogging = pmap.get("ENABLE_LOGGING");
	String userID = pmap.get("USER_ID");
	
	if(enableLogging != null && enableLogging.toUpperCase().equals("TRUE")){
		def body = message.getBody(java.lang.String) as String;
		def messageLog = messageLogFactory.getMessageLog(message);
		if(messageLog != null){
			messageLog.addAttachmentAsString("Payload EC Push Event", body, "text/xml");
		}
	}
	
	//Error handling for invalid push event
    if(userID == null || (userID != null && userID.equals(""))){
    	throw new Exception("Invalid push event message. The user ID could not be read, please check the configuration in Employee Central.   ");
    }
       
	return message;
}