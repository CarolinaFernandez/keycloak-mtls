#!/usr/bin/env bash

DIRECT_KEYCLOAK=0
PROXIED_KEYCLOAK=0

function parse_args_keycloak() {
    if [[ "$1" == "direct" ]]; then
        DIRECT_KEYCLOAK=1
    elif [[ "$1" == "proxy" ]]; then
        PROXIED_KEYCLOAK=1
    else
        return 1
    fi
}

function print_help() {
    echo "Allowed parameters:"
    echo "    (-d|--deploy) (direct|proxy)"
    echo "    (-u|--undeploy) (direct|proxy)"
    echo "    (-t|--test) (direct|proxy)"
}

function deploy_keycloak() {
    parse_args_keycloak "$1"
    parse_result="$?"
    if [[ ${parse_result} == 1 ]]; then
        echo "Deployment mode not chosen. Exiting..."
	print_help
	exit ${parse_result}
    elif [[ ${DIRECT_KEYCLOAK} == 1 ]]; then
        echo "Deploying Keycloak in direct mode..."
        docker-compose -f docker-compose-direct.yaml up -d
    elif [[ ${PROXIED_KEYCLOAK} == 1 ]]; then
        echo "Deploying Keycloak in proxy mode..."
        docker-compose -f docker-compose-proxy.yaml up -d
    fi
}

function undeploy_keycloak() {
    parse_args_keycloak "$1"
    parse_result="$?"
    if [[ ${parse_result} == 1 ]]; then
        echo "Deployment mode not chosen. Exiting..."
        print_help
        exit ${parse_result}
    elif [[ ${DIRECT_KEYCLOAK} == 1 ]]; then
        echo "Undeploying Keycloak in direct mode..."
        docker-compose -f docker-compose-direct.yaml down
    elif [[ ${PROXIED_KEYCLOAK} == 1 ]]; then
        echo "Undeploying Keycloak in proxy mode..."
        docker-compose -f docker-compose-proxy.yaml down
    fi
}

function test_keycloak() {
    parse_args_keycloak "$1"
    parse_result="$?"
    if [[ ${parse_result} == 1 ]]; then
        echo "Deployment mode not chosen. Exiting..."
        print_help
        exit ${parse_result}
    elif [[ ${DIRECT_KEYCLOAK} == 1 ]]; then
        echo "Testing Keycloak in direct mode..."
        python3 keycloak-token-get-direct.py
    elif [[ ${PROXIED_KEYCLOAK} == 1 ]]; then
        echo "Testing Keycloak in proxy mode..."
        python3 keycloak-token-get-proxy.py
    fi
}

function parse_args() {
    while [[ "$#" -gt 0 ]]; do
        case $1 in
            -h|--help) print_help; exit 0 ;; 
            -d|--deploy) deploy_keycloak "$2"; shift ; exit 0 ;; 
            -u|--undeploy) undeploy_keycloak "$2"; shift ; exit 0 ;;
            -t|--test) test_keycloak "$2"; shift ; exit 0 ;; 
	    *) print_help; exit 1 ;;
        esac
        shift
    done
}

parse_args "$@"
deploy_keycloak
