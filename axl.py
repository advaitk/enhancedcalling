# -*- coding: utf-8 -*-
import logging
import sys
import copy
from zeep import Client, Settings
from zeep.cache import SqliteCache
from zeep.transports import Transport
from zeep.exceptions import Fault
from zeep.plugins import HistoryPlugin
import zeep.helpers


from requests import Session
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter


# class InsecureHttpsAdapter(HTTPAdapter):
#     def cert_verify(self, conn, url, verify, cert):
#         self.log = log = logging.getLogger(__name__)
#         log.info("In cert_verify")
# The WSDL is a local file
WSDL_FILE = 'schema/AXLAPI.wsdl'

class axl_client(object):
    def __init__(self, user, password, address):
        self.log = logging.getLogger(__name__)
        self.user = user
        self.password = password
        self.address = address

    def create_session(self):
        self.log.info("Starting a new Session")
        self.session = Session()
        self.session.auth = HTTPBasicAuth(self.user, self.password)

        #TODO: Look to import certifi
        self.session.verify = False
        from urllib3.exceptions import InsecureRequestWarning
        import requests
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

        # strict=False is not always necessary, but it allows zeep to parse imperfect XML
        settings = Settings( strict=False, xml_huge_tree=True )

        self.transport = Transport(cache=SqliteCache(), session=self.session, timeout=10)
        self.client = Client( WSDL_FILE, transport=self.transport, settings=settings)
        self.service = self.client.create_service('{http://www.cisco.com/AXLAPIService/}AXLAPIBinding', self.address)
        self.log.info("Session Created")

    def close_session(self):
        self.session.close()
    
    def get_version(self):
        resp = self.service.getCCMVersion()
        self.log.info("CUCM Version :" + resp['return']['componentVersion']['version'])
        return resp['return']['componentVersion']['version']

    def get_nodes(self):
        resp = self.service.listProcessNode(
            searchCriteria = {"processNodeRole": 'CUCM Voice/Video'},
            returnedTags = {"name": "true"}
            )
        nodes = resp['return']['processNode']
        self.log.info(nodes)
        names = [ n['name'] for n in nodes if n['name'] != 'EnterpriseWideData' ]
        self.log.info(names)
        return names
    
    def get_user(self, userid):
        try:
            resp = self.service.getUser(userid=userid)
            self.log.debug("Found {} for input {}".format(resp['return']['user']['userid'], userid))
            return resp['return']['user']
        except Fault as fault:
            self.log.error(fault.code)
            self.log.error(fault.message)
        return None

    def get_phone(self, device_name):
        try:
            resp = self.service.getPhone(name=device_name)
            self.log.debug("Found device with name {} for input {}".format(resp['return']['phone']['name'], device_name))
            return resp['return']['phone']
        except Fault as fault:
            self.log.error(fault.code)
            self.log.error(fault.message)
        return None
    

    def calculate_pstn_userid(self, main_user):
       self.log.info("Trying to calculate pstn userid for: " + main_user['userid'])
       ''' Need to support multiple devices, which require multiple user objects'''
       pstn_userid = main_user['userid'] + ".pstn"
       count = 0
       while True:
           if None == self.get_user(pstn_userid):
               self.log.info("Found right userid for pstn :" + pstn_userid)
               return pstn_userid
           else:
               if count < 10:
                   count +=1
                   pstn_userid = "{}_{}.pstn".format(main_user['userid'], count)
               else:
                   self.log.error("Unable to calculate pstn userid after attempts: " + count)
                   return None

    def create_sparkRD(self, pstn_userid, main_user):
        self.log.info("Trying to create SparkRD device for: " + pstn_userid)

        copy_from_device = None
        self.log.debug("Looking up User Device to copy configs from")
        try:
           device_names = main_user['associatedDevices']['device']
           if len(device_names) != 0 :
               copy_from_device = self.get_phone(device_names[0])
               self.log.info("Found device to copy configs from : {}".format(copy_from_device['name']))
        except KeyError:
            self.log.error("User {} has no associated devices".format(main_user['userid']))
        
        if copy_from_device == None:
            raise RuntimeError("Failed to find a device for user {} to copy configs from: ".format(main_user['userid']))
        
        ''' These are the configs we need from users another device for the SparkRD to work'''
        keys = ['callingSearchSpaceName', 'subscribeCallingSearchSpaceName', 'rerouteCallingSearchSpaceName','presenceGroupName']
        s = {k:v['_value_1'] for (k, v) in zeep.helpers.serialize_object(copy_from_device).items() if k in keys}
        self.log.info("Using Copied device configs: " + str(s))

        device_name = 'SparkRD' + pstn_userid.replace('.pstn', '').upper()
        phone = {
            'name': device_name,
            'description': pstn_userid + '-SparkRD',
            'ownerUserName': pstn_userid,
            'product': 'Cisco Spark Remote Device',
            'model': 'Cisco Spark Remote Device',
            'class': 'Phone',
            'protocol': 'CTI Remote Device',
            'protocolSide': 'User',
            'devicePoolName': copy_from_device['devicePoolName'],
            'callingSearchSpaceName': copy_from_device['callingSearchSpaceName'],
            'subscribeCallingSearchSpaceName': copy_from_device['subscribeCallingSearchSpaceName'],
            'rerouteCallingSearchSpaceName': copy_from_device['rerouteCallingSearchSpaceName'],
            'presenceGroupName': copy_from_device['presenceGroupName'],
            'commonPhoneConfigName': 'Standard Common Phone Profile',
            'locationName': 'Hub_None',
            'useTrustedRelayPoint': 'Default',
            'builtInBridgeStatus': 'Default',
            'packetCaptureMode': 'None',
            'certificateOperation': 'No Pending Operation',
            'deviceMobilityMode': 'Default',
            'allowCtiControlFlag': 'true',
            'lines': {
                'line' : [
                    {
                        'index': 1,
                        'dirn' : {
                            'pattern': main_user['primaryExtension']['pattern'],
                            'routePartitionName': main_user['primaryExtension']['routePartitionName']
                        }
                    }
                ]
            }
        }
        try:
            resp = self.service.addPhone(phone)
            self.log.info(resp)
            return device_name
        except Fault as fault:
            self.log.error(fault.code)
            self.log.error(fault.message)
            raise RuntimeError("Failed to create SparkRD device for: " + pstn_userid) from fault
        return None

    def create_pstn_user(self, pstn_userid, main_user):
        self.log.info("Trying to create .pstn user for " + main_user['userid'])

        pstn_user = {
            'userid': pstn_userid,
            'mailid': pstn_userid + '@' + main_user['mailid'].split('@')[1],
            'directoryUri': pstn_userid + '@' + main_user['directoryUri'].split('@')[1],
            'firstName': main_user['firstName'],
            'lastName': main_user['lastName'],
            'password': pstn_userid,
            'pin': 123456,
            'enableMobility': 'true',
            'enableEmcc': 'true',
            'homeCluster': 'true',
            'imAndPresenceEnable': 'true',
            'enableMobileVoiceAccess': 'true',
            'remoteDestinationLimit': '4',
            'enableCti':  'true',
            'presenceGroupName': main_user['presenceGroupName']['_value_1'],
       }
        self.log.debug(pstn_user)
        try:
            resp = self.service.addUser(pstn_user)
            return resp
        except Fault as fault:
            self.log.error(fault.code)
            self.log.error(fault.message)
            raise RuntimeError("Failed to create .pstn user for " + main_user['userid']) from fault
        return None
    
    def create_rd(self, destination, sparkrd_name, pstn_userid):
        self.log.info("Trying to create RD for outbound to {} using {} for user {}".format(
            destination,sparkrd_name, pstn_userid))
        rd = {
            'name': 'Cisco Webex Teams',
            'destination': destination,
            'ctiRemoteDeviceName': sparkrd_name,
            'ownerUserId': pstn_userid,
            'enableExtendAndConnect': True,
            'answerTooSoonTimer': 1500,
            'answerTooLateTimer': 19000,
            'delayBeforeRingingCell': 4000
        }
        try:
            resp = self.service.addRemoteDestination(remoteDestination=rd)
            return resp
        except Fault as fault:
            self.log.error(fault.code)
            self.log.error(fault.message)
            raise RuntimeError("Failed to create .RD for out bound calls from UCM for :" +pstn_userid ) from fault
        return None
