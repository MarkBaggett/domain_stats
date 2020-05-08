import logging
import requests
import rdap
import json
import datetime
import dateutil.parser
import dateutil.tz

log = logging.getLogger("domain_stats")

def get_config(update_url):
    try:
        config = requests.get( update_url + "/version.json").json()
    except Exception as e:
        print(f"Unable to retreive /version.json info from {update_url} {str(e)}")
        return 9999,99999
    return config.get("min_client_version"), config.get("min_database_version")

def update_database(self, latest_version, update_url):
        new_records_count = 0
        latest_major, latest_minor = map(int, str(latest_version).split("."))
        current_major, current_minor = map(int, str(self.version).split("."))
        dst_folder = pathlib.Path(self.filename).parent / "data" / f"{current_major}"
        if not dst_folder.exists():
            os.makedirs(dst_folder)
        log.info(f"Updating from {self.version} to {latest_version}")
        if latest_major > current_major:
            log.info("WARNING: Domain Stats database is a major revision behind. Database required rebuild.")
            raise Exception("WARNING: Domain Stats database is a major revision behind. Database required rebuild.")
        target_updates = range(current_minor+1, latest_minor+1 )
        for update in target_updates:
            version = f"{current_major}.{update}"
            log.info(f"Now applying update {version}")
            tgt_url = f"{update_url}/{current_major}/{update}.txt"
            dst_path = pathlib.Path().cwd() / "data" / f"{current_major}" / f"{update}.txt"
            try:           
                urllib.request.urlretrieve(tgt_url, str(dst_path))
            except:
                print(f"ERROR: Unable to access database updates. {tgt_url}")
                log.critical(f"Unable to access database updates. {tgt_url}")
                return self.version, 0
            new_records_count += self.process_update_file(str(dst_path))
        self.version = latest_version
        self.lastupdate = datetime.datetime.utcnow()
        db = sqlite3.connect(self.filename, timeout=15)
        cursor = db.cursor()
        cursor.execute("update info set version=?, lastupdate=?",(self.version, self.lastupdate))
        db.commit()
        return latest_version, new_records_count

def retrieve_data(action_name,eventlist):
    for entry in eventlist:
        if entry.get("eventAction") == action_name:
            return entry.get("eventDate")
    return None

def get_domain_record(domain):
    client = rdap.client.RdapClient()
    client.url = "https://www.rdap.net"
    client.timeout = 5
    try:
        resp = client.get_domain(domain).data
    except Exception as e:
        return "ERROR","ERROR", str(e)
    reg = retrieve_data( 'registration', resp.get('events'))
    reg = dateutil.parser.isoparse(reg)
    reg.replace(tzinfo=datetime.timezone.utc)
    exp = retrieve_data( 'expiration', resp.get('events'))
    try:
        exp = dateutil.parser.isoparse(exp)
    except Exception as e:
        return "ERROR","ERROR", f"Invalid RDAP response Domain: {domain} generated {str(e)}"
    exp.replace(tzinfo=datetime.timezone.utc)
    return reg,exp,""