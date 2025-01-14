
## LCOV and GCOVR scripts

Generate coverage reports on pull requests.  

## Instructions to test gcovr locally  

Run tests in a docker container such as ubuntu:24.04, or the latest LTS Ubuntu.  

Configure a few variables and settings that would already be available in a Jenkins job but
if run in standalone mode would need to be set. The following code might be manually
copied into the script. Or run this in a shell first.

```
apt-get update
apt-get install sudo

mkdir -p test
cd test

export REPONAME=url
export ORGANIZATION=cppalliance
ghprbTargetBranch=develop
export JOBFOLDER="${REPONAME}_job_folder"

echo "Initial cleanup. Remove job folder"
rm -rf ${JOBFOLDER}
echo "Remove target folder"
rm -rf ${REPONAME}
echo "Remove boost-root"
rm -rf boost-root

git clone https://github.com/$ORGANIZATION/$REPONAME ${JOBFOLDER}
cd ${JOBFOLDER}

# Then proceed with the lcov processing

./lcov-jenkins-gcc-13.sh # or the name of the current script, which may be gcc-16, etc.
```
