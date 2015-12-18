#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import codecs
import re
import json
from copy import copy
from datetime import datetime
from HTMLParser import HTMLParser


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


class FbHTMLParserFindPostID(FbHTMLParserBase):
    def __init__(self, callback_found_post_id):
        FbHTMLParserBase.__init__(self, callback_target_tag_began=self._post_id_tag_began)
        self.target_tag = 'div'
        self.target_attr_name = 'id'
        self.target_attr_val = 'mall_post_'
        self._pttrn_post_id = re.compile('^' + self.target_attr_val + '(\d+)')
        self.target_attr_val_startswith = True
        self.callback_found_post_id = callback_found_post_id

    def _post_id_tag_began(self, tag, attrs):
        attrib_dict = dict(attrs)
        assert 'id' in attrib_dict
        m = self._pttrn_post_id.search(attrib_dict['id'])
        if m and m.group(1):
            self.callback_found_post_id(m.group(1))


class FbHTMLParserFindPost(FbHTMLParserBase):
    def __init__(self, callback_found_post):
        FbHTMLParserBase.__init__(self, callback_target_tag_ended=self._post_tag_ended)
        self.callback_found_post = callback_found_post
        self.target_tag = 'div'
        self.target_attr_name = 'class'
        self.target_attr_val = '_5pbx userContent'
        self.post_text = []

    def _post_tag_ended(self):
        self.callback_found_post(self.post_text)
        self.post_text = []     # reset

    def handle_data(self, data):
        if self.got_target_level is not None:
            self.post_text.append(data)


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

                    # post_id = c['post_id']
                    # if post_id not in comments:
                    #     comments[post_id] = []
                    # comments[post_id].append(c_out)


class FbParser(object):
    def __init__(self):
        self.find_code_hidden_elem_parser = FbHTMLParserFindCodeHiddenElem(self.found_code_hidden_elem_callback)
        self.find_post_id_parser = FbHTMLParserFindPostID(self.found_post_id_callback)
        self.find_post_parser = FbHTMLParserFindPost(self.found_post_callback)
        self.find_comment_parser = FbHTMLParserFindComment(self.found_comment_callback)

        self.post_ids = []
        self.posts = []
        self.cur_post_num = 0

    def parse(self, html):
        self.find_code_hidden_elem_parser.feed(html)
        self.find_comment_parser.feed(html)

        print(len(self.post_ids), len(self.posts))

    def found_code_hidden_elem_callback(self, data):
        single_line_data = data.replace('\n', ' ').replace('\r', '')
        self.find_post_id_parser.feed(single_line_data)
        self.find_post_parser.feed(single_line_data)

    def found_post_id_callback(self, post_id):
        self.post_ids.append(post_id)

    def found_post_callback(self, post):
        #print('POST %d: ' % self.post_ids[self.cur_post_num], data)
        self.posts.append(post)
        self.cur_post_num += 1

    def found_comment_callback(self, data):
        pass
        # print('COMMENT:', data)


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