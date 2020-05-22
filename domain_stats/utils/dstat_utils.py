import yaml
import sqlite3
import datetime
import collections
import threading
import socket
import json
import logging



def get_creation_date(whois_record, debug=False):
    born_on = whois_record.get("creation_date","invalid-creation_date")
    if type(born_on) == list:
        #Enhancement: Improve by fiding the most recent born on date
        born_on = min(born_on)
    if born_on == "invalid-creation_date":
        log.debug("{} Improve whois record parser for creation date.{}".format('*'*50, whois_record))
    try:
        datetime_object = datetime.datetime.strptime(str(born_on), '%Y-%m-%d %H:%M:%S')
    except Exception as e:
        log.debug("Creation date parsing could not convert to timestamp. Falling to client query. {}".format( str(e)))
        return False
    return datetime_object

def reduce_domain(domain_in):
    parts =  domain_in.strip().split(".")
    if len(parts)> 2: 
        if parts[-1] not in ['com','org','net','gov','edu']:
            if parts[-2] in ['co', 'com','ne','net','or','org','go','gov','ed','edu','ac','ad','gr','lg','mus','gouv']:
                domain = ".".join(parts[-3:])
            else:
                domain = ".".join(parts[-2:])
        else:
            domain = ".".join(parts[-2:])
            #print("trim top part", domain_in, domain)
    else:
        domain = ".".join(parts)
    return domain.lower()

def get_db():
    db =  sqlite3.connect(config.database_file, timeout=15)
    return db

def new_domain(cursor, rank,domain):
    sql = "insert or ignore into domains (domain,seen_by_web, seen_by_us, seen_by_you, rank, other) values (?,?,?,?,?,?) " 
    with lock:
        if rank == "-2":
            try:
                cursor.execute("delete from domains where domain = ?", (domain,)) 
            except Exception as e:
                print("Warning: {}".format( str(e)))
        else:
            try:
                result = cursor.execute(sql , (domain, "ESTABLISHED", "ESTABLISHED", "FIRST-CONTACT" ,rank, "{}" ) )
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e) or "is not unique" in str(e):
                    return False
                else:
                    print("Error inserting record - {},{}".format(str(e),dir(e)))
                    raise(e)
    return True


def load_config():
    with open("domain_stats.yaml") as fh:
        yaml_dict = yaml.safe_load(fh.read())
    Configuration = collections.namedtuple("Configuration", list(yaml_dict) )
    return Configuration(**yaml_dict)

def update_config(**set_attribs):
    current_config = load_config()
    mutable_config = current_config._asdict()
    for each_attrib,each_val in set_attribs.items():
        mutable_config[each_attrib] = each_val
    with open('domain_stats.yaml', 'w') as fp:
        yaml.dump(dict(mutable_config), fp, default_flow_style=False)
    Configuration = collections.namedtuple("Configuration", list(mutable_config) )
    return Configuration(**mutable_config)

def verify_domain(domain):
    parts = domain.split(".")
    if parts[0] in [ 'co', 'com','ne','net','or','org','go','gov','ed','edu','ac','ad','gr','lg','mus','gouv']:
        return False
    try:
        resolved = socket.gethostbyname(domain)
    except socket.gaierror as e:
        if e.errno == socket.EAI_NODATA:
            #print("No Data error",  domain)
            return True
        elif e.errno == socket.EAI_NONAME:
            #print("No name error",domain)
            return True
        else: 
            print("No dns name", domain, str(e))
            with open("dnserrors.log", mode="a") as fh:
                fh.write(domain + "\n")
            return False
    return True

config = load_config()
lock = threading.Lock()

log = logging.getLogger(__name__)
logfile = logging.FileHandler('domain_stats.log')
logformat = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
logfile.setFormatter(logformat)

if config.log_detail==0:
    log.setLevel(level=logging.CRITICAL)
elif config.log_detail==1:
    log.addHandler(logfile)
    log.setLevel(logging.INFO)
else:
    log.addHandler(logfile)
    log.setLevel(logging.DEBUG)


