#!/bin/bash

SCRIPT_PATH=$(dirname $(realpath -s $0))

docker run --rm -it \
  -v $SCRIPT_PATH/data:/data \
  tesla_gateway_data /bin/bash
