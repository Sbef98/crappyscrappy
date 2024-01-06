#!/bin/bash
for i in {1..10}
do
   scrapy runspider agent.py -o output$i.json &
done