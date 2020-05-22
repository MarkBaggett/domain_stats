FROM ubuntu:18.04

# Install all the tools
RUN apt-get update && apt-get install python3.8 python3-pip -y
RUN python3 -m pip install setuptools rdap pyyaml domain_stats 
RUN mkdir /host_mounted_dir

CMD [ "domain_stats /host_mounted_dir" ]
