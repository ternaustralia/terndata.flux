#!/bin/sh

# fail on first error
set -e


# this script is meant to run inside container with current working dir
# where source code is mounted.
apt update
apt install git make 
apt install -y python3-sphinx

pip install '.[docs]'

pip install -r requirements-docs.txt

cd docs
make "$@"