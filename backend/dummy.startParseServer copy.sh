#!/bin/bash
parse-dashboard --dev --appId  --masterKey  --serverURL http://localhost:1337/parse --appName  &
while :
do
    parse-server ./config.json
done