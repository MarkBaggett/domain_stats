#!/usr/bin/env python2
import logging
import os
import sqlite3

import requests


class domainLookup:
    """
    Caches results in a database and can be synced with expiration dates set to expire
    """

    # TODO Create option to requery for domains with no WHOIS
    # TODO Create option to not store whois data if no whois_data exist.

    NO_WHOIS = 'NO WHOIS'
    NO_RECORD_RETURNED = 'No whois record'
    NO_DATE = '0000-00-00 00:00:00'
    NO_CREATED = NO_DATE
    NO_EXPIRED = NO_DATE
    NORM_PRE_WHOIS = '1996-01-01 00:00:00'
    DOMAIN_STATS_PATH = 'domain/registrar/creation_date/expiration_date'

    # Setup logging
    logger = logging.getLogger('domain_lookup')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    def __init__(self, url=None,
                 verbose=False,
                 db='whois1.db',
                 db_path='./',
                 renew_expired=False,
                 allow_none=True,
                 debug=False):

        self.url = url
        self.db = db
        self.db_path = db_path
        self.columns = ['domain_name', 'org', 'creation_date', 'expiration_date']
        self.renew_expired = renew_expired
        self.allow_none = allow_none
        self.debug = debug
        self.verbose = verbose
        self.first_connect = False

        if self.db is not None:
            if self.db_path:
                self.database = os.path.join(self.db_path,
                                             db)
            else:
                self.database = \
                    os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 'database', db))
            if not os.path.exists(self.db_path):
                os.makedirs(self.db_path)
                self.custom_print('Creating directory {dir}'.format(dir=self.db_path))

            if not os.path.exists(self.database):
                with open(self.database, 'w'):
                    self.custom_print('Creating file {dir}'.format(dir=self.database))
                    self.first_connect = True
                    pass

        if not url:
            raise Exception('Please specify the URL where domain_stats is running')
        try:
            if self.db:
                self.conn = sqlite3.connect(self.database)
                self.cur = self.conn.cursor()
                if self.first_connect:
                    self.custom_print('Creating table: domain_records')
                    self.create_table()
            else:
                print("[ERROR] You must specify a db name. Example: whois.db")
        except Exception as e:
            print(e)

        self.verbose = verbose

    def custom_print(self, msg, debug=False):
        if self.verbose:
            self.logger.info(str(msg))
        if debug:
            self.logger.debug(str(msg))

    def query_record(self, path, domain):
        full_url = self.url + '/' + path + '/' + domain
        out = None
        try:
            out = requests.get(full_url).content
        except Exception as e:
            self.custom_print(e)
        return out

    def create_table(self):
        self.cur.execute("CREATE TABLE IF NOT EXISTS domain_records (id INTEGER PRIMARY KEY,"
                         " domain_name TEXT, org TEXT, creation_date DATE, expiration_date DATE,"
                         " time_inserted DATETIME DEFAULT CURRENT_TIMESTAMP)")
        self.conn.commit()

    def record_insert(self, record):
        self.cur.execute("insert into domain_records({table_columns}) values (?,?,?,?)".format(
            table_columns=', '.join(self.columns)), record)
        self.conn.commit()

    def select_record(self, domain):
        self.cur.execute("SELECT * FROM domain_records WHERE domain_name=?", (domain,))
        rows = self.cur.fetchall()
        return rows

    def record_check(self, v, lower=False, last=False):
        value = v
        if type(value) == list:
            if last and len(value) > 1:
                value = value[-1]
            else:
                value = ', '.join(value)
        if lower and value is not None:
            value = value.lower()
        return value

    def date_check(self, date):
        if type(date) == list:
            return date[-1]
        else:
            return date

    def normalize_record(self, domain, record):
        try:
            org, creation_date, expiration_date = record.strip().split(";")[:-1]
            if 'before' in creation_date:
                creation_date = self.NORM_PRE_WHOIS
            expiration_date = self.date_check(expiration_date)
            if org is None:
                org = 'No Org Listed'
            db_rec = (domain, org, creation_date, expiration_date)
        except:
            db_rec = (domain, self.NO_WHOIS, self.NO_CREATED, self.NO_EXPIRED)
        return db_rec

    def retrieve_domain(self, domain):
        domain_present = False
        record = self.select_record(domain)
        self.custom_print('Checking database...')
        if record:
            r = record[0]

            record = {'domain': r[1],
                      'org': r[2],
                      'creation_date': r[3],
                      'expiration_date': r[4],
                      'cached': r[5]}

            self.custom_print('%s found in database!' % domain)
        elif not record and not domain_present:
            self.custom_print('%s not found in database. Querying domain_stats...' % domain)
            record = self.query_record(self.DOMAIN_STATS_PATH, domain)
            if self.NO_RECORD_RETURNED not in record:
                # CHECK FOR NONTYPE RECORDS
                norm_record = self.normalize_record(domain, record)
                db_ready = not any(elem is None for elem in norm_record)

                if db_ready:
                    record = {'domain': norm_record[0],
                              'org': norm_record[1],
                              'creation_date': norm_record[2],
                              'expiration_date': norm_record[3]}

                    self.record_insert(norm_record)
                    self.custom_print('%s inserted into database!' % domain)

                else:
                    self.custom_print((domain, record, norm_record), debug=self.debug)
            elif (record is None or self.NO_RECORD_RETURNED in record) and self.allow_none:
                # NO RECORD PRESENT - populate with dummy data
                record = {'domain': domain, 'org': self.NO_WHOIS, 'creation_date': self.NO_CREATED,
                          'expiration_date': self.NO_EXPIRED}
                self.record_insert(record)
                self.custom_print("No WHOIS for %s - storing" % domain)
            else:
                # Do not store WHOIS for blank domains
                self.custom_print("No WHOIS for %s - not storing" % domain)

        return record
