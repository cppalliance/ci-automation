#!/bin/bash

# See docs at https://github.com/cppalliance/ci-automation/blob/master/scripts/docs/README.md

set -e

scriptname="lcov-jenkins-gcc-13.sh"
echo "Starting $scriptname"

# READ IN COMMAND-LINE OPTIONS

TEMP=$(getopt -o h:: --long help::,skip-gcovr::,skip-genhtml::,skip-diff-report::,only-gcovr:: -- "$@")
eval set -- "$TEMP"

# extract options and their arguments into variables.
while true ; do
    case "$1" in
        -h|--help)
            helpmessage="""
usage: $scriptname [-h] [--skip-gcovr] [--skip-genhtml] [--skip-diff-report] [--only-gcovr]

Builds library documentation.

optional arguments:
  -h, --help            Show this help message and exit
  --skip-gcovr          Don't run gcovr
  --skip-genhtml        Don't run genhtml
  --skip-diff-report    Don't run the diff-report
  --only-gcovr          Only run the main gcovr report, which is the same as multiple
                        skip options.
                        If the goal is to run gcovr, this is the preferred method
                        since this flag can be modified to skip other steps later.
"""

            echo ""
            echo "$helpmessage" ;
            echo ""
            exit 0
            ;;
        --skip-gcovr)
            skipgcovroption="yes" ; shift 2 ;;
        --skip-genhtml)
            skipgenhtmloption="yes" ; shift 2 ;;
        --skip-diff-report)
            skipdiffreportoption="yes" ; shift 2 ;;
        --only-gcovr)
            skipdiffreportoption="yes" ; skipgenhtmloption="yes" ; shift 2 ;;
        --) shift ; break ;;
        *) echo "Internal error!" ; exit 1 ;;
    esac
done

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

pip install --upgrade gcovr==8.6 || true

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

    # lcov --ignore-errors unused --remove coverage.info -o coverage_filtered.info '*/test/*' '*/extra/*' '*/example/*'
    lcov --ignore-errors unused --extract coverage.info "*/boost/$SELF/*" "*/$SELF/src/*" -o coverage_filtered.info
    sed "s|${BOOST_ROOT}/boost/$SELF|${BOOST_ROOT}/libs/$SELF/include/boost/$SELF|g" coverage_filtered.info > coverage_remapped.info

}

collect_coverage

# Now the tracefile is coverage_filtered.info
if [ ! "$skipgenhtmloption" = "yes" ]; then
    genhtml -o genhtml coverage_remapped.info
fi

#########################
#
# gcovr
#
#########################

if [ ! "$skipgcovroption" = "yes" ]; then

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

    # First pass, output json
    gcovr --merge-mode-functions separate --sort uncovered-percent --html-title "$REPONAME" --merge-lines --exclude-unreachable-branches --exclude-throw-branches --exclude '.*/test/.*' --exclude '.*/extra/.*' --exclude '.*/example/.*'  --exclude '.*/examples/.*' --filter "$GCOVRFILTER" --html --output "${outputlocation}/index.html" --json-summary-pretty --json-summary "$outputlocation/summary.json" --json "$outputlocation/coverage-raw.json"

    # Fix paths
    python3 "ci-automation/scripts/fix_paths.py" \
        "$outputlocation/coverage-raw.json" \
        "$outputlocation/coverage-fixed.json" \
        --repo "$REPONAME"

    # Create symlinks so gcovr can find source files at repo-relative paths
    ln -sfn "$BOOST_CI_SRC_FOLDER/include" "$(pwd)/include" 2>/dev/null || true
    ln -sfn "$BOOST_CI_SRC_FOLDER/src" "$(pwd)/src" 2>/dev/null || true

    # Second pass, generate html
    gcovr -a "$outputlocation/coverage-fixed.json" --merge-mode-functions separate --sort uncovered-percent --html-nested --html-template-dir=ci-automation/gcovr-templates/html --html-title "$REPONAME" --merge-lines --exclude-unreachable-branches --exclude-throw-branches --exclude '.*/test/.*' --exclude '.*/extra/.*' --exclude '.*/example/.*' --exclude '.*/examples/.*' --html --output "${outputlocation}/index.html" --json-summary-pretty --json-summary "$outputlocation/summary.json"

    ls -al "${outputlocation}"

    # Generate tree.json for sidebar navigation
    python3 "ci-automation/scripts/gcovr_build_tree.py" "$outputlocation"

    # Generate coverage badges
    python3 "ci-automation/scripts/generate_badges.py" "$outputlocation" --json "$outputlocation/summary.json"

fi

#########################################################################
#
# The following section is to generate a diff-report
#
#########################################################################

if [ ! "$skipdiffreportoption" = "yes" ]; then

    #########################
    #
    # Collect coverage again the same way on the target branch, usually develop
    #
    #########################

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

    diff-coverage-report/diff-coverage-report.py -D difference \
        -O "$BOOST_CI_SRC_FOLDER/diff-report" \
        -B "$BOOST_CI_SRC_FOLDER_TARGET/coverage_filtered.info" \
        -T "$BOOST_CI_SRC_FOLDER_ORIG/coverage_filtered.info" \
        -S "$BOOST_CI_SRC_FOLDER_ORIG" \
        -P "$BOOST_CI_SRC_FOLDER_TARGET" "$BOOST_CI_SRC_FOLDER_ORIG" \
           "$BOOST_ROOT/libs/$SELF"      "$BOOST_CI_SRC_FOLDER_ORIG" \
           "$BOOST_ROOT/boost"           "$BOOST_CI_SRC_FOLDER_ORIG/include/boost"

    # In the event that diff-coverage-report.py doesn't run, ensure
    # an empty directory exists anyway to upload to S3.
    mkdir -p "$BOOST_CI_SRC_FOLDER/diff-report"
    touch "$BOOST_CI_SRC_FOLDER/diff-report/test.txt"

    # Done, return everything back.
    cd "$BOOST_CI_SRC_FOLDER"

fi
