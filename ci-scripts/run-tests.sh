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
#
# Note: We can ignore runtime warning "numpy.ndarray size changed" as 
# numpy actually ignores them. https://github.com/numpy/numpy/blob/main/numpy/__init__.py#L320-L323.
# This is a known issue with netCDF4. See https://github.com/unidata/netcdf4-python/issues/1354.
# The issue can be reproduced by:
# python -c "import numpy;import warnings;warnings.filterwarnings('error');import netCDF4"
pytest  -W ignore::DeprecationWarning -W ignore::RuntimeWarning --junit-xml=./test-reports/xunit.xml "$@"

# do we want coverage reporting?
# pytest --cov=ecoimages_port_api --cov-report=html