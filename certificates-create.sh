#!/usr/bin/env bash

#
# Generates certificates for Keycloaks
# [WARNING] Adds a new entry in /etc/hosts with the FQDN for the local Keycloak
#
# Sources:
# - https://github.com/keycloak/keycloak/issues/15481 (steps for Niko Koebler's video)
# - https://gist.github.com/sethvargo/81227d2316207b7bd110df328d83fad8
#

ROOT_DIR=${PWD}
cd x509

# Variables
CA_NAME="ca"
CLIENT_NAME="client"
SERVER_NAME="server"
CERT_DN_C="CT"
CERT_DN_ST="State"
CERT_DN_L="City"
CERT_DN_O="Company"
CERT_DN_OU="Department"
CERT_DN_BASE=$(echo "${CERT_DN_OU}.${CERT_DN_O}.${CERT_DN_C}" | tr '[:upper:]' '[:lower:]')
CERT_DN_EXT_CA="${CA_NAME}"
CERT_DN_CN_CA="${CERT_DN_EXT_CA}.${CERT_DN_BASE}"
CERT_DN_MAIL_CA="${CERT_DN_EXT_CA}@${CERT_DN_BASE}"
CERT_DN_EXT_SERVER="${SERVER_NAME}"
CERT_DN_CN_SERVER="${CERT_DN_EXT_SERVER}.${CERT_DN_BASE}"
CERT_DN_MAIL_SERVER="${CERT_DN_EXT_SERVER}@${CERT_DN_BASE}"
CERT_DN_EXT_CLIENT="${CLIENT_NAME}.${SERVER_NAME}"
CERT_DN_CN_CLIENT="${CERT_DN_EXT_CLIENT}.${CERT_DN_BASE}"
CERT_DN_MAIL_CLIENT="${CERT_DN_EXT_CLIENT}@${CERT_DN_BASE}"
KEYSTORE_PASSWORD="changeit"

rm -f *.csr *.p12 *.pem *.ext *.truststore
rm -f ${SERVER_NAME}.crt ${SERVER_NAME}.key ${CLIENT_NAME}.crt ${CLIENT_NAME}.key 

# Root CA
cat > "${CA_NAME}.v3.ext" << EOF
[req]
default_bits = 4096
encrypt_key  = no # Change to encrypt the private key using des3 or similar
default_md   = sha256
prompt       = no
utf8         = yes
# Specify the DN here so we aren't prompted (along with prompt = no above).
distinguished_name = req_distinguished_name
# Extensions for SAN IP and SAN DNS
req_extensions = v3_req
# Be sure to update the subject to match your organization.
[req_distinguished_name]
C  = ${CERT_DN_C}
ST = ${CERT_DN_ST}
L  = ${CERT_DN_L}
O  = ${CERT_DN_O}
OU = ${CERT_DN_OU}
CN = ${CERT_DN_CN_CA}
emailAddress = ${CERT_DN_MAIL_CA}
# Allow client and server auth. You may want to only allow server auth.
# Link to SAN names.
[v3_req]
authorityKeyIdentifier = keyid,issuer
basicConstraints       = critical, CA:TRUE
nsCertType             = client, email
subjectKeyIdentifier   = hash
keyUsage               = critical, keyCertSign, digitalSignature, keyEncipherment
extendedKeyUsage       = clientAuth, serverAuth
EOF
if [[ ! -f ${CA_NAME}.crt ]]; then
  openssl req -x509 -sha256 -days 3650 -newkey rsa:4096 -keyout ${CA_NAME}.key -nodes -out ${CA_NAME}.crt -subj "/C=${CERT_DN_C}/ST=${CERT_DN_ST}/L=${CERT_DN_L}/O=${CERT_DN_O}/OU=${CERT_DN_OU}/CN=${CERT_DN_CN_CA}/emailAddress=${CERT_DN_MAIL_CA}" -extensions v3_req -config ${CA_NAME}.v3.ext
fi

# Keycloak server certificate
openssl req -new -newkey rsa:4096 -keyout ${SERVER_NAME}.key -out ${SERVER_NAME}.csr -nodes -subj "/C=${CERT_DN_C}/ST=${CERT_DN_ST}/L=${CERT_DN_L}/O=${CERT_DN_O}/OU=${CERT_DN_OU}/CN=${CERT_DN_CN_SERVER}/emailAddress=${CERT_DN_MAIL_SERVER}"
cat > "${SERVER_NAME}.v3.ext" << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
EOF
openssl x509 -req -CA ${CA_NAME}.crt -CAkey ${CA_NAME}.key -in ${SERVER_NAME}.csr -out ${SERVER_NAME}.crt -days 365 -CAcreateserial -extfile ${SERVER_NAME}.v3.ext

# Client certificate
openssl req -new -newkey rsa:4096 -nodes -keyout ${CLIENT_NAME}.key -out ${CLIENT_NAME}.csr -subj "/C=${CERT_DN_C}/ST=${CERT_DN_ST}/L=${CERT_DN_L}/O=${CERT_DN_O}/OU=${CERT_DN_OU}/CN=${CERT_DN_CN_CLIENT}/emailAddress=${CERT_DN_MAIL_CLIENT}"
cat > "${CLIENT_NAME}.v3.ext" << EOF
authorityKeyIdentifier=keyid,issuer
nsCertType = client, email
subjectKeyIdentifier = hash
basicConstraints=CA:FALSE
keyUsage = critical, digitalSignature, nonRepudiation, keyEncipherment
extendedKeyUsage = clientAuth, emailProtection
EOF
openssl x509 -req -CA ${CA_NAME}.crt -CAkey ${CA_NAME}.key -in ${CLIENT_NAME}.csr -out ${CLIENT_NAME}.crt -days 365 -CAcreateserial -extfile ${CLIENT_NAME}.v3.ext

# Export certificates and private keys to a p12 file to import them more easily
cat ${CLIENT_NAME}.crt ${CLIENT_NAME}.key > ${CLIENT_NAME}.pem
openssl pkcs12 -password pass:"" -export -in ${CLIENT_NAME}.pem -inkey ${CLIENT_NAME}.key -out ${CLIENT_NAME}.p12 -name "${CLIENT_NAME}"
cat ${CA_NAME}.crt ${CA_NAME}.key > ${CA_NAME}.pem

# Verify certificates (no "-x509_strict" added since these seem to miss extensions from its generation)
openssl verify -verbose -x509_strict -CAfile ${CA_NAME}.crt -CApath . ${SERVER_NAME}.crt
openssl verify -verbose -x509_strict -CAfile ${CA_NAME}.crt -CApath . ${CLIENT_NAME}.crt

# Keystore and trustore required by Keycloak
[[ $(dpkg -l | grep ca-certificates | wc -l) -eq 0 ]] && sudo apt install -y ca-certificates
# Create PKCS#12 servidor and client
openssl pkcs12 -export -name server-cert -in "$CA_NAME.crt" -inkey "$CA_NAME.key" -out "${SERVER_NAME}".keystore -passout pass:"$KEYSTORE_PASSWORD"
openssl pkcs12 -export -name "$CLIENT_NAME" -in "$CLIENT_NAME.crt" -inkey "$CLIENT_NAME.key" -out "$CLIENT_NAME.p12" -password pass:""
# Import client and CA certificates in truststore
keytool -import -alias client-cert -file "$CLIENT_NAME.crt" -keystore "${SERVER_NAME}".truststore -storepass "$KEYSTORE_PASSWORD" -noprompt
keytool -import -alias ca-cert -file "$CA_NAME.crt" -keystore "${SERVER_NAME}".truststore -storepass "$KEYSTORE_PASSWORD" -noprompt

# Generate entry at /etc/hosts with the server FQDN, as required by Keycloak in production mode
if [[ $(cat /etc/hosts | grep "${CERT_DN_CN_SERVER}" | wc -l) -eq 0 ]]; then
cat <<EOF | sudo tee -a /etc/hosts

# Local Keycloak (production mode)
127.0.0.1       ${CERT_DN_CN_SERVER}
EOF
fi

cd ${ROOT_DIR}
