#!/usr/bin/env bash

set -o errexit   # abort on nonzero exitstatus
set -o nounset   # abort on unbound variable
set -o pipefail  # don't hide errors within pipes

if [ -z "${SPARK_DEBUG_DISABLED}" ] && [ -z "${SPARK_DRIVER_DISABLED}" ]; then
    socat tcp-l:5567,fork,reuseaddr tcp:127.0.0.1:5050 &
    cd /dotnet/HelloSpark/bin/Debug/netcoreapp"${DOTNET_CORE_VERSION}"
    "${SPARK_HOME}"/bin/spark-submit --packages "${SPARK_SUBMIT_PACKAGES}" --class org.apache.spark.deploy.dotnet.DotnetRunner --jars "/dotnet/HelloSpark/bin/Debug/netcoreapp${DOTNET_CORE_VERSION}/*.jar" --master local microsoft-spark-3-2_2.12-"${DOTNET_SPARK_VERSION}".jar debug 5050
fi