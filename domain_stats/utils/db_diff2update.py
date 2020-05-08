import sqlite3
import pathlib
import sys
import argparse


parser=argparse.ArgumentParser()
parser.add_argument('fresh_install',help='Path to a domain_stats.db from a fresh install of the module (with all current updates).')
parser.add_argument('updated_db', help='Path to domain_stats.db with updated records that you would like to generate a update file for.')
parser.add_argument('-o','--outfile',default="update.txt",help='Path to the file to create or overwrite that will contain the new records.')
args = parser.parse_args()
  


database_with_new_records = args.updated_db
fresh_install_database = args.fresh_install

if not pathlib.Path(database_with_new_records).is_file():
    print("The updated database path specified doesn't point to a database.")
    sys.exit(1)
if not pathlib.Path(fresh_install_database).is_file():
    print("The new install database path specified doesn't point to a database.")
    sys.exit(1)

outfile = open("update.txt","wt")


#Open both the fresh and updated databases
db = sqlite3.connect(database_with_new_records)
cursor = db.cursor()
cursor.execute("attach database ? as fresh",(fresh_install_database,))

sql = "select domain,seen_by_web,expires from domains where domain not in (select domain from fresh.domains where domain==fresh.domains.domain) and expires < date('now')"
#Go through all the new records and create an entry in the update file.
for domain,web,exp in cursor.execute(sql):
     outfile.write(f"+,{domain},{web},{exp}\n")

#Deleted expired records
sql = "select domain,seen_by_web,expires from fresh.domains where expires < date('now');"
for domain,web,exp in cursor.execute(sql):
     outfile.write(f"-,{domain},{web},{exp}\n")

outfile.close()