#!/usr/bin/env python3

import requests

# Disable warnings due to the lack of validation of the TLS certificate
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

client_cert_path = "./x509/client.crt"
client_key_path = "./x509/client.key"
client_id = "keycloak-client"
keycloak_url = "https://server.department.company.ct:8443"
realm_name = "x509"
token_url = f"{keycloak_url}/realms/{realm_name}/protocol/openid-connect/token"

headers = {"Content-Type": "application/x-www-form-urlencoded"}
payload = {"client_id": client_id, "grant_type": "client_credentials"}

#
# Option A: hack of Keycloak's code
#
try:
    from keycloak import KeycloakOpenID
    from keycloak.urls_patterns import URL_TOKEN

    # Object to be used only for mTLS connections (since its
    # connection will be configured in the next command to
    # pass both client certificate and key)
    keycloak_openid = KeycloakOpenID(
        server_url=keycloak_url,
        realm_name=realm_name,
        client_id=client_id,
        verify=False,
    )
    keycloak_openid.connection._s.cert = (client_cert_path, client_key_path)
    # Payload obtained from src/keycloak/keycloak_openid.py
    params_path = {"realm-name": realm_name}
    # payload = {
    #    "client_id": keycloak_openid.client_id,
    #    "grant_type": "client_credentials",
    # }
    data_raw = keycloak_openid.connection.raw_post(
        URL_TOKEN.format(**params_path), data=payload
    )
    token = data_raw.json()
    print(f"Token: {token}")
except Exception as e:
    print(e)

#
# Option B: requests
#

try:
    data = requests.post(
        url=token_url,
        headers=headers,
        cert=(client_cert_path, client_key_path),
        data=payload,
        verify=False,
    )
    print(f"Token: {data.json()}")
except Exception as e:
    print(e)
