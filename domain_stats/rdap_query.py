import logging
import requests
import rdap
import json
import datetime
import dateutil.parser
import dateutil.tz
import pathlib
import os
import sqlite3

log = logging.getLogger("domain_stats")

def get_config(update_url):
    try:
        config = requests.get( update_url + "/version.json").json()
    except Exception as e:
        print("Unable to retreive /version.json info from {} {}".format( update_url,str(e)))
        return 9999,99999
    return config.get("min_client_version"), config.get("min_database_version")
    

def retrieve_data(action_name,eventlist):
    for entry in eventlist:
        if entry.get("eventAction") == action_name:
            return entry.get("eventDate")
    return None

def get_domain_record(domain):
    client = rdap.client.RdapClient()
    client.url = "https://www.rdap.net"
    client.timeout = 5
    log.debug("RDAP Query of domain {0}".format(domain)) 
    try:
        resp = client.get_domain(domain).data
    except Exception as e:
        return "ERROR","ERROR", str(e)
    reg = retrieve_data( 'registration', resp.get('events'))
    reg = dateutil.parser.isoparse(reg)
    reg.replace(tzinfo=datetime.timezone.utc)
    exp = retrieve_data( 'expiration', resp.get('events'))
    try:
        exp = dateutil.parser.isoparse(exp)
    except Exception as e:
        return "ERROR","ERROR", "Invalid RDAP response Domain:{} generated {}".format(domain,str(e))
    exp.replace(tzinfo=datetime.timezone.utc)
    log.debug("RDAP Query of domain {0} resolved {1}".format(domain,resp)) 
    return reg,exp,""