#!/bin/bash

i=0
for tuple in "$@"; do
    IFS=':' read -r version name <<< "$tuple"

    echo "Processing tuple: VERSION=$version, NAME=$name, IMAGE=$version:$name:$i"
    BITTENSOR_VERSION=$version NODE_TYPE=$name sudo docker build -t "$version:$name:$i" .
    i=$((i+1))
done
