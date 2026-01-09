
## Initial Setup

Check the size of the remote machine by running `nproc` or `htop` and observe the number of cpus. The server automatically resizes each week to "small" in case it is not being used. There is a GitHub Actions job https://github.com/cppalliance/ci-automation/actions/workflows/cursor-server-resize.yml to increase the instance size.  

On the target machine, clone this repository.

```
cd $HOME
mkdir -p $HOME/github/cppalliance
cd $HOME/github/cppalliance/
git clone https://github.com/cppalliance/ci-automation
```

One-time step: modify $PATH to discover scripts.  

```
vi ~/.bashrc
# at the end of the file
export PATH=$HOME/github/cppalliance/ci-automation/remote-workstation/scripts:$PATH
```

Restart the terminal, or logout/login. Check $PATH.

```
env
```

## Tests

This is the main section. Clone a git repository to run tests on.  

```
cd $HOME
mkdir -p $HOME/github/boostorg
cd $HOME/github/boostorg
git clone https://github.com/boostorg/json
cd json
```

From within a repo (such as json or beast2) run a test script:  

```
clang-20.sh
```

The full list of test scripts is found in $HOME/github/cppalliance/ci-automation/remote-workstation/scripts/   

`cleanup.sh` removes /tmp/job-* directories.
