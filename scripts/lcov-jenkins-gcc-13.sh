#!/bin/bash

# See docs at https://github.com/cppalliance/ci-automation/blob/master/scripts/docs/README.md

set -ex

echo "Starting lcov-jenkins-gcc-13.sh"

timestamp=$(date +"%Y-%m-%d-%H-%M-%S")

env

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

# expecting a venv to already exist in /opt/venv.
export pythonvirtenvpath=/opt/venv
if [ -f ${pythonvirtenvpath}/bin/activate ]; then
    # shellcheck source=/dev/null
    source ${pythonvirtenvpath}/bin/activate
fi

# pip install --upgrade gcovr==8.4 || true

gcovr --version

export B2_TOOLSET="gcc-13"
export LCOV_VERSION="v2.3"
export LCOV_OPTIONS="--ignore-errors mismatch"

export REPO_NAME=${ORGANIZATION}/${REPONAME}
export PATH=~/.local/bin:/usr/local/bin:$PATH
export BOOST_CI_CODECOV_IO_UPLOAD="skip"

# lcov will be present later
export PATH=/tmp/lcov/bin:$PATH
# command -v lcov
# lcov --version

collect_coverage () {

    git clone https://github.com/boostorg/boost-ci.git boost-ci-cloned --depth 1
    cp -prf boost-ci-cloned/ci .
    rm -rf boost-ci-cloned

    SELF=$(basename "$REPO_NAME")
    export SELF
    BOOST_CI_SRC_FOLDER=$(pwd)
    export BOOST_CI_SRC_FOLDER

    echo "In collect_coverage. Running common_install.sh"
    # shellcheck source=/dev/null
    . ./ci/common_install.sh

    # Formatted such as "cppalliance/buffers cppalliance/http-proto"
    for EXTRA_LIB in ${EXTRA_BOOST_LIBRARIES}; do
        EXTRA_LIB_REPO=$(basename "$EXTRA_LIB")
        if [ ! -d "$BOOST_ROOT/libs/${EXTRA_LIB_REPO}" ]; then
            pushd "$BOOST_ROOT/libs"
            git clone "https://github.com/${EXTRA_LIB}" -b "$BOOST_BRANCH" --depth 1
            popd
        fi
    done

    echo "In collect_coverage. Running codecov.sh"
    cd "$BOOST_ROOT/libs/$SELF"
    ci/travis/codecov.sh

    cd "$BOOST_CI_SRC_FOLDER"

    # was:
    # lcov --ignore-errors unused --remove coverage.info -o coverage_filtered.info '*/test/*' '*/extra/*'
    lcov --ignore-errors unused --extract coverage.info "*/boost/$SELF/*" "*/$SELF/src/*" -o coverage_filtered.info
}

collect_coverage

# Now the tracefile is coverage_filtered.info
genhtml -o genhtml coverage_filtered.info

#########################
#
# gcovr
#
#########################

GCOVRFILTER=".*/$REPONAME/.*"
if [ -d "gcovr" ]; then
    rm -r gcovr
fi
mkdir gcovr
cd ../boost-root
if [ ! -d ci-automation ]; then
    git clone -b master https://github.com/cppalliance/ci-automation
else
    cd ci-automation
    git pull || true
    cd ..
fi

outputlocation="$BOOST_CI_SRC_FOLDER/gcovr"
# gcovr --merge-mode-functions separate -p --html-nested --html-template-dir=ci-automation/gcovr-templates/html --exclude-unreachable-branches --exclude-throw-branches --exclude '.*/test/.*' --exclude '.*/extra/.*' --exclude '.*/example/.*' --filter "$GCOVRFILTER" --html --output "${outputlocation}/index.html"
gcovr --merge-mode-functions separate -p --html-nested --exclude-unreachable-branches --exclude-throw-branches --exclude '.*/test/.*' --exclude '.*/extra/.*' --exclude '.*/example/.*' --filter "$GCOVRFILTER" --html --output "${outputlocation}/index.html"
ls -al "${outputlocation}"

# Generate tree.json for sidebar navigation
python3 "ci-automation/scripts/gcovr_build_tree.py" "$outputlocation"

#########################################################################
#
# Collect coverage again the same way on the target branch, usually develop
#
#########################################################################

# preparation:

# "$CHANGE_TARGET" is a variable from multibranch-pipeline.
TARGET_BRANCH="${CHANGE_TARGET:-develop}"

cd "$BOOST_CI_SRC_FOLDER"
BOOST_CI_SRC_FOLDER_ORIG=$BOOST_CI_SRC_FOLDER
rm -rf ../boost-root
cd ..
# It was possible to have the new folder be named $SELF.
# But just to be extra careful, choose another name such as
ADIRNAME=${SELF}-target-branch-iteration
if [ -d "$ADIRNAME" ]; then
    mv "$ADIRNAME" "$ADIRNAME.bck.$timestamp"
fi
git clone -b "$TARGET_BRANCH" "https://github.com/$ORGANIZATION/$SELF" "$ADIRNAME"
cd "$ADIRNAME"
# The "new" BOOST_CI_SRC_FOLDER:
BOOST_CI_SRC_FOLDER=$(pwd)
export BOOST_CI_SRC_FOLDER
BOOST_CI_SRC_FOLDER_TARGET=$(pwd)
export BOOST_CI_SRC_FOLDER_TARGET

# done with prep, now everything is the same as before

collect_coverage

# diff coverage report generation

BOOST_CI_SRC_FOLDER=$BOOST_CI_SRC_FOLDER_ORIG
cd "$BOOST_CI_SRC_FOLDER/.."

if [ ! -d diff-coverage-report ]; then
    git clone https://github.com/grisumbras/diff-coverage-report
else
    cd diff-coverage-report
    git pull || true
    cd ..
fi

diff -Nru0 --minimal -x '.git' -x '*.info' -x genhtml -x gcovr -x diff-report \
     "$BOOST_CI_SRC_FOLDER_TARGET" "$BOOST_CI_SRC_FOLDER_ORIG" | tee difference

# diff-coverage-report/diff-coverage-report.py -D difference \
#     -O "$BOOST_CI_SRC_FOLDER/diff-report" \
#     -B "$BOOST_CI_SRC_FOLDER_TARGET/coverage_filtered.info" \
#     -T "$BOOST_CI_SRC_FOLDER_ORIG/coverage_filtered.info" \
#     -S "$BOOST_CI_SRC_FOLDER_ORIG" \
#     -P "$BOOST_CI_SRC_FOLDER_TARGET" "$BOOST_CI_SRC_FOLDER_ORIG" \
#        "$BOOST_ROOT/libs/$SELF"      "$BOOST_CI_SRC_FOLDER_ORIG" \
#        "$BOOST_ROOT/boost"           "$BOOST_CI_SRC_FOLDER_ORIG/include/boost"

# In the event that diff-coverage-report.py doesn't run, ensure
# an empty directory exists anyway to upload to S3.  
mkdir -p "$BOOST_CI_SRC_FOLDER/diff-report"
touch "$BOOST_CI_SRC_FOLDER/diff-report/test.txt"

# Done, return everything back.
cd "$BOOST_CI_SRC_FOLDER"
