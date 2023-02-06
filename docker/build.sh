#!/usr/bin/env bash

# Create different versions of the .NET for Apache Spark runtime docker image
# based on the Apach Spark and .NET for Apache Spark version.

set -o errexit # abort on nonzero exit status
set -o nounset # abort on unbound variable
set -o pipefail # dont hide errors within pipes

readonly conda_apache_spark_version=3.3.1
readonly dotnet_apache_spark_version=3.2.1
readonly conda_hadoop_short_version=3
readonly dotnet_hadoop_short_version=3.2
readonly scala_version=2.12
readonly dotnet_core_version=3.1
readonly dotnet_spark_version=2.1.1
readonly cuda_version=11.4.0
readonly ubuntu_version=18.04
proxy=""

build_dotnet=false
build_conda=false
use_gpu=false

main() {

    echo "Executing main"

    if [[ $build_dotnet == false ]] && [[ $build_conda == false ]]
    then
        echo "No build option provided. Use -d/--dotnet to build spark with dotnet or -c/--conda for spark with conda."
    else
        build_java_base
    fi

    if [ $build_conda == true ]
    then
        echo "Building Apache Spark ${conda_apache_spark_version} image"

        build_spark_with_conda_runtime
    elif [ $build_dotnet == true ]
    then
        echo "Building .NET for Apache Spark ${dotnet_spark_version} runtime image with Apache Spark ${dotnet_apache_spark_version}"

        build_dotnet_sdk
        build_dotnet_spark_base_runtime
        build_dotnet_spark_runtime
    fi
     
    trap finish EXIT ERR

    exit 0
}

#######################################
# Runs the docker build command with the related build arguments
# Arguments:
#   The image name (incl. tag)
# Result:
#   A local docker image with the specified name
#######################################
build_image() {
    local image_name="${1}"
    local docker_file_name="${2}"
    local apache_spark_version=""
    local hadoop_short_version=""
    local java_base_image="ubuntu:${ubuntu_version}"

    if [ $# -ge 3 ]
    then
        apache_spark_version="${3}"
        hadoop_short_version="${4}"
    fi

    if [ $use_gpu == true ]
    then
        java_base_image="nvidia/cuda:${cuda_version}-base-ubuntu${ubuntu_version}"
    fi

    local build_args="--build-arg SPARK_VERSION=${apache_spark_version}
        --build-arg HADOOP_VERSION_SHORT=${hadoop_short_version}
        --build-arg JAVA_BASE_IMAGE=${java_base_image}"
    local cmd="docker build ${build_args} -f ${docker_file_name} -t ${image_name} ."

    if [ -n "${proxy}" ]
    then
        build_args+=" --build-arg HTTP_PROXY=${proxy} --build-arg HTTPS_PROXY=${proxy}"
    fi

    echo "Building ${image_name}"

    ${cmd}
}

#######################################
# Use the Dockerfile Dockerfile.java-base to build the image of the first stage
# Result:
#   A java-sdk image tagged with the sdk version.
#######################################
build_java_base() {
    local image_name="java-base:8"
    local docker_file_name="Dockerfile.java-base"

    build_image "${image_name}" "shared/${docker_file_name}"
}

#######################################
# Use the Dockerfile.spark to build the spark image followed by using the Dockerfile.conda
# to build image with conda.
# Result:
#   A spark and conda docker image tagged with the Apache Spark version.
#######################################
build_spark_with_conda_runtime() {
    local spark_image_name="spark:${conda_apache_spark_version}"
    local spark_docker_file_name="Dockerfile.spark"
    local conda_image_name="spark-conda:${conda_apache_spark_version}"
    local conda_docker_file_name="Dockerfile.conda"
    local folder_name="spark_conda"

    build_image "${spark_image_name}" "${folder_name}/${spark_docker_file_name}" "${conda_apache_spark_version}" "${conda_hadoop_short_version}"

    build_image "${conda_image_name}" "${folder_name}/${conda_docker_file_name}" "${conda_apache_spark_version}" "${conda_hadoop_short_version}"
}

#######################################
# Use the Dockerfile.dotnet-sdk to build the image of the second stage
# Result:
#   A dotnet-sdk docker image tagged with the .NET core version
#######################################
build_dotnet_sdk() {
    local image_name="dotnet-sdk:${dotnet_core_version}"
    local docker_file_name="Dockerfile.dotnet-sdk"

    build_image "${image_name}" "spark_dotnet/${docker_file_name}"
}

#######################################
# Use the Dockerfile.dotnet-spark-base to build the image of the third stage
# The image contains the specified .NET for Apache Spark version plus the HelloSpark example
#   for the correct TargetFramework and Microsoft.Spark package version
# Result:
#   A dotnet-spark-base-runtime docker image tagged with the .NET for Apache Spark version
#######################################
build_dotnet_spark_base_runtime() {
    local image_name="dotnet-spark-base-runtime:${dotnet_spark_version}"
    local docker_file_name="Dockerfile.dotnet-spark-base"

    build_image "${image_name}" "spark_dotnet/${docker_file_name}" 
}

#######################################
# Use the Dockerfile.dotnet-spark to build the image of the last stage
# The image contains the specified Apache Spark version
# Result:
#   A dotnet-spark docker image tagged with the .NET for Apache Spark version and the Apache Spark version.
#######################################
build_dotnet_spark_runtime() {
    local image_name="dotnet-spark:${dotnet_spark_version}-${dotnet_apache_spark_version}"
    local docker_file_name="Dockerfile.dotnet-spark"

    build_image "${image_name}" "spark_dotnet/${docker_file_name}" "${dotnet_apache_spark_version}" "${dotnet_hadoop_short_version}"
}

finish()
{
    result=$?
    exit ${result}
}

for arg in "$@"
do
    case "$arg" in
        --dotnet|-d)
            build_dotnet=true
            echo "dotnet choosen"
            ;;
        --conda|-c)
            build_conda=true
            echo "conda choosen"
            ;;
        --gpu|-g)
            use_gpu=true
            echo "gpu enabled"
            ;;
    esac
done

main
