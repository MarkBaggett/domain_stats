FROM ubuntu:18.04

#docker build -tag domain_stats_image http://github.com/markbaggett/domain_stats.git
#Configure the container choosing your hosts path and port
#docker run --name domain_stats_container -v /<a path on your host>:/host_mounted_dir -p 8000:<port on your host> domain_stats_image

 
# Install all the tools
RUN apt-get update && apt-get install python3.8 python3-pip -y
RUN python3 -m pip install setuptools rdap pyyaml flask diskcache gunicorn requests python-dateutil publicsuffixlist
RUN mkdir /app
COPY . /app
RUN cd app && pip3 install . 
RUN mkdir /host_mounted_dir

CMD ["domain-stats" ,"/host_mounted_dir"]
