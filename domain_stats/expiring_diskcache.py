from diskcache import FanoutCache

class ExpiringCache:

    def __init__(self, cache_path):
        self.cache = FanoutCache(directory=cache_path, timeout=2, retry=True)

    def set(self, domain, domain_record, hours_to_live, tag=None): 
        self.cache.set(domain, domain_record, expire = hours_to_live*3600, tag=tag)

    def get(self, key):
        return self.cache.get(key)

    def cache_dump(self):
        return "Not implemented"

    def cache_load(self):
        return "Not implemented"

    def cache_info(self):
         return "Not Implemented"

    def cache_report(self):
         return "Not Implemented"

    def keys(self):
        return "Not implemented"
