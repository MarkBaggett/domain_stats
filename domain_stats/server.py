import logging
from flask import Flask, jsonify, request, session, abort
import functools
import datetime
import argparse
import pathlib
import sys
import os

log = logging.getLogger("domain_stats")
default_flask_logger = logging.getLogger('werkzeug')
default_flask_logger.setLevel(logging.CRITICAL)


from publicsuffixlist import PublicSuffixList
from domain_stats.config import Config
from domain_stats.network_io import IscConnection
import domain_stats.rdap_query as rdap
from domain_stats.freq import FreqCounter
from domain_stats.expiring_diskcache import ExpiringCache
from diskcache import Cache

os.chdir("/home/student/mydata")

#current directory must be set by launcher to the location of the config and database
cache = ExpiringCache(os.getcwd())
memocache = Cache(pathlib.Path().cwd() / "memocache")
if not memocache.get("rdap_good"):
    memocache.set("rdap_good",0)
    memocache.set("rdap_fail",0)
config = Config(os.getcwd()+"/domain_stats.yaml")

if config.get("enable_freq_scores"):
    freq = FreqCounter()
    freq.load(config.get("freq_table"))

logfile = logging.FileHandler(str(pathlib.Path.cwd() / 'domain_stats.log'))
logformat = logging.Formatter('%(asctime)s : %(levelname)s : %(module)s : %(process)d : %(message)s')
logfile.setFormatter(logformat)
if config['log_detail'] == 0:
    log.setLevel(level=logging.CRITICAL)
elif config['log_detail'] == 1:
    log.addHandler(logfile)
    log.setLevel(logging.INFO)
else:
    log.addHandler(logfile)
    log.setLevel(logging.DEBUG)

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

@app.route("/stats-reset", methods=['GET'])
def cache_reset():
    cache.cache.stats(enable=True, reset=True)
    memocache.set("rdap_good",0)
    memocache.set("rdap_fail",0)
    return jsonify({"text":"Success"})

@app.route("/cache_browse", methods=['GET'])
def cache_browse():
    offset = request.args.get('offset',0, type=int)
    limit = request.args.get('limit',100, type=int)
    max_limit = min( limit, app.config.get("cache_browse_limit",100))
    resp = cache.cache_dump(offset,max_limit)
    if len(resp) >= limit:
        resp.insert(0, {"next":f"{request.base_url}?offset={offset+limit}&limit={limit}"})
    return jsonify(resp)

@app.route("/cache_get", methods=['GET'])
def cache_get():
    domain = request.args.get('domain')
    if not domain:
        return jsonify({"text":"Try /cache_get?domain=markbaggett.com"})
    resp = cache.cache_get(domain)
    return jsonify(resp)

@app.route("/<string:domain>", methods=['GET'])
def get_domain(domain):
    log.debug("New Request for domain {0}.".format(domain) )
    #Reduce the domain and produce an error if it can't be reduced
    domain = reduce_domain(domain)
    if not domain:
        return json_response("ERROR","ERROR","ERROR","ERROR",['No valid eTLD exists for this domain.'],'ERROR')                
    #retreive value from cache and serve it without modification
    cache_data = cache.get(domain)
    log.debug("Is the domain in cache? {}".format(bool(cache_data)))
    if cache_data:
        return cache_data
    #Not in cache so build a new record, return it an store it in cache
    else:
        freq_score = "disabled"
        alerts = []
        if app.config.get("enable_freq_scores"):
            freq_score = freq.probability(domain)
            if freq_score[0] < app.config.get("freq_avg_alert") and freq_score[1] < app.config.get("freq_word_alert"):
                alerts.append("LOW-FREQ-SCORES")
            elif freq_score[0] < app.config.get("freq_avg_alert") or freq_score[1] < app.config.get("freq_word_alert"):
                alerts.append("SUSPECT-FREQ-SCORE")
        if app.config.get("mode")=="rdap":
            alerts.append("YOUR-FIRST-CONTACT")
            rdap_seen_by_you = (datetime.datetime.utcnow()+datetime.timedelta(hours=app.config['timezone_offset']))
            rdap_seen_by_web, rdap_expires, rdap_error = rdap.get_domain_record(domain)
            if rdap_error:
                cache_expiration = app.config.get("rdap_error_ttl_days",7) * 86400
                alerts.append(rdap_error)
                resp = json_response("ERROR","ERROR","ERROR","ERROR",alerts,freq_score)
                if "YOUR-FIRST-CONTACT" in alerts:
                    alerts.remove("YOUR-FIRST-CONTACT")
                cache_resp = json_response("ERROR","ERROR","ERROR","ERROR",alerts, freq_score)
                cache.set(domain, cache_resp, seconds_to_live=cache_expiration)
                if app.config.get("count_rdap_errors",False):
                    memocache.incr("rdap_fail")
                log.debug("rdap failed for domain {0}. Cached {1} seconds.".format(domain,cache_expiration) )
                return resp
            #if not expires and its doesn't expire for two years then its established.
            est_day_age = app.config.get("established_days_age",720)
            now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
            domain_age_seconds = (now - rdap_seen_by_web).total_seconds()
            until_expires = (rdap_expires - now).total_seconds()
            if domain_age_seconds > (est_day_age *86400):
                category = "ESTABLISHED"      
            else:
                category = "NEW"
                #It stays in the cache until it becomes established or it expires
                until_established = (est_day_age * 86400) - domain_age_seconds
                until_expires = min( until_expires, until_established )
            resp = json_response(rdap_seen_by_web, "RDAP", rdap_seen_by_you, category, alerts , freq_score )
            if "YOUR-FIRST-CONTACT" in alerts:
                alerts.remove("YOUR-FIRST-CONTACT")
            cache_response = json_response(rdap_seen_by_web, "RDAP", rdap_seen_by_you, category, alerts, freq_score )
            cache.set(domain, cache_response, until_expires)
            if app.config.get("count_rdap_errors",False):
                memocache.incr("rdap_good")
            log.debug("rdap success for domain {0}.Expires {1}.Cached {2} {3}".format(domain,rdap_expires,until_expires,category) )
            return resp 
        else:
            #Mode is not RDAP ask SANS ISC for domain data
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
    os.chdir("/home/student/mydata")
    x = config_app("/home/student/mydata")
    x.run(host="0.0.0.0",port=5730)

