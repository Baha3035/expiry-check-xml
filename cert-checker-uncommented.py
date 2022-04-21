from kubernetes import client, config
import base64
import json
import xml.etree.ElementTree as ET
import os
from datetime import datetime
import requests
#from time import strptime

def main():
    config.load_config()
    v1 = client.CoreV1Api()
    secrets = v1.list_secret_for_all_namespaces(watch=False) 
    for scrt in secrets.items:
        scrt_metadata = scrt.metadata
        if scrt_metadata.name == 'basistech-license':
            pagerDuty_url = 'https://events.pagerduty.com/v2/enqueue'
            routing_key = '99e192c897654d42959aa25ab6195ee0'
            numberOfDaysToCheck = os.getenv('NUMBER')
            clusterName = os.getenv('CLUSTER_NAME')
            data_license = scrt.data.get('rlp-license.xml')  # license encoded version
            #print(data_license)
            decoded_data_license = base64.b64decode(data_license)
            str_decoded_data = decoded_data_license.decode("utf-8")
            #print(str_decoded_data)
            xml_license = ET.fromstring(str_decoded_data)
            expirationDate = xml_license.find('expiration').text.replace(",", "")
            #print(expirationDate.text)
            # for child in xml_license:
            #     print(child.attrib)
            #response = requests.get(f'http://admin.{svc.metadata.namespace}.cluster.local:8765/api/v1/license/expiration')
            #expirationDate = response.json().split("T")[0]
            # print("The license will expire on " + expirationDate)
            license_Expiry_day = datetime.strptime(expirationDate, '%b %d %Y')
            print(license_Expiry_day)
            today = datetime.today()
            diff = license_Expiry_day - today 
            daysLeftBeforeExpiration = diff.days
            print("We have " + str(daysLeftBeforeExpiration) + " days before the license expires")
            if daysLeftBeforeExpiration <= int(numberOfDaysToCheck):
                 data = json.dumps(
                     {
                         'payload': {
                             'summary': f'{clusterName} env={scrt.metadata.namespace} BasisTech License going to expire within 14 days',
                             'source': f'{clusterName} env={scrt.metadata.namespace}',
                             'severity': "info",
                             'custom_details': f'{clusterName} env={scrt.metadata.namespace} Basistech License Expiration on {expirationDate}',
                         },
                         'routing_key': routing_key,
                         'event_action': 'trigger'
                     }
                 )
                 resp = requests.post(url=pagerDuty_url, data=data) 
                 return daysLeftBeforeExpiration  

if __name__ == '__main__':
    main()
