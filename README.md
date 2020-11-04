

You need a directory for the data.

```
student@573:~$ mkdir /home/student/datadir
```

I'm working in a python virtual environment, this is not required but sure makes testing easier..

```
student@573:~$ python -m venv ~/test_multiprocess
student@573:~$ source ~/test_multiprocess/bin/activate
```

Lets also create a test dir for our source code. Then in clone the new branch and install.

```
(test_multiprocess) student@573:~$ mkdir test
(test_multiprocess) student@573:~$ cd test
(test_multiprocess) student@573:~/test$ git clone --single-branch --branch multiprocessed http://github.com/markbaggett/domain_stats
Cloning into 'domain_stats'...
warning: redirecting to https://github.com/markbaggett/domain_stats/
remote: Enumerating objects: 47, done.
remote: Counting objects: 100% (47/47), done.
remote: Compressing objects: 100% (32/32), done.
remote: Total 463 (delta 23), reused 37 (delta 15), pack-reused 416
Receiving objects: 100% (463/463), 12.55 MiB | 15.56 MiB/s, done.
Resolving deltas: 100% (247/247), done.
(test_multiprocess) student@573:~/test$ cd domain_stats/
(test_multiprocess) student@573:~/test/domain_stats$ pip install .
Processing /home/student/test/domain_stats
Collecting diskcache (from domain-stats==0.0.1)
  Using cached https://files.pythonhosted.org/packages/fc/d6/7b8fa70e57f7b54e01da2664a6ee21afc315c29906bd46e9905fb246c5ac/diskcache-5.0.3-py3-none-any.whl

this is truncated.. it is ok if you see a few "failed building wheel" messages

  Failed building wheel for pyyaml

as long as you see this..

Successfully installed Jinja2-2.11.2 MarkupSafe-1.1.1 Werkzeug-1.0.1 certifi-2020.6.20 chardet-3.0.4 click-7.1.2 diskcache-5.0.3 domain-stats-0.0.1 flask-1.1.2 gunicorn-20.0.4 idna-2.10 itsdangerous-1.1.0 munge-1.1.0 publicsuffixlist-0.7.5 python-dateutil-2.8.1 pyyaml-5.3.1 rdap-1.1.0 requests-2.24.0 six-1.15.0 urllib3-1.25.11
```

Now run the new ds_launcher command and pass the datadir.  First time it will create the require config files.  Number of CPUs and threads are calculated based on hardware you are running on.

```
(test_multiprocess) student@573:~/test/domain_stats$ python -m domain_stats.ds_launcher /home/student/datadir
Would you like to setup this directory now?/home/student/datadir
(test_multiprocess) student@573:~/test/domain_stats$ python -m domain_stats.ds_launcher /home/student/datadir
Would you like to setup this directory now?y
What port to listen on? (Enter for 0.0.0.0): 
What port to listen on? (Enter for 5730): 
How many cpu cores can I use? (Enter for 3): 
How many threads per cores can I have? (Enter for 3): 
```

Second time it will launch a multiprocessed version.

```
(test_multiprocess) student@573:~/test/domain_stats$ python -m domain_stats.ds_launcher /home/student/datadir
Existing config found in directory. Using it.
[2020-11-04 08:10:23 -0800] [18946] [INFO] Starting gunicorn 20.0.4
[2020-11-04 08:10:23 -0800] [18946] [INFO] Listening at: http://0.0.0.0:5730 (18946)
[2020-11-04 08:10:23 -0800] [18946] [INFO] Using worker: threads
[2020-11-04 08:10:23 -0800] [18949] [INFO] Booting worker with pid: 18949
[2020-11-04 08:10:23 -0800] [18950] [INFO] Booting worker with pid: 18950
[2020-11-04 08:10:23 -0800] [18951] [INFO] Booting worker with pid: 18951
Using config /home/student/datadir/domain_stats.yaml
Using config /home/student/datadir/domain_stats.yaml
Using config /home/student/datadir/domain_stats.yaml
^C[2020-11-04 08:10:28 -0800] [18946] [INFO] Handling signal: int
[2020-11-04 08:10:29 -0800] [18946] [INFO] Shutting down: Master
```