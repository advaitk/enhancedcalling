# -*- coding: utf-8 -*-


import os, sys
from dotenv import load_dotenv
load_dotenv()

import logging
import logging.config

import click
from log import log_config
logging.config.dictConfig(log_config.common_log_config)
from axl import axl_client as axclient
from csdm import csdm_client as csclient

log = logging.getLogger(__name__)

@click.command()
@click.option("--userid",
              prompt="Userid of device owneer",
              help="Userid not email")
@click.option("--devicemac", 
              prompt="MAC Address of Device", 
              help="format 'AA:BB::CC:DD:EE:FF'")
def run(userid, devicemac):
    click.echo("Got input userid : {} : macaddress : {}".format(userid,devicemac))
    execute(userid, devicemac)


def execute(userid, devicemac):
    log.info("Got input userid : {} : macaddress : {}".format(userid,devicemac))

    axl_client = axclient(os.getenv( 'AXL_USERNAME'), os.getenv( 'AXL_PASSWORD'),os.getenv( 'CUCM_ADDRESS' ))
    axl_client.create_session()

    csdm_client = csclient(os.getenv('CSDM_ORGID'), os.getenv('CSDM_ACESSTKN'))
    log.info(os.getenv('CSDM_ORGID'))
    log.info(os.getenv('CSDM_ACESSTKN'))

    #0
    UCM_VERSION = axl_client.get_version()
    log.info(UCM_VERSION)
    nodes = axl_client.get_nodes()

    HOME_CLUSTER_FQDN = " ".join(nodes)
    log.info("Done with #0")

    #1 
    main_user = axl_client.get_user(userid)
    log.info(main_user)
    log.info("Done with #1")

    #2
    cloud_device = csdm_client.get_device(devicemac)
    log.info(cloud_device)
    log.info("Done with #2")


    #3
    cloud_place = csdm_client.get_place(cloud_device['cisUuid'])
    log.info(cloud_place)
    log.info("Done with #3")

    #4
    #4.1 
    pstn_userid = axl_client.calculate_pstn_userid(main_user)
    log.info(pstn_userid)
    log.info("Done with #4.1")

    #4.2
    pstn_user_uuid = axl_client.create_pstn_user(pstn_userid,main_user)
    pstn_user = axl_client.get_user(pstn_userid)
    log.info(pstn_user)
    log.info("Done with #4.2")

    #5
    sparkrd_phone_name = axl_client.create_sparkRD(pstn_userid, main_user)
    log.info(sparkrd_phone_name)
    log.info("Done with #5")

    #6
    linked_place = csdm_client.link_device2user(cloud_device['cisUuid'], pstn_user['directoryUri'])
    log.info(linked_place)
    log.info("Done with #6")

    #7
    status = csdm_client.create_place(
            cloud_device['cisUuid'],
            HOME_CLUSTER_FQDN,
            main_user['primaryExtension']['pattern'].replace('\\', ''),
            pstn_user['directoryUri'],
            UCM_VERSION,
            "",
            os.getenv('SIP_DEST_OVERRIDE'))
    log.info(status)
    log.info("Done with #7")

    #9
    axl_client.create_rd(linked_place['sipUrl'], sparkrd_phone_name, pstn_user['userid'])
    log.info("Done with #9")

    print("Done Enabling Enhanced mode for Cloud device SIP : {} : Userid : {} : SparkRD : {} "
         .format(linked_place['sipUrl'],pstn_userid, sparkrd_phone_name))

    #Clean up
    axl_client.close_session()

if __name__ == '__main__':
    run()
