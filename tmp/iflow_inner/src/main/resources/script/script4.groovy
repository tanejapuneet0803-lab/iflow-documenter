import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;
def Message processData(Message message) {

    def properties = message.getProperties();
    Integer exceptionCounter = properties.get("EXCEPTION_COUNTER");

    if(exceptionCounter > 3){
        throw new Exception("Exception occured. Maximum number of retries failed.");
    }
      
    return message;
}