#!/bin/bash

# let's make a list of urls
list=("https://www.unimore.it/" "https://www.unibo.it/it" "https://www.unipr.it/" "https://www.unipd.it/" "https://www.unimi.it/it" "https://www.unina.it/" "https://www.unipg.it/" "https://www.uniparthenope.it/")

while true; do
    #let's iterate over the list
    for i in "${list[@]}"
    do
       #let's bash launchspiders_serial.sh  passing the url as argument
       bash launchspiders_serial.sh $i &
    done
    # wait for 5 minutes
    sleep 300
done