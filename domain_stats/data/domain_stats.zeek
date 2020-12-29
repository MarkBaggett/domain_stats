#Zeek/Bro integration script
#Thanks to SANS Instructor Don Williams for writing this https://www.sans.org/instructors/donald-williams 
#Don based this off of Dustin Lee's Security Onion integration Script here: https://github.com/dlee35/domain_stats2_so/blob/master/domainstats.bro

module DomainStats;

#Uncomment the next line if running in a VM or other system where packets normally have bad checksums.
#redef ignore_checksums = T;

export {
    # This redef is purely for testing pcap and not designed for active networks
    # Set to F or comment before adding to production
    # redef exit_only_after_terminate = T;

    global domainstats_url = "http://localhost:5730/"; # add desired DS url here
    global ignore_domains = set(".rdap.net"); # add domains to exclude here
    global queried_domains: table[string] of count &default=0 &create_expire=1days; # keep state of domains to prevent duplicate queries
    global domain_suffixes = /MATCH_NOTHING/; # idea borrowed from: https://github.com/theflakes/bro-large_uploads
    redef enum Log::ID += { LOG };
    
    type Info: record {
        ts: time             &log;
        uid: string          &log;
        query: string        &log;
        alert: string        &log;
        category: string     &log;
        freq_avg_prob: string &log;
        freq_word_prob: string &log;
        seen_by_web: string  &log;
        seen_by_isc: string   &log;
        seen_by_you: string  &log;
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
                        local resbody = fmt("%s", data);
                        local alerts_entry = split_string(resbody,/,\"category/)[0];
                        local alerts = strip(gsub(split_string(alerts_entry,/:/)[1],/\"/,""));
                        local cat_entry = split_string(resbody, /\",\"freq/)[0];
                        local cat_string = split_string( cat_entry, /category\":\"/ )[1];
                        local freq_entry = split_string(resbody, /\],\"seen_by_isc/)[0];
                        freq_entry = split_string(freq_entry, /freq\":\[/)[1];
                        local freq_avg_prob = split_string( freq_entry, /,/)[0];
                        local freq_word_prob = split_string( freq_entry, /,/)[1];
                        local seen_by_isc_entry = split_string(resbody,/\",\"seen_by_web/)[0];
                        local seen_by_isc_date = split_string(seen_by_isc_entry,/seen_by_isc\":\"/)[1];
                        local seen_by_web_entry = split_string(resbody,/\",\"seen_by_you/)[0];
                        local seen_by_web_date = split_string(seen_by_web_entry,/by_web\":\"/)[1];
                        local seen_by_you_entry = split_string(resbody,/seen_by_you\":\"/)[1];
                        local seen_by_you_date = split_string(seen_by_you_entry,/\"/)[0];
                        local rec: DomainStats::Info = [$ts=c$start_time, $uid=c$uid, $query=domain, $seen_by_web=seen_by_web_date, $seen_by_isc=seen_by_isc_date, $seen_by_you=seen_by_you_date, $category=cat_string, $alerts=alerts,$freq_avg_prob=freq_avg_prob, $freq_word_prob=freq_word_prob];
                        Log::write(DomainStats::LOG, rec);
                    }
                }
            }
        }
    }
}