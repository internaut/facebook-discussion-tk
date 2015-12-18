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
        self._pttrn_post_id = re.compile('^' + self._post_outer_id_startswith + '(\d+)')

        self._observed_tags = ('div', 'abbr', 'h5', 'a', 'span')

        self.callback_found_post = callback_found_post

        self.cur_tag_level = dict((tag, 0) for tag in self._observed_tags)

        self.post_outer_tag_level = None
        self.post_author_tag_level = None
        self.post_inner_tag_level = None
        self.cur_post_id = None
        self.cur_post_date = None
        self.cur_post_author = None
        self.cur_post_text = []
        self.cur_post_comments = []

        self.comment_list_tag_level = None
        self.comment_list_content_tag_level = None
        self.comment_list_content_author_tag_level = None
        self.comment_list_content_message_tag_level = None
        self.comment_replies_tag_level = None
        self.cur_comment = None

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
                m = self._pttrn_post_id.search(attrib_dict['id'])
                if m and m.group(1):
                    self.cur_post_id = m.group(1)
                    self.post_outer_tag_level = self.cur_tag_level[tag]
                return

            # check if we have an inner post div (contains post message text)
            if self.post_outer_tag_level is not None and self.post_inner_tag_level is None\
                    and '_5pbx' in tag_classes and 'userContent' in tag_classes:
                self.post_inner_tag_level = self.cur_tag_level[tag]

            # check if we have a comment list
            if self.post_outer_tag_level is not None and 'UFIList' in tag_classes:
                self.comment_list_tag_level = self.cur_tag_level[tag]
                self.cur_post_comments = []

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
            if self.post_author_tag_level is not None and self.post_author_tag_level == self.cur_tag_level[tag]:
                self.post_author_tag_level = None
        elif tag == 'a':
            # check comment author:
            if self.comment_list_content_author_tag_level is not None and self.comment_list_content_author_tag_level == self.cur_tag_level[tag]:
                self.comment_list_content_author_tag_level = None
        elif tag == 'span':
            # check comment message:
            if self.comment_list_content_message_tag_level is not None and self.comment_list_content_message_tag_level == self.cur_tag_level[tag]:
                self.comment_list_content_message_tag_level = None
        elif tag == 'div':
            # check inner post tag
            if self.post_inner_tag_level is not None and self.post_inner_tag_level == self.cur_tag_level[tag]:
                self.post_inner_tag_level = None

            # check comment list
            if self.comment_list_tag_level is not None and self.comment_list_tag_level == self.cur_tag_level[tag]:
                self.comment_list_tag_level = None

            # check comment content
            if self.comment_list_content_tag_level is not None and self.comment_list_content_tag_level == self.cur_tag_level[tag]:
                assert self.cur_comment
                self.comment_list_content_tag_level = None
                self.cur_post_comments.append(self.cur_comment)
                self.cur_comment = None     # reset

            # check outer post tag
            if self.post_outer_tag_level is not None and self.post_outer_tag_level == self.cur_tag_level[tag]:
                self.post_outer_tag_level = None

                post_data = {
                    'id': self.cur_post_id,
                    'date': self.cur_post_date,
                    'from': self.cur_post_author,
                    'message': u'\n'.join(self.cur_post_text),
                    'comments': self.cur_post_comments
                }
                self.callback_found_post(post_data)
                self.cur_post_text = []  # reset
                self.cur_post_comments = []
                self.cur_post_id = None     # reset

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
                'message': None,
                'comments': []
            }

        if self.comment_list_content_message_tag_level is not None:
            assert self.cur_comment
            self.cur_comment['message'] = data


class FbHTMLParserBase(HTMLParser):
    def __init__(self, callback_target_tag_began=None, callback_target_tag_ended=None):
        HTMLParser.__init__(self)
        self.target_tag = None
        self.target_tag_level = 0
        self.target_attr_name = None
        self.target_attr_val = None
        self.target_attr_val_startswith = False
        self.got_target_level = None
        self.callback_target_tag_began = callback_target_tag_began
        self.callback_target_tag_ended = callback_target_tag_ended

    def handle_starttag(self, tag, attrs):
        assert self.target_tag is not None

        if self.target_attr_name is None:
            attr_matches = True
        else:
            if self.target_attr_val_startswith:
                attr_matches = any([a_name == self.target_attr_name and a_val.startswith(self.target_attr_val)
                                    for a_name, a_val in attrs])
            else:
                attr_matches = any([a_name == self.target_attr_name and a_val == self.target_attr_val
                                    for a_name, a_val in attrs])

        if tag == self.target_tag:
            self.target_tag_level += 1
            if self.target_tag_level is not None and attr_matches:
                self.got_target_level = self.target_tag_level
                if self.callback_target_tag_began:
                    self.callback_target_tag_began(tag, attrs)
    
    def handle_endtag(self, tag):
        assert self.target_tag is not None

        if tag == self.target_tag and self.target_tag_level > 0:
            self.target_tag_level -= 1

            if self.got_target_level is not None and self.target_tag_level == self.got_target_level:
                if self.callback_target_tag_ended:
                    self.callback_target_tag_ended()
                self.got_target_level = None


class FbHTMLParserFindComment(FbHTMLParserBase):
    _pttrn_json_arg = re.compile('bigPipe.onPageletArrive\((.+)\);\n\},\s"onPageletArrive', re.MULTILINE | re.DOTALL)

    def __init__(self, callback_found_comment):
        FbHTMLParserBase.__init__(self)
        self.callback_found_comment = callback_found_comment
        self.target_tag = 'script'
        self.comment_data = {}

    def handle_data(self, data):
        req_profile_attrs = ('id', 'name')
        req_comment_attrs = ('ftentidentifier', 'body', 'timestamp', 'author')

        if self.got_target_level is not None:
            if not data.startswith('require("TimeSlice").guard(function () {'):
                return
            m = self._pttrn_json_arg.search(data)
            if m and m.group(1):
                arg_dict = json.loads(m.group(1), encoding='utf-8')
                if not 'jsmods' in arg_dict or not 'instances' in arg_dict['jsmods']:
                    return

                profiles = {}
                comments = []

                for instance_arr in arg_dict['jsmods']['instances']:
                    for some_list in instance_arr:
                        if type(some_list) == list:
                            for some_obj_in_some_list in some_list:
                                if type(some_obj_in_some_list) == dict:
                                    if 'profiles' in some_obj_in_some_list:
                                        for pdata in some_obj_in_some_list['profiles']:
                                            if any(k not in pdata for k in req_profile_attrs):
                                                continue
                                            profiles[pdata['id']] = pdata['name']

                                    if 'comments' in some_obj_in_some_list:
                                        for cdata in some_obj_in_some_list['comments']:
                                            if any(k not in cdata for k in req_comment_attrs):
                                                continue
                                            post_id = cdata['ftentidentifier']
                                            msg = cdata['body'].get('text')
                                            ts = cdata['timestamp'].get('time')

                                            if not any((post_id, msg, ts)):
                                                continue

                                            comment = {
                                                'post_id': post_id,
                                                'author_id': cdata['author'],
                                                'date': datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
                                                'from': None,
                                                'message': msg
                                            }

                                            comments.append(comment)

                for c in comments:
                    c_out = copy(c)
                    c_out['from'] = profiles.get(c['author_id'])
                    del c_out['author_id']

                    self.callback_found_comment(c_out)


class FbParser(object):
    def __init__(self):
        self.find_post_parser = FbHTMLParserFindPost(self.found_post_callback)
        self.posts = []

    def parse(self, html):
        self.find_post_parser.feed(html)

        pprint(self.posts)

    def found_post_callback(self, post):
        self.posts.append(post)


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



def parse_html_file(html_file):
    print("> parsing HTML file '%s'..." % html_file)

    parser = FbParser()
    with codecs.open(html_file, 'r', 'utf-8') as f:
        html_content = f.read()
        parser.parse(html_content)


if __name__ == '__main__':
    main()