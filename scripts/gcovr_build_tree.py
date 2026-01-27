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
                    'link': None
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
            name = entry['name']
            is_dir = entry['is_dir'] or '.' not in name
            coverage = entry['coverage']
            link = entry['link']

            node = {
                'name': name,
                'coverage': coverage,
                'coverageClass': get_coverage_class(coverage),
                'isDirectory': is_dir,
                'link': link,
                'children': []
            }

            # If directory with a link, recursively get its children
            if is_dir and link and link in file_entries:
                node['children'] = build_node_from_file(link, visited.copy())

            nodes.append(node)

        # Sort: directories first, then files, alphabetically
        nodes.sort(key=lambda x: (not x['isDirectory'], x['name'].lower()))
        return nodes

    # Start from index.html
    tree = build_node_from_file('index.html')
    return tree


def inject_tree_data(output_dir, tree):
    """Inject tree data as JavaScript variable into all HTML files."""
    output_path = Path(output_dir)
    tree_script = f'<script>window.GCOVR_TREE_DATA={json.dumps(tree)};</script>'

    count = 0
    for html_file in output_path.glob('*.html'):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if already injected (look for the actual data, not just the var name)
            if 'window.GCOVR_TREE_DATA=[' in content or 'window.GCOVR_TREE_DATA={' in content:
                continue

            # Inject before </body>
            if '</body>' in content:
                content = content.replace('</body>', f'{tree_script}\n</body>')
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                count += 1
        except Exception as e:
            print(f"Warning: Could not inject into {html_file}: {e}", file=sys.stderr)

    return count


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

    # Inject tree data into HTML files for local file:// access
    injected = inject_tree_data(output_dir, tree)
    print(f"Injected tree data into {injected} HTML files")


if __name__ == '__main__':
    main()
