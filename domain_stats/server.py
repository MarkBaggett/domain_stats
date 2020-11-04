import logging
from flask import Flask, jsonify, request, session, abort
import functools
import datetime
import argparse
import pathlib
import sys
import os

log = logging.getLogger("domain_stats")

#default_flask_logger = logging.getLogger('werkzeug')
#default_flask_logger.setLevel(logging.ERROR)
#logfile = logging.FileHandler( './domain_stats.log')
#logformat = logging.Formatter('%(asctime)s : %(levelname)s : %(module)s : %(message)s')
#logfile.setFormatter(logformat)

from publicsuffixlist import PublicSuffixList
from domain_stats.config import Config
from domain_stats.expiring_diskcache import cache
from domain_stats.network_io import IscConnection
import domain_stats.rdap_query as rdap

app = Flask(__name__)
app.name = "domain_stats"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] ="Change This to a unique very long string for your installation. Make it a few hundred characters long. You never have to remember it or use it, but you want it to be unique to your install."
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=10)
#app.logger.removeHandler(default_handler)

def json_response(web,isc,you,cat,alert):
    return jsonify({"seen_by_web":web,"seen_by_isc":isc, "seen_by_you":you, "category":cat, "alerts":alert})

@cache.cache.memoize(typed=True, tag='reduced_domain')
def reduce_domain(domain_in):
    if not PublicSuffixList().publicsuffix(domain_in,accept_unknown=False):
        return None
    domain = PublicSuffixList().privatesuffix(domain_in)
    if domain:
        domain=domain.lower()
    else:
        log.debug("No eTLD for {}".format(domain))
    log.debug("Trimmed domain from {0} to {1}".format(domain_in,domain))
    return domain

@app.route("/<string:domain>", methods=['GET'])
def get_domain(domain):
   log.debug("New Request for domain {0}.  Here is the cache info:{1} {2}".format(domain,cache.keys(),cache.cache_info() ))
    #First try to get it from the Memory Cache
    domain = reduce_domain(domain)
    if not domain:
        return json_response("ERROR","ERROR","ERROR","ERROR",['No valid eTLD exists for this domain.'])                
    cache_data = cache.get(domain)
    log.debug("Is the domain in cache? {}".format(bool(cache_data)))
    if cache_data:
        return cache_data
    #If it isn't in the memory cache check the database
    else:
        if app.config.get("mode")=="rdap":
            alerts = ["YOUR-FIRST-CONTACT"]
            rdap_seen_by_you = (datetime.datetime.utcnow()+datetime.timedelta(hours=app.config['timezone_offset']))
            rdap_seen_by_web, rdap_expires, rdap_error = rdap.get_domain_record(domain)
            if rdap_seen_by_web == "ERROR":
                cache_expiration = 1
                if rdap_error:
                    alerts.append(rdap_error)
                #FIXME Include FIRSTCONTACT in resp but not cacher
                resp = json_response("ERROR","ERROR","ERROR","ERROR",alerts)
                cache_resp = json_response("ERROR","ERROR","ERROR","ERROR",[rdap_error])
                cache.set(domain, cache_resp, hours_to_live=cache_expiration)
                return resp
            category = "NEW"
            #if not expires and its doesn't expire for two years then its established.
            if rdap_seen_by_web < (datetime.datetime.utcnow() - datetime.timedelta(days=365*2)).replace(tzinfo=datetime.timezone.utc):
                category = "ESTABLISHED"
            resp = json_response(rdap_seen_by_web, "RDAP", rdap_seen_by_you, category, alerts )
            #Build a response just for the cache that stores ISC alerts for 24 hours. 
            if "YOUR-FIRST-CONTACT" in alerts:
                alerts.remove("YOUR-FIRST-CONTACT")
            until_expires = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) - rdap_expires
            cache_expiration = min( 720 , (until_expires.seconds//360))
            cache_response = json_response(rdap_seen_by_web, "RDAP", rdap_seen_by_you, category, alerts )
            cache.set(domain, cache_response, cache_expiration)
            return resp 
        else:
            #Your here so its not in the database look to the isc?
            #if the ISC responds with an error put that in the cache
            alerts = ["YOUR-FIRST-CONTACT"]
            isc_seen_by_you = (datetime.datetime.utcnow()+datetime.timedelta(hours=app.config['timezone_offset']))
            isc_seen_by_web, isc_expires, isc_seen_by_isc, isc_alerts = isc_connection.retrieve_isc(domain)
            #handle code if the ISC RETURNS AN ERROR HERE
            #Handle it.  Cache the error for some period of time.
            #If it isn't an error then its a new entry for the database (only) no cache
            if isc_seen_by_web == "ERROR":
                cache_expiration = isc_seen_by_isc
                resp = json_response("ERROR","ERROR","ERROR","ERROR",isc_alerts)
                cache.set(domain, resp, hours_to_live=cache_expiration)
                return resp
            #here the isc returned a good record for the domain. Put it in the database and calculate an uncached response
            category = "NEW"
            #if not expires and its doesn't expire for two years then its established.
            if isc_seen_by_web < (datetime.datetime.utcnow() - datetime.timedelta(days=365*2)):
                category = "ESTABLISHED"
            alerts.extend(isc_alerts)
            resp = json_response(isc_seen_by_web, isc_seen_by_isc, isc_seen_by_you, category, alerts )
            #Build a response just for the cache that stores ISC alerts for 24 hours. 
            if "YOUR-FIRST-CONTACT" in alerts:
                alerts.remove("YOUR-FIRST-CONTACT")
            if "ISC-FIRST-CONTACT" in alerts:
                alerts.remove("ISC-FIRST-CONTACT")
            if alerts:
               cache_expiration = 24     #Alerts are only cached for 24 hours
            else:
               until_expires = datetime.datetime.utcnow() - isc_expires
               cache_expiration = min( 720 , (until_expires.seconds//360))
            cache_response = json_response(isc_seen_by_web, isc_seen_by_isc, isc_seen_by_you, category, alerts )
            cache.set(domain, cache_response, cache_expiration)
            database.update_record(domain, isc_seen_by_web, isc_expires, isc_seen_by_isc, datetime.datetime.utcnow())
            return resp

def config_app(working_path):
    working_path = pathlib.Path(working_path)
    if not working_path.is_dir():
        print("Sorry.  The path specified is invalid.  The directory you provide must already exist.")
        sys.exit(1)
    if sys.version_info.minor < 5 or sys.version_info.minor < 3:
        print("Please update your installation of Python.")
        sys.exit(1)
    #Initialize the global variables
    if not (working_path / "domain_stats.yaml").exists():
        print("No configuration file found.")
        sys.exit(1)
    yaml_path = str(working_path / "domain_stats.yaml")
    print("Using config {}".format( str(yaml_path)))
    app.config.update(Config(str(yaml_path)))
    os.chdir(working_path)
    return app

