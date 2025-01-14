
## GCOV/LCOV PROCESSING

- lcov-jenkins-gcc-13.sh: a script used by Jenkins jobs to process test coverage, and output lcov/gcov results.  
- gcov-compare.py: Compares the coverage changes of a pull request, and displays a sort of "chart" indicating if coverage has increased or decreased.  

Modifying lcov-jenkins-gcc-13.sh affects all current jobs. Therefore, when testing, add scripts such as lcov-jenkins-experimental.sh, etc.

See docs/README.md for instructions about running lcov in a local test environment.
