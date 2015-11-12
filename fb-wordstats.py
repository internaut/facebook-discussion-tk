# -*- coding: utf-8 -*-
from __future__ import print_function
import sys

from pattern.text.de import split, parse
from libleipzig import Baseform
from suds import WebFault

LIBLEIPZIG_FOR_LEMMATA = True

text = u"""Eine Katze liegt auf einer Matte. Viele Katzen liegen auf vielen Matten. Die Katzen schlafen,
die Matten nicht. Die Hunde schlafen auch nicht. Man hört ihr lautes Gebell draußen vor dem Haus. In
vielen Häusern schlafen viele Katzen. Häuser haben Türen."""

parsed_text = parse(text, lemmata=True)


def lemma_and_type_from_leipzig(word):
    try:
        base = Baseform(word)
        if base and base[0].Grundform:
            return base[0].Grundform.lower(), base[0].Wortart
        else:
            return None, None
    except WebFault:
        print('WebFault while using libleipzig', file=sys.stderr)
        return None, None

nouns = {}
for sentence in split(parsed_text):
    print('SENTENCE: %s' % sentence)
    for w in sentence.words:
        print('> WORD: %s' % w)
        if w.type.startswith('NN') and w.string:
            l = None
            came_from_leipzig = False
            if LIBLEIPZIG_FOR_LEMMATA:
                l, wordtype = lemma_and_type_from_leipzig(w.string)
                if l and wordtype:
                    if wordtype != 'N':  # libleipzig has other opinion than pattern.de: this is no noun
                        print('>> libleipzig: no noun')
                        continue
                    came_from_leipzig = True
            if not l:
                l = w.lemma or w.string
                came_from_leipzig = False
            print('>> NOUN: %s (%s, %s)' % (w.string,  l, came_from_leipzig))
            if l not in nouns:
                nouns[l] = 0
            nouns[l] += 1

print('---')
sorted_nouns = sorted(nouns.items(), key=lambda item: item[1], reverse=True)
for lemma, count in sorted_nouns:
    print('%s:\t\t%d' % (lemma, count))

