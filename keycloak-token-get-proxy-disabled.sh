#!/usr/bin/env bash

SERVER_FQDN="server.department.company.ct"
X509_DIR="./x509"

curl -ik \
  --location --request POST https://${SERVER_FQDN}:8443/realms/x509/protocol/openid-connect/token \
  --header "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "client_id=keycloak-client" \
  --data-urlencode "grant_type=client_credentials" \
  --cert ${X509_DIR}/client.crt \
  --key ${X509_DIR}/client.key
