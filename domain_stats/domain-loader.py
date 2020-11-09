import logging
import datetime
import argparse
import pathlib
import sys
import os

log = logging.getLogger("domain_stats_util_whois")

from domain_stats.config import Config
from domain_stats.expiring_diskcache import ExpiringCache
from domain_stats.freq import FreqCounter
from flask import Flask,jsonify


def whois_patch_domain(domain, freq, alerts):
    who_rec = whois.whois(domain)
    if not who_rec:
        if args.verbose: print(f"No whois record found for {domain}")
        return 0
    created = who_rec.get('creation_date')
    if not created:
        if args.verbose: print(f"No creation date found for {domain}")
        return 0
    if isinstance(created,list):
        created = max(created)
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
    if domain_age_seconds > (est_day_age *86400):
        category = "ESTABLISHED"      
    else:
        category = "NEW"
        until_established = (est_day_age * 86400) - domain_age_seconds
        until_expires = min( until_expires, until_established )
    with app.app_context():
        resp = jsonify({"seen_by_web":created , "seen_by_isc":"WHOIS", "seen_by_you":now, "category":category, "alerts":alerts, "freq_score": freq})
    if args.preview:
        print(f"Patchup record for {domain} \nTo {resp.json}")
    else:
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

parser = argparse.ArgumentParser()
parser.add_argument("data_folder", help="Folder it data")
parser.add_argument("-p","--preview", action="store_true", help="Do not commit to disk. Show changes.")
parser.add_argument("-d","--domain_file", help="Open specified domain file and use whois to build entries.")
parser.add_argument("-e","--errors", action="store_true", help="Try to use whois to resolve each entry with an RDAP error")
parser.add_argument("-v","--verbose",action="store_true", help="Be verbose in output.")

args = parser.parse_args()
#current directory must be set by launcher to the location of the config and database
cache = ExpiringCache(args.data_folder)
config = Config( args.data_folder + "/domain_stats.yaml")

est_day_age = config.get("established_days_age",720)
now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

if args.domain_file:
    fc = FreqCounter()
    fc.load( args.data_folder +"/" + config.get("freq_table", "freqtable2018.freq") )
    written = 0
    for eachline in open(args.domain_file):
        domain = eachline.strip()
        freq = fc.probability(domain)
        written += whois_patch_domain(domain, freq, [])
    print(f"{written} entries added to database.")
elif args.errors:
    written = 0
    for domain in cache.cache:
        val, expires = cache.cache.get(domain, expire_time=True)
        if val.get("seen_by_web") != "ERROR":
            continue
        whois_patch_domain(domain, val.get("freq_score"), val.get("alerts"))
    print(f"{written} rdap errors were fixed.")
else:
    print("Use either the --domains or --errors argument.")

cache.cache.close()