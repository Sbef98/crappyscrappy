#!/bin/bash
for i in {1..50}
do
   scrapy runspider agent.py -L INFO &
done