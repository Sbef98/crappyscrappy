#!/bin/bash
#while true; do
# let's read the url from the arguments
url=$1
while true
do
   scrapy runspider agent.py -a start_urls=$url, -L INFO
done