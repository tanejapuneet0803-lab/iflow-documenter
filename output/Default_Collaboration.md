# Default Collaboration

## Summary

**iFlow Name:** Default Collaboration  
**Description:** Employee Mastr Data replication from Employee Central to ERP Payroll  

| Property | Value |
| --- | --- |
| Component Version | 1.1 |
| HTTP Session Handling | onExchange |
| Log Level | All events |
| Server Trace | false |
| Return Exception to Sender | false |
| Allowed Headers | USER_ID |
| Namespace Mapping | `xmlns:ns2=http://notification.event.successfactors.com` |

**Senders:** EC_PUSH_EVENT, Sender1  
**Receivers:** EC_CE_API_QUERY, S4_Cloud, Receiver1  
**Processes:** 9  
**Groovy Scripts:** 14  

## Data Flow Diagram (ASCII)

```
  [Sender1] --ProcessDirect ({{PROCESS_DIRECT_URL}})--> [iFlow Entry]
  [EC_PUSH_EVENT] --SOAP ({{SFSF_EC_PUSH_URL}})--> [iFlow Entry]
       |
       +--> [Scheduled Processing]
       |        +--> (calls) [Query Employee Master Data]
       |        +--> (calls) [Read External Parameters]
       |        +--> (calls) [Write Last Modified Date]
       |        +--> (calls) [Read Last Modified Date]
       |        +--> [Script: initializeLoopCounter.groovy]
       |
       +--> [Push Processing]
       |        +--> (calls) [Read External Parameters]
       |        +--> (calls) [Query Employee Master Data]
       |        +--> [Script: LogPayloadPushEvent.gsh]
       |
       +--> [Process S/4 data]
       |        +--> (calls) [Send data to S/4]
       |        +--> [Script: script3.groovy]
       |
  Sub-processes (called internally):
    [Create Bundle Message and Send to S4]
    [Query Employee Master Data]
    [Send data to S/4]
    [Write Last Modified Date]
    [Read External Parameters]
    [Read Last Modified Date]
       |
       +--> [Receiver1] via ProcessDirect ({{PROCESS_DIRECT_URL}})
       +--> [EC_CE_API_QUERY] via SuccessFactors ({{SFSF_EC_BASE_URL}})
       +--> [S4_Cloud] via SOAP ({{SAP_ERP_ENDPOINT_URL}})
```

## Adapter Configuration

### Sender Adapters

| Name | System | Type | Address | Transport | Message Protocol | Authentication |
| --- | --- | --- | --- | --- | --- | --- |
| ProcessDirect | Sender1 | ProcessDirect | `{{PROCESS_DIRECT_URL}}` | Not Applicable | Not Applicable | - |
| SOAP | EC_PUSH_EVENT | SOAP | `{{SFSF_EC_PUSH_URL}}` | HTTP | SOAP 1.x | {{AUTHENTICATION_PUSH}} |

### Receiver Adapters

| Name | System | Type | Address | Transport | Message Protocol | Authentication |
| --- | --- | --- | --- | --- | --- | --- |
| ProcessDirect | Receiver1 | ProcessDirect | `{{PROCESS_DIRECT_URL}}` | Not Applicable | Not Applicable | - |
| Compound_API_Query | EC_CE_API_QUERY | SuccessFactors | `{{SFSF_EC_BASE_URL}}` | HTTP | SOAP | {{AUTHENTICATION}} |
| SOAP | S4_Cloud | SOAP | `{{SAP_ERP_ENDPOINT_URL}}` | HTTP | Plain SOAP | {{SAP_ERP_enableBasicAuthentication_5}} |

### Additional Adapter Properties

**SOAP**

| Key | Value |
| --- | --- |
| `WSSecurityType` | VerifyMessage |
| `maximumAttachmentSize` | 100 |
| `useWSAddressing` | 0 |
| `soapOptions` | cxfRobust |
| `CheckTimeStamp` | 0 |
| `WSSecurity_SignatureAlgorithm_Inbound` | SHA1 |
| `SigningOrder` | SignBeforeEncryption |
| `clientCertificates` | <row><cell id='clientCertificate.subjectDN'>{{Subject_DN}}</cell><cell id='clientCertificate.issuerDN'>{{Issuer_DN}}</cell></row> |
| `X509TokenAssertion` | WssX509V3Token10 |
| `maximumBodySize` | 40 |
| `messageExchangePattern` | RequestReply |
| `WSSecurity` | None |
| `SaveIncomingSignedMessage` | 0 |
| `SenderBasicSecurityProfileCompliant` | 1 |
| `RecipientTokenIncludeStrategy` | Never |
| `AlgorithmSuiteAssertion` | Basic128Rsa15 |
| `serviceDefinition` | Manual |
| `userRole` | {{USER_ROLE}} |
| `InitiatorTokenIncludeStrategy` | AlwaysToRecipient |

**Compound_API_Query**

| Key | Value |
| --- | --- |
| `sfsfSOAPReceiverDataCenterUrl` | Other |
| `receiveTimeOut` | {{SFSF_EC_TIMEOUT}} |
| `pagesize` | {{SFSF_EC_QUERY_PAGE_SIZE}} |
| `alias` | {{SFSF_EC_LOGON_CREDENTIALS_NAME}} |
| `urlSuffixSOAP` | /sfapi/v1/soap |
| `query` | SELECT ${property.OBJECTS_SELECT_STATEMENT} FROM CompoundEmployee WHERE ${property.USER_ID_PARAMETER} ${property.PERSON_ID_EXTERNAL_PARAMETER} ${property.LAST_MODIFIED_DATE_PARAMETER} ${property.FILTER_PARAMETERS} |
| `proxyType` | default |
| `queryType` | querySync |
| `timeOut` | 1 |
| `batchProcess` | 1 |
| `sfsfSoapAPIParams` | ${property.SFAPI_PARAMETERS} |
| `retryOnFailure` | 1 |
| `operation` | Query |
| `entity` | CompoundEmployee |

**SOAP**

| Key | Value |
| --- | --- |
| `cleanupHeaders` | 1 |
| `privateKeyAlias` | {{PRIVATE_KEY_ALIAS}} |
| `location_id` | {{SAP_CC_LOCATION_ID}} |
| `CompressMessage` | 0 |
| `requestTimeout` | {{SAP_ERP_TIMEOUT}} |
| `allowChunking` | {{SAP_ERP_allowChunking_3}} |
| `proxyType` | {{SAP_ERP_proxyType_2}} |
| `credentialName` | {{SAP_ERP_LOGON_CREDENTIALS_NAME}} |


## Mapping Logic

### Mapping Scripts

**`Mapping.gsh`**  
Mapping.gsh is a Groovy/GSH script used in an SAP CPI iFlow. It reads properties: EXTENSIBILITY_USAGE, FULL_TRANSMISSION_START_DATE, REPLICATION_TARGET_SYSTEM. It sets headers: SapMessageId, SapMessageIdEx.

### Routing Conditions

| Route Name | Expression Type | Condition |
| --- | --- | --- |
| Data found | XML | `/queryCompoundEmployeeResponse/CompoundEmployee` |
| last modified date update | NonXML | `${property.PERSON_ID_EXTERNAL} = '' and ${property.USER_ID} = ''` |
| Route 1 | NonXML | `${property.EXCEPTION_COUNTER} <= '3'` |
| new timestamp | NonXML | `${property.EXECUTION_TIMESTAMP} != null and ${property.EXECUTION_TIMESTAMP} != ''` |

### Script Steps by Process

**Create Bundle Message and Send to S4**

- `LogPayloadERP.gsh` — _Log S/4 Message_
- `Mapping.gsh` — _Mapping of Bundle Message_

**Query Employee Master Data**

- `SetQueryParameter.gsh` — _Build Query_
- `LogPayloadCompoundResult.gsh` — _Log Compound API Result_

**Send data to S/4**

- `script5.groovy` — _wait 5 minutes_

**Scheduled Processing**

- `initializeLoopCounter.groovy` — _Initialize Loop Counter_

**Read External Parameters**

- `logExternalParameters.groovy` — _Log External Parameters_

**Push Processing**

- `LogPayloadPushEvent.gsh` — _Log Payload Push Event_

**Process S/4 data**

- `script3.groovy` — _Init Exception counter_


## Error Handling

### Process: Send data to S/4

**Exception Subprocess:** `Exception Subprocess 1`  

| Step | Type | Script |
| --- | --- | --- |
| Error Start 1 | - | - |
| Restore Body | Enricher | - |
| Send data to S/4 | ProcessCallElement | - |
| End 5 | - | - |
| Check for exception | Script | `script4.groovy` |
| Exception handling | Script | `script1.groovy` |
| Router 3 | ExclusiveGateway | - |

### Scripts with Error / Validation Logic

**`LogPayloadCompoundResult.gsh`**  
LogPayloadCompoundResult.gsh is a Groovy/GSH script used in an SAP CPI iFlow. It reads properties: ENABLE_LOGGING, PROCESS_VARIANT, loopCounter. It sets properties: loopCounter. It validates inputs and raises errors such as: "process_variant property undefined". Notable calls: messageLog.addAttachmentAsString.

**`LogPayloadERP.gsh`**  
LogPayloadERP.gsh is a Groovy/GSH script used in an SAP CPI iFlow. It reads properties: ENABLE_LOGGING, PROCESS_VARIANT, loopCounter. It validates inputs and raises errors such as: "process_variant property undefined". Notable calls: messageLog.addAttachmentAsString.

**`LogPayloadPushEvent.gsh`**  
LogPayloadPushEvent.gsh is a Groovy/GSH script used in an SAP CPI iFlow. It reads properties: ENABLE_LOGGING, USER_ID. It sets properties: loopCounter. It validates inputs and raises errors such as: "Invalid push event message. The user ID could not be read, please check the conf". Notable calls: messageLog.addAttachmentAsString.

**`script2.groovy`**  
script2.groovy is a Groovy/GSH script used in an SAP CPI iFlow. It validates inputs and raises errors such as: "HTTP Status Code 500".

**`script4.groovy`**  
script4.groovy is a Groovy/GSH script used in an SAP CPI iFlow. It validates inputs and raises errors such as: "Exception occured. Maximum number of retries failed.".

**`SetQueryParameter.gsh`**  
SetQueryParameter.gsh is a Groovy/GSH script used in an SAP CPI iFlow. It reads properties: COMPANY, COMPANY_TERRITORY_CODE, CONTINGENT_WORKERS, EMPLOYEE_CLASS, ENABLE_LOGGING, ENABLE_TIME_DEPENDENT_EMPLOYEE_SELECTION, EXTERNAL_COST_CENTER_ID_USAGE, FULL_TRANSMISSION_START_DATE…. It sets properties: FILTER_PARAMETERS, LAST_MODIFIED_DATE_PARAMETER, OBJECTS_SELECT_STATEMENT, PERSON_ID_EXTERNAL_PARAMETER, SFAPI_PARAMETERS, USER_ID, USER_ID_PARAMETER. It validates inputs and raises errors such as: "Configuration Error: Please enter FULL_TRANSMISSION_START_DATE in the format yyy". Notable calls: messageLog.setStringProperty.


## Externalised Parameters

| Parameter | Used In |
| --- | --- |
| `{{AUTHENTICATION}}` | Adapter config |
| `{{AUTHENTICATION_PUSH}}` | Adapter config |
| `{{Issuer_DN}}` | Adapter config |
| `{{PRIVATE_KEY_ALIAS}}` | Adapter config |
| `{{PROCESS_DIRECT_URL}}` | Adapter config |
| `{{SAP_CC_LOCATION_ID}}` | Adapter config |
| `{{SAP_ERP_ENDPOINT_URL}}` | Adapter config |
| `{{SAP_ERP_LOGON_CREDENTIALS_NAME}}` | Adapter config |
| `{{SAP_ERP_TIMEOUT}}` | Adapter config |
| `{{SAP_ERP_allowChunking_3}}` | Adapter config |
| `{{SAP_ERP_enableBasicAuthentication_5}}` | Adapter config |
| `{{SAP_ERP_proxyType_2}}` | Adapter config |
| `{{SFSF_EC_BASE_URL}}` | Adapter config |
| `{{SFSF_EC_LOGON_CREDENTIALS_NAME}}` | Adapter config |
| `{{SFSF_EC_PUSH_URL}}` | Adapter config |
| `{{SFSF_EC_QUERY_PAGE_SIZE}}` | Adapter config |
| `{{SFSF_EC_TIMEOUT}}` | Adapter config |
| `{{Subject_DN}}` | Adapter config |
| `{{USER_ROLE}}` | Adapter config |


## Dependencies

### External Systems

| System | Adapter Type | Direction |
| --- | --- | --- |
| EC_CE_API_QUERY | SuccessFactors | Receiver |
| EC_PUSH_EVENT | SOAP | Sender |
| Receiver1 | ProcessDirect | Receiver |
| S4_Cloud | SOAP | Receiver |
| Sender1 | ProcessDirect | Sender |

### Groovy Scripts

| Script | Summary |
| --- | --- |
| `CustomFunctions.gsh` | CustomFunctions.gsh is a Groovy/GSH script used in an SAP CPI iFlow |
| `GenerateSAPMessageID.gsh` | GenerateSAPMessageID.gsh is a Groovy/GSH script used in an SAP CPI iFlow |
| `initializeLoopCounter.groovy` | initializeLoopCounter.groovy is a Groovy/GSH script used in an SAP CPI iFlow |
| `logExternalParameters.groovy` | logExternalParameters.groovy is a Groovy/GSH script used in an SAP CPI iFlow |
| `LogPayloadCompoundResult.gsh` | LogPayloadCompoundResult.gsh is a Groovy/GSH script used in an SAP CPI iFlow |
| `LogPayloadERP.gsh` | LogPayloadERP.gsh is a Groovy/GSH script used in an SAP CPI iFlow |
| `LogPayloadPushEvent.gsh` | LogPayloadPushEvent.gsh is a Groovy/GSH script used in an SAP CPI iFlow |
| `Mapping.gsh` | Mapping.gsh is a Groovy/GSH script used in an SAP CPI iFlow |
| `script1.groovy` | script1.groovy is a Groovy/GSH script used in an SAP CPI iFlow |
| `script2.groovy` | script2.groovy is a Groovy/GSH script used in an SAP CPI iFlow |
| `script3.groovy` | script3.groovy is a Groovy/GSH script used in an SAP CPI iFlow |
| `script4.groovy` | script4.groovy is a Groovy/GSH script used in an SAP CPI iFlow |
| `script5.groovy` | script5.groovy is a Groovy/GSH script used in an SAP CPI iFlow |
| `SetQueryParameter.gsh` | SetQueryParameter.gsh is a Groovy/GSH script used in an SAP CPI iFlow |

### Adapter Types Used

- ProcessDirect
- SOAP
- SuccessFactors
