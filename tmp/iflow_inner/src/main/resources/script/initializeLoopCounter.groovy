import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;

def Message processData(Message message) {
	
	// Initialize Loop Counter and set property
	Integer loopCounter = 0;
	message.setProperty("loopCounter", loopCounter);
	
	return message;
}

