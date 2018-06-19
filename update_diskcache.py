#!/usr/bin/env python3

import time
import re
import pickle
import argparse
import six


if six.PY2:
    raise(Exception("You should only use Python 3 to build the offline cache."))

try:
    import whois
except Exception as e:
    print(str(e))
    print("You need to install the Python whois module.  Install PIP (https://bootstrap.pypa.io/get-pip.py).  Then 'pip install python-whois' ")
    sys.exit(0)

def preload_domains(domain_list, delay=0.1):
    global cache
    print("Now preloading %d domains from alexa in the whois cache." %(len(domain_list)))
    dcount = 0
    dtenth = len(domain_list)/10
    for eachalexa,eachdomain in re.findall(r"^(\d+),(\S+)", "".join(domain_list), re.MULTILINE):
        time.sleep(delay)
        dcount += 1
        if (dcount % dtenth) == 0:
            print("Loaded %d percent of whois cache." % (float(dcount)/len(domain_list)*100))
        try:
            domain_info = whois.whois(eachdomain)
            if not any(domain_info.values()):
                print("No whois record for %s" % (eachdomain))
                continue
        except Exception as e:
            print("Error querying whois server: %s" % (str(e)))     
            continue
        domain_info["time"] = time.time()
        domain_info['alexa'] = eachalexa
        cache[eachdomain] = domain_info
    print("Domain Cache Fully Loaded")


parser=argparse.ArgumentParser()
parser.add_argument('-c','--count',type=int, help='The number of domains to read into the disk cache',default=1000)
parser.add_argument('-f','--file',help='Name of the file to write.',default="domain_cache.dst")
parser.add_argument('-a','--append',action="store_true", required=False,help='Append to existing file instead of overwriting.')
args = parser.parse_args()
print args

cache = {}
try:
    alexa = open("top-1m.csv").readlines()[900:args.count]
except Exception as e:
    raise(Exception("Cant find your alexa top-1m.csv file. {0}".format(str(e))))

if args.append:
    try:
        fh = open("domain_cache.dst") 
        cache = pickle.load(fh)
        fh.close()
    except Exception as e:
        raise(Exception("An error occured loading the disk cache {0}".format(str(e)))) 

preload_domains(alexa)

try:
    fh = open(args.file,"w")
    pickle.dump(cache, fh, protocol=2)
    fh.close()
except Exception as e:
    raise(Exception("Unable to create your disk cache file. {0}".format(str(e))))


