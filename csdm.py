# -*- coding: utf-8 -*-
import logging
import json
import requests

SEARCH_URL='https://csdm-a.wbx2.com/csdm/api/v1/organization/{}/devices/_search'
PLACE_URL='https://csdm-a.wbx2.com/csdm/api/v1/organization/{}/places/{}'
UCM_PLACE_URL='https://uss-a.wbx2.com/uss/api/v1/orgs/{}/ucmplaceinfo/{}'

class csdm_client(object):

    def __init__(self, orgid, access_token):
        self.log = log = logging.getLogger(__name__)
        self.orgid = orgid
        self.access_token = access_token

    def get_device(self, device_mac):
        self.log.info("Searching for device with MAC :" + device_mac)
        url = SEARCH_URL.format(self.orgid)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': "Bearer {}".format(self.access_token)
        }
        query = {
            "query": {
                "query":"{}".format(device_mac)
            },
            "size": 10,
            "from": 0, 
            "sortOrder":"asc"
        }
        r = requests.post(url, headers=headers, json=query)
        r.raise_for_status()
        try:
            device = r.json()['hits']['hits'][0]
            self.log.debug(json.dumps(device, indent=4, sort_keys=True))
            return device
        except KeyError:
            self.log.error("Device not found for MAC:" + device_mac)
            raise RuntimeError

    def get_place(self, place_id):
        self.log.info("Searching for Place with UUID :" + place_id)
        url = PLACE_URL.format(self.orgid, place_id)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': "Bearer {}".format(self.access_token)
        }
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        place = r.json()
        self.log.info(json.dumps(place, indent=4, sort_keys=True))
        return place
    
    def link_device2user(self, device_uuid, pstn_mailid):
        self.log.info("Trying to enable Hybrid Calling for Personal mode place :" + device_uuid)
        url = PLACE_URL.format(self.orgid, device_uuid)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': "Bearer {}".format(self.access_token)
        }
        body = {
            "entitlements":[
                "spark",
                "webex-squared",
                "squared-fusion-ec",
                "squared-fusion-uc"
            ],
            "extLinkedAccts":[
                {
                    "providerID":"squared-fusion-uc",
                    "accountGUID":pstn_mailid,
                    "status": "unconfirmed-email"
                }
            ],
            "placeType":None
        }
        r = requests.patch(url, headers=headers, json=body)
        r.raise_for_status()

        place = r.json()
        self.log.info(json.dumps(place, indent=4, sort_keys=True))
        return place

    def create_place(
        self,
        device_uuid,
        home_cluster_fqdn,
        primary_dn,
        directory_uri,
        ucm_version,
        telephone_number,
        sip_dest_override):

        self.log.info("Trying to create a Place")
        url = UCM_PLACE_URL.format(self.orgid, device_uuid)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': "Bearer {}".format(self.access_token)
        }
        body = {
            "homeClusterFQDN": home_cluster_fqdn,
            "primaryDN": primary_dn,
            "directoryUri": directory_uri,
            "ucmVersion": ucm_version,
            "telephoneNumber": telephone_number,
            "sipDestinationOverride": sip_dest_override
        }
        r = requests.put(url, headers=headers, json=body)
        r.raise_for_status()
        self.log.info("Done Creating the Place/Sync process")
        return True
