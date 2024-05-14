
## GCOV/LCOV PROCESSING

- lcov-jenkins.sh: a script used by Jenkins jobs to process test coverage, and output lcov/gcov results.  
- lcov-development.sh: almost identical to lcov-jenkins.sh. However the purpose of this script is to test locally in a container, and possibly use this as a location to add new features that will eventually be migrated into the live production in lcov-jenkins.sh. Submit proposed updates here.  
- gcov-compare.py: Compares the coverage changes of a pull request, and displays a sort of "chart" indicating if coverage has increased or decreased.  


