#!/bin/bash

set -xe

ID=$(uuidgen)
export ID
echo "ID is $ID"

mkdir -p /tmp/job-"$ID"/{upper,work,merged}

mount -t overlay overlay -o lowerdir=/opt/boost-ci/boost-root,upperdir=/tmp/job-"$ID"/upper,workdir=/tmp/job-"$ID"/work /tmp/job-"$ID"/merged

