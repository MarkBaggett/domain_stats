Here are some quick multiprocessing installation instructions.


If you want to do this in a python virtual environment create one and activate it.

```
student@573:~$ python -m venv ~/venvs/onetimerun/
student@573:~$ source ~/venvs/onetimerun/bin/activate
(onetimerun) student@573:~$
```

Next install the program

```
(onetimerun) student@573:~$ git clone --single-branch --branch multiprocessed http://github.com/markbaggett/domain_stats
Cloning into 'domain_stats'...
warning: redirecting to https://github.com/markbaggett/domain_stats/
remote: Enumerating objects: 47, done.
remote: Counting objects: 100% (47/47), done.
remote: Compressing objects: 100% (32/32), done.
remote: Total 463 (delta 23), reused 37 (delta 15), pack-reused 416
Receiving objects: 100% (463/463), 12.55 MiB | 15.56 MiB/s, done.
Resolving deltas: 100% (247/247), done.

(test_multiprocess) student@573:~/test$ cd domain_stats/
(onetimerun) student@573:~/domain_stats$ pip install .
Processing /home/student/domain_stats

Output Truncaded.  Dont worry about any errors such as..

  error: invalid command 'bdist_wheel'
  Failed building wheel for pyyaml

as long as you see this Success at the end

Successfully installed Jinja2-2.11.2 MarkupSafe-1.1.1 Werkzeug-1.0.1 certifi-2020.6.20 chardet-3.0.4 click-7.1.2 diskcache-5.0.3 domain-stats-0.0.1 flask-1.1.2 gunicorn-20.0.4 idna-2.10 itsdangerous-1.1.0 munge-1.1.0 publicsuffixlist-0.7.5 python-dateutil-2.8.1 pyyaml-5.3.1 rdap-1.1.0 requests-2.24.0 six-1.15.0 urllib3-1.25.11
```

Next run domain-stats-settings and give it the path to store your data. Answer the questions if you don't know a better answer then just press enter. Dont forget to say "YES" to commit your settings to the disk.  If you want to change these just rerun settings.

```
(onetimerun) student@573:~/domain_stats$ mkdir /home/student/ds1
(onetimerun) student@573:~/domain_stats$ domain-stats-settings /home/student/ds1
Set value for ip_address. Default=0.0.0.0 Current=0.0.0.0 (Enter to keep Current): 
Set value for local_port. Default=5730 Current=5730 (Enter to keep Current): 
Set value for workers. Default=3 Current=3 (Enter to keep Current): 
Set value for threads_per_worker. Default=3 Current=3 (Enter to keep Current): 
Set value for timezone_offset. Default=0 Current=0 (Enter to keep Current): 
Set value for established_days_age. Default=730 Current=730 (Enter to keep Current): 
Set value for enable_freq_scores. Default=True Current=True (Enter to keep Current): 
Set value for mode. Default=rdap Current=rdap (Enter to keep Current): 
Set value for freq_avg_alert. Default=5.0 Current=5.0 (Enter to keep Current): 
Set value for freq_word_alert. Default=4.0 Current=4.0 (Enter to keep Current): 
Set value for log_detail. Default=0 Current=0 (Enter to keep Current): 
Commit Changes to disk?y
```

Last run domain stats.  Again you must pass the path to the data location.

```
(onetimerun) student@573:~/domain_stats$ domain-stats /home/student/ds1
Existing config found in directory. Using it.
[2020-11-05 15:34:45 -0800] [26382] [INFO] Starting gunicorn 20.0.4
[2020-11-05 15:34:45 -0800] [26382] [INFO] Listening at: http://0.0.0.0:5730 (26382)
[2020-11-05 15:34:45 -0800] [26382] [INFO] Using worker: threads
[2020-11-05 15:34:45 -0800] [26385] [INFO] Booting worker with pid: 26385
[2020-11-05 15:34:45 -0800] [26386] [INFO] Booting worker with pid: 26386
[2020-11-05 15:34:45 -0800] [26387] [INFO] Booting worker with pid: 26387
Using config /home/student/ds1/domain_stats.yaml
Using config /home/student/ds1/domain_stats.yaml
Using config /home/student/ds1/domain_stats.yaml
```