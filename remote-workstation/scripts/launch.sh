#!/bin/bash

# Run this script while in a boost library repository, such as /opt/github/boostorg/json.
# It will detect the library is "json" from the path name.
# And copy the contents of the dir into tests.

set -e

ID=$(uuidgen)
export ID
echo "ID is $ID"

# Preflight check

number_of_cpus=$(nproc)
if [ "$number_of_cpus" -lt 4 ]; then
    echo "The number of CPUs is $number_of_cpus. Resize at https://github.com/cppalliance/ci-automation/actions/workflows/cursor-server-resize.yml"
    printf 'Continue (y/n)? '
    read -r answer
    if [ "$answer" != "${answer#[Yy]}" ] ;then
        true
    else
        echo "Exiting"
        exit 1
    fi
fi

####

if WORKSPACE=$(git rev-parse --show-toplevel 2> /dev/null); then
    LIBRARY=$(basename "$WORKSPACE")
    echo "Library name is $LIBRARY"
else
    echo "Not a git repo. Exiting."
    exit 1
fi

export BOOST_ROOT="$HOME/github/boostorg/boost-root"
export BOOST_ROOT_PARENT="$HOME/github/boostorg"
export BOOST_BRANCH=develop
mkdir -p "$BOOST_ROOT_PARENT"
cd "$BOOST_ROOT_PARENT"
if [ ! -d boost-root ]; then
    git clone -b $BOOST_BRANCH https://github.com/boostorg/boost.git boost-root 
fi
cd boost-root
git pull
git submodule update --init
pwd
ls

# Optionally set another $EXTRA_BOOST_LIBRARIES in the calling script.
# Otherwise use these defaults.
if [ -z "${EXTRA_BOOST_LIBRARIES}" ]; then
    EXTRA_BOOST_LIBRARIES="cppalliance/buffers cppalliance/capy cppalliance/http"
fi 
for EXTRA_LIB in ${EXTRA_BOOST_LIBRARIES}; do
    REFRESH_EXTRA_LIB="ok"
    EXTRA_LIB_REPO=$(basename "$EXTRA_LIB")
    if [ ! -d "$BOOST_ROOT/libs/${EXTRA_LIB_REPO}" ]; then
        pushd "${BOOST_ROOT}/libs"
        git clone https://github.com/"${EXTRA_LIB}" -b "$BOOST_BRANCH" --depth 1
        popd
    else
        # refresh extra lib:
        pushd "$BOOST_ROOT/libs/${EXTRA_LIB_REPO}"
        if ! git checkout "$BOOST_BRANCH"; then
            REFRESH_EXTRA_LIB="failed"
        fi
        if ! git pull; then
            REFRESH_EXTRA_LIB="failed" 
        fi
        popd
    fi
    if [ "$REFRESH_EXTRA_LIB" = "failed" ]; then
        pushd "${BOOST_ROOT}/libs"
        rm -rf "${EXTRA_LIB_REPO}"
        git clone https://github.com/"${EXTRA_LIB}" -b "${BOOST_BRANCH}" --depth 1
        popd
    fi
done

if [ ! -f "b2" ]; then
    echo "b2 not found, running ./bootstrap.sh"
    ./bootstrap.sh
fi

# shellcheck disable=SC2046
if find . -maxdepth 1 -name "b2" -mtime +30 | grep -q .
then
    echo "b2 is older than 30 days. Rebuild. Running ./bootstrap.sh."
    ./bootstrap.sh
fi
echo "Running ./b2 headers"
./b2 headers

# 
# Job startup
mkdir -p /tmp/job-"$ID"/{upper,work,merged}

sudo mount -t overlay overlay -o lowerdir="$HOME"/github/boostorg/boost-root,upperdir=/tmp/job-"$ID"/upper,workdir=/tmp/job-"$ID"/work /tmp/job-"$ID"/merged

cd /tmp/job-"$ID"/merged/libs
rm -rf "$LIBRARY"
cp -rp "$WORKSPACE" "$LIBRARY"
cd /tmp/job-"$ID"/merged/

DEFAULT_BUILD_VARIANT="debug,release"
DEFAULT_ADDRESS_MODEL="64"
DEFAULT_TOOLSET="gcc-13"
DEFAULT_CXXSTD="20"

if [ -n "${matrix_compiler}" ]
then
    echo -n "using ${matrix_toolset} : : ${matrix_compiler}" > ~/user-config.jam
    echo " ;" >> ~/user-config.jam
fi

matrix_build_jobs=$( (nproc || sysctl -n hw.ncpu) 2> /dev/null )

B2_ARGS=("-j" "$matrix_build_jobs")

if [ -n "${matrix_toolset}" ]
then
    B2_ARGS+=("toolset=${matrix_toolset}")
else
    B2_ARGS+=("toolset=$DEFAULT_TOOLSET")
fi
if [ -n "${matrix_cxxstd}" ]
then
    B2_ARGS+=("cxxstd=${matrix_cxxstd}")
else
    B2_ARGS+=("cxxstd=$DEFAULT_CXXSTD")
fi
if [ -n "${matrix_build_variant}" ]
then
    B2_ARGS+=("variant=${matrix_build_variant}")
else
    B2_ARGS+=("variant=$DEFAULT_BUILD_VARIANT")
fi
if [ -n "${matrix_threading}" ]
then
    B2_ARGS+=("threading=${matrix_threading}")
fi
if [ -n "${matrix_ubsan}" ]
then
    export UBSAN_OPTIONS="print_stacktrace=1"
    B2_ARGS+=("undefined-sanitizer=norecover" "linkflags=-fuse-ld=gold" "define=UBSAN=1" "debug-symbols=on" "visibility=global")
fi
if [ -n "${matrix_cxxflags}" ]
then
    B2_ARGS+=("cxxflags=${matrix_cxxflags}")
fi
if [ -n "${matrix_address_model}" ]
then
    B2_ARGS+=("address-model=${matrix_address_model}")
else
    B2_ARGS+=("address-model=${DEFAULT_ADDRESS_MODEL}")
fi
if [ -n "${matrix_linkflags}" ]
then
    B2_ARGS+=("linkflags=${matrix_linkflags}")
fi
B2_ARGS+=("libs/$LIBRARY/test")

echo "Running ./b2" "${B2_ARGS[@]}"
./b2 "${B2_ARGS[@]}"

echo "Test complete. See /tmp/job-$ID/merged"
