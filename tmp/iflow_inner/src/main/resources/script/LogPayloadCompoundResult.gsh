import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;
import java.lang.Exception;

def Message processData(Message message) {

	def pmap = message.getProperties();
	String enableLogging = pmap.get("ENABLE_LOGGING");
	String processVariant = pmap.get("PROCESS_VARIANT");
	
	Integer loopCounter = message.getProperty("loopCounter");
	loopCounter = loopCounter + 1;
	message.setProperty("loopCounter", loopCounter);
	
	if(enableLogging != null && enableLogging.toUpperCase().equals("TRUE")){
		def body = message.getBody(java.lang.String) as String;
		def messageLog = messageLogFactory.getMessageLog(message);
		if(messageLog != null){
			if(processVariant != null && processVariant.equals("1")){
				messageLog.addAttachmentAsString("Payload " + loopCounter.toString() + " Compound API Result", body, "text/xml");
			}else{
				throw new Exception("process_variant property undefined");
			}
		}
	}
       
	return message;
}