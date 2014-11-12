#!/bin/bash

## Pars Docker call to HOST and pars JSON Return, write technical information about container into Shared folder:
## Inside shared folder will be created subfolder with container name and 2 files *.json and *.json.txt
docker -H tcp://`netstat -nr | grep '^0\.0\.0\.0' | awk '{print $2}'`:4243 inspect `hostname` | /root/.scripts/cont_data.py

## run puppet on each container start/up/initital run
apt-get update
puppet apply -d -v --parser future --config_version=/etc/puppet/scripts/get-config-version --modulepath=/etc/puppet/environments/docker/modules/ /etc/puppet/environments/docker/manifests
#rm -rf /var/lib/apt/lists/*

## Done
/bin/bash
