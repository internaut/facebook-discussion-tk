#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import json
import time
import csv

import wordstats

LIMIT_PRINT = 20
wordstats.LIBLEIPZIG_FOR_LEMMATA = False

output_file = None

def main():
    global output_file
    if len(sys.argv) < 3:
        print("usage: %s <json-file> <output-csv-file>" % sys.argv[0], file=sys.stderr)
        exit(1)

    json_file, output_file = sys.argv[1:3]
    with open(json_file) as f:
        json_data = json.load(f)

    analyse(json_data)


def analyse(json_data):
    append_output = False
    for label, data in json_data.items():
        print("> analysing data from '%s' (%s)" % (label, data['meta']['type']))
        print(">> name: '%s'" % data['meta']['name'])
        print(">> facebook id: '%s'" % data['meta']['fb_id'])
        print(">> collection date: '%s'" % data['meta']['date'])
        print(">> number of collection posts: %d" % len(data['data']))

        sum_counts = {}
        print(">> counting nouns", end='')
        sys.stdout.flush()
        for post in data['data']:
            counts = wordstats.count_nouns_in_text(post['message'])
            add_up_noun_counts(sum_counts, counts)
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
