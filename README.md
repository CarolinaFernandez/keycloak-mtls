# Mutual TLS in Keycloak

One-click deployment and configuration for Keycloak to provide two working methods based on mutual TLS (mTLS):
1. Authenticate users from the browser.
1. Authenticate clients without a browser.

Two deployment modes are provided:
1. Direct access to Keycloak (i.e. where clients will directly authenticate against Keycloak).
1. Reverse proxy mode (i.e. where clients will traverse one or more intermediate nodes like e.g. API gateways to authenticate against Keycloak).

This will deploy:
* Keycloak in production mode, loading pregenerated realm configuration.
* Postgres bound to Keycloak as persistence layer.
* Keycloak proxy using NGINX (if the "proxy" mode is selected).
  * *Note*: this is a simple, limited configuration that showcases the reverse proxy passing the escaped certificate header.

## Configuration and deployment

First, generate the certificates.
**Warning**: this will add an entry into your /etc/hosts file to include the FQDN from Keycloak, so it works in production mode.

```bash
./certificates-create.sh
```

All files will be located under the "x509" folder.
**Note**: if wishing to authenticate from the browser, you should import the "./x509/client.p12" file into your certificate store through your selected browser.

Now, decide whether you wish to keep the direct or reverse proxy deployment modes and run the main script to deploy the stack:

```bash
./run.sh -h

Allowed parameters:
    (-d|--deploy) (direct|proxy)
    (-u|--undeploy) (direct|proxy)
    (-t|--test) (direct|proxy)

# Example 1: direct mode
./run.sh -d direct

# Example 2: proxy mode
./run.sh -d proxy
```

Now you can point to the Keycloak instance. A couple of notes on that, depending on the mode:
* Direct mode: you will be able to directly login with the client certificate previously imported from the web browser.
  * Access https://server.department.company.ct:8443/realms/x509/account/ and click on "Sign in".
* Proxy mode: you will not be able to use the certificate from the web browser with this configuration. However, you can see in the first redirection call from Nginx to Keycloak that the escaped certificate (extracted from the certificate store) is transmitted in the appropriate header(s).
  * Access https://server.department.company.ct and notice the redirection (and two certificate prompt requests, the first from Nginx and the second from Keycloak).

## Undeployment

To stop the stack you can execute:

```bash
./run.sh -h

Allowed parameters:
    (-d|--deploy) (direct|proxy)
    (-u|--undeploy) (direct|proxy)
    (-t|--test) (direct|proxy)

# Example 1: direct mode
./run.sh -u direct

# Example 2: proxy mode
./run.sh -u proxy
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

Once Keyloak server has finished loading, select one option or another depending on the mode you run Keycloak:

```bash
./run.sh -h

Allowed parameters:
    (-d|--deploy) (direct|proxy)
    (-u|--undeploy) (direct|proxy)
    (-t|--test) (direct|proxy)

# Example 1: direct mode
./run.sh -t direct

# Example 2: proxy mode
./run.sh -t proxy
```

The code is provided as unit tests in the files "keycloak-token-get-direct.py" and "keycloak-token-get-proxy.py".
You can now use the generated token to retrieve information from protected endpoints.

## Notes

### General resource configuration

The following configuration was used and exported in the "keycloak/export/realm-export.json" file, which is imported to bootstrap all process.
The exported data from the user was added manually, following instructions from https://stackoverflow.com/a/76414472.

**Note**: alternatively, the resources can be automatically created using the "keycloak-resources-create.py" script (which requires both python-keycloak and requests commands).

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

### NGINX reverse proxy

Note that...
