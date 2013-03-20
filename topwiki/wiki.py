import re
import os
import sys
import argparse
import itertools
from heapq import heappush, heappop
from BeautifulSoup import BeautifulSoup as BS

from mem import wget

'''
TODO:
step by step interactive
manually prune
continue to run base on previous state
'''

def info(msg):
    print >> sys.stderr, msg

VERBOSE = 0
def debug(msg):
    if VERBOSE > 1:
        print >> sys.stderr, msg


WIKI_BASE = 'http://en.wikipedia.org'
def wiki_join(tagid):
    return WIKI_BASE +tagid

def wiki_text(url):
    return os.path.basename(url)


IMPORTANCE_SEEALSO = 200
IMPORTANCE_OCCUR = 1

class Tag(object):
    '''A tag represents a wiki url and corresponding info such as importance,
    frequency, depth which are used to calculate weight of this page.
    '''

    def __init__(self, url,
                 importance=IMPORTANCE_SEEALSO/2,
                 depth=0,
                 text=None,
                 frequency=1):
        '''
        '''

        self.url = url
        self.importance = importance
        self.frequency = frequency
        self.depth = depth
        self._doc = None
        self.visited = False
        self.text = text if text else wiki_text(url)
        self.excluded = False

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, that):
        return hash(self) == hash(that)

    def iter_doc(self):
        if self._doc is None:
            self._doc =Doc(wget(self.url), self.depth)
        return self._doc

    @property
    def weight(self):
        return float(self.frequency + self.importance) / (self.depth + 1)

    def __str__(self):
        buf = '(%s, %.1f, %s+%s/%s)' % (self.text,
                                        self.weight,
                                        self.frequency,
                                        self.importance,
                                        self.depth)
        return buf.encode('utf8')

    def update(self, that):
        if self == that:
            self.frequency += that.frequency
            self.importance += that.importance
            self.depth = min(self.depth, that.depth)
            self.visited = self.visited or that.visited
        return self


class Doc(object):

    LOCAL = re.compile('^/wiki/')

    def __init__(self, html, depth):
        self.html = html
        self.depth = depth + 1

    def __iter__(self):
        dom = BS(self.html)
        content = dom.find(id='content')
        if content:
            for a in content.findAll('a', href=self.LOCAL):
                href = a['href']
                text = a.string
                if href and text:
                    yield Tag(wiki_join(href),
                              IMPORTANCE_OCCUR,
                              self.depth,
                              text)

            see = content.find(id='See_also')
            if see:
                tab = see.parent.findNext('table')
                if tab:
                    for a in tab.findAll('a', href=self.LOCAL):
                        href = a['href']
                        text = a.string
                        if href and text:
                            yield Tag(wiki_join(href),
                                      IMPORTANCE_SEEALSO,
                                      self.depth,
                                      text)


class Queue(object):

    counter = itertools.count(1)

    def __init__(self):
        self.pq = []
        self.cnt2entry = {}
        self.tag2cnt = {}

    def push(self, tag):
        if tag.url in self.tag2cnt:
            self.cnt2entry[self.tag2cnt[tag.url]][2] = False

        cnt = next(self.counter)
        entry = [-tag.weight, cnt, True, tag]
        self.tag2cnt[tag.url] = cnt
        self.cnt2entry[cnt] = entry

        heappush(self.pq, entry)

    def pop(self):
        while self.pq:
            _priority, cnt, valid, tag = heappop(self.pq)
            del self.cnt2entry[cnt]
            if valid and tag.weight >= 1:
                return tag


class Cloud(object):

    def __init__(self, tags=(), excluding=None):
        self.queue = Queue()
        self.repo = {}
        for tag in tags:
            self.push(tag)
        self.excluding = excluding if excluding else ()

    def push(self, tag):
        if tag.url in self.repo:
            self.repo[tag.url].update(tag)
            tag = self.repo[tag.url]
        else:
            self.repo[tag.url] = tag

        if not tag.visited:
            self.queue.push(tag)

    def pop(self):
        tag = self.queue.pop()
        if tag:
            self.repo[tag.url].visited = True
            return tag

    def start(self, n):
        i = 0
        while i < n:
            tag = self.pop()
            debug('pop: %s' % tag)

            if not tag: # queue empty
                break

            if i > 0:
                # exclude matched tag but not the first one which is given by
                # user from command line
                for ex in self.excluding:
                    if ex.match(tag.text):
                        debug('skip: %s' % tag)
                        tag.excluded = 1
                        break

                if tag.excluded:
                    continue

            i += 1
            info('tag: %s' % tag.text)
            for tagi in tag.iter_doc():
                debug('put: %s' % tagi)
                self.push(tagi)

    def write_tags(self, fp):
        for tag in self.repo.itervalues():
            if tag.visited and not tag.excluded:
                print >> fp, '|'.join([str(tag.weight),
                                       tag.text,
                                       tag.url,
                                       ])


class ExcludePattern(object):

    def __init__(self, pattern):
        self._pattern_string = pattern
        self.pattern = re.compile('^'+pattern+'$')

    def match(self, string):
        return self.pattern.match(string)


def main():
    args = parse_args()
    global VERBOSE
    VERBOSE = args.verbose

    #genesis = Tag('/wiki/Yacc', 'yacc', 0, IMPORTANCE_SEEALSO/2, 0)
    #genesis = Tag('/wiki/Formal_language', 'Formal_language', 0, IMPORTANCE_SEEALSO/2, 0)
    #genesis = Tag('/wiki/Automata_theory', 'Automata_theory', 0, IMPORTANCE_SEEALSO/2, 0)
    #genesis = Tag('/wiki/Turing_machine', 'Turing_machine', 0, IMPORTANCE_SEEALSO/2, 0)

    cloud = Cloud([Tag(args.seed)], args.exclude)
    cloud.start(args.topn)

    if args.output_file:
        with open(args.output_file, 'w') as fp:
            cloud.write_tags(fp)
    else:
        cloud.write_tags(sys.stdout)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('seed')
    parser.add_argument('topn', default=10, type=int)
    parser.add_argument('-e', '--exclude', action='append', type=ExcludePattern)
    parser.add_argument('-v', '--verbose', action='count')
    parser.add_argument('-o', '--output-file')
    return parser.parse_args()


if __name__ == '__main__':
    main()
