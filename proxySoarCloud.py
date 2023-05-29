import requests
import os
import xml.etree.ElementTree as ET
from datetime import timedelta, datetime

from abstractProxy import AbstractProxy

DOMAIN = 'https://scsservices2.azurewebsites.net'

CHECK_IN_DUTY_CODE = '4'
CHECK_IN_DUTY_STATUS = '4'
CHECK_OUT_DUTY_CODE = '8'
CHECK_OUT_DUTY_STATUS = '5'

OOO_REQUEST_COMPLETE_CHECK_TYPE = '9'
OOO_WITHDRAW_CHECK_TYPE = '0'

class ProxySoarCloud(AbstractProxy):
  def __init__(self):
    self.jwt = ''

  def login(self):
    url = f'{DOMAIN}//SCSService.asmx'
    acc = os.getenv('ACC')
    pwd = os.getenv('PPP')
    headers = {
      "Content-Type": "application/soap+xml",
    }
    payload_xml = """
      <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
          <SystemObjectRun xmlns="http://scsservices.net/">
            <args>
              <SessionGuid>00000000-0000-0000-0000-000000000000</SessionGuid>
              <Action>Login</Action>
              <Format>Xml</Format>
              <Bytes/>
              <Value>&lt;?xml version="1.0" encoding="utf-16"?&gt;
                &lt;TLoginInputArgs xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"&gt;
                &lt;AppName&gt;App&lt;/AppName&gt;
                &lt;CompanyID&gt;SCS285&lt;/CompanyID&gt;
                &lt;UserID&gt;__ACC__&lt;/UserID&gt;
                &lt;Password&gt;__PPP__&lt;/Password&gt;
                &lt;LanguageID&gt;zh-TW&lt;/LanguageID&gt;
                &lt;UserHostAddress /&gt;
                &lt;IsSaveSessionBuffer&gt;true&lt;/IsSaveSessionBuffer&gt;
                &lt;ValidateCode /&gt;
                &lt;OAuthType&gt;NotSet&lt;/OAuthType&gt;
                &lt;IsValidateRegister&gt;false&lt;/IsValidateRegister&gt;
                &lt;/TLoginInputArgs&gt;
              </Value>
            </args>
          </SystemObjectRun>
        </soap12:Body>
      </soap12:Envelope>
    """
    payload_xml = payload_xml.replace("__ACC__", str(acc)).replace("__PPP__", str(pwd))
    requests.post(url, data=payload_xml, headers=headers)

  def check_in_out(self, is_check_in_type):
    url = f'{DOMAIN}/prohrm/api/app/card/gps'
    headers = {
      "Content-Type": "application/soap+xml",
    }
    payload_xml = """
      <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
          <BusinessObjectRun xmlns="http://scsservices.net/">
            <args>
              <SessionGuid>0009947c-965f-4051-8917-68f76b7e7b4b</SessionGuid>
              <ProgID>WATT0022000</ProgID>
              <Action>ExecFunc</Action>
              <Format>Xml</Format>
              <Bytes/>
              <Value>&lt;?xml version="1.0" encoding="utf-16"?&gt;
                &lt;TExecFuncInputArgs xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"&gt;
                  &lt;FuncID&gt;ExecuteSwipeData_Web&lt;/FuncID&gt;
                  &lt;Parameters&gt;
                    &lt;Parameter&gt;
                      &lt;Name&gt;DutyCode&lt;/Name&gt;
                      &lt;Value xsi:type="xsd:int"&gt;___DUTY_CODE___&lt;/Value&gt;
                    &lt;/Parameter&gt;
                    &lt;Parameter&gt;
                      &lt;Name&gt;DutyStatus&lt;/Name&gt;
                      &lt;Value xsi:type="xsd:int"&gt;___DUTY_STATUS___&lt;/Value&gt;
                    &lt;/Parameter&gt;
                    &lt;Parameter&gt;
                      &lt;Name&gt;GPSLocation&lt;/Name&gt;
                      &lt;Value xsi:type="xsd:string"&gt;___GPS_LOCATION___&lt;/Value&gt;
                    &lt;/Parameter&gt;
                    &lt;Parameter&gt;
                      &lt;Name&gt;CompanyID&lt;/Name&gt;
                      &lt;Value xsi:type="xsd:string"&gt;SCS285&lt;/Value&gt;
                    &lt;/Parameter&gt;
                    &lt;Parameter&gt;
                      &lt;Name&gt;GpsAddress&lt;/Name&gt;
                      &lt;Value xsi:type="xsd:string"&gt;___GPS_ADDRESS___&lt;/Value&gt;
                    &lt;/Parameter&gt;
                    &lt;Parameter&gt;
                      &lt;Name&gt;NoCheckOnDutyStatus&lt;/Name&gt;
                      &lt;Value xsi:type="xsd:boolean"&gt;true&lt;/Value&gt;
                    &lt;/Parameter&gt;
                  &lt;/Parameters&gt;
                &lt;/TExecFuncInputArgs&gt;
              </Value>
            </args>
          </BusinessObjectRun>
        </soap12:Body>
      </soap12:Envelope>
    """
    dutyCode = CHECK_IN_DUTY_CODE if is_check_in_type else CHECK_OUT_DUTY_CODE
    dutyStatus = CHECK_IN_DUTY_STATUS if is_check_in_type else CHECK_OUT_DUTY_STATUS
    gpsLocation = '25.0307104191219,121.558177293395'
    gpsAddress = '11052,信義區,基隆路二段 41–77'
    payload_xml = payload_xml.replace("___DUTY_CODE___", dutyCode).replace("___DUTY_STATUS___", dutyStatus).replace("___GPS_LOCATION___", gpsLocation.encode('utf-8')).replace("___GPS_ADDRESS___", gpsAddress.encode('utf-8'))
    requests.post(url, data=payload_xml, headers=headers)

  # OoO request/withdraw handlers
  
  def is_sign_off_completed(self, form):
    # judged all types as completed, except OOO_WITHDRAW_CHECK_TYPE 0
    check_type_element = form.find(".//TMP_CHECKTYPE")
    if check_type_element is not None:
      return not check_type_element.text == OOO_WITHDRAW_CHECK_TYPE
    else:
      return False
  
  def parse_summary_text_to_date_list(self, start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%dT%H:%M:%S").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%dT%H:%M:%S").date()

    date_list = []
    delta = timedelta(days=1)
    current_date = start_date
    while current_date <= end_date:
      date_list.append(current_date)
      current_date += delta
    return date_list
  
  def get_OoO_date_list_from_forms(self, forms):
    OoO_list = set()      
    for watt_element in forms:
      start_date_str = watt_element.findtext("STARTDATE")
      end_date_str = watt_element.findtext("ENDDATE")
      OoO_list_per_form = self.parse_summary_text_to_date_list(start_date_str, end_date_str)
      for OoO_date in OoO_list_per_form:
        OoO_list.add(OoO_date)
    return OoO_list
  
  # in progress handlers(judged all types as completed, except CheckType == 0)

  def check_today_OoO_in_progress_status(self, today):
    return False, False
  
  # finished handlers
  
  def get_finished_form_list(self):
    url = f'{DOMAIN}//SCSService.asmx'
    headers = {
      "Content-Type": "application/soap+xml",
      "Connection": "keep-alive"
    }
    payload_xml = """
      <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
        <soap12:Body>
          <BOFind xmlns="http://scsservices.net/">
            <inputArgs>
              <SessionGuid>1543c22f-bc8b-478c-afc8-3a3d0a1bb64c</SessionGuid>
              <ProgID>WATT0022500</ProgID>
              <Keyword/>
              <SelectFields>*</SelectFields>
              <DateValue>0001-01-01T00:00:00</DateValue>
              <UserFilter>A.DataType = 1</UserFilter>
              <SelectCount>20</SelectCount>
              <SelectSection>0</SelectSection>
              <SourceProgID>WATT0022500</SourceProgID>
              <SourceFieldName/>
            </inputArgs>
          </BOFind>
        </soap12:Body>
      </soap12:Envelope>
    """
    response = requests.post(url, data=payload_xml, headers=headers)
    tree = ET.fromstring(response.text)
    watt_elements = tree.findall('.//WATT0022500')
    return watt_elements if watt_elements else []
  
  def check_today_OoO_finished_status(self, today):
    finishedOoORequestForms = list(filter(self.is_sign_off_completed, self.get_finished_form_list()))
    finishedOoORequestDateList = self.get_OoO_date_list_from_forms(finishedOoORequestForms)
    return today in finishedOoORequestDateList, False