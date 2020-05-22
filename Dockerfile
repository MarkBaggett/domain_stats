FROM ubuntu:18.04

# Install all the tools
RUN apt-get update && apt-get install python3.8 -y
RUN cd domain_stats && python3.8 setup.py install

CMD [ "domain_stats /host_mounted_dir" ]
