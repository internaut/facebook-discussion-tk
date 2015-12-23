# -*- coding: utf-8 -*-
from __future__ import print_function
from collections import defaultdict
import sys
import time

from pattern.text.de import split, parse
from libleipzig import Baseform
from suds import WebFault

LIBLEIPZIG_FOR_LEMMATA = True
LIBLEIPZIG_FAIL_RETRIES = 10
LIBLEIPZIG_FAIL_RETRIES_SLEEP_SEC = 1

STRINGS_STARTWITH_BLACKLIST = ()
STRINGS_EQUALS_BLACKLIST = ()
STRINGS_EQUALS_CS_BLACKLIST = ()    # case sensitive

# text = u"""Eine Katze liegt auf einer Matte. Viele Katzen liegen auf vielen Matten. Die Katzen schlafen,
# die Matten nicht. Die Hunde schlafen auch nicht. Man hört ihr lautes Gebell draußen vor dem Haus. In
# vielen Häusern schlafen viele Katzen. Häuser haben Türen."""


def lemma_and_type_from_leipzig(word):
    base = Baseform(word)
    if base and base[0].Grundform:
        return base[0].Grundform.lower(), base[0].Wortart
    else:
        return None, None


def count_nouns_in_text(text):
    parsed_text = parse(text, lemmata=True)

    nouns = defaultdict(int)
    for sentence in split(parsed_text):
        # print('SENTENCE: %s' % sentence)
        for w_i, w in enumerate(sentence.words):
            # print('> WORD: %s (%s)' % (w, w.string))
            if w.string and len(w.string) > 1 \
                    and w.string.lower() not in STRINGS_EQUALS_BLACKLIST \
                    and w.string not in STRINGS_EQUALS_CS_BLACKLIST \
                    and not any([w.string.lower().startswith(bl_word) for bl_word in STRINGS_STARTWITH_BLACKLIST]) \
                    and (w.type.startswith('NN') or (LIBLEIPZIG_FOR_LEMMATA and w_i > 0 and w.string[0].isupper())):
                l = None
                came_from_leipzig = False
                if LIBLEIPZIG_FOR_LEMMATA:
                    libleipzig_err = True
                    libleipzig_retries = 0
                    while libleipzig_err and libleipzig_retries <= LIBLEIPZIG_FAIL_RETRIES:
                        try:
                            l, wordtype = lemma_and_type_from_leipzig(w.string)
                            libleipzig_err = False
                        except WebFault:
                            print('WebFault while using libleipzig (retry %d)' % libleipzig_retries, file=sys.stderr)
                            libleipzig_retries += 1
                            time.sleep(LIBLEIPZIG_FAIL_RETRIES_SLEEP_SEC)

                    if l and wordtype:
                        if wordtype != 'N':  # libleipzig says this is no noun
                            # print('>> libleipzig: no noun')
                            continue
                        came_from_leipzig = True
                    else:
                        # print('>> libleipzig: undetermined')
                        pass
                if not l:
                    l = w.lemma or w.string
                    came_from_leipzig = False
                # print('>> NOUN: %s (%s, %s)' % (w.string,  l, came_from_leipzig))

                nouns[l] += 1

    # print('---')
    # sorted_nouns = sorted(nouns.items(), key=lambda item: item[1], reverse=True)
    # for lemma, count in sorted_nouns:
    #     print('%s:\t\t%d' % (lemma, count))

    return nouns
