#!/usr/bin/env bash

set -o errexit   # abort on nonzero exitstatus
set -o nounset   # abort on unbound variable
set -o pipefail  # don't hide errors within pipes

if [ $START_THRIFT_SERVER == true ]; then
    echo "Starting thrift server"
    sleep 60
    "${SPARK_HOME}"/sbin/start-thriftserver.sh
fi