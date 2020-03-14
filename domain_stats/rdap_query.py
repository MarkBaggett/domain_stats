import rdap
import json
import datetime
import dateutil.parser
import dateutil.tz
import logging


def retrieve_data(action_name,eventlist):
    for entry in eventlist:
        if entry.get("eventAction") == action_name:
            return entry.get("eventDate")
    return None

def get_domain_record(domain):
    client = rdap.client.RdapClient()
    client.url = "https://www.rdap.net"
    client.timeout = 5
    try:
        resp = client.get_domain(domain).data
    except Exception as e:
        return "ERROR","ERROR", str(e)
    reg = retrieve_data( 'registration', resp.get('events'))
    reg = dateutil.parser.isoparse(reg)
    reg.replace(tzinfo=datetime.timezone.utc)
    exp = retrieve_data( 'expiration', resp.get('events'))
    exp = dateutil.parser.isoparse(exp)
    exp.replace(tzinfo=datetime.timezone.utc)
    return reg,exp,""