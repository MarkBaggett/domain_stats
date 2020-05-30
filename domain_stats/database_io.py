import logging
import sqlite3
import threading
import datetime
import pathlib
import urllib
import os
from publicsuffixlist import PublicSuffixList

log = logging.getLogger("domain_stats")

  
class database_stats:
    def __init__(self, hit=0,miss=0, insert=0, delete=0) :
        self.hit = hit
        self.miss = miss
        self.insert = insert
        self.delete = delete

    def __repr__(self):
        repr = "database_stats(hit={0},miss={1},insert={2},delete={3})".format(self.hit,self.miss,self.insert,self.delete)
        return repr

def reduce_domain(domain_in):
    domain = PublicSuffixList().privatesuffix(domain_in).lower()
    log.debug("Trimmed domain from {0} to {1}".format(domain_in,domain))
    return domain

class DomainStatsDatabase(object):

    def __init__(self, filename):
        self.filename = filename
        self.lock = threading.Lock()
        self.stats = database_stats()
        if not pathlib.Path(self.filename).exists():
            print("WARNING: Database not found. {}".format(self.filename))
            return
        db = sqlite3.connect(filename, timeout=15)
        cursor = db.cursor()
        self.version,self.created,self.lastupdate = cursor.execute("select version,created,lastupdate from info").fetchone()

    def create_file(self, filename):
        datab = sqlite3.connect(filename)
        cursor = datab.cursor()
        cursor.execute("CREATE TABLE domains (domain text NOT NULL UNIQUE,seen_by_web timestamp not NULL,expires timestamp not NULL,seen_by_isc timestamp not NULL,seen_by_you timestamp not NULL)")
        cursor.execute("CREATE TABLE info (version real NOT NULL,created timestamp not NULL,lastupdate timestamp not NULL)")
        new_info = (1.0, datetime.datetime.utcnow(), datetime.datetime.utcnow())
        cursor.execute("insert into info (version, created, lastupdate) values (?,?,?)", new_info)
        datab.commit()
        self.version, self.created, self.last_update = new_info

    def reset_first_contact(self):
        db= sqlite3.connect(self.filename)
        log.info("Database_admin was used to reset all of the seen_by_you dates to FIRST-CONTACT")
        print("Resetting all seen_by_you dates to FIRST-CONTACT.")
        cursor = db.cursor()
        cursor.execute("update domains set seen_by_you=?", ("FIRST-CONTACT",))
        db.commit() 
        print("RESET! You probably want to also delete your .cache file at this time.")

    def update_record(self, domain, record_seen_by_web, record_expires, record_seen_by_isc, record_seen_by_you):
        record_seen_by_web = record_seen_by_web.strftime('%Y-%m-%d %H:%M:%S')
        record_expires = record_expires.strftime('%Y-%m-%d %H:%M:%S')
        #If it was an RDAP record "seen by you" will contain the RDAP date so just make it a local database record.
        if record_seen_by_isc == "RDAP":
            record_seen_by_isc = "LOCAL"
        if record_seen_by_isc != "LOCAL":
            record_seen_by_isc = record_seen_by_isc.strftime('%Y-%m-%d %H:%M:%S')
        if record_seen_by_you != "FIRST-CONTACT":
            record_seen_by_you = record_seen_by_you.strftime('%Y-%m-%d %H:%M:%S')
        db = sqlite3.connect(self.filename, timeout=15)
        cursor = db.cursor()
        log.info("Writing to database {} {} {} {} {} {}".format(self.filename, domain, record_seen_by_web, record_expires, record_seen_by_isc, record_seen_by_you))
        sql = "insert or replace into domains (domain, seen_by_web,expires,seen_by_isc,seen_by_you) values (?,?,?,?,?)"
        with self.lock:
            cursor.execute(sql, (domain, record_seen_by_web, record_expires, record_seen_by_isc, record_seen_by_you))
            db.commit()
            self.stats.insert += 1
        return 1

    def delete_record(self, domain, expires=None):
        log.info("Deleting record from database for {}".format(domain))
        db = sqlite3.connect(self.filename, timeout=15)
        cursor = db.cursor()
        deletecount = 0
        with self.lock:
            if expires:
                result = cursor.execute("delete from domains where domain=? and expires=?", (domain,expires))
            else:    
                result = cursor.execute("delete from domains where domain=?", (domain,))
            db.commit()
            deletecount = result.rowcount
            self.stats.delete += deletecount
        return deletecount

    def get_record(self, domain):
        #Pass the timezone offset  hardcoded to utc for now
        #If record not found returns None,None,None,None
        #If record found rturns dates seen by web,expired,isc and you
        #If record is in database but domain registration expired it deletes the record and ignores it.
        timezone_offset = 0
        db = sqlite3.connect(self.filename, timeout=15)
        cursor = db.cursor()
        record = cursor.execute("select seen_by_web,expires, seen_by_isc, seen_by_you from domains where domain = ?" , (domain,) ).fetchone()
        if record:
            web,expires,isc,you = record
        else:
            self.stats.miss += 1
            log.info("No record in the database for {} returning None.".format(domain))
            return (None,None,None,None)
        web = datetime.datetime.strptime(web, '%Y-%m-%d %H:%M:%S')
        expires = datetime.datetime.strptime(expires, '%Y-%m-%d %H:%M:%S')
        if expires < datetime.datetime.utcnow():
            log.info("Expired domain in database deleted. {} {}".format( domain,expires))
            with self.lock:
                cursor.execute("delete from domains where domain=?", (domain,))
                db.commit()
                self.stats.delete += 1
            return (None,None,None,None)
        if isc != "LOCAL":
            isc = datetime.datetime.strptime(isc, '%Y-%m-%d %H:%M:%S')
        if you != "FIRST-CONTACT":
            you = datetime.datetime.strptime(you, '%Y-%m-%d %H:%M:%S')
        else:
            with self.lock:
                cursor.execute("update domains set seen_by_you=? where domain =?", ((datetime.datetime.utcnow()+datetime.timedelta(hours=timezone_offset)).strftime("%Y-%m-%d %H:%M:%S"), domain))
                db.commit()
        self.stats.hit += 1
        return (web,expires,isc,you)

    def process_update_file(self, update_file):
        """ Process csv in the format command, domain, web, expire, seen_by_isc """
        """ if command is + we add the record setting if it doesnt already exist"""
        """ if command is - we delete the record"""
        if not pathlib.Path(update_file).exists():
            log.info("The specified update file {} does not exists.".format(update_file))
            return 0
        new_domains = open(update_file).readlines()
        num_recs = len(new_domains)
        db = sqlite3.connect(self.filename, timeout=15)
        cursor = db.cursor()    
        for pos,entry in enumerate(new_domains):
            if pos % 50 == 0:
                print("\r|{0:-<50}| {1:3.2f}%".format("X"*( 50 * pos//num_recs), 100*pos/num_recs),end="")
            command, domain, web, expires = entry.strip().split(",")
            domain = reduce_domain(domain)
            web = datetime.datetime.strptime(web, '%Y-%m-%d %H:%M:%S')
            expires = datetime.datetime.strptime(expires, '%Y-%m-%d %H:%M:%S')
            if command == "+":
                record = cursor.execute("select seen_by_web, expires, seen_by_isc, seen_by_you from domains where domain = ?" , (domain,) ).fetchone()
                if not record:
                    self.update_record(domain, web, expires,"LOCAL", "FIRST-CONTACT")
                    log.debug("Record added to database for domain {}".format(domain))
                else:
                    with self.lock:
                        cursor.execute("update domains set expires=? where domain =?", (expires, domain))
                        db.commit()
                        log.debug("Record for {0} already exists. Expiration was {1} is now {2}.".format(domain, record[1], expires))
            elif command == "-":
                self.delete_record(domain,expires)
                log.debug("Deleted record for {}".format(domain) )
        db.commit()
        print("\r|XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX| 100.00% FINISHED")
        return num_recs

    def update_database(self, latest_version, update_url):
        new_records_count = 0
        latest_major, latest_minor = map(int, str(latest_version).split("."))
        current_major, current_minor = map(int, str(self.version).split("."))
        dst_folder = pathlib.Path(self.filename).parent / "data" / str(current_major)
        if not dst_folder.exists():
            os.makedirs(dst_folder)
        log.info("Updating from {} to {}".format(self.version,latest_version))
        if latest_major > current_major:
            log.info("WARNING: Domain Stats database is a major revision behind. Database required rebuild.")
            raise Exception("WARNING: Domain Stats database is a major revision behind. Database required rebuild.")
        target_updates = range(current_minor+1, latest_minor+1 )
        for update in target_updates:
            version = "{}.{}".format(current_major,update)
            log.info("Now applying update {}".format(version))
            tgt_url = "{}/{}/{}.txt".format(update_url, current_major, update)
            dst_path = pathlib.Path().cwd() / "data" / str(current_major) / "{}.txt".format(update)
            try:           
                urllib.request.urlretrieve(tgt_url, str(dst_path))
            except:
                print("ERROR: Unable to access database updates. {}".format(tgt_url))
                log.critical("Unable to access database updates. {}".format(tgt_url))
                return self.version, 0
            new_records_count += self.process_update_file(str(dst_path))
        self.version = latest_version
        self.lastupdate = datetime.datetime.utcnow()
        db = sqlite3.connect(self.filename, timeout=15)
        cursor = db.cursor()
        cursor.execute("update info set version=?, lastupdate=?",(self.version, self.lastupdate))
        db.commit()
        return latest_version, new_records_count