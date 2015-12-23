#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import codecs
import json
import os

from fb_parser import FbParser


def main():
    num_args = len(sys.argv)
    if num_args < 3:
        print('usage: %s <html-file1> [html-file2 ...] <output-json-file>' % sys.argv[0], file=sys.stderr)
        exit(1)

    html_files = sys.argv[1:num_args - 1]
    output_file = sys.argv[num_args - 1]

    output_json_data = {}
    for html_file in html_files:
        file_basename = os.path.basename(html_file)
        try:
            rdot_idx = file_basename.rindex('.')
            label = file_basename[:rdot_idx]
        except ValueError:
            label = file_basename

        json_data = parse_html_file(html_file)

        if label not in output_json_data:
            output_json_data[label] = json_data
        else:
            output_json_data[label]['data'].append(json_data['data'])

    print("> writing result JSON file '%s'..." % output_file)
    with codecs.open(output_file, 'w', 'utf-8') as f:
        json.dump(output_json_data, f, indent=2)


def parse_html_file(html_file):
    print("> parsing HTML file '%s'..." % html_file)

    parser = FbParser()
    output = {}
    with codecs.open(html_file, 'r', 'utf-8') as f:
        html_content = f.read()
        parser.parse(html_content)
        output = parser.output

    return output


if __name__ == '__main__':
    main()
