from diskcache import FanoutCache

class ExpiringCache:

    def __init__(self, cache_path):
        self.cache = FanoutCache(directory=cache_path, timeout=2, retry=True)

    def set(self, domain, domain_record, hours_to_live, tag=None): 
        self.cache.set(domain, domain_record, expire = hours_to_live*3600, tag=tag)

    def get(self, key):
        return self.cache.get(key)

    def cache_dump(self, limit=100,offset=0):
        res = []
        for eachkey in selfcache.iterkeys():
            if offset != 0:
                offset -= 1
                continue
            res.append( self.cache.get(eachkey) )
            if limit == 0:
                break
            limit -= 1
        return res

    def cache_info(self):
        hits,miss = self.cache.stats()
        size = self.cache.volume()
        warnings = self.cache.check(fix=True)
        return {"hit":hits, "miss":miss, "size": size, "warnings":warnings}

