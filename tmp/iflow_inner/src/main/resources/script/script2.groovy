import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;
def Message processData(Message message) {
    
       def header = message.getHeaders();
       String httpStatusCode = header.get("HTTPStatusCode");
       
       if("500".equals(httpStatusCode)){
           throw new Exception("HTTP Status Code 500");
       }

       return message;
}