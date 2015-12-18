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

        self._observed_tags = ('div', 'abbr', 'h5')

        self.post_outer_tag_level = None
        self.post_author_tag_level = None
        self.post_inner_tag_level = None
        self.cur_post_id = None
        self.cur_post_date = None
        self.cur_post_author = None
        self.cur_tag_level = dict((tag, 0) for tag in self._observed_tags)
        self.post_text = []
        self.callback_found_post = callback_found_post

        self._post_outer_id_startswith = 'mall_post_'
        self._pttrn_post_id = re.compile('^' + self._post_outer_id_startswith + '(\d+)')

    def handle_starttag(self, tag, attrs):
        if tag not in self._observed_tags:
            return

        attrib_dict = dict(attrs)
        self.cur_tag_level[tag] += 1

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
                    and 'class' in attrib_dict and attrib_dict['class'] == '_5pbx userContent':
                self.post_inner_tag_level = self.cur_tag_level[tag]
        elif tag == 'abbr':
            # check if we have a date field
            if self.post_outer_tag_level is not None\
                    and 'class' in attrib_dict and attrib_dict['class'] == '_5ptz'\
                    and 'data-utime' in attrib_dict:
                dt_obj = datetime.fromtimestamp(int(attrib_dict['data-utime']))
                self.cur_post_date = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        elif tag == 'h5':
            # check if we have an author field
            if self.post_outer_tag_level is not None and self.post_author_tag_level is None\
                    and 'class' in attrib_dict and attrib_dict['class'] == '_5pbw':
                self.post_author_tag_level = self.cur_tag_level[tag]

    def handle_endtag(self, tag):
        if tag not in self._observed_tags:
            return

        if tag == 'h5':
            if self.post_author_tag_level is not None and self.post_author_tag_level == self.cur_tag_level[tag]:
                self.post_author_tag_level = None
        elif tag == 'div':
            # check inner post tag
            if self.post_inner_tag_level is not None and self.post_inner_tag_level == self.cur_tag_level[tag]:
                self.post_inner_tag_level = None

                post_data = {
                    'id': self.cur_post_id,
                    'date': self.cur_post_date,
                    'from': self.cur_post_author,
                    'message': u'\n'.join(self.post_text)
                }
                self.callback_found_post(post_data)
                self.post_text = []  # reset

            if self.post_outer_tag_level is not None and self.post_outer_tag_level == self.cur_tag_level[tag]:
                self.post_outer_tag_level = None
                self.cur_post_id = None     # reset

        self.cur_tag_level[tag] -= 1

    def handle_data(self, data):
        if self.post_author_tag_level is not None:
            self.cur_post_author = data

        if self.post_inner_tag_level is not None:
            self.post_text.append(data)


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


class FbHTMLParserFindCodeHiddenElem(FbHTMLParserBase):
    def __init__(self, callback_found_elem_comment):
        FbHTMLParserBase.__init__(self)
        self.callback_found_elem_comment = callback_found_elem_comment
        self.target_tag = 'code'
        self.target_attr_name = 'class'
        self.target_attr_val = 'hidden_elem'

    def handle_comment(self, data):
        if self.got_target_level is not None:
            self.callback_found_elem_comment(data)


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
        self.find_code_hidden_elem_parser = FbHTMLParserFindCodeHiddenElem(self.found_code_hidden_elem_callback)
        self.find_post_parser = FbHTMLParserFindPost(self.found_post_callback)
        self.find_comment_parser = FbHTMLParserFindComment(self.found_comment_callback)

        self.collected_posts = []
        self.collected_comments = []

    def parse(self, html):
        self.find_code_hidden_elem_parser.feed(html)
        self.find_comment_parser.feed(html)

        output = []
        for p in self.collected_posts:
            p_out = copy(p)
            p_out['comments'] = []
            for c in self.collected_comments:
                if c['post_id'] == p['id']:
                    p_out['comments'].append(c)

            output.append(p_out)

        pprint(output)

    def found_code_hidden_elem_callback(self, data):
        single_line_data = data.replace('\n', ' ').replace('\r', '')
        self.find_post_parser.feed(single_line_data)

    def found_post_callback(self, post):
        self.collected_posts.append(post)

    def found_comment_callback(self, comment):
        self.collected_comments.append(comment)


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