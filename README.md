#domain_stats.py
#Version 1.0 
#Written by Mark Baggett @markbaggett
#Under direction of Justin Henderson @securitymapper
#Thanks to Justin Henderson for being the complete creative force behind the program.  He said what he wanted.  I wrote it. 

domain_stats.py is a web API to deliver domain information from whois and alexa. 
Some security enterprise management systems are capable of querying web APIs for additional information.  This API provides easy access to that information for those systems.

## Getting Started

**Start domain_stats.py**

```
python domain_stats.py -ip 127.0.0.1 8000
```

## Queries

The API is simple.  Once the server is started you can query either the Alexa ranking of a domain:

`http://<ip>:<port>/alexa/<domain>`

#### Example

```bash
student@SEC573:~$ curl http://127.0.0.1:8000/alexa/sans.org
25646
```

This tells us that SANS.ORG is the 25646th most popular domain on the internet.  So it probably isn't a phishing site.  

_**NOTE:** The alexa option is only available with the alexa database is provided as a command line option. You can download a copy of the data at http://s3.amazonaws.com/alexa-static/top-1m.csv.zip_

**NOTE FUTHER**  Alexa has discontinued their support for the top 1 million.  Cisco Umbrella is now offering a free alternative.  It can be downloaded here https://s3-us-west-1.amazonaws.com/umbrella-static/index.html  The files are using the exact same format and should be used with this tool instead of the alexa data which will quickly become outdated.   Thanks to Justin Henderson for finding the link to the Cisco replacment!

As not to break startup script, etc in existing deployements we will keep the -a --alexa command line arguments.


You can also query whois domain information for a domain.   This query will return the entire whois record for sans.org

```bash
student@SEC573:~$ curl http://127.0.0.1:8000/domain/sans.org
```

Alternatively you can query individual entries in the whois record by including field names in the path.

```bash
student@SEC573:~$ curl http://127.0.0.1:8000/domain/creation_date/sans.org
1995-08-04 04:00:00;
```

Queryable Fields
------

| WHOIS        | Location           | Misc  |
| ------------- |:-------------:| -----:|
| name  | zipcode    | dnssec |
| domain_name     | city       |   referral_url |
| expiration_date | state      |    alexa |
| creation_date | address     |    status |
| updated_date | country      |     |
| registrar |        |     |
| whois_server|        |     |
| emails |        |     |
| name_servers| 


You can query more than one field by simply listing the additional fields in the path.  The domain is always the last entry in the path.

```bash
student@SEC573:~$ curl http://127.0.0.1:8000/domain/creation_date/state/zipcode/city/sans.org
1995-08-04 04:00:00; MD; 20814; Bethesda;
```

Some fields such as *name_servers* or *updated_date* may contain multiple values.  By default the server will only return one of those values (the last one in the list).   _If you would like all of the values you can place an asterisk after the field name._  

Consider these two examples:

### Example 1

```bash
student@SEC573:~$ curl http://127.0.0.1:8000/domain/name_servers/google.com
ns4.google.com;
```
### Example 2

```bash
student@SEC573:~$ curl http://127.0.0.1:8000/domain/name_servers*/google.com
[u'NS1.GOOGLE.COM', u'NS2.GOOGLE.COM', u'NS3.GOOGLE.COM', u'NS4.GOOGLE.COM', u'ns3.google.com', u'ns1.google.com', u'ns2.google.com', u'ns4.google.com']; 
```

The first query returns a single name server where the second returns all the name servers.  This works the same for all the fields with multiple values.  If the __--all__ command line option is specified when the server is started it will always return all the fields.   Now lets look at the command line options for the server.


## Arguments

```bash
student@SEC573:~$ python domain_stats.py --help
usage: domain_stats.py [-h] [-ip ADDRESS] [-c CACHE_TIME] [-v] [-a ALEXA]
                       [--all] [--preload PRELOAD] [--delay DELAY]
                       [--garbage-cycle GARBAGE_CYCLE]
                       port

positional arguments:
  port                  You must provide a TCP Port to bind to

optional arguments:
  -h, --help            show this help message and exit
  -ip ADDRESS, --address ADDRESS
                        IP Address for the server to listen on. Default is
                        127.0.0.1 
  -c CACHE_TIME, --cache-time CACHE_TIME
                        Number of seconds to hold a whois record in the cache.
                        Default is 3600 (1 hour). Set to 0 to save forever.
  -v, --verbose         Print verbose output to the server screen. -vv is more
                        verbose.
  -a ALEXA, --alexa ALEXA
                        Provide a local file path to an Alexa top-1m.csv
  --all                 Return all of the values in a field if multiples
                        exist. By default it only returns the last value.
  --preload PRELOAD     preload cache with this number of the top Alexa domain
                        entries. set to 0 to disable preloading. Default 1000
  --delay DELAY         Delay between whois lookups while staging the initial
                        cache. Default is 0.1
  --garbage-cycle GARBAGE_CYCLE
                        Delete entries in cache older than --cache-time at
                        this iterval (seconds). Default is 86400
```

_Most of these arguments are optional._  The only thing you **MUST** specify is which port you want it to listen on.   The other options you probably want to use are --alexa (or -a), --delay and --preload.

__--alexa__ is followed by the path to the alexa top 1 million csv file discussed earlier. --preload is followed by an integer that says how many of those alexa domains you want to automatically do whois looks for to store in the cache on the server.  As stated above, you should use the Cisco Umbrella files now that Alexa has been discontinued. : https://s3-us-west-1.amazonaws.com/umbrella-static/index.html  

__--delay__ can be used to cause control the delay between whois queries when preloading the servers cache.  Most of the other options control that cache.  By default when an domain is queried from a whois server it is cached for 1 hour.  You can change this with --cache-time.

__--cache-time__ is followed by the number of seconds to store an entry in the cache. 86400 seconds is one day.   Setting the --cache-time to 0 will keep entries in memory forever (or until all memory is consumed and the server crashes)  The __--garbage-cycle__ option specifies how long to delay between cycles of cleaning up the cached entries older than --cache-time. 

Here is an example of starting the server on port 8000 and only loading the top 100 most common alexa entries

```bash
student@SEC573:~$ python domain_stats.py --preload 100 -a ~/Downloads/top-1m.csv 8000 
```
