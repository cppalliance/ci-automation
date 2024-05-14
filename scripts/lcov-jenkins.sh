#!/bin/bash

set -ex

if [ -z "${REPONAME}" ]; then
        echo "Please set the env variable REPONAME"
        exit 1
fi

if [ -z "${ORGANIZATION}" ]; then
        echo "Please set the env variable ORGANIZATION"
        exit 1
fi

# export USER=$(whoami)
# echo "USER is ${USER}"

# these packages are already installed on containers.
sudo apt-get update
sudo apt-get install -y python3-pip sudo git curl jq

# codecov.sh installs perl packages also
# sudo apt-get install -y libcapture-tiny-perl libdatetime-perl libdatetime-format-dateparse-perl
sudo apt-get install -y libdatetime-format-dateparse-perl

export B2_TOOLSET="gcc-11"
export LCOV_VERSION="v2.1"
export LCOV_OPTIONS="--ignore-errors mismatch"

export REPO_NAME=${ORGANIZATION}/${REPONAME}
export PATH=~/.local/bin:/usr/local/bin:$PATH
export BOOST_CI_CODECOV_IO_UPLOAD="skip"

run_coverage_reports () {

    git clone https://github.com/boostorg/boost-ci.git boost-ci-cloned --depth 1
    cp -prf boost-ci-cloned/ci .
    rm -rf boost-ci-cloned

    export SELF=`basename $REPO_NAME`
    export BOOST_CI_SRC_FOLDER=$(pwd)

    . ./ci/common_install.sh

    # Formatted such as "cppalliance/buffers cppalliance/http-proto"
    for EXTRA_LIB in ${EXTRA_BOOST_LIBRARIES}; do
        EXTRA_LIB_REPO=`basename $EXTRA_LIB`
        if [ ! -d "$BOOST_ROOT/libs/${EXTRA_LIB_REPO}" ]; then
            pushd $BOOST_ROOT/libs
            git clone https://github.com/${EXTRA_LIB} -b $BOOST_BRANCH --depth 1
            popd
        fi
    done

    cd $BOOST_ROOT/libs/$SELF
    ci/travis/codecov.sh

    pip3 install --user gcovr
    cd $BOOST_CI_SRC_FOLDER

    export PATH=/tmp/lcov/bin:$PATH
    command -v lcov
    lcov --version

    lcov --ignore-errors unused --remove coverage.info -o coverage_filtered.info '*/test/*' '*/extra/*'

    # Now the tracefile is coverage_filtered.info
    genhtml --flat -o genhtml coverage_filtered.info

    #########################
    #
    # gcovr
    #
    #########################

    GCOVRFILTER=".*/$REPONAME/.*"
    mkdir gcovr
    mkdir -p json
    cd ../boost-root
    gcovr -p --html-details --exclude '.*/test/.*' --exclude '.*/extra/.*' --filter "$GCOVRFILTER" --html --output $BOOST_CI_SRC_FOLDER/gcovr/index.html
    ls -al $BOOST_CI_SRC_FOLDER/gcovr

    gcovr -p --json-summary --exclude '.*/test/.*' --exclude '.*/extra/.*' --filter "$GCOVRFILTER" --output $BOOST_CI_SRC_FOLDER/json/summary.json
    # jq . $BOOST_CI_SRC_FOLDER/json/summary.json

    gcovr -p --json --exclude '.*/test/.*' --exclude '.*/extra/.*' --filter "$GCOVRFILTER" --output $BOOST_CI_SRC_FOLDER/json/coverage.json
    # jq . $BOOST_CI_SRC_FOLDER/json/coverage.json
}

run_coverage_reports

#########################################################################
#
# RUN EVERYTHING AGAIN the same way on the target branch, usually develop
#
#########################################################################

# preparation:

# change this to an env variable from pull request builder:
TARGET_BRANCH=$ghprbTargetBranch

cd $BOOST_CI_SRC_FOLDER
BOOST_CI_SRC_FOLDER_ORIG=$BOOST_CI_SRC_FOLDER
rm -rf ../boost-root
cd ..
git clone -b $TARGET_BRANCH https://github.com/$ORGANIZATION/$SELF
cd $SELF
# The "new" BOOST_CI_SRC_FOLDER:
export BOOST_CI_SRC_FOLDER=$(pwd)
export BOOST_CI_SRC_FOLDER_TARGET=$(pwd)

# done with prep, now everything is the same as before

run_coverage_reports

# Done with building target branch. Return everything back.

BOOST_CI_SRC_FOLDER=$BOOST_CI_SRC_FOLDER_ORIG
cd $BOOST_CI_SRC_FOLDER

#########################################
#
# gcov-compare.py. download and run it.
#
#########################################

mkdir -p ~/.local/bin
GITHUB_REPO_URL="https://github.com/cppalliance/ci-automation/raw/master"
DIR="scripts"
FILENAME="gcov-compare.py"
URL="${GITHUB_REPO_URL}/$DIR/$FILENAME"
FILE=~/.local/bin/$FILENAME 
if [ ! -f "$FILE" ]; then
    curl -s -S --retry 10 -L -o $FILE $URL && chmod 755 $FILE
fi

$FILE $BOOST_CI_SRC_FOLDER_ORIG/json/summary.json $BOOST_CI_SRC_FOLDER_TARGET/json/summary.json > gcovr/coverage_diff.txt
