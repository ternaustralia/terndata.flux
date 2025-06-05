#!/bin/sh

# fail on first error
set -e

# this script is meant to run inside container with current working dir
# where source code is mounted.
#apk add py3-psutil
#pip install -e .
pip install -r requirements.txt
pip install -r requirements-test.txt

# some ini options that may be interesting:
#   elasticsearch_host, elasticsearch_port
#   junit_logging=no|log|system-out|system-err|out-err|all
#   jnuti_duration_report=total|call
#   junit_family=legacy|xunit1|xunit2
pytest  -W ignore::DeprecationWarning -W ignore::RuntimeWarning --junit-xml=./test-reports/xunit.xml "$@"

# do we want coverage reporting?
# pytest --cov=ecoimages_port_api --cov-report=html