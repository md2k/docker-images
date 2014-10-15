#!/bin/bash

## Pars Docker call to HOST and pars JSON Return, write technical information about container into Shared folder:
## Inside shared folder will be created subfolder with container name and 2 files *.json and *.json.txt
docker -H tcp://`netstat -nr | grep '^0\.0\.0\.0' | awk '{print $2}'`:4243 inspect `hostname` | /root/.scripts/cont_data.py

## Done
/bin/bash

