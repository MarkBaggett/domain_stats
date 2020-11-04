import gunicorn
import multiprocessing
import os

os.environ["SERVER_SOFTWARE"] = "domain_stats-0.0.8"
bind = "0.0.0.0:10000"
workers = multiprocessing.cpu_count() * 2 + 1
threads = multiprocessing.cpu_count() * 3
gunicorn.SERVER_SOFTWARE = 'domain_stats-0.0.8'
