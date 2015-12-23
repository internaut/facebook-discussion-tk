#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import json
import time
import csv
from pprint import pprint

import wordstats

LIMIT_PRINT = 20
wordstats.LIBLEIPZIG_FOR_LEMMATA = False
wordstats.STRINGS_STARTWITH_BLACKLIST = (
    'http:',
    'https:',
    u'„'
)
wordstats.STRINGS_EQUALS_BLACKLIST = (
    'emoticon',
    ':d',
    'seid',
    'ja',
    'du',
    'hast',
    'bist',
    'euch',
    'hab',
    'habt',
    'sowas',
    'passiert',
    'eure',
    'nein',
    'oder',
    'die',
    'und',
    'jetzt',
    'wir',
    'das',
    'ist',
    'mehr',
    'mal',
    'dich',
    'auf'
)

wordstats.STRINGS_EQUALS_CS_BLACKLIST = (
    'Is'
)

output_file = None


def main():
    global output_file
    num_args = len(sys.argv)
    if num_args < 3:
        print("usage: %s <json-file-1> [json-file-2 ...] <output-csv-file>" % sys.argv[0], file=sys.stderr)
        exit(1)

    json_files = sys.argv[1:num_args - 1]
    output_file = sys.argv[num_args - 1]

    merged_json_data = {}
    for json_file in json_files:
        print("> reading JSON file '%s'..." % json_file)
        with open(json_file) as f:
            json_data = json.load(f)
            for label, data in json_data.items():
                if label not in merged_json_data:
                    merged_json_data[label] = data
                else:
                    merged_json_data[label]['data'].extend(data['data'])

    # pprint(merged_json_data)
    analyse(merged_json_data)


def flatten_messages(messages, level=1):
    flat_msgs = []
    # print('%s num. messages: %d' % ('>' * (level + 2), len(messages)))
    for m in messages:
        flat_msgs.append(m)

        if 'comments' in m and len(m['comments']) > 0:
            flat_msgs.extend(flatten_messages(m['comments'], level + 1))

    return flat_msgs


def analyse(json_data):
    append_output = False
    for label, data in json_data.items():
        print("> analysing data from '%s' (%s)" % (label, data['meta']['type']))
        print(">> name: '%s'" % data['meta']['name'])
        print(">> facebook id: '%s'" % data['meta']['fb_id'])
        print(">> collection date: '%s'" % data['meta']['date'])
        print(">> flattening posts and comments...")

        flat_messages = flatten_messages(data['data'])
        print(">> number of overall messages: %d" % len(flat_messages))

        sum_counts = {}
        print(">> counting nouns", end='')
        sys.stdout.flush()
        for i, post in enumerate(flat_messages):
            counts = wordstats.count_nouns_in_text(post['message'])
            add_up_noun_counts(sum_counts, counts)

            if i % 100 == 0:
                print(".", end='')
                sys.stdout.flush()

            if wordstats.LIBLEIPZIG_FOR_LEMMATA:
                time.sleep(1)
        print()
        sorted_counts = sorted(sum_counts.items(), key=lambda item: item[1], reverse=True)
        print(">> top %d nouns of overall %d nouns:" % (LIMIT_PRINT, len(sum_counts)))
        print_sum_counts(sorted_counts, limit=LIMIT_PRINT)

        write_output_to_file(label, sorted_counts, append=append_output)
        append_output = True

    print("> all done")


def write_output_to_file(label, sum_counts, append=False):
    print(">> writing output to file '%s'" % output_file)

    fmode = 'a' if append else 'w'
    with open(output_file, fmode + 'b') as f:
        writer = csv.writer(f)
        for noun, count in sum_counts:
            writer.writerow([label.encode('utf-8'), noun.encode('utf-8'), count])

    print(">> done")


def add_up_noun_counts(s, a):
    for noun, count in a.items():
        if noun not in s:
            s[noun] = 0
        s[noun] += count


def print_sum_counts(sorted_counts, limit=None):
    for i, items in enumerate(sorted_counts):
        noun, count = items
        print('>>> %s (%d)' %(noun, count))

        if limit and i > limit:
            break


if __name__ == '__main__':
    main()
