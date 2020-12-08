import logging
import datetime
import argparse
import pathlib
import sys
import os
import time
import json
import requests
import pathlib


log = logging.getLogger("domain_stats_util_whois")

from domain_stats.config import Config
from domain_stats.expiring_diskcache import ExpiringCache
from domain_stats.freq import FreqCounter
from flask import Flask,jsonify

def max(listofdatetimes):
    m = None
    for eachd in listofdatetimes:
        if not isinstance(eachd,datetime.datetime):
            continue
        if eachd > m:
            m = eachd
    return m

def to_json(**kwargs):
    with app.app_context():
        resp = jsonify(**kwargs).json
    return resp


def import_domain_rec(import_rec, never_expire=False):
    """ import rec is created by the export of this same program.  Records look like this
    {"freq_score": [9.3769, 6.832], "seen_by_isc": "TOP1M", "seen_by_web": "Mon, 26 Nov 2018 01:42:03 GMT", "expires": 1637890923.0005548, "domain": "betterme-magazine.com"},
    """
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    domain = import_rec.get("domain")
    created = import_rec.get("seen_by_web")
    isc_tag = pathlib.Path(args.importer).stem
    by_you = now
    alerts = []
    freq = import_rec.get("freq_score")
    if freq[0] < app.config.get("freq_avg_alert", 5.0) and freq[1] < app.config.get("freq_word_alert",4.0):
        alerts.append("LOW-FREQ-SCORES")
    elif freq[0] < app.config.get("freq_avg_alert",5.0) or freq[1] < app.config.get("freq_word_alert",4.0):
        alerts.append("SUSPECT-FREQ-SCORE")
    created_as_date = datetime.datetime.strptime(created,"%a, %d %b %Y %H:%M:%S %Z")
    created_as_date = created_as_date.replace(tzinfo=datetime.timezone.utc)
    domain_age_seconds = (now - created_as_date).total_seconds()
    if domain_age_seconds > (app.config.get('established_days_age', 730) *86400):
        category = "ESTABLISHED"      
    else:
        category = "NEW"
    expire = None
    record_expires = import_rec.get("expires")
    if not never_expire and record_expires:
        expire = datetime.datetime.fromtimestamp(record_expires).replace(tzinfo=datetime.timezone.utc) - now
        expire = expire.total_seconds()   
    resp = to_json(**{"seen_by_web":created , "seen_by_isc":isc_tag, "seen_by_you":now, "category":category, "alerts":alerts, "freq": freq})
    if args.verbose:
        print(f"Patchup record for {domain} \nTo {resp}")
    cache.cache.set( domain, resp, expire= expire, tag=isc_tag)
    return 1


def whois_patch_domain(domain, alerts, freq=None):
    now = datetime.datetime.utcnow()
    try:
       who_rec = whois.whois(domain)
    except:
        return 0
    if not who_rec:
        if args.verbose: print(f"No whois record found for {domain}")
        return 0
    created = who_rec.get('creation_date')
    if not created:
        if args.verbose: print(f"No creation date found for {domain}")
        return 0
    if isinstance(created,list):
        created = max(created)
    if not isinstance(created, datetime.datetime):
        print(f"{created} is not datetime")
        return 0
    created = created.replace(tzinfo=datetime.timezone.utc)
    domain_age_seconds = (now - created).total_seconds()
    expires = who_rec.get("expiration_date")
    if not expires:
        if args.verbose: print(f"No expiration date found for {domain}")
        return 0
    if isinstance(expires,list):
        expires = max(expires)
    expires = expires.replace(tzinfo=datetime.timezone.utc)
    until_expires = (expires - now).total_seconds()
    if domain_age_seconds > (config.get('established_days_age', 730) *86400):
        category = "ESTABLISHED"      
    else:
        category = "NEW"
        until_established = (config.get('established_days_age', 730) * 86400) - domain_age_seconds
        until_expires = min( until_expires, until_established )
    if not freq:
        freq = fc.probability(domain)
        if freq[0] < config.get("freq_avg_alert", 5.0) and freq[1] < config.get("freq_word_alert",4.0):
            alerts.append("LOW-FREQ-SCORES")
        elif freq[0] < config.get("freq_avg_alert",5.0) or freq[1] < config.get("freq_word_alert",4.0):
            alerts.append("SUSPECT-FREQ-SCORE")
    with app.app_context():
        resp = jsonify({"seen_by_web":created , "seen_by_isc":"WHOIS", "seen_by_you":now, "category":category, "alerts":alerts, "freq_score": freq})
    print(f"Patchup record for {domain} \nTo {resp.json}")
    cache.cache.set( domain, resp.json, expire= until_expires, tag="whois")
    return 1

app = Flask(__name__)
app.name = "domain_stats"

try:
    import whois
except Exception as e:
    print(str(e))
    print("You need to install the Python whois module.  Install PIP (https://bootstrap.pypa.io/get-pip.py).  Then 'pip install python-whois' ")
    sys.exit(0)

args=config=cache=fc= None

def main():
    global args, config, cache, fc
    parser = argparse.ArgumentParser()
    parser.add_argument("data_folder", help="Folder with the domain data must be provided")
    parser.add_argument("-e","--export", help="Export database entries as json to the specified text file.")
    parser.add_argument("-i","--import", dest="importer", help="Import the specified json text file into the database.")
    parser.add_argument("-d","--domain_file", help="Open specified domain file and build records for them.")
    parser.add_argument("-f","--fix", action="store_true", help="Use whois to resolve each entry with an RDAP error")
    parser.add_argument("-nx","--no-expire", dest='noexpire', action="store_true", help="Set imported record never to expire instead of using domain expiration.")
    parser.add_argument("-v","--verbose",action="store_true", help="Be verbose in output.")

    args = parser.parse_args('-e /home/student/domain_stats/test.export /home/student/dstest'.split())
    #current directory must be set by launcher to the location of the config and database
    cache = ExpiringCache(args.data_folder)
    config = Config( args.data_folder + "/domain_stats.yaml")

    establish_age = config.get("established_days_age",720)
    low_avg = config.get('freq_avg_alert',5.0)
    low_word = config.get('freq_word_alert',4.0)
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    fc = FreqCounter()
    fc.load( args.data_folder +"/" + config.get("freq_table", "freqtable2018.freq") )
    if args.domain_file:
        written = 0
        ip = config.get("ip_address","127.0.0.1")
        port = config.get("local_port")
        with open(args.domain) as domain_file:
            for eachline in domain_file:
                domain = eachline.strip()
                url = f"http://{ip}:{port}/{domain}"
                resp = requests.get(url).json()
                if resp.get("seen_by_web") == "ERROR":
                    written += whois_patch_domain(domain, [])
                elif "FIRST CONTACT" in resp.get("alerts"):
                    written += 1 
                time.sleep(1)
        print(f"{written} entries added to database.")
    elif args.fix:
        written = 0
        for domain in cache.cache:
            val, expires = cache.cache.get(domain, expire_time=True)
            if not val:
                continue
            if val.get("seen_by_web") != "ERROR":
                continue
            written += whois_patch_domain(domain, val.get("alerts"), val.get("freq"),)
        print(f"{written} rdap errors were fixed.")
    elif args.export:
        result = []
        for domain in cache.cache:
            val, expires = cache.cache.get(domain, expire_time=True)
            if not val:
                continue
            if val.get("seen_by_web")=="ERROR":
                continue
            val['seen_by_isc'] = args.export.split(".")[0]
            del val['category']
            del val['seen_by_you']
            del val['alerts']
            val.update({"expires":expires, "domain":domain})
            result.append(to_json(**val))
        res = json.dumps(result)
        fh = open(args.export,"wt")
        fh.write(res)
        fh.close()
    elif args.importer:
        written = 0
        with open(args.importer) as fh:
            new_data = json.load(fh)
        for each_entry in new_data:
            import_domain_rec(each_entry, args.noexpire)
    else:
        print("Use either the --domains or --errors argument.")

    cache.cache.close()


if __name__=="__main__":
    main()
