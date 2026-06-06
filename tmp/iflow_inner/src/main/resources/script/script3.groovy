import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;

def Message processData(Message message) {
	
	// Initialize Exception Counter and set property
	Integer exceptionCounter = 0;
	message.setProperty("EXCEPTION_COUNTER", exceptionCounter);
	
	return message;
}