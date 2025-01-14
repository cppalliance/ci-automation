#!/usr/bin/python3

# Compare govr json output to show the amount of code coverage changes in a commit or pull request

import sys
import json
from pprint import pprint
from collections import defaultdict

if len(sys.argv) >= 2:
    newcoveragefile = sys.argv[1]
    # print("newcoveragefile is " + newcoveragefile)
else:
    # a default
    newcoveragefile = "summary.pr.json"
    # print("newcoveragefile is using a default value of summary.pr.json")

if len(sys.argv) >= 3:
    targetbranchcoveragefile = sys.argv[2]
    # print("targetbranchcoveragefile is " + targetbranchcoveragefile)
else:
    # a default
    targetbranchcoveragefile = "summary.develop.json"
    # print("targetbranchcoveragefile is using a default value of summary.targetbranch.json")

json_file = open(newcoveragefile, "r")
newcoveragedata = json.load(json_file)
json_file.close()
json_file = open(targetbranchcoveragefile, "r")
targetbranchcoveragedata = json.load(json_file)
json_file.close()

new_files = {}

for filedict in newcoveragedata["files"]:
    filename = filedict["filename"]
    new_files[filename] = filedict

targetbranch_files = {}
for filedict in targetbranchcoveragedata["files"]:
    filename = filedict["filename"]
    targetbranch_files[filename] = filedict

diff_files = defaultdict(dict)

for file in new_files:
    if file in targetbranch_files:
        diff_line_percent = (
            new_files[file]["line_percent"] - targetbranch_files[file]["line_percent"]
        )
        diff_line_percent = round(diff_line_percent, 2)
        if isinstance(diff_line_percent, float) and diff_line_percent.is_integer():
            diff_line_percent = int(diff_line_percent)
        # print(new_files[file]["line_percent"],targetbranch_files[file]["line_percent"],diff_line_percent)
    else:
        diff_line_percent = new_files[file]["line_percent"] - 100
        diff_line_percent = round(diff_line_percent, 2)
        if isinstance(diff_line_percent, float) and diff_line_percent.is_integer():
            diff_line_percent = int(diff_line_percent)
        # print(diff_line_percent)

    diff_files[file]["diff_line_percent"] = diff_line_percent

# Output results

print("")
print(
    'Each number represents a percentage line coverage difference of one file. For example "0" means 0% change in a file, "-7" is 7% less coverage, etc.'
)
print("")

formatter = 0
for file in diff_files:
    print(str(diff_files[file]["diff_line_percent"]).rjust(4) + " ", end="")
    formatter = formatter + 1
    if formatter % 20 == 0:
        print("")
print("")
