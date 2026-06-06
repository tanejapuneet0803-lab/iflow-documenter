import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;
def Message processData(Message message) {
    
    def headers = message.getHeaders();
    String userId = headers.get("USER_ID");
    
    // only if not push event
    if(userId == null || "".equals(userId)){
        // wait 5 minutes
        sleep(300000);
    }
       
    return message;
}