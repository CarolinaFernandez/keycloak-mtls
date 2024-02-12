#!/usr/bin/env python3

ca_bundle = "./x509/so_ca.crt"
client_cert_path = "./client.crt"
client_key_path = "./client.key"
client_id = "keycloak-client"
keycloak_url = "server.department.company.ct"
realm_name = "x509"
token_url = f"{keycloak_url}/realms/{realm_name}/protocol/openid-connect/token"

headers = {"Content-Type": "application/x-www-form-urlencoded"}

payload = {"client_id": client_id, "grant_type": "client_credentials"}

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
