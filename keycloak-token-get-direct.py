#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    from keycloak import KeycloakOpenID
    from keycloak.urls_patterns import URL_TOKEN
except:
    pass

import base64
import copy
import requests
import unittest
import urllib

# Disable warnings due to the lack of validation of the TLS certificate
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TestTokenExtraction(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestTokenExtraction, self).__init__(*args, **kwargs)
        self.proto = "https"
        self.port = 8443
        self.client_id = "keycloak-client"
        self.realm_name = "x509"
        self.api_base_url = f"{self.proto}://server.department.company.ct:{self.port}"
        self.api_token_url = f"{self.api_base_url}/realms/{self.realm_name}/protocol/openid-connect/token"
        self.ssl_verify = False
        # Client certificates
        self.client_cert_path = "./x509/client.crt"
        self.client_cert_data = open(self.client_cert_path, "r").read()
        self.client_key_path = "./x509/client.key"
        # Server certificates
        self.server_cert_path = "./x509/server.crt"
        self.server_cert_data = open(self.server_cert_path, "r").read()
        self.server_key_path = "./x509/server.key"
        # Request base content
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        # Base payload
        self.payload = {
            "client_id": self.client_id,
            "grant_type": "client_credentials",
        }

    def test_success_mtls_pythonlib(self):
        # Object to be used only for mTLS connections (since its
        # connection will be configured in the next command to
        # pass both client certificate and key)
        keycloak_openid = KeycloakOpenID(
            server_url=self.api_base_url,
            realm_name=self.realm_name,
            client_id=self.client_id,
            verify=False,
        )
        # Hack: setup mTLS connection's cert and key
        keycloak_openid.connection._s.cert = (
            self.client_cert_path,
            self.client_key_path,
        )
        # Payload obtained from src/keycloak/keycloak_openid.py
        params_path = {"realm-name": self.realm_name}
        payload = copy.deepcopy(self.payload)
        data = keycloak_openid.connection.raw_post(
            URL_TOKEN.format(**params_path), data=payload
        )
        self.assertIsNotNone(data.json())
        access_token = data.json().get("access_token")
        self.assertIsNotNone(access_token)
        self.assertIsNone(data.json().get("refresh_token"))

    def test_success_mtls_requests(self):
        payload = copy.deepcopy(self.payload)
        data = requests.post(
            url=self.api_token_url,
            headers=self.headers,
            cert=(self.client_cert_path, self.client_key_path),
            data=payload,
            verify=False,
        )
        self.assertIsNotNone(data.json())
        access_token = data.json().get("access_token")
        self.assertIsNotNone(access_token)
        self.assertIsNone(data.json().get("refresh_token"))


if __name__ == "__main__":
    unittest.main()
