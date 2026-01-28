#!/bin/bash
set -e

# Network Initialization Script
# Usage: ./init_network.sh

NETWORK_NAME="lex_net"

if ! docker network ls | grep -q "$NETWORK_NAME"; then
    echo "Creating network: $NETWORK_NAME"
    docker network create "$NETWORK_NAME"
else
    echo "Network $NETWORK_NAME already exists."
fi
