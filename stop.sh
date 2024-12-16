#!/bin/bash

# 중지할 컨테이너 검색
containers=$(docker ps --filter "name=param" --filter "name=worker" -q)

if [ -z "$containers" ]; then
  echo "No matching containers found."
else
  echo "killing containers: $containers"
  docker kill $containers
fi