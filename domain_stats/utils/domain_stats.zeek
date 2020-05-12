#Zeek/Bro integration script
#Thanks to SANS Instructor Don Williams for writing this https://www.sans.org/instructors/donald-williams 
#Don based this off of Dustin Lee's Security Onion integration Script here: https://github.com/dlee35/domain_stats2_so/blob/master/domainstats.bro

module DomainStats;

export {
    # This redef is purely for testing pcap and not designed for active networks
    # Set to F or comment before adding to production
    # redef exit_only_after_terminate = T;

    global domainstats_url = "http://localhost:8000/"; # add desired DS url here
    global ignore_domains = set(".rdap.net"); # add domains to exclude here
    global queried_domains: table[string] of count &default=0 &create_expire=1days; # keep state of domains to prevent duplicate queries
    global domain_suffixes = /MATCH_NOTHING/; # idea borrowed from: https://github.com/theflakes/bro-large_uploads
    redef enum Log::ID += { LOG };
    
    type Info: record {
        ts: time             &log;
        uid: string          &log;
        query: string        &log;
        seen_by_web: string  &log;
        seen_by_isc: string   &log;
        seen_by_you: string  &log;
        category: string         &log;
        other: string        &log &optional;
    };
}    

event zeek_init() &priority=5
{
    domain_suffixes = set_to_regex(ignore_domains, "(~~)$");
    Log::create_stream(DomainStats::LOG, [$columns=Info, $path="domainstats"]);
}

event dns_request(c: connection, msg: dns_msg, query: string, qtype: count, qclass: count)
{
        if (c$id$resp_p == 53/udp || c$id$resp_p == 53/tcp) {
	local dsurl = domainstats_url;
        local domain = fmt("%s",c$dns$query);
        if (domain in queried_domains || domain_suffixes in domain) {
            return;
        }
	else {
            local request: ActiveHTTP::Request = [
                $url = dsurl + domain
            ];
            queried_domains[domain] = 1;
            when (local res = ActiveHTTP::request(request)) {
                if (|res| > 0) {
                    if (res?$body && |split_string(res$body,/,/)| > 2) {
                        local resbody = fmt("%s", res$body);
                        local seen_by_web_parse = gsub(split_string(resbody,/,/)[0],/\{/,"");
                        local seen_by_web_date = strip(split_string1(gsub(split_string1(seen_by_web_parse,/:/)[1],/\"/,""),/\./)[0]); 
                        local seen_by_isc_parse = split_string(resbody,/,/)[1];
                        local seen_by_isc_date = strip(split_string1(gsub(split_string1(seen_by_isc_parse,/:/)[1],/\"/,""),/\./)[0]); 
                        local seen_by_you_parse = split_string(resbody,/,/)[2];
                        local seen_by_you_date = strip(split_string1(gsub(split_string1(seen_by_you_parse,/:/)[1],/\"/,""),/\./)[0]); 
                        local cat_parse = split_string(resbody,/,/)[3];
                        local cat_num = strip(gsub(split_string(cat_parse,/:/)[1],/\"/,"")); 
                        local other_parse = gsub(split_string(resbody,/,/)[4],/\}|\{/,"");
                        local other_info = strip(gsub(split_string(other_parse,/:/)[1],/\"/,"")); 
                        local rec: DomainStats::Info = [$ts=c$start_time, $uid=c$uid, $query=domain, $seen_by_web=seen_by_web_date, $seen_by_isc=seen_by_isc_date, $seen_by_you=seen_by_you_date, $category=cat_num, $other=other_info]; 
                        Log::write(DomainStats::LOG, rec);
                    }
                }
            }
        }
    }
}