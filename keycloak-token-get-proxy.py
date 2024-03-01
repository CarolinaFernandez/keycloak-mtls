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

    def test_success_mtls_clientcerts_pythonlib(self):
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
        # NB: encode certificate properly to e.g. change \n by %0A, space by %20, etc
        client_cert_data_enc = urllib.parse.quote(self.client_cert_data)
        # Hack: add to connection's headers
        keycloak_openid.connection.add_param_headers(
            "X-Client-Cert", client_cert_data_enc
        )
        data = keycloak_openid.connection.raw_post(
            URL_TOKEN.format(**params_path), data=payload
        )
        self.assertIsNotNone(data.json())
        access_token = data.json().get("access_token")
        self.assertIsNotNone(access_token)
        self.assertIsNone(data.json().get("refresh_token"))

    def test_success_mtls_clientcerts(self):
        #
        # mTLS with grant_type=client_credentials (X-Client-Cert header as explicitly defined in Keycloak's Docker env var)
        # - KC_SPI_X509CERT_LOOKUP_NGINX_SSL_CLIENT_CERT
        #
        """
        Expected result: success
        Test target: ask for token with (allowed) client X509 certificate in header
        """

        payload = self.payload
        headers_auth = copy.deepcopy(self.headers)
        # NB: encode certificate properly to e.g. change \n by %0A, space by %20, etc
        client_cert_data_enc = urllib.parse.quote(self.client_cert_data)
        headers_auth.update({"X-Client-Cert": client_cert_data_enc})
        data = requests.post(
            url=self.api_token_url,
            headers=headers_auth,
            # NB: establish mTLS connection with credentials from internal servers (not client's -- that will be passed from headers)
            cert=(self.server_cert_path, self.server_key_path),
            data=payload,
            verify=self.ssl_verify,
        )
        self.assertIsNotNone(data.json())
        access_token = data.json().get("access_token")
        self.assertIsNotNone(access_token)
        self.assertIsNone(data.json().get("refresh_token"))


if __name__ == "__main__":
    unittest.main()
