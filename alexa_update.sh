#!/bin/bash
rm -f top-1m.csv.zip
/usr/bin/wget http://s3.amazonaws.com/alexa-static/top-1m.csv.zip
/usr/bin/unzip -o top-1m.csv.zip
