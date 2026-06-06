import com.sap.gateway.ip.core.customdev.util.Message;
import java.util.HashMap;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Calendar;
import java.lang.Exception;

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
    String processVariant = pmap.get("PROCESS_VARIANT");
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
    
    //Error handling for external parameters
    if(enableLogging == null || (!enableLogging.equals("TRUE") && !enableLogging.equals("FALSE"))){
    	throw new Exception("Configuration Error: Please enter either TRUE or FALSE in the parameter ENABLE_LOGGING.   ");
    }
    if(fullTransmissionStartDate == null || fullTransmissionStartDate.length() < 10){ 
    	throw new Exception("Configuration Error: Please enter FULL_TRANSMISSION_START_DATE in the format yyyy-MM-dd.   ");
    }
    if(externalCostCenterIDUsage == null || (!externalCostCenterIDUsage.toUpperCase().equals("TRUE") && !externalCostCenterIDUsage.toUpperCase().equals("FALSE"))){
    	throw new Exception("Configuration Error: Please enter either TRUE or FALSE in the parameter EXTERNAL_COST_CENTER_ID_USAGE.   ");
    }
    if(multipleJobEvents == null || (!multipleJobEvents.toUpperCase().equals("TRUE") && !multipleJobEvents.toUpperCase().equals("FALSE"))){
    	throw new Exception("Configuration Error: Please enter either TRUE or FALSE in the parameter MULTIPLE_JOB_EVENTS.   ");
    }
    if(enableTimeDependentEmployeeSelection == null || (!enableTimeDependentEmployeeSelection.toUpperCase().equals("TRUE") && !enableTimeDependentEmployeeSelection.toUpperCase().equals("FALSE"))){
    	throw new Exception("Configuration Error: Please enter either TRUE or FALSE in the parameter ENABLE_TIME_DEPENDENT_EMPLOYEE_SELECTION.   ");
    }
    if(matchingEmploymentsOnly == null || (!matchingEmploymentsOnly.toUpperCase().equals("TRUE") && !matchingEmploymentsOnly.toUpperCase().equals("FALSE"))){
    	throw new Exception("Configuration Error: Please enter either TRUE or FALSE in the parameter MATCHING_EMPLOYMENTS_ONLY.   ");
    }
    if(retryWaitTime != null){
        int retryWaitTimeInteger = retryWaitTime.toInteger();
        // longer than 10 minutes
        if(retryWaitTimeInteger > 600000 || retryWaitTimeInteger < 1){
            throw new Exception("Invalid value for parameter RETRY_WAIT_TIME_MS. Please enter a value between 1 and 600000.   ");
        }
    }
    
    
    
    //Set general object list for select statement
    String objectsSelectStatement = "person, personal_information, address_information, email_information, phone_information, employment_information, job_information, payment_information, global_assignment_information, job_relation";
    
    if(contingentWorkers != null && (contingentWorkers.equals("2") || contingentWorkers.equals("3"))){
        objectsSelectStatement = objectsSelectStatement + ", workorder";
    }
    
    message.setProperty("OBJECTS_SELECT_STATEMENT", objectsSelectStatement);
    if(messageLog != null){
		messageLog.setStringProperty("OBJECTS_SELECT_STATEMENT: ", objectsSelectStatement);
	}
  	
  	//Only process for process_variant = 1
  	if(processVariant != null && processVariant.equals("1")){
  		
  		if(initiateFullLoad != 'TRUE'){
  		    //Set ECERP_LAST_MODIFIED_DATE
      		if(lastModifiedDate == null || lastModifiedDate.equals("") || lastModifiedDate.equals("null")){
      			//Get USER_SET_LAST_MODIFIED_DATE_TIME
      			lastModifiedDate = userSetLastModifiedDateTime;
      		}
      		if(lastModifiedDate == null || lastModifiedDate.equals("") || lastModifiedDate.equals("null") || lastModifiedDate.length() < 20){
      		    if((userId == null || userId.equals("")) && (personIdExternal == null || personIdExternal.equals(""))){
      			    throw new Exception("Configuration Error: Please enter a valid value for USER_SET_LAST_MODIFIED_DATE_TIME in the format: yyyy-MM-dd'T'HH:mm:ss'Z'.   ");
      		    }
      		}else{
      			if(messageLog != null){
      				messageLog.setStringProperty("LAST_MODIFIED_DATE: ", lastModifiedDate);
      			}
      		}
  		}
  		
  		//Build dynamic where statement
  		String queryPersonID = "";
  		String queryLastModifiedDate = "";
  		String queryUserId = "";

  		//If user Id parameter is set use it
  		if(userId != null && !userId.equals("")){
  			
  			// add multi-valued selection parameter for user id to where clause 
  			userId = userId.replaceAll(",", "', '");
  			queryUserId = "user_id IN ('" + userId + "')";
  			
  		}
  		//If person_id_external filter parameter is set use it
  		else if(personIdExternal != null && !personIdExternal.equals("")){
  			
  			// add multi-valued selection parameter for person id to where clause 
  			personIdExternal = personIdExternal.replaceAll(" ", "");
  			personIdExternal = personIdExternal.replaceAll(",", "', '");
  			queryPersonID = "person_id_external IN ('" + personIdExternal + "')";
  		
  		//otherwise use last_modified_date
  		}else if(initiateFullLoad != 'TRUE'){
  			
  			//add selection parameter for last modified date
  			queryLastModifiedDate = "last_modified_on >= to_datetime('" + lastModifiedDate.toString().substring(0,19) + "Z" + "')";
  			
  		}
  		
  		//Set USER_ID_PARAMETER
  		message.setProperty("USER_ID_PARAMETER", queryUserId);
  		if(messageLog != null){
  			messageLog.setStringProperty("USER_ID_PARAMETER ", queryUserId);
  		}
  		
  		//Set PERSON_ID_EXTERNAL_PARAMETER
  		message.setProperty("PERSON_ID_EXTERNAL_PARAMETER", queryPersonID);
  		if(messageLog != null){
  			messageLog.setStringProperty("PERSON_ID_EXTERNAL_PARAMETER ", queryPersonID);
  		}
  		
  		//Set LAST_MODIFIED_DATE_PARAMETER
  		message.setProperty("LAST_MODIFIED_DATE_PARAMETER", queryLastModifiedDate);
  		if(messageLog != null){
  			messageLog.setStringProperty("LAST_MODIFIED_DATE_PARAMETER ", queryLastModifiedDate);
  		}
  		
  	}
    
	String query = "";
	
	if(initiateFullLoad != 'TRUE'){
	    query = query + " AND ";
	}
	
	// add filter parameter for hiringNotCompleted
	query = query + " hiringNotCompleted = 'false'";
	
	// only replicate Standard Assignment and Global Assignment
	query = query + " AND assignment_class IN ('ST','GA')";
	
	// add multi-valued selection parameter for company to where clause 
	// format: ... IN ('Company1','Company2')
	if (company != null && !company.equals("") && !company.equals("<company>")) {
		company_split = company.split(",");
		for (int j=0; j < company_split.length; j++) {
			if (j==0) 
				company = "'" + company_split[j].trim() + "'";
			else
				company = company + ",'" + company_split[j].trim() + "'"; 	        		        	
		}
		if(matchingEmploymentsOnly != null && matchingEmploymentsOnly.toUpperCase().equals("TRUE")){
			query = query + " AND employment_information_company IN (" + company + ")";
		}else{
			query = query + " AND company IN (" + company + ")";
		}    	  
	}
	
	// add multi-valued selection parameter for company territory code to where clause 
	// format: ... IN ('CompanyTerritoryCode1','CompanyTerritoryCode2')
	if(companyTerritoryCode != null && !companyTerritoryCode.equals("") && !companyTerritoryCode.equals("<country>")) {
	    companyTerritoryCode_split = companyTerritoryCode.split(",");
		for (int j=0; j < companyTerritoryCode_split.length; j++) {
			if (j==0) 
				companyTerritoryCode = "'" + companyTerritoryCode_split[j].trim() + "'";
			else
				companyTerritoryCode = companyTerritoryCode + ",'" + companyTerritoryCode_split[j].trim() + "'"; 	        		        	
		}
		if(matchingEmploymentsOnly != null && matchingEmploymentsOnly.toUpperCase().equals("TRUE")){
			query = query + " AND employment_information_country IN (" + companyTerritoryCode + ")";
		}else{
			query = query + " AND company_territory_code IN (" + companyTerritoryCode + ")";
		}   
	}
	
	// add multi-valued selection parameter for employee class to where clause 
	// format: ... IN ('employeeClass1','employeeClass2')
	if(employeeClass != null && !employeeClass.equals("") && !employeeClass.equals("<employee_class>")) {
		employeeClass_split = employeeClass.split(",");
		for (int k=0; k < employeeClass_split.length; k++) {
			if (k==0) 
				employeeClass = "'" + employeeClass_split[k].trim() + "'";
			else
				employeeClass = employeeClass + ",'" + employeeClass_split[k].trim() + "'"; 	        		        	
		} 	  	
		query = query + " AND employee_class IN (" + employeeClass + ")";	   
	}
	
	// add selectFromDate if ENABLE_TIME_DEPENDENT_EMPLOYEE_SELECTION is enabled
	if ("TRUE".equals(enableTimeDependentEmployeeSelection.toUpperCase()) || (matchingEmploymentsOnly != null && matchingEmploymentsOnly.toUpperCase().equals("TRUE"))) {
	// check if at least one filter parameter is filled
		if((company != null && !company.equals("") && !company.equals("<company>"))
				|| (companyTerritoryCode != null && !companyTerritoryCode.equals("") && !companyTerritoryCode.equals("<country>"))
				|| (employeeClass != null && !employeeClass.equals("") && !employeeClass.equals("<employee_class>"))){
			query = query + " AND selectFromDate = to_date('" + fullTransmissionStartDate + "','yyyy-MM-dd')";
		}
	}

    // add selection parameter for sadditional selection of contingent workers to where clause 
	if(contingentWorkers.equals("1")){
		query = query + " AND isContingentWorker IN ('0')";
	}else if(contingentWorkers.equals("2")) {
    	query = query + " AND isContingentWorker IN ('1')";
    }else if(contingentWorkers.equals("3")) {
    	query = query + " AND isContingentWorker IN ('0','1')";
    }else{
    	//stop processing and log error message
    	throw new Exception("Configuration Error: \"" + contingentWorkers + "\" is not a valid input for external parameter CONTINGENT_WORKERS. Please enter either 1, 2, or 3.   ");
    }
    
    // add selection parameter for full transmission start date 
	if(fullTransmissionStartDate != null && fullTransmissionStartDate != "") {	
		query = query + " AND effective_end_date >= to_date('" + fullTransmissionStartDate +"')";
	}

	//Set FILTER_PARAMETERS
	message.setProperty("FILTER_PARAMETERS", query);
	if(messageLog != null){
		messageLog.setStringProperty("FILTER_PARAMETERS: ", query);
	}
	
	//*** Set SFAPI Parameters ***
	
	String SFAPIParameters = "agent=S4CloudHCI;purgeOptions=validateEffectiveEndDateFilter";
	
	if(externalCostCenterIDUsage.toUpperCase().equals("TRUE")) {
		SFAPIParameters = SFAPIParameters + ";externalKeyMapping=costCenter";
	}
	if(multipleJobEvents.toUpperCase().equals("TRUE")) {
		SFAPIParameters = SFAPIParameters + ";resultOptions=allJobChangesPerDay";
	}
	
	//Filtering "Global Information"
	
    if(matchingEmploymentsOnly != null && matchingEmploymentsOnly.toUpperCase().equals("TRUE")){
			if ((company != null && !company.equals("") && !company.equals("<company>")) ||
			(companyTerritoryCode != null && !companyTerritoryCode.equals("") && !companyTerritoryCode.equals("<country>"))) {
	        SFAPIParameters = SFAPIParameters + ";suppressUnwantedGlobalInfo=yes"
			}
    }
	
	message.setProperty("SFAPI_PARAMETERS", SFAPIParameters);
	
	return message;

}