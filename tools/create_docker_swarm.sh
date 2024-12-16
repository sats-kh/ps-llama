#!/bin/bash
# Create the overlay network of docker swarm
# Check if IP address is passed as a parameter
#if [ -z "$1" ] || [ -z "$2" ]; then
#  echo "Usage: $0 <IP_ADDRESS> <NETWORK_NAME>"
#  exit 1
#fi
if [ -z "$1" ]; then
  echo "Usage: $0 <IP_ADDRESS> <NETWORK_NAME>"
  exit 1
fi

# Initialize Docker Swarm
docker swarm init --advertise-addr "$1"

docker network create \
  --driver overlay \
  --attachable \
  ps-llama-network
#  "$2"