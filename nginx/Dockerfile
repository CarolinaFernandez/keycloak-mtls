FROM nginx:1.24.0

RUN apt-get update -y && \
    apt-get install -y vim openssh-client curl
RUN touch ~/.vimrc

WORKDIR /
RUN mkdir -p /etc/nginx/auth/

WORKDIR /etc/nginx/auth
# Certificates
COPY ./certificates-create.sh .
RUN ./certificates-create.sh

WORKDIR /etc/nginx/conf.d/
# Specific cfg
COPY ./keycloak.nginx.conf .

ENTRYPOINT ["nginx", "-g", "daemon off;"]
