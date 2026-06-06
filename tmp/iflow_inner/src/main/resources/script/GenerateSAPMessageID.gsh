import com.sap.gateway.ip.core.customdev.util.Message;

def Message processData(Message message) {

	//Set SAP Message IDs
	messIDEx = java.util.UUID.randomUUID().toString();
	messID = messIDEx.replaceAll("-", "").toUpperCase();
	message.setHeader("SapMessageId", messID);
	message.setHeader("SapMessageIdEx", messIDEx);


	return message;
}