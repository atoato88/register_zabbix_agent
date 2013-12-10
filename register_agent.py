# -*- coding:utf-8 -*-
"""
@param event_id id for target event 
@param broken_hostname name for broken physical server. specify hostname with full match.
@return succes 0
        failure 1
"""

# TODO:implement logging
# TODO:error process for others

import sys
import os
from os import path
import time
import pprint
import ConfigParser
from novaclient.v1_1.client import Client
import novaclient.exceptions

event_id = '9097'
broken_hostname = 'vbox03-01'

# FIXME: modify to include own hostname. because this script may be kicked in multihost at same time.
execute_hostname = os.uname()[1]
zabbix_message_start_script = execute_hostname + ':[START]auto evacuate script start. event id:%s'
zabbix_message_finish_script = execute_hostname + ':[FINISH]auto evacuate script finish. event id:%s'

argvs = sys.argv
argc = len(argvs)
print argvs
print argc

if argc == 3:
    event_id = argvs[1]
    broken_hostname = argvs[2]
else:
    print 'usage: <command> <event_id on zabbix> <broken physical hostname>'
    sys.exit(1)

# ---------------------------------------------------------------------------------------
# load settings
config = ConfigParser.ConfigParser()
config.read( path.dirname( path.abspath( __file__ ) ) + '/' + 'register_agent.conf')

zabbix_user = config.get('DEFAULT', 'zabbix_user')
zabbix_password = config.get('DEFAULT', 'zabbix_password')
zabbix_url = config.get('DEFAULT', 'zabbix_url')
zabbix_comment_update = config.getboolean('DEFAULT', 'zabbix_comment_update')
ignore_zabbix_api_connection = config.getboolean('DEFAULT', 'ignore_zabbix_api_connection')

# ---------------------------------------------------------------------------------------

if zabbix_comment_update:
    from pyzabbix import ZabbixAPI

"""
update comment on event specified by event_id
@param zabbix_api zabbix api object
@param event_id id for target event 
@param message messega for update
"""
def zabbixapi_acknowledge(zabbix_api, event_id, mymessage):
    if zabbix_comment_update:
        try:
            zabbix_api.event.acknowledge(eventids=event_id, message=mymessage[:255] if len(mymessage) > 255 else mymessage)
        except Exception as e:
            print 'some errors occurs with zabbixapi connection'
            print e
            if not ignore_zabbix_api_connection:
                raise e

# create zabbix api object
def get_zabbix_api():
    zapi = None
    if zabbix_comment_update:
        zapi = ZabbixAPI(zabbix_url)
        try:
            zapi.login(zabbix_user, zabbix_password)
        except Exception as e:
            print 'some errors occurs'
            print e
    return zapi


"""
register host to ZabbixServer
@param zabbix_api zabbix api object
@param templates:list templates which related to host with.
@param bmc_ip_address ip address of BMC which host has.
@param ip_address ip address of host has ZabbixServer connect to it for ZabbixAgent.
@param label explain this host
@param hostname hostname of this host
"""
def register_host_to_zabbix(zabbix_api, conf):
    result = 0
    template_list=[]

    for i in conf['templates']:
        template_list.append(
            {'templateid': str(i)}
            )
    if zabbix_comment_update:
        try:
            #TODO check existance of target host
            if not zabbix_api.host.exists(host=conf['hostname']):
                #now we has no host which is named 'hostname'
                #go forward
                a = zabbix_api.host.create(
                    host=conf['hostname'],
                    name=conf['label'] + conf['hostname'],
                    interfaces=[
                          {
                            "type": 1, # zabbix agent
                            "main": 1,
                            "useip": 1,
                            "ip": conf['ip_address'],
                            "dns": "",
                            "port": "10050"
                          },
                          {
                            "type": 2, # SNMP
                            "main": 1,
                            "useip": 1,
                            "ip": conf['bmc_ip_address'],
                            "dns": "",
                            "port": "161"
                          }
                      ],
                    groups= [
                      {
                        "groupid": "2"
                        }
                      ],
                    templates= template_list,
                    inventory= {
                        "oob_ip": conf['bmc_ip_address']
                      }
                    )
                print a

            #TODO register host to zabbix server
            #zabbix_api.host.
        except Exception as e:
            print 'some errors occurs with zabbixapi connection2'
            print e
            if not ignore_zabbix_api_connection:
                raise e
    return result


def main():
    result = 0
    try:
        # create zabbix api object
        zapi = get_zabbix_api()


        # update trigger comment on zabbix
        conf={
            'templates':['10094','10050','dd'],
            'bmc_ip_address':'192.168.4.1',
            'ip_address':'192.168.6.1',
            'label':'explain text',
            'hostname':'hogehoge3'
            }
        register_host_to_zabbix(zapi, conf)

    except Exception as e:
        zabbixapi_acknowledge(zapi, event_id, str(e))
        result = 1
    finally:
        sys.exit(result)

if __name__ == '__main__':
    main()

