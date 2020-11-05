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
from domain_stats.network_io import IscConnection
import domain_stats.rdap_query as rdap
from domain_stats.freq import FreqCounter
from domain_stats.expiring_diskcache import ExpiringCache
from diskcache import Cache

#current directory must be set by launcher to the location of the config and database
cache = ExpiringCache(os.getcwd())
memocache = Cache(pathlib.Path().cwd() / "memocache")
if not memocache.get("rdap_good"):
    memocache.set("rdap_good",0)
    memocache.set("rdap_fail",0)
config = Config(os.getcwd()+"/domain_stats.yaml")

if config.get("enable_freq_scores"):
    freq = FreqCounter()
    freq.load("freqtable2018.freq")

app = Flask(__name__)
app.name = "domain_stats"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] ="Change This to a unique very long string for your installation. Make it a few hundred characters long. You never have to remember it or use it, but you want it to be unique to your install."
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=10)
#app.logger.removeHandler(default_handler)

def json_response(web,isc,you,cat,alert,freq=None):
    resp = {"seen_by_web":web,"seen_by_isc":isc, "seen_by_you":you, "category":cat, "alerts":alert}
    if app.config.get("enable_freq_scores"):
        resp['freq_score'] = freq
    return jsonify(resp)

@memocache.memoize(tag="reduce_domain")
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

@app.route("/stats", methods=['GET'])
def cache_info():
    res = cache.cache_info()
    res.update({ "rdap_good":memocache.get("rdap_good"), "rdap_fail": memocache.get("rdap_fail")})
    return jsonify(res)

@app.route("/<string:domain>", methods=['GET'])
def get_domain(domain):
    log.debug("New Request for domain {0}." )
    #First try to get it from the Memory Cache
    domain = reduce_domain(domain)
    if not domain:
        return json_response("ERROR","ERROR","ERROR","ERROR",['No valid eTLD exists for this domain.'],'ERROR')                
    cache_data = cache.get(domain)
    log.debug("Is the domain in cache? {}".format(bool(cache_data)))
    if cache_data:
        return cache_data
    #If it isn't in the memory cache check the database
    else:
        freq_score = "disabled"
        alerts = []
        if app.config.get("enable_freq_scores"):
            freq_score = freq.probability(domain)
            if freq_score[0] < app.config.get("freq_avg_alert") or freq_score[1] < app.config.get("freq_word_alert"):
                alerts.append("LOW-FREQ-SCORE")
        if app.config.get("mode")=="rdap":
            alerts.append("YOUR-FIRST-CONTACT")
            rdap_seen_by_you = (datetime.datetime.utcnow()+datetime.timedelta(hours=app.config['timezone_offset']))
            rdap_seen_by_web, rdap_expires, rdap_error = rdap.get_domain_record(domain)
            if rdap_error:
                cache_expiration = 1
                alerts.append(rdap_error)
                resp = json_response("ERROR","ERROR","ERROR","ERROR",alerts,"ERROR")
                cache_resp = json_response("ERROR","ERROR","ERROR","ERROR",[rdap_error],"ERROR")
                cache.set(domain, cache_resp, hours_to_live=cache_expiration)
                memocache.incr("rdap_fail")
                return resp
            category = "NEW"
            #if not expires and its doesn't expire for two years then its established.
            age = app.config.get("established_days_age")
            if rdap_seen_by_web < (datetime.datetime.utcnow() - datetime.timedelta(days=365*2)).replace(tzinfo=datetime.timezone.utc):
                category = "ESTABLISHED"
            resp = json_response(rdap_seen_by_web, "RDAP", rdap_seen_by_you, category, alerts , freq_score )
            #Build a response just for the cache that stores ISC alerts for 24 hours. 
            if "YOUR-FIRST-CONTACT" in alerts:
                alerts.remove("YOUR-FIRST-CONTACT")
            until_expires = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) - rdap_expires
            cache_expiration = min( 720 , (until_expires.seconds//360))
            cache_response = json_response(rdap_seen_by_web, "RDAP", rdap_seen_by_you, category, alerts, freq_score )
            cache.set(domain, cache_response, cache_expiration)
            memocache.incr("rdap_good")
            return resp 
        else:
            #Instead of RDAP ask SANS ISC for domain data
            return "ISC Mode is still in development"
         

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
    app.config.update(config)
    os.chdir(working_path)
    return app

if __name__ == "__main__":
    x = config_app("/home/student/dsdata2")
    x.run()

