import pathlib
import os
import sys
import shutil
import multiprocessing
import pickle
import datetime
from diskcache import FanoutCache
from domain_stats.config import Config


def create_gunicorn_config(tgt_folder,ip,port,cpu,thread):
    gunicorn_config = f"""
import gunicorn
import multiprocessing
import os

os.environ["SERVER_SOFTWARE"] = "domain_stats-0.0.8"
bind = "{ip}:{port}"
workers = {cpu}
threads = {thread}
gunicorn.SERVER_SOFTWARE = 'domain_stats-0.0.8'
    """
    config_file = pathlib.Path(tgt_folder / "gunicorn_config.py")
    config_file.write_text(gunicorn_config)

def import_data_feed(tgt_folder, url):
    print("not implemented yet")

def import_old_cache(tgt_folder):
    typed_cache = input("Where is the old_cache file (not folder) located? ")
    old_cache = pathlib.Path(typed_cache)
    if not old_cache.is_file:
        print("That file doesn't exist.")
        sys.exit(1)
    NewCache = FanoutCache(directory=f"{tgt_folder}/database", timeout=2, retry=True)
    with open(old_cache, "rb") as fhandle:
        other = pickle.load(fhandle)
        for key,val in other:
            expiration, _, data = val
            seconds_to_live = (expiration - datetime.datetime.utcnow()).total_seconds()
            NewCache.set(key, data , expire = seconds_to_live, tag="import")
    NewCache.close()

def launch_from_config(tgt_folder):
    os.chdir(tgt_folder)
    launch_cmd = f"""{sys.executable} -m gunicorn.app.wsgiapp 'domain_stats.server:config_app("{tgt_folder}")' -c {tgt_folder}/gunicorn_config.py"""
    os.system(launch_cmd)

def setup_folder(tgt_folder):
    source_folder = pathlib.Path(os.path.realpath(__file__)).parent
    shutil.copy(source_folder / "domain_stats.yaml", tgt_folder)
 
    listener_ip = input("What port to listen on? (Enter for 0.0.0.0): ") or "0.0.0.0"
    listener_port = input("What port to listen on? (Enter for 5730): ") or "5730"
    rec_workers = multiprocessing.cpu_count() * 2 + 1
    num_workers = input(f"How many cpu cores can I use? (Enter for {rec_workers}): ") or rec_workers
    rec_threads = multiprocessing.cpu_count() * 3
    num_threads = input(f"How many threads per cores can I have? (Enter for {rec_threads}): ") or rec_threads
    create_gunicorn_config(tgt_folder, listener_ip, listener_port, num_workers, num_threads)

    # import_data_feed(tgt_folder, "http://gist.github.com/markbaggett/domain_stats_init_file")
    # if input("Import old domain_stats data? ").lower().startswith('y'):
    #     import_old_cache(tgt_folder)

if len(sys.argv) != 2:
    typed_folder = input("Where do you want to store your domain_stats data and binaries? ")
else:
    typed_folder = sys.argv[1]

tgt_folder = pathlib.Path(typed_folder)
if not tgt_folder.is_dir():
    print("That directory does not exist. Please create it and/or try again.")
    sys.exit(1)
if (tgt_folder / "domain_stats.yaml").is_file():
    print("Existing config found in directory. Using it.")
    launch_from_config(tgt_folder)
elif input("Would you like to setup this directory now?").lower().startswith("y"):
    setup_folder(tgt_folder)

