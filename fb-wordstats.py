# -*- coding: utf-8 -*-

from pattern.text.de import split, parse

text = u"""Eine Katze liegt auf einer Matte. Viele Katzen liegen auf vielen Matten. Die Katzen schlafen,
die Matten nicht. Die Hunde schlafen auch nicht. Man hört ihr lautes Gebell draußen vor dem Haus. In
vielen Häusern schlafen viele Katzen. Häuser haben Türen."""

parsed_text = parse(text, lemmata=True)

nouns = {}
for sentence in split(parsed_text):
    print('SENTENCE: %s' % sentence)
    for w in sentence.words:
        print('> WORD: %s' % w)
        if w.type.startswith('NN'):
            l = w.lemma or w.string
            print('>> NOUN: %s (%s)' % (w.string,  l))
            if l not in nouns:
                nouns[l] = 0
            nouns[l] += 1

print('---')
sorted_nouns = sorted(nouns.items(), key=lambda item: item[1], reverse=True)
for lemma, count in sorted_nouns:
    print('%s:\t\t%d' % (lemma, count))
