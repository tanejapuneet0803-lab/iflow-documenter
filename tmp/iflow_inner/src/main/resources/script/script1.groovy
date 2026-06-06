import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;
def Message processData(Message message) {
       
       def properties = message.getProperties();
       Integer exceptionCounter = properties.get("EXCEPTION_COUNTER");
       String retryWaitTime = properties.get("RETRY_WAIT_TIME_MS");
       
       exceptionCounter += 1;
       
       message.setProperty("EXCEPTION_COUNTER", exceptionCounter);
       
       int retryWaitTimeInteger = 10000;
       if(retryWaitTime != null){
           retryWaitTimeInteger = retryWaitTime.toInteger();
       }
       
       if(exceptionCounter <= 3){
           sleep(retryWaitTimeInteger);
       }

       return message;
}