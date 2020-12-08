import pathlib
import os
import sys
import shutil
import yaml
import multiprocessing


def create_gunicorn_config(tgt_folder,ip,port,cpu,thread):
    gunicorn_config = f"""
import gunicorn
import multiprocessing
import os

os.environ["SERVER_SOFTWARE"] = "domain_stats"
bind = "{ip}:{port}"
workers = {cpu}
threads = {thread}
gunicorn.SERVER_SOFTWARE = 'domain_stats'
    """
    config_file = pathlib.Path(tgt_folder / "gunicorn_config.py")
    config_file.write_text(gunicorn_config)

def update_setting(config, key, default):
    current_val = config.get(key,default)
    new_val = input(f"Set value for {key}. Default={default} Current={current_val} (Enter to keep Current): ") or current_val
    config[key]= default.__class__(new_val)    

def setup_directory(tgt_folder):
    config = {}
    file_path = tgt_folder / "domain_stats.yaml"
    if file_path.is_file():
        print("Existing config found in directory. Using it.") 
        config = yaml.safe_load(file_path.read_text())
        if not config:
            print("domain_stats.yaml config exists but is blank or could not be loaded. Erase the file to begin again.")
            sys.exit(1)
    source_folder = pathlib.Path(os.path.realpath(__file__)).parent
    if not (tgt_folder / "freqtable2018.freq").is_file():
        shutil.copy(source_folder / "data/freqtable2018.freq", tgt_folder)
    #create gunicorn config
    update_setting(config, "ip_address", "127.0.0.1")
    update_setting(config, "local_port", "5730")
    rec_workers = multiprocessing.cpu_count() * 2 + 1
    update_setting(config, "workers", rec_workers)
    rec_threads = multiprocessing.cpu_count() * 3
    update_setting(config, "threads_per_worker", rec_threads)
    #Configure Additional settings in domain_stats.yaml
    update_setting(config,'timezone_offset', 0)
    update_setting(config,'established_days_age', 730)
    update_setting(config,'mode',"rdap")
    update_setting(config,"rdap_error_ttl_days",7)
    update_setting(config,'freq_table', 'freqtable2018.freq')
    update_setting(config,'enable_freq_scores', True)
    update_setting(config,'freq_avg_alert',5.0)
    update_setting(config,'freq_word_alert',4.0)
    update_setting(config,'log_detail',0)
    update_setting(config,'count_rdap_errors',False)
    update_setting(config,'cache_browse_limit',100)
    if input("Commit Changes to disk?").lower().startswith("y"):
        create_gunicorn_config(tgt_folder, config['ip_address'], config['local_port'],config['workers'], config['threads_per_worker'])
        with file_path.open('w') as fp:
            yaml.dump(config, fp, default_flow_style=False)
        print("Configuration Written.")
        print("If this is a new installation you might consider preloading the top1m.import file with domain-stats-utils.")
    else:
        print("The configuration selected was not saved.")

def main():
    if len(sys.argv) != 2:
        typed_folder = input("Where do you want to store your domain_stats data and binaries? ")
    else:
        typed_folder = sys.argv[1]

    tgt_folder = pathlib.Path(typed_folder)
    if not tgt_folder.is_dir():
        print("That directory does not exist. Please create it and/or try again.")
        sys.exit(1)

    setup_directory(tgt_folder)

if __name__ == "__main__":
    main()


    