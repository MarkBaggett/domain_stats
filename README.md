# domain_stats2

## Introduction
Domain_stats is a log enhancment utility that is intended help you find threats in your environment. It will identify the following possible threats in your environment.
 - Domains that were recently registered
 - Domains that no one in your organization has ever visited before
 - Domains with hostnames that appear to be random characters
 - Domains that the security community has identified as new (**Pending ISC Integration)
 - Domains that SANS ISC issues warning for (**Pending ISC Integration)

## The Old Domain_stats support
This version of domains_stats provides a number of benefits over the old version including performance, scalability, alerting, and isc integration. It does focus on born-on information which was the primary use of the tool and achieves its increaces performance by not processing the entire whois record. If you are looking for a copy of the old domain_stats which rendered ALL of the whois record rather than just the born-on information please let me make two suggestions.  First, that functionality has been moved to a new tool called "APIify" which can render any standard linux command in a json response for consumption. It also has improved caching and scalability over the old domain_stats. You can download [APIify HERE](https://github.com/markbaggett/apiify). You can also find the old version of domain_stats [in the releases section](https://github.com/MarkBaggett/domain_stats/releases/tag/1.0).

## Special Thanks
Thanks to the following individuals for their support, suggestions and inspirations without whom this version of domain_stats would not be possible.  
 - Justin Henderson [@securitymapper](https://twitter.com/securitymapper)
 - Don Williams [@bashwrapper](https://twitter.com/bashwrapper)
 - Dustin "cuz" Lee [@_dustinlee](https://twitter.com/_dustinlee)
 - Luke Flinders [@The1WhoPrtNocks](https://twitter.com/The1WhoPrtNocks)

## Ubuntu system preparation:
On Ubuntu you usually have to install Python PIP first. At a bash prompt run the following:
```
$ apt-get install python3-pip
```

## Install published package via PIP
```
$ python3 -m pip install domain-stats
```

## Install from latest source via PIP
Alternatively download the latest build from this github repo and install it as follows. Use PIP to install domain_stats rather than running setup.py.
```
$ git clone https://github.com/markbaggett/domain_stats
$ cd domain_stats
$ python3 -m pip install .
```

## Configure and Start

One the package is installed, make a directory that will be used to for storage of data and configuration files. Then run 'domain-stats-settings' and followed by 'domain-stats'. Both of those programs require you pass it the path to your data directory. The first command 'domain-stats-settings' creates or edits the required settings files. If you are not sure how to answer the questions just press enter and allow it to create the configuration files. The second command 'domain-stats' will run the server.

```
$ mkdir /mydata
$ domain-stats-settings /mydata
$ domain-stats /mydata
```

Here is what that looks like installed from source.

![alt text](./domain_stats.gif "Installation and use")

## Optional Load of top1m
**With the server up and running** you can use ```domain-stats-utils``` to enhance the domain stats data.  For example, to use whois to patch records that RDAP was unable to resolve you can use the -f or --fix option.
```
$ domain-stats-utils -f /path_to_data
```
You can also avoid the initial (likely to be terms of service violating) volume of request to RDAP when you first start your server by prestaging a group of roughly 35K records from domains taken from the Cisco Umbrealla Projects top1m domains. **WARNING: By choosing to prepopulate these domains in the 'seen database' you will not be alerted to the "FIRST CONTACT" when someone visits them for the first time**. That said, these are from the top 1 million most commonly used domains and you likely don't care about first contact with them.  To import these you again use domain-stats-utils. These records will be tagged with "top1m" in the "seen-by-isc" field.
```
$ domain-stats-utils -i domains-stats\data\top1m.import -nx /mydata
```
The -nx options tells domain_stats to never expire these records from its cache. Without this option it will use its default behavior and the records will expire from the database when the domain registration expires.  For the top most commonly used established domains this will prevent you from unessisarily looking up the domain registration date every year for these sites.

---
## Install and runnning in a container

To get a container up and running with domain_stats `docker build` passing the git file as a url. The `docker run` command must mount a directory into the container as the folder "host_mounted_dir" and to TCP port 8000 so you can access the server. In the example below port 5730 on the docker server is forwarded to the domain_stats server running inside the container on port 8000. Run docker run once with the -it option so you can go through the setup questions. One change you must make for a docker configuration is to change the default port from 127.0.0.1 to 0.0.0.0.   Otherwise, if you do not know a better answer then the default just press ENTER. When it is finished run the container again with the -d and --name options as shown below. After that you can `docker stop domain_stats` and `docker start domain_stats` as needed.
 
```
$ docker build --tag domain_stats_image http://github.com/markbaggett/domain_stats.git
$ mkdir ~/dstat_data
$ docker run -it --rm -v ~/dstat_data:/host_mounted_dir -p 8000:5730 domain_stats_image
Set value for ip_address. Default=127.0.0.1 Current=127.0.0.1 (Enter to keep Current): 0.0.0.0 
Set value for local_port. Default=5730 Current=5730 (Enter to keep Current): 
Set value for workers. Default=3 Current=3 (Enter to keep Current): 
Set value for threads_per_worker. Default=3 Current=3 (Enter to keep Current): 
Set value for timezone_offset. Default=0 Current=0 (Enter to keep Current): 
Set value for established_days_age. Default=730 Current=730 (Enter to keep Current): 
Set value for mode. Default=rdap Current=rdap (Enter to keep Current): 
Set value for freq_table. Default=freqtable2018.freq Current=freqtable2018.freq (Enter to keep Current): 
Set value for enable_freq_scores. Default=True Current=True (Enter to keep Current):
Set value for freq_avg_alert. Default=5.0 Current=5.0 (Enter to keep Current): 
Set value for freq_word_alert. Default=4.0 Current=4.0 (Enter to keep Current): 
Set value for log_detail. Default=0 Current=0 (Enter to keep Current): 
Commit Changes to disk?y

$ docker run -d --name domain_stats -v ~/dstat_data:/host_mounted_dir -p 8000:5730 --restart unless-stopped domain_stats_image
```

Once the container is running if you would like to change the settings or use the domain-stats-utils to import domains you can launch a second terminal process in the running image.  For example, here is how to import the top1m domains.  Always point domain-stats-utils and domain-stats-settings to /host_mounted_dir/ when inside the container.

```
$ docker exec -it domain_stats /bin/bash
root@8f6561dc0766:/# domain-stats-utils -i /app/domain_stats/data/top1m.import -nx /host_mounted_dir/
root@8f6561dc0766:/# exit
```
or 
```
$ docker exec -it domain_stats /bin/bash
root@8f6561dc0766:/# domain-stats-settings /host_mounted_dir/
root@8f6561dc0766:/# exit

```
---

## To Run domain_stats as a service
If you are not going to use a docker you may want to run domain_stats as a server. After installing domain_stats as described above you can set it to run as a service on your system using the provided .service file in the data folder. It will be necessary to edit the domain_stats.service file and change the "WorkingDirectory" entry so that it points to the location you are storing your data. After editing the file add the ["domain_stats.service"](./domain_stats/data/domain_stats.service) file to your `/etc/systemd/system` folder.  Then use `systemctl enable domain_stats` to set it to start automatically. 

## SEIM Integration:
This varies depending upon the SEIM. The web interface is designed for your SEIM to make API calls to it.  It will respond back with a JSON responce for you it to consume.  Since many SEIM products are already configured to consume ZEEK logs another easy option is to add the ["domain_stats.zeek"](./domain_stats/data/domain_stats.zeek) module to your zeek configuration. Check the zeek domainstats.log for "NEW" domains and check for alerts such as "YOUR-FIRST-CONTACT".

### Example Zeek Configuration:

Assuming that zeek is installed in `/opt/zeek` and you don't already have custom scripts configured you can do this:

 - Place domain_stats.zeek in a new directory called `/opt/zeek/share/zeek/policy/custom-script`
 - Add `@load ./domain_stats` to a new file called `/opt/zeek/share/zeek/policy/custom-script/__load__.zeek`  
 - Add `@load custom-scripts` to `/opt/zeek/share/zeek/site/local.zeek`
 - Make sure curl is installed. This is a dependency of zeeks ActiveHTTP module. (try `apt install curl`)
 - If you are running zeek in a VM you need uncomment `redef ignore_checksums = T;` in domain_stats.zeek
 - Start domain_stats server
 - In zeekctl `deploy`
 - Confirm domain_stats appears in loaded_scripts.log


## Using domain_stats

When LogStash or any other system makes a web request to the system it returns back data relevant to the domain queried.

The request is in the form ```http://ip:port/domain```  For example:
```
$ wget -q -O- http://127.0.0.1:5730/sans.org
{"alerts":["YOUR-FIRST-CONTACT"],"category":"ESTABLISHED","freq_score":[6.2885,7.9696],"seen_by_isc":"RDAP","seen_by_web":"Fri, 04 Aug 1995 04:00:00 GMT","seen_by_you":"Sat, 07 Nov 2020 17:19:49 GMT"}
```

#### Here is what the response fields mean

 - alerts - A list of alarms associated with the domain queried.  This can include
   * YOUR-FIRST-CONTACT   - This is the first time you have every queried this domain
   * SUSPECT-FREQ-SCORE   - One of the two freq scores is low
   * LOW-FREQ-SCORE       - Both of the freq scores are low
   * Other                - Other alerts may be added with ISC integration

 - SEEN_BY_YOU - This is the date this domain was first seen by you

 - SEEN_BY_ISC  - This may be one of a few possible values
   * RDAP      - When in RDAP mode this will contain the word RDAP
   * datetime  - When in ISC mode this will contain the date and time when the domain was first seen by the ISC
   * top1m or other name - When domains are preloaded into your database with domain-stats-utils the name of the import is displayed here
   
 - SEEN_BY_WEB - This is the date when the domain was first seen on the internet (ie the registration date)

 - CATEGORY    - This can be one of two possible values
   * NEW         - The registration date is less than the configured "established_days_age" (Default is two years)
   * ESTABLISHED - The domain is more than "established_days_age" days old

 - freq_score  - This contains two values measuring the "normalness" of the domain letters. If these numbers are below the thresholds established in the settings it will generate alerts.

#### In addition to requesting a domain the following urls can be used to check on your server.

```
$ wget -q -O- http://127.0.0.1:5730/stats  
```
This will show statistics on the efficiency of the cache and rdap. This also runs a consistency check on the database and repairs any issues.  The database is locked while this is running so don't constantly hit this url.

```
$ wget -q -O- http://127.0.0.1:5730/stats-reset  
```
Resets the RDAP failure and success

```
$ wget -q -O- http://127.0.0.1:5730/cache_get?domain=python.org
```
This will retrieve the record from the cache if it exists.

```
$ wget -q -O- http://127.0.0.1:5730/cache_browse?offset=1&limit=100
```
This will retrieve the first 100 record from the cache and display them.  Adjust offset and limit to see others.


## Configuration
To change the settings run the tool <domain-stats-settings> and pass it the path where your data is stored.

```
$ domain-stats-settings /home/student/mydata
Existing config found in directory. Using it.
Set value for ip_address. Default=0.0.0.0 Current=0.0.0.0 (Enter to keep Current): 
Set value for local_port. Default=5730 Current=5730 (Enter to keep Current): 
Set value for workers. Default=3 Current=1 (Enter to keep Current): 
Set value for threads_per_worker. Default=3 Current=3 (Enter to keep Current): 
Set value for timezone_offset. Default=0 Current=0 (Enter to keep Current): 
Set value for established_days_age. Default=730 Current=730 (Enter to keep Current): 
Set value for mode. Default=rdap Current=rdap (Enter to keep Current): 
Set value for rdap_error_ttl_days. Default=7 Current=7 (Enter to keep Current): 
Set value for freq_table. Default=freqtable2018.freq Current=freqtable2018.freq (Enter to keep Current): 
Set value for enable_freq_scores. Default=True Current=True (Enter to keep Current): 
Set value for freq_avg_alert. Default=5.0 Current=5.0 (Enter to keep Current): 
Set value for freq_word_alert. Default=4.0 Current=4.0 (Enter to keep Current): 
Set value for log_detail. Default=0 Current=3 (Enter to keep Current): 
Set value for cache_browse_limit. Default=100 Current=100 (Enter to keep Current): 
Commit Changes to disk?y
```
I think most of these are self explainatory.  Here is a description of the ones that are not or require some discussion.
 - ip_address - You listen on this ip.  127.0.0.1 is safer than 0.0.0.0.  Otherwise unauthenticated anyone on your network can see the dns cache for your enterprise. IPTABLES is nice.
 - mode - 'rdap' is all that works right now.
 - timezone_offset - If set, this is only used on the "seen_by_you" date.  By default all times are UTC.
 - rdap_error_ttl_days - RDAP errors are cached are cached for a short period of time for performance.  By default it is 7 days.
 - established_days_age - Defines how long before a domain is considered established.  Default is two years.
 - freq_table - If you created custom freq tables you can select them here.  They should be stored in your data directory.
 - enable_freq_scores - If you don't want freq scores, disabling them can enhance your server performance
 - log_detail - Logging will significantly impact performance.  Id suggest leaving it disabled unless you are diagnosing an issue.
 - cache_browse_limit - Limit the max number of records that someone can request with http://ip:port/cache_browse?offset=0&limit=9999999999999


# RDAP vs ISC Support
They each have their own advantages.  We will discuss them here.

- RDAP works today! The ISC support engine is still in the works.
- If you trust your ISP, and commercial and government entities that support DNS infrastructure with your DNS queries but not the ISC then RDAP will let you live in your bubble.
- As of August 2019 RDAP ICANN requires providers support for gTLDs (Top Level: .com, .gov, etc) and not ccTLDs (country code :google.com.au, .ga.us, etc) or eTLDs (Effective TLDs: Where we register domains). You basically can't resolve those domains until ISC support is enabled.  More info on RDAP Support timelines are [HERE](https://www.icann.org/resources/pages/rdap-background-2018-08-31-en)
 - ISC support will support all domains and not be limited by RDAP support. 
 - ISC will provide additional alerting on domains

# ISC API Specification 
API requests look like this
```
{"command":  <command string>,  additional arguments depending upon command}
```
Valid COMMANDS include "CONFIG", "STATUS", and "QUERY"



### **CONFIG command requests configuration options the ISC would like to enforce on the client**
request:
```
{"command": "config"}
```
response:
```
{"min_software_version": "major.minor string",  "min_database_version", "major.minor string", prohitited_tlds:["string1","string2"]}
```
- clients will not query ISC for Domains listed in prohibited_tlds.   Examples may be ['.local', '.arpa']
- If min_software_version is higher than the client software version it causes the software to abort
- if min_database_version is higher than database version it forces the client to download new domains from github.com/markbaggett and add it to its local database



### **STATUS command allows the clients to tell the ISC how they are doing and see if they can continue.  This can be used to tune client efficiency and reduce ISC requests.**
Request:
```
{"command":"status", "client_version":client_version, "database_version":database_version, "cache_efficiency":[cache.hits, cache.miss, cache.expire], "database_efficiency":[database_stats.hits, database_stats.miss]}
```
Response:
```
{"interval": "integer number of minutes ISC wishes to wait until next status update", "deny_client": "client message string"}
```
- interval: The interval tells the client how many minutes to wait before sending another status updates
- deny_client: If set aborts the client with the specified message



### **QUERY command allows clients to query a domain record.**
Requests:
```
{"command": "query", "domain": "example.tld"}
```
RESPONSES (two possible):
##### A success response looks like this:

```
{"seen_by_web": '%Y-%m-%d %H:%M:%S', "expires": '%Y-%m-%d %H:%M:%S', "seen_by_isc":'%Y-%m-%d %H:%M:%S', "alerts":['list','of','alerts]}
```
   - seen_by_web is the domains creation date from the whois record. The time stamp must be in '%Y-%m-%d %H:%M:%S' format
   - expires is the date that the domains registration expires from the whois record. The timestamp must be in '%Y-%m-%d %H:%M:%S' format
   - seen_by_isc is the date that the first domain_stats client requested this domain from the isc. If this was the first request it will have the current date and time and 'ISC-FIRST-CONTACT' will be added to the alerts. The timestamp must be in '%Y-%m-%d %H:%M:%S' format.
   - Alerts must include "ISC-FIRST-CONTACT" if this is the first time anyone has ever queried ISC for this domain
   - Setting any additional alerts limits will cause the client record to not be commited to the database. Instead it is cached for 24 hours on the client.  After 24 hours the client will query the isc again.
##### An error response looks like this:

```
{"seen_by_web":"ERROR", "expires":"ERROR", "seen_by_isc":<integer specifying cache time to live>, "alerts":['alerts','for','that','domain']}
```
   - seen_by_web and expires must be set to "ERROR" when an error has occured.
   - Error time to live tell the client how long to cache and reuse the error for that domain.
   - Integer > 0 - will cache the error for that many hours
   - 0 - will not cache the error at all
   - -1 - will cache it such that it does not expire, but the domain can still drop out of cache based on LRU algorithm
   - -2 - PERMANENT cache entry.  Will never expire.  DANGEROUS. Use with caution.
    
