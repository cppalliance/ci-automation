#!/usr/bin/env python3
"""
Fix file paths in gcovr JSON output.

Transforms boost-root-relative paths to repo-relative paths so that
gcovr's second pass (HTML generation) produces clean navigation.

Usage: python3 fix_paths.py <input.json> <output.json> --repo <REPONAME>
"""

import argparse
import json
import re
import sys


def fix_path(path, reponame):
    """Remap a single file path from boost-root layout to repo-relative."""
    # Strip leading ../
    while path.startswith('../'):
        path = path[3:]

    # libs/{REPO}/include/... -> include/...
    m = re.match(rf'^libs/{re.escape(reponame)}/include/(.*)', path)
    if m:
        return 'include/' + m.group(1)

    # libs/{REPO}/src/... -> src/...
    m = re.match(rf'^libs/{re.escape(reponame)}/src/(.*)', path)
    if m:
        return 'src/' + m.group(1)

    # libs/{REPO}/... (other) -> ...
    m = re.match(rf'^libs/{re.escape(reponame)}/(.*)', path)
    if m:
        return m.group(1)

    # boost/{REPO}/... -> include/boost/{REPO}/...
    m = re.match(rf'^boost/{re.escape(reponame)}/(.*)', path)
    if m:
        return f'include/boost/{reponame}/' + m.group(1)

    # boost/{REPO} (exact) -> include/boost/{REPO}
    if path == f'boost/{reponame}':
        return f'include/boost/{reponame}'

    return path


def fix_json(data, reponame):
    """Fix all file paths in a gcovr JSON structure."""
    if 'files' not in data:
        print("Warning: no 'files' key in JSON", file=sys.stderr)
        return data

    for entry in data['files']:
        # Summary format uses "filename", full JSON format uses "file"
        for key in ('filename', 'file'):
            if key in entry:
                entry[key] = fix_path(entry[key], reponame)

    return data


def main():
    parser = argparse.ArgumentParser(description='Fix file paths in gcovr JSON output')
    parser.add_argument('input', help='Input JSON file')
    parser.add_argument('output', help='Output JSON file')
    parser.add_argument('--repo', required=True, help='Boost library repo name (e.g. json, url)')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)

    data = fix_json(data, args.repo)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

    count = len(data.get('files', []))
    print(f"Fixed paths for {count} files: {args.input} -> {args.output}")


if __name__ == '__main__':
    main()
