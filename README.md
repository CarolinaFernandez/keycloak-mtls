# Mutual TLS in Keycloak

One-click deployment and configuration for Keycloak to provide two working methods based on mutual TLS (mTLS):
1. Authenticate users from the browser.
1. Authenticate clients without a browser.
1. Provide (by default) a reverse proxy mode.

This will deploy:
* Keycloak in production mode, loading pregenerated realm configuration.
* Postgres bound to Keycloak as persistence layer.

## Configuration and deployment

First, generate the certificates.
**Warning**: this will add an entry into your /etc/hosts file to include the FQDN from Keycloak, so it works in production mode.

```bash
./certificates-create.sh
```

All files will be located under `x509`.

Now, decide whether you wish to keep the reverse proxy mode enabled (default) or not.
To disable it, go to "docker-compose.yaml" and comment the lines with `PROXY_ADDRESS_FORWARDING` and `KC_SPI_X509CERT_LOOKUP*`:

```bash
## mTLS setup to provide client's certificate through header
#- PROXY_ADDRESS_FORWARDING=true
#- KC_SPI_X509CERT_LOOKUP_PROVIDER=nginx
##- KC_SPI_X509CERT_LOOKUP_NGINX_SSL_CLIENT_CERT=ssl-client-cert
#- KC_SPI_X509CERT_LOOKUP_NGINX_SSL_CLIENT_CERT=X-Client-Cert
```

Finally, run the following to deploy the stack:

```bash
docker-compose -f docker-compose.yaml up -d
```

## Undeployment

To stop the stack you can execute:

```bash
docker-compose -f docker-compose.yaml down
```

And to remove the Docker volume for Postgres, you may enact the following command (names might vary slightly on your environment):

```bash
docker volume rm keycloak-mtls_keycloak-db-data
```

## Evaluation

### Authentication as an interacting user from a browser

Load the generated `x509/client.p12` file into your browser. Click "enter" when prompted for a password (i.e. no password).

Then open your browser, ideally in private mode to run these tests, since the certificate wil be loaded during the session.
Point it to the default "home URL" for e.g. the "account" client. In this local example: https://server.department.company.ct:8443/realms/x509/account/

You will be prompted for the matching certificate (the client certificate loaded beforehand). Accept and you will be directed to an information review page, after which you will be logged in.

### Authentication as a non-interacting user (client) from the terminal

Depending on the mode you run Keycloak by (set through env vars in docker-compose.yaml), run some of the following to obtain the token:

```bash
# Option A: proxy is enabled (default)
## NOTE: one test may fail if `python-keycloak` library is not available via PIP (tested with version="3.7.0").
python3 keycloak-token-get-proxy-enabled.py

# Option B: proxy is not enabled
./keycloak-token-get-proxy-disabled.sh
## NOTE: one test may fail if `python-keycloak` library is not available via PIP (tested with version="3.7.0").
python3 keycloak-token-get-proxy-disabled.py 
```

You can now use the generated token to retrieve information from protected endpoints.

## Notes

### Configuration

The following configuration was used and exported in the `keycloak/export/realm-export.json` file, which is imported to bootstrap all process.
The exported data from the user was added manually, following instructions from https://stackoverflow.com/a/76414472.

**Note**: alternatively, the resources can be automatically created using the `keycloak-resources-create.py` script (which requires both python-keycloak and requests commands).

**Realm** (required by X509 client and X509 browser access)
Create a new realm with the following information:
- General settings
  - Name = x509
- Login
  - Require SSL = All requests

**Authentication** (required by X509 browser access)
Create a new authentication flow with the following information:
- General settings
  - Name = x509 browser
- Steps
  - Cookie [Alternative]
  - X509/Validate Username Form [Alternative]
    - Alias = x509-config
    - User Identity Source = Subject's e-mail
    - A regular expression to extract user identity = `(.*?)(?:,|$)`
    - User mapping method = Username or Email
  - x509 browser forms [Alternative]
    - Username Password Form [Required]
Then bind it as the default "browser flow"

**User** (required by X509 browser access)
Create a new user with the following information:
- Username = keycloak-user
- Email = client.server@department.company.ct

**Client** (required by X509 client)
Create a new client with the following information:
- Settings
  - Client ID = keycloak-client
  - Client authentication = On
  - Authentication flow = { Standard flow, Direct access grants, Service accounts role, OAuth 2.0 Device AUthorization Grant }
- Credentials
  - Client Authenticator = X509 Certificate
  - Allow regex pattern comparison = On
  - Subject DN = `(.*?)CN=(.*)client(.*).server.department.company.ct(.*?)(?:$)`

Note that the first working method ("Authenticate users from the browser") requires the creation of the authentication flow and the user, whereas the second working method ("Authenticate clients without a browser") requires creating the client.
