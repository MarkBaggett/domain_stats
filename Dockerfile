FROM ubuntu:18.04

# Install all the tools
RUN apt-get update && apt-get install python3.8 python3-pip -y
RUN python3 -m pip install setuptools 
RUN mkdir /domain_stats
RUN mkdir /host_mounted_dir
COPY . /domain_stats
RUN cd domain_stats && python3.8 setup.py install

CMD [ "domain_stats /host_mounted_dir" ]
