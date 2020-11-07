from diskcache import FanoutCache
import datetime

class ExpiringCache:

    def __init__(self, cache_path):
        self.cache = FanoutCache(directory=cache_path, timeout=2, retry=True)

    def set(self, domain, domain_record, seconds_to_live, tag=None): 
        self.cache.set(domain, domain_record, expire = seconds_to_live, tag=tag)

    def get(self, key):
        return self.cache.get(key)

    def cache_dump(self,offset=0, limit=100):
        res = []
        for eachkey in self.cache:
            if offset != 0:
                offset -= 1
                continue
            if limit == 0:
                break
            val, expires = self.cache.get(eachkey, expire_time=True)
            exp_date = datetime.datetime.fromtimestamp(expires)
            res.append( {"domain":eachkey,"cache_value": val.get_json() ,"cache_expires":exp_date} )
            limit -= 1
        return res

    def cache_get(self,key):
        val, expires = self.cache.get(key, expire_time=True)
        if not val:
            return {"text":"That domain is not in the database."}
        exp_date = datetime.datetime.fromtimestamp(expires)
        res = {"domain":key,"cache_value": val.get_json() ,"cache_expires":exp_date} 
        return res

    def cache_info(self):
        hits,miss = self.cache.stats()
        size = self.cache.volume()
        warnings = self.cache.check(fix=True)
        return {"hit":hits, "miss":miss, "size": size, "warnings":warnings}

