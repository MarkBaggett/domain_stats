import csv
import sqlite3
import datetime


#domain, web_born_on, web_expires, Rank, seen_by_you   

databasename = "dstat.db"
filename="sample_com_v30_full_1000.csv"
createstr="""
CREATE TABLE domains (
 domain text NOT NULL UNIQUE,
 seen_by_web timestamp not NULL,
 expires timestamp not NULL,
 seen_by_isc timestamp not NULL,
 seen_by_you timestamp not NULL
);
"""

#sqlite dump establishe to txt
#.headers off
#.mode csv
#.output 2.txt
#select domain from domains where seen_by_web <  date('now','-2 years');
#.quit

def get_db():
    db =  sqlite3.connect(databasename, timeout=15, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    return db

def create_tables():
    datab = get_db()
    cursor = datab.cursor()
    cursor.execute(createstr)
    datab.commit();

create_tables()

with open(filename) as fhandle:
    sql = "insert into domains (domain,seen_by_web, expires, seen_by_isc, seen_by_you) values (?,?,?,?,?) " 
    csvreader = csv.DictReader(fhandle)
    db = get_db()
    cursor = db.cursor()
    for eachrow in csvreader:
        #import pdb;pdb.set_trace()
        domain  = eachrow.get("domainName")
        registered = eachrow.get("createdDate")
        expires = eachrow.get("expiresDate")
        if not registered or not expires:
            continue
        #import pdb;pdb.set_trace()
        registered = datetime.datetime.strptime(registered, '%Y-%m-%dT%H:%M:%SZ')
        expires = datetime.datetime.strptime(expires, '%Y-%m-%dT%H:%M:%SZ')
        print(f"inserting {domain}")
        cursor.execute(sql , (domain, registered, expires, "NA" ,"FIRST-CONTACT" ) )
    db.commit()
