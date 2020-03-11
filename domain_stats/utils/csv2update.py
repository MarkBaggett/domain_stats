import csv
import sqlite3
import datetime


#domain, web_born_on, web_expires, Rank, seen_by_you   

filename="sample_com_v30_full_1000.csv"
update_file = "1.0.csv"

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


with open(filename) as fhandle, open(update_file,"w") as uhandle:
    csvreader = csv.DictReader(fhandle)
    for eachrow in csvreader:
        #import pdb;pdb.set_trace()
        domain  = reduce_domain(eachrow.get("domainName"))
        registered = eachrow.get("createdDate")
        expires = eachrow.get("expiresDate")
        if not registered or not expires:
            continue
        #import pdb;pdb.set_trace()
        registered = datetime.datetime.strptime(registered, '%Y-%m-%dT%H:%M:%SZ')
        expires = datetime.datetime.strptime(expires, '%Y-%m-%dT%H:%M:%SZ')
        new_entry = f"+,{domain},{registered},{expires}\n"
        uhandle.write(new_entry)
        #print(f"writing {domain}")
