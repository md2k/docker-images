#! /usr/bin/env python

import os, sys, json, re

# Load Json from STDIN which is returned by command : docker -H tcp://`netstat -nr | grep '^0\.0\.0\.0' | awk '{print $2}'`:4243 inspect `hostname`
data = json.load(sys.stdin)[0]

cont_data = dict()

cont_data['Id'] = data['Id']
cont_data['Name'] = re.sub('[!@#$/]', '', data['Name'] )
cont_data['Hostname'] = data['Config']['Hostname']
cont_data['Ip'] = data['NetworkSettings']['IPAddress']
cont_data['Gw'] = data['NetworkSettings']['Gateway']
cont_data['Image'] = data['Config']['Image']

#print json.dumps(cont_data, ensure_ascii=false)

directory = '/media/' + cont_data['Name']

if not os.path.exists(directory):
    os.makedirs(directory)

with open(directory + '/' + 'container.json', 'w') as outfile:
  json.dump(cont_data, outfile, ensure_ascii=False)

with open(directory + '/' + 'container.json.txt', 'w') as outfileformated:
  json.dump(cont_data, outfileformated, ensure_ascii=False, indent=2, sort_keys=True)

#print json.dumps(cont_data, ensure_ascii=False, indent=2, sort_keys=True)
