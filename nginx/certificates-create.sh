#!/usr/bin/env bash

name="nginx"

ssh-keygen -t rsa -b 4096 -f ${name}.key -q -P ""
# https://gist.github.com/danreedy/910179
openssl genrsa 4096 > ${name}.key
# Create the self-signed certificate for all (*) addresses
openssl req -new -x509 -nodes -sha1 -days 3650 -key ${name}.key << ANSWERS  > ${name}.crt
CT
State
City
Company
Department
*
nginx@localhost
ANSWERS
