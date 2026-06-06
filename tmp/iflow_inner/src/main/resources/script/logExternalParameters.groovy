import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;

def Message processData(Message message) {
	
	//Properties  
	def pmap = message.getProperties();
    def messageLog = messageLogFactory.getMessageLog(message);

    String enableLogging = pmap.get("ENABLE_LOGGING");
    String fullTransmissionStartDate = pmap.get("FULL_TRANSMISSION_START_DATE");
    String lastModifiedDate = pmap.get("LAST_MODIFIED_DATE");
    String company = pmap.get("COMPANY");
    String companyTerritoryCode = pmap.get("COMPANY_TERRITORY_CODE");
    String employeeClass = pmap.get("EMPLOYEE_CLASS");
    String contingentWorkers = pmap.get("CONTINGENT_WORKERS");
    String personIdExternal = pmap.get("PERSON_ID_EXTERNAL");
    String userId = pmap.get("USER_ID");
    String externalCostCenterIDUsage = pmap.get("EXTERNAL_COST_CENTER_ID_USAGE");
    String multipleJobEvents = pmap.get("MULTIPLE_JOB_EVENTS");
    String userSetLastModifiedDateTime = pmap.get("USER_SET_LAST_MODIFIED_DATE_TIME");
    String pushURL = pmap.get("SFSF_EC_PUSH_URL");
    String enableTimeDependentEmployeeSelection = pmap.get("ENABLE_TIME_DEPENDENT_EMPLOYEE_SELECTION");
    String matchingEmploymentsOnly = pmap.get("MATCHING_EMPLOYMENTS_ONLY");
    String initiateFullLoad = pmap.get("INITIATE_FULL_LOAD");
    String retryWaitTime = pmap.get("RETRY_WAIT_TIME_MS");
    
    //initialize user ID
    if(userId == null){
    	userId = "";
    	message.setProperty("USER_ID", userId);
    }
    
    // Prepare string for MPL attachment content
 	String externalParameters;
 	externalParameters = "ENABLE_LOGGING = " + enableLogging;
 	externalParameters = externalParameters + "\nFULL_TRANSMISSION_START_DATE = " + fullTransmissionStartDate;
 	externalParameters = externalParameters + "\nCOMPANY = " + company;
 	externalParameters = externalParameters + "\nCOMPANY_TERRITORY_CODE = " + companyTerritoryCode;
 	externalParameters = externalParameters + "\nEMPLOYEE_CLASS = " + employeeClass;
 	externalParameters = externalParameters + "\nCONTINGENT_WORKERS = " + contingentWorkers;
 	externalParameters = externalParameters + "\nPERSON_ID_EXTERNAL = " + personIdExternal;
 	externalParameters = externalParameters + "\nUSER_ID = " + userId;
 	externalParameters = externalParameters + "\nEXTERNAL_COST_CENTER_ID_USAGE = " + externalCostCenterIDUsage;
 	externalParameters = externalParameters + "\nMULTIPLE_JOB_EVENTS = " + multipleJobEvents;
 	externalParameters = externalParameters + "\nUSER_SET_LAST_MODIFIED_DATE_TIME = " + userSetLastModifiedDateTime;
 	externalParameters = externalParameters + "\nSFSF_EC_PUSH_URL = " + pushURL;
 	externalParameters = externalParameters + "\nENABLE_TIME_DEPENDENT_EMPLOYEE_SELECTION = " + enableTimeDependentEmployeeSelection;
 	externalParameters = externalParameters + "\nMATCHING_EMPLOYMENTS_ONLY = " + matchingEmploymentsOnly;
 	externalParameters = externalParameters + "\nINITIATE_FULL_LOAD = " + initiateFullLoad;
 	externalParameters = externalParameters + "\nRETRY_WAIT_TIME_MS = " + retryWaitTime;
 	
 	// Log parameters	
 	if (messageLog != null) {
 		messageLog.addAttachmentAsString("Externalized Parameters", externalParameters, "text/plain");
 	}
	
	return message;
}

