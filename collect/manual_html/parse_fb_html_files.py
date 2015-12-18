#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import codecs
import re
import json
from pprint import pprint
from copy import copy
from datetime import datetime
from HTMLParser import HTMLParser


class FbHTMLParserFindPost(HTMLParser):
    def __init__(self, callback_found_post):
        HTMLParser.__init__(self)

        self._post_outer_id_startswith = 'mall_post_'

        self._observed_tags = ('div', 'abbr', 'h5', 'a', 'span')

        self.callback_found_post = callback_found_post

        self.cur_tag_level = dict((tag, 0) for tag in self._observed_tags)

        self.post_outer_tag_level = None
        self.post_author_tag_level = None
        self.post_inner_tag_level = None
        self.cur_post_date = None
        self.cur_post_author = None
        self.cur_post_text = []
        self.cur_post_comments = []
        self.orig_post_comments = None

        self.comment_list_tag_level = None
        self.comment_list_content_tag_level = None
        self.comment_list_content_author_tag_level = None
        self.comment_list_content_message_tag_level = None
        self.comment_replies_tag_level = None
        self.cur_comment = None
        self.prev_comment = None

    def handle_starttag(self, tag, attrs):
        if tag not in self._observed_tags:
            return

        attrib_dict = dict(attrs)
        self.cur_tag_level[tag] += 1

        if 'class' in attrib_dict:
            tag_classes = attrib_dict['class'].split()
        else:
            tag_classes = []

        if tag == 'div':
            # check if we have a outer post div
            if self.post_outer_tag_level is None\
                    and 'id' in attrib_dict and attrib_dict['id'].startswith(self._post_outer_id_startswith):
                self.post_outer_tag_level = self.cur_tag_level[tag]

            # check if we have an inner post div (contains post message text)
            if self.post_outer_tag_level is not None and self.post_inner_tag_level is None\
                    and '_5pbx' in tag_classes and 'userContent' in tag_classes:
                self.post_inner_tag_level = self.cur_tag_level[tag]

            # check if we have a comment list
            if self.post_outer_tag_level is not None and 'UFIList' in tag_classes:
                self.comment_list_tag_level = self.cur_tag_level[tag]
                self.cur_post_comments = []

            # check if we have a reply list on a comment
            if self.comment_list_tag_level is not None and 'UFIReplyList' in tag_classes:
                self.comment_replies_tag_level = self.cur_tag_level[tag]
                assert self.prev_comment and type(self.cur_post_comments) == list \
                       and type(self.prev_comment.get('comments')) == list
                self.orig_post_comments = self.cur_post_comments
                self.cur_post_comments = self.prev_comment.get('comments')

            # check if we have a comment content in a comment list:
            if self.comment_list_tag_level is not None and 'UFICommentContentBlock' in tag_classes:
                self.comment_list_content_tag_level = self.cur_tag_level[tag]
        elif tag == 'a':
            # check if we have an author in a comment content:
            if self.comment_list_content_tag_level is not None and 'UFICommentActorName' in tag_classes:
                self.comment_list_content_author_tag_level = self.cur_tag_level[tag]
        elif tag == 'span':
            # check if we have a comment message:
            if self.comment_list_content_tag_level is not None and 'UFICommentBody' in tag_classes:
                self.comment_list_content_message_tag_level = self.cur_tag_level[tag]
        elif tag == 'abbr':
            # check if we have a post date field
            if self.post_outer_tag_level is not None and self.comment_list_tag_level is None\
                    and '_5ptz' in tag_classes and 'data-utime' in attrib_dict:
                dt_obj = datetime.fromtimestamp(int(attrib_dict['data-utime']))
                self.cur_post_date = dt_obj.strftime('%Y-%m-%d %H:%M:%S')

            # check if we have a comment date field
            if self.comment_list_tag_level is not None\
                    and 'livetimestamp' in tag_classes and 'data-utime' in attrib_dict:
                dt_obj = datetime.fromtimestamp(int(attrib_dict['data-utime']))
                assert self.cur_comment
                self.cur_comment['date'] = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        elif tag == 'h5':
            # check if we have an author field
            if self.post_outer_tag_level is not None and self.post_author_tag_level is None\
                    and '_5pbw' in tag_classes:
                self.post_author_tag_level = self.cur_tag_level[tag]

    def handle_endtag(self, tag):
        if tag not in self._observed_tags:
            return

        if tag == 'h5':
            if self.post_author_tag_level == self.cur_tag_level[tag]:
                self.post_author_tag_level = None
        elif tag == 'a':
            # check comment author:
            if self.comment_list_content_author_tag_level == self.cur_tag_level[tag]:
                self.comment_list_content_author_tag_level = None
        elif tag == 'span':
            # check comment message:
            if self.comment_list_content_message_tag_level == self.cur_tag_level[tag]:
                self.comment_list_content_message_tag_level = None
        elif tag == 'div':
            # check inner post tag
            if self.post_inner_tag_level == self.cur_tag_level[tag]:
                self.post_inner_tag_level = None

            # check comment list
            if self.comment_list_tag_level == self.cur_tag_level[tag]:
                self.comment_list_tag_level = None

            # check comment reply list
            if self.comment_replies_tag_level == self.cur_tag_level[tag]:
                self.cur_post_comments = self.orig_post_comments
                self.comment_replies_tag_level = None

            # check comment content
            if self.comment_list_content_tag_level == self.cur_tag_level[tag]:
                assert self.cur_comment
                self.comment_list_content_tag_level = None
                self.cur_comment['message'] = ' '.join(self.cur_comment['message'])
                self.cur_post_comments.append(self.cur_comment)
                self.prev_comment = self.cur_comment
                self.cur_comment = None     # reset

            # check outer post tag
            if self.post_outer_tag_level == self.cur_tag_level[tag]:
                self.post_outer_tag_level = None

                post_data = {
                    'date': self.cur_post_date,
                    'from': self.cur_post_author,
                    'message': u'\n'.join(self.cur_post_text),
                    'comments': self.cur_post_comments
                }
                self.callback_found_post(post_data)
                self.cur_post_text = []  # reset
                self.cur_post_comments = []
                self.prev_comment = None

        self.cur_tag_level[tag] -= 1

    def handle_data(self, data):
        if self.post_author_tag_level is not None:
            self.cur_post_author = data

        if self.post_inner_tag_level is not None:
            self.cur_post_text.append(data)

        if self.comment_list_content_author_tag_level is not None:
            self.cur_comment = {
                'from': data,
                'date': None,
                'message': [],
                'comments': []
            }

        if self.comment_list_content_message_tag_level is not None:
            assert self.cur_comment
            self.cur_comment['message'].append(data)


class FbParser(object):
    def __init__(self):
        self.find_post_parser = FbHTMLParserFindPost(self.found_post_callback)
        self._posts = []

    @property
    def output(self):
        return self._posts

    def parse(self, html):
        self.find_post_parser.feed(html)

    def found_post_callback(self, post):
        self._posts.append(post)


def main():
    num_args = len(sys.argv)
    if num_args < 3:
        print('usage: %s <html-file1> [html-file2 ...] <output-json-file>' % sys.argv[0], file=sys.stderr)
        exit(1)

    html_files = sys.argv[1:num_args - 1]
    output_file = sys.argv[num_args - 1]

    output_json_data = {}
    for html_file in html_files:
        json_data = parse_html_file(html_file)
        # TODO ...
        output_json_data = json_data

    print("> writing result JSON file '%s'..." % output_file)
    with codecs.open(output_file, 'w', 'utf-8') as f:
        json.dump(output_json_data, f, indent=2)


def parse_html_file(html_file):
    print("> parsing HTML file '%s'..." % html_file)

    parser = FbParser()
    output = None
    with codecs.open(html_file, 'r', 'utf-8') as f:
        html_content = f.read()
        parser.parse(html_content)
        output = parser.output

    return output


if __name__ == '__main__':
    main()