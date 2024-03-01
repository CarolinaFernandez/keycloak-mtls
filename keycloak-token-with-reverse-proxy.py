#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Disable warnings due to the lack of validation of the TLS certificate
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Client
client_cert_path = "./x509/client.crt"
client_cert_data = open(client_cert_path, "r").read()
client_key_path = "./x509/client.key"
client_key_data = open(client_key_path, "r").read()
client_id = "keycloak-client"
# Server
server_cert_path = "./x509/server.crt"
server_key_path = "./x509/server.key"
# keycloak_url = "https://127.0.0.1:8443"
keycloak_url = "https://server.department.company.ct:8443"
realm_name = "x509"
token_url = f"{keycloak_url}/realms/{realm_name}/protocol/openid-connect/token"

headers = {"Content-Type": "application/x-www-form-urlencoded"}
# headers = {"Content-Type": "application/json"}
payload = {"client_id": client_id, "grant_type": "client_credentials"}

try:
    # TODO - Test sending client cert in header only
    client_cert_data_ns = client_cert_data.replace("\n", "")
    ## Internal expected header
    headers.update({"X-Client-Cert": client_cert_data_ns})
    ## Sample expected header
    headers.update({"SSL_CLIENT_CERT": client_cert_data_ns})
    # https://www.keycloak.org/server/reverseproxy
    # https://stackoverflow.com/a/47187279/2186237
    # https://github.com/keycloak/keycloak/issues/10553
    # https://keycloak.discourse.group/t/x509-authentication-with-keycloak-on-kubernetes-via-ingress/16035/33
    # https://stackoverflow.com/a/71314650
    # https://github.com/keycloak/keycloak/blob/main/services/src/main/java/org/keycloak/services/x509/X509ClientCertificateLookup.java
    headers.update(
        {
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Host": "server.department.company.ct",
            "X-Forwarded-For": "server.department.company.ct",
        }
    )
    data = requests.post(
        url=token_url,
        headers=headers,
        # TODO - Test establishing mTLS connection with keycloak or AAC specific credentials (not the client one)
        # cert=(client_cert_path, client_key_path),
        # FIXME - Keycloak is retrieving certificates based on the connection itself
        # (the API server with CN=api.so.assets.i2cat.net) and not on the headers
        # (the client1 client with CN=client1.client.so.assets.i2cat.net) -- where the authZ takes place
        # against DN=(.*).client.so.assets.i2cat [thus, the API server does not match]
        cert=(server_cert_path, server_key_path),
        data=payload,
        # json=payload,
        verify=False,
    )
    print(f"Token: {data.json()}")
except Exception as e:
    print(e)
