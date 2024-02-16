#!/usr/bin/env python3

from keycloak import KeycloakAdmin
from keycloak import KeycloakOpenID
from keycloak import KeycloakOpenIDConnection
from keycloak.urls_patterns import URL_TOKEN
import os

# Disable warnings due to the lack of validation of the TLS certificate
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


keycloak_url = "https://server.department.company.ct:8443"
username = "admin"
password = "admin"
realm_name_default = "master"
realm_name_new = "x509-test"
client_id = "so-client-x509-flow_clients-credentials"
account_url = f"{keycloak_url}/realms/{realm_name_new}/account/"
# Certificates and token retrieval
client_cert_path = "./x509/client.crt"
client_key_path = "./x509/client.key"
token_url = f"{keycloak_url}/realms/{realm_name_new}/protocol/openid-connect/token"

# Set keycloak admin connection to master realm
keycloak_connection_admin = KeycloakOpenIDConnection(
    server_url=keycloak_url,
    username=username,
    password=password,
    realm_name=realm_name_default,
    verify=False,
)
keycloak_admin = KeycloakAdmin(connection=keycloak_connection_admin)

# Cleanup: delete any previous instance of the realm
try:
    keycloak_admin.delete_realm(realm_name_new)
except Exception:
    pass

# Realm creation
try:
    keycloak_admin.create_realm(payload={"realm": realm_name_new}, skip_exists=False)
except:
    keycloak_admin.delete_realm(realm_name_new)
    keycloak_admin.create_realm(payload={"realm": realm_name_new}, skip_exists=False)

# Change realm
keycloak_admin.change_current_realm(realm_name_new)
realm_config = {
    "enabled": True,
    "sslRequired": "all",
}
keycloak_admin.update_realm(realm_name=realm_name_new, payload=realm_config)

# Client configuration
client_config = {
    "clientId": client_id,
    "baseUrl": account_url,
    "enabled": True,
    "authorizationServicesEnabled": False,
    "directAccessGrantsEnabled": True,
    "serviceAccountsEnabled": True,
    "clientAuthenticatorType": "client-x509",
    "attributes": {
        "oauth2.device.authorization.grant.enabled": True,
        "x509.subjectdn": "(.*?)CN=(.*)client(.*).server.department.company.ct(.*?)(?:$)",
        "x509.allow.regex.pattern.comparison": "true",
    },
}

# Create client
client_gen_id = keycloak_admin.create_client(payload=client_config, skip_exists=False)
print(f"Client created with ID={client_gen_id}")

#
# X509 browser-based authentication
#

import requests


# Used later
def get_updated_headers_with_admin_token():
    # keycloak_admin._connection.get_token()
    # admin_token = keycloak_admin._connection.token
    admin_token = requests.post(
        f"{keycloak_url}/realms/master/protocol/openid-connect/token",
        data={
            "client_id": "admin-cli",
            "grant_type": "password",
            "username": "admin",
            "password": "admin",
        },
        verify=False,
    )
    admin_token = admin_token.json()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {admin_token.get('access_token')}",
    }
    return headers


## NOTE: this is not working (403: unknown error)
## Set keycloak admin connection to specific realm
# keycloak_connection_admin = KeycloakOpenIDConnection(
#    server_url=keycloak_url,
#    client_id=client_id,
#    token=token,
#    realm_name=realm_name_new,
#    user_realm_name=realm_name_new,
#    verify=False
# )
# keycloak_admin = KeycloakAdmin(connection=keycloak_connection_admin2)

flow_name = "x509browser"

# Create authentication flow
# auth_flow_payload = {
#    "id": flow_name,
#    "alias": flow_name,
#    "description": "X509-based browser authentication",
#    "providerId": "basic-flow",
#    "topLevel": True,
#    "builtIn": False,
#    "authenticationExecutions": [
#        {
#            "authenticatorConfig": "",
#            "authenticator": "",
#            "authenticatorFlow": "",
#            "requirement": "",
#            "priority": 1,
#            "authenticatorFlow": True,
#            "flowAlias": "",
#            "userSetupAllowed": True
#        }
#    ]
# }
# keycloak_admin.create_authentication_flow(auth_flow_payload, skip_exists=True)

# https://www.keycloak.org/docs-api/23.0.6/rest-api/index.html#AuthenticationExecutionInfoRepresentation
# Create authentication flow execution
# NOTE: this is not working (400: unknown error)
# flow_cookie_payload = {
#    "id": f"{flow_name}.cookie",
#    "requirement": "ALTERNATIVE",
#    "displayName": "",
#    "alias": f"{flow_name}.cookie",
#    "description": "",
#    "requirementChoices": ["REQUIRED", "ALTERNATIVE", "DISABLED"],
#    "configurable": False,
#    "authenticationFlow": False,
#    "providerId": "auth-cookie",
#    "authenticationConfig": "",
#    "flowId": flow_name,
#    "level": 1,
# }
# keycloak_admin.create_authentication_flow_execution(flow_cookie_payload, "Cookie")

# Copy browser authentication flow
auth_flow_payload = {
    "newName": flow_name,
}
keycloak_admin.copy_authentication_flow(auth_flow_payload, "browser")

# Remove non-needed fields
auth_flow_contents = keycloak_admin.get_authentication_flow_executions(flow_name)
auth_flow_exec_remove = [
    "Kerberos",
    "Identity Provider Redirector",
    f"{flow_name} Browser - Conditional OTP",
]
auth_flow_exec_remove_contents = list(
    filter(lambda x: x.get("displayName") in auth_flow_exec_remove, auth_flow_contents)
)
for auth_flow_entry in auth_flow_exec_remove_contents:
    keycloak_admin.delete_authentication_flow_execution(auth_flow_entry.get("id"))

# https://www.keycloak.org/docs-api/23.0.6/rest-api/index.html#AuthenticationFlowRepresentation
# Create X509 Validate Client User and Name Form
# auth_flow_x509_payload = {
#    "id": "",
#    "alias": "",
#    "description": "",
#    "providerId": "auth-x509-client-username-form",
#    "topLevel": False,
#    "builtIn": True,
#    "authenticationExecutions": [
#        {
#            "authenticatorConfig": "",
#            "authenticator": "",
#            "authenticatorFlow": "",
#            "requirement": "",
#            "priority": 1,
#            "authenticatorFlow": True,
#            "flowAlias": "",
#            "userSetupAllowed": False
#        }
#    ]
#
# }

# payload={
#    "alias": "test-subflow",
#    "provider": "basic-flow",
#    "type": "something",
#    "description": "something",
# }
# keycloak_admin.create_authentication_flow_subflow(payload, flow_name, skip_exists=True)

# NOTE: creating the object but not honouring the correct requirement or order/index
## Level: 0 (top-level), index: 1 (2nd position)
keycloak_admin.create_authentication_flow_execution(
    {
        "provider": "auth-x509-client-username-form",
        "level": "0",
        "index": "1",
        "requirement": "ALTERNATIVE",
    },
    flow_name,
)

# Get new flow exec setup and increase its priority
auth_flow_contents = keycloak_admin.get_authentication_flow_executions(flow_name)
auth_flow_exec_filter_contents = list(
    filter(
        lambda x: x.get("displayName") == "X509/Validate Username Form",
        auth_flow_contents,
    )
)

auth_flow_exec_x509_id = auth_flow_exec_filter_contents[0].get("id")

# Mark as alternative, then place in the correct position (reorder to index=1, after "Cookie")
headers = get_updated_headers_with_admin_token()
auth_flow_exec_payload = auth_flow_exec_filter_contents[0]
auth_flow_exec_payload["requirement"] = "ALTERNATIVE"
auth_flow_exec_payload["level"] = 0
auth_flow_exec_payload["index"] = 1
requests.put(
    url=f"{keycloak_url}/admin/realms/{realm_name_new}/authentication/flows/{flow_name}/executions",
    headers=headers,
    json=auth_flow_exec_payload,
    verify=False,
)

headers = get_updated_headers_with_admin_token()
requests.post(
    url=f"{keycloak_url}/admin/realms/{realm_name_new}/authentication/executions/{auth_flow_exec_x509_id}/raise-priority",
    headers=headers,
    verify=False,
)

# Configure execution step
headers = get_updated_headers_with_admin_token()
data = requests.post(
    url=f"{keycloak_url}/admin/realms/{realm_name_new}/authentication/executions/{auth_flow_exec_x509_id}/config",
    headers=headers,
    json={
        "alias": "x509-config",
        "config": {
            "x509-cert-auth.mapping-source-selection": "Subject's e-mail",
            "x509-cert-auth.canonical-dn-enabled": "false",
            "x509-cert-auth.serialnumber-hex-enabled": "false",
            "x509-cert-auth.regular-expression": "(.*?)(?:$)",
            "x509-cert-auth.mapper-selection": "Username or Email",
            "x509-cert-auth.timestamp-validation-enabled": "true",
            "x509-cert-auth.crldp-checking-enabled": "false",
            "x509-cert-auth.ocsp-fail-open": "false",
            "x509-cert-auth.ocsp-responder-uri": "",
            "x509-cert-auth.ocsp-responder-certificate": "",
            "x509-cert-auth.keyusage": "",
            "x509-cert-auth.extendedkeyusage": "",
            "x509-cert-auth.certificate-policy": "",
            "x509-cert-auth.certificate-policy-mode": "All",
        },
    },
    verify=False,
)

# Bind authentication flow as default for browser
headers = get_updated_headers_with_admin_token()
realm_data = keycloak_admin.get_realm(realm_name_new)
realm_payload = realm_data
# Translate text to boolean to be able to send as JSON
realm_payload["enabled"] = True
realm_payload["loginWithEmailAllowed"] = True
realm_payload["defaultRole"]["composite"] = True
realm_payload["browserFlow"] = flow_name
data = requests.put(
    url=f"{keycloak_url}/admin/realms/{realm_name_new}",
    headers=headers,
    json=realm_payload,
    verify=False,
)

# Create user and add correct email
keycloak_admin.create_user(
    {
        "username": "keycloak-user",
        "email": "client.server@department.company.ct",
        "enabled": True,
    },
    exist_ok=True,
)

#
# Test client's token creation
#

# Object to be used only for mTLS connections (since its
# connection will be configured in the next command to
# pass both client certificate and key)
keycloak_openid = KeycloakOpenID(
    server_url=keycloak_url,
    realm_name=realm_name_new,
    client_id=client_id,
    verify=False,
)
# Direct hack on the connection object to support mTLS connections
keycloak_openid.connection._s.cert = (client_cert_path, client_key_path)
# Payload obtained from src/keycloak/keycloak_openid.py
params_path = {"realm-name": realm_name_new}
payload = {
    "client_id": keycloak_openid.client_id,
    "grant_type": "client_credentials",
}

try:
    data_raw = keycloak_openid.connection.raw_post(
        URL_TOKEN.format(**params_path), data=payload
    )
    token = data_raw.json()
    print(f"Token for client: {token}")
except Exception as e:
    print(e)
