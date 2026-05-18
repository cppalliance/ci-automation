#!/usr/bin/env python3
"""
Build a JSON tree structure from gcovr HTML output.
This enables true inline expand/collapse in the sidebar.
"""

import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class FileListParser(HTMLParser):
    """Parse gcovr HTML to extract file list entries and current path."""

    def __init__(self):
        super().__init__()
        self.entries = []
        self.current_path = ''
        self.in_file_row = False
        self.current_entry = {}
        self.capture_text = None
        self.in_breadcrumb = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Detect breadcrumb to extract current path
        if tag == 'div' and attrs_dict.get('class') == 'breadcrumb':
            self.in_breadcrumb = True

        # Detect file-row divs
        if tag == 'div' and 'class' in attrs_dict:
            classes = attrs_dict['class'].split()
            if 'file-row' in classes:
                self.in_file_row = True
                self.current_entry = {
                    'name': attrs_dict.get('data-filename', ''),
                    'coverage': attrs_dict.get('data-coverage', '0'),
                    'is_dir': 'directory' in classes,
                    'link': None,
                    'linesTotal': attrs_dict.get('data-lines', ''),
                    'linesExec': attrs_dict.get('data-lines-exec', ''),
                    'linesCoverage': attrs_dict.get('data-lines-coverage', ''),
                    'linesClass': attrs_dict.get('data-lines-class', ''),
                    'functionsCoverage': attrs_dict.get('data-functions-coverage', ''),
                    'functionsClass': attrs_dict.get('data-functions-class', ''),
                    'branchesCoverage': attrs_dict.get('data-branches-coverage', ''),
                    'branchesClass': attrs_dict.get('data-branches-class', ''),
                }

        # Capture links in file rows
        if self.in_file_row and tag == 'a':
            href = attrs_dict.get('href', '')
            if href and not self.current_entry.get('link'):
                self.current_entry['link'] = href

        # Capture coverage percent
        if self.in_file_row and tag == 'span' and 'class' in attrs_dict:
            if 'coverage-percent' in attrs_dict['class']:
                self.capture_text = 'coverage'

    def handle_data(self, data):
        if self.capture_text == 'coverage' and self.in_file_row:
            match = re.search(r'([\d.]+)%?', data.strip())
            if match:
                self.current_entry['coverage'] = match.group(1)
            self.capture_text = None

    def handle_endtag(self, tag):
        if tag == 'div' and self.in_file_row and self.current_entry.get('name'):
            self.entries.append(self.current_entry)
            self.current_entry = {}
            self.in_file_row = False
        if tag == 'div' and self.in_breadcrumb:
            self.in_breadcrumb = False


def parse_html_file(filepath):
    """Parse a single HTML file and extract entries."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        parser = FileListParser()
        parser.feed(content)
        return parser.entries
    except Exception as e:
        print(f"Error parsing {filepath}: {e}", file=sys.stderr)
        return []


def get_coverage_class(coverage):
    """Determine coverage class based on percentage."""
    try:
        pct = float(coverage)
        if pct >= 90:
            return 'coverage-high'
        elif pct >= 75:
            return 'coverage-medium'
        else:
            return 'coverage-low'
    except:
        return 'coverage-unknown'


def clean_name(raw_name):
    """Strip leading relative-path prefixes (./ and ../) but preserve the rest of the path.

    Multi-segment names like 'boost/url/url_view.hpp' are kept intact here
    so that normalize_tree() can later split them into a proper nested
    directory structure.
    """
    if not raw_name:
        return raw_name
    cleaned = raw_name
    while cleaned.startswith('../') or cleaned.startswith('./'):
        cleaned = cleaned[3:] if cleaned.startswith('../') else cleaned[2:]
    return cleaned or raw_name


def normalize_tree(nodes):
    """Expand multi-segment node names into a proper nested directory structure.

    A node whose name is e.g. 'boost/url/url_view.hpp' becomes a synthetic
    'boost' directory containing a 'url' directory containing 'url_view.hpp'.
    Multiple entries sharing a prefix get merged under one parent directory.

    This is required because gcovr collapses single-child intermediate
    directories in its HTML, so what reaches us as a single 'file' entry
    can really represent multiple levels of nesting.

    Doing this here (Python) rather than in the browser keeps the JSON
    contract simple: every node has a single-segment name.
    """
    if not nodes:
        return nodes

    groups = {}
    order = []

    for node in nodes:
        name = node.get('name', '')
        slash_idx = name.find('/')

        if slash_idx == -1:
            if name in groups:
                # Merge with existing entry of the same name
                existing = groups[name]
                if node.get('link'):
                    existing['link'] = node['link']
                if node.get('coverage'):
                    existing['coverage'] = node['coverage']
                if node.get('coverageClass'):
                    existing['coverageClass'] = node['coverageClass']
                if node.get('children'):
                    existing['children'] = (existing.get('children') or []) + node['children']
            else:
                groups[name] = dict(node)
                order.append(name)
        else:
            prefix = name[:slash_idx]
            rest = name[slash_idx + 1:]

            if prefix not in groups:
                groups[prefix] = {
                    'name': prefix,
                    'coverage': '',
                    'coverageClass': 'coverage-unknown',
                    'linesTotal': '',
                    'linesExec': '',
                    'linesCoverage': '',
                    'linesClass': '',
                    'functionsCoverage': '',
                    'functionsClass': '',
                    'branchesCoverage': '',
                    'branchesClass': '',
                    'isDirectory': True,
                    'link': None,
                    'children': [],
                }
                order.append(prefix)
            if not groups[prefix].get('children'):
                groups[prefix]['children'] = []

            child_node = dict(node)
            child_node['name'] = rest
            groups[prefix]['children'].append(child_node)

    result = []
    for name in order:
        node = groups[name]
        if node.get('children'):
            node['children'] = normalize_tree(node['children'])
        result.append(node)

    return result


def sort_tree(nodes):
    """Recursively sort each level: directories first, then files, alphabetical within."""
    if not nodes:
        return
    nodes.sort(key=lambda x: (not x.get('isDirectory', False), x.get('name', '').lower()))
    for node in nodes:
        if node.get('children'):
            sort_tree(node['children'])


def build_tree(output_dir):
    """Build complete tree structure by following links recursively."""
    output_path = Path(output_dir)

    # Map from HTML filename to entries
    file_entries = {}

    # Parse all HTML files
    for html_file in output_path.glob('index*.html'):
        entries = parse_html_file(html_file)
        file_entries[html_file.name] = entries

    def build_node_from_file(html_filename, visited=None):
        """Recursively build tree from HTML file."""
        if visited is None:
            visited = set()

        if html_filename in visited:
            return []
        visited.add(html_filename)

        entries = file_entries.get(html_filename, [])
        nodes = []

        for entry in entries:
            name = clean_name(entry['name'])
            is_dir = entry['is_dir'] or '.' not in name
            coverage = entry['coverage']
            link = entry['link']

            node = {
                'name': name,
                'coverage': coverage,
                'coverageClass': get_coverage_class(coverage),
                'linesTotal': entry.get('linesTotal', ''),
                'linesExec': entry.get('linesExec', ''),
                'linesCoverage': entry.get('linesCoverage', ''),
                'linesClass': entry.get('linesClass', ''),
                'functionsCoverage': entry.get('functionsCoverage', ''),
                'functionsClass': entry.get('functionsClass', ''),
                'branchesCoverage': entry.get('branchesCoverage', ''),
                'branchesClass': entry.get('branchesClass', ''),
                'isDirectory': is_dir,
                'link': link,
                'children': []
            }

            # If directory with a link, recursively get its children
            if is_dir and link and link in file_entries:
                node['children'] = build_node_from_file(link, visited.copy())

            nodes.append(node)

        # Expand any multi-segment names into nested directories, then
        # sort every level (directories first, then files, alphabetically).
        nodes = normalize_tree(nodes)
        sort_tree(nodes)
        return nodes

    # Start from index.html
    tree = build_node_from_file('index.html')
    return tree


def inject_tree_data(output_dir, tree):
    """Inject tree data into the generated JS file's placeholder line.

    The JS file contains a final line of the form
        window.GCOVR_TREE_DATA = ...;
    (either an empty default from the Jinja template, or a previously
    injected value). We replace that single assignment with the real tree.
    Doing this in one shared .js file rather than inline in every .html
    page avoids duplicating the tree JSON across hundreds of HTML files.

    Note: gcovr renames the template file `gcovr.js` to `index.js` in the
    output directory, so that's what we target here.
    """
    output_path = Path(output_dir)
    js_file = output_path / 'index.js'
    if not js_file.exists():
        print(f"Warning: index.js not found at {js_file}", file=sys.stderr)
        return 0

    new_assignment = f'window.GCOVR_TREE_DATA = {json.dumps(tree)};'

    try:
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Non-greedy match up to the first `;` — safe because file paths
        # never contain a literal `;`. DOTALL handles pretty-printed JSON
        # spanning multiple lines from `tojson(2)` in the template.
        # Pass a lambda for the replacement so that any backslashes in the
        # JSON aren't interpreted as regex backreferences.
        new_content, count = re.subn(
            r'window\.GCOVR_TREE_DATA\s*=\s*.*?;',
            lambda _m: new_assignment,
            content,
            count=1,
            flags=re.DOTALL,
        )

        if count == 0:
            # No placeholder found — append the assignment so the data is
            # still defined globally.
            new_content = content.rstrip() + '\n' + new_assignment + '\n'

        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return 1
    except Exception as e:
        print(f"Warning: Could not inject into {js_file}: {e}", file=sys.stderr)
        return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: build_tree.py <gcovr_output_dir>", file=sys.stderr)
        sys.exit(1)

    output_dir = sys.argv[1]

    if not os.path.isdir(output_dir):
        print(f"Error: {output_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    tree = build_tree(output_dir)

    # Write tree.json
    tree_file = os.path.join(output_dir, 'tree.json')
    with open(tree_file, 'w', encoding='utf-8') as f:
        json.dump(tree, f, indent=2)

    print(f"Generated {tree_file} with {len(tree)} root entries")

    # Inject tree data into the generated index.js placeholder
    injected = inject_tree_data(output_dir, tree)
    if injected:
        print(f"Injected tree data into {output_dir}/index.js")
    else:
        print("Warning: tree data was not injected into index.js", file=sys.stderr)


if __name__ == '__main__':
    main()
