import re
import sys
import os
import getopt
import cPickle
import urllib2
import urllib
import itertools
from heapq import heappush, heappop
import logging.config
import logging
from BeautifulSoup import BeautifulSoup as BS

from mem import StringCache
from limit import Limit


logger = logging.getLogger('crawler.wiki')


def curl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204 Safari/534.16')
    logger.info('urlopen '+url)
    f = urllib2.urlopen(req)
    return f.read()

GET = StringCache(Limit(curl, 60, 3, 20), 'cache_wiki')


def wiki_join(tagid):
    return 'http://en.wikipedia.org'+tagid




SEEALSO = 200
OCCUR = 1

class Tag(object):

    def __init__(self, id, text, frequence, importance, depth):
        self.id = id
        self.url = wiki_join(self.id)
        self.frequence = frequence
        self.importance = importance
        self.depth = depth
        self._doc = None
        self.visited = False

    def __hash__(self):
        return self.id

    @property
    def doc(self):
        if self._doc is None:
            self._doc =Doc(GET(self.url), self.depth)
        return self._doc

    @property
    def weight(self):
        return (self.frequence + self.importance + 1.) / (self.depth + 1.)

    def __str__(self):
        return '(%s, %.1f, %d+%d/%d)' % (self.id, self.weight, self.frequence, self.importance, self.depth)

    def __iadd__(self, r):
        if self.id == r.id:
            self.frequence += r.frequence
            self.importance += r.importance
            self.depth = min(self.depth, r.depth)
            self.visited = self.visited or r.visited
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
                    yield Tag(href, text, OCCUR, 0, self.depth)

            see = content.find(id='See_also')
            if see:
                ul = see.parent.findNextSibling('ul')
                if ul:
                    for a in ul.findAll('a', href=self.LOCAL):
                        href = a['href']
                        text = a.string
                        if href and text:
                            yield Tag(href, text, 0, SEEALSO, self.depth)


class Queue(object):

    counter = itertools.count(1)

    def __init__(self):
        self.pq = []
        self.cnt2entry = {}
        self.tag2cnt = {}

    def push(self, tag):
        if tag.id in self.tag2cnt:
            self.cnt2entry[self.tag2cnt[tag.id]][2] = False

        cnt = next(self.counter)
        entry = [-tag.weight, cnt, True, tag]
        self.tag2cnt[tag.id] = cnt
        self.cnt2entry[cnt] = entry

        heappush(self.pq, entry)

    def pop(self):
        while self.pq:
            priority, cnt, valid, tag = heappop(self.pq)
            del self.cnt2entry[cnt]
            if valid and tag.weight >= 1:
                return tag


class Cloud(object):

    def __init__(self, tags=[]):
        self.queue = Queue()
        self.repo = {}
        if tags:
            map(self.push, tags)

    def push(self, tag):
        if tag.id in self.repo:
            self.repo[tag.id] += tag
            tag = self.repo[tag.id]
        else:
            self.repo[tag.id] = tag

        if not tag.visited:
            self.queue.push(tag)

    def pop(self):
        tag = self.queue.pop()
        self.repo[tag.id].visited = True
        return tag

    def round(self):
        tag = self.pop()
        logger.info('fetch '+str(tag))
        for t in tag.doc:
            logger.debug('add '+str(t))
            self.push(t)

    def start(self, n):
        for _ in range(n):
            self.round()

    def print_tags(self):
        for id, tag in self.repo.iteritems():
            if tag.visited:
                text = urllib.unquote(id)[len('/wiki/'):].replace('_', ' ').encode('utf8')
                print '|'.join([str(tag.weight), text, tag.url.encode('utf8')])


def main(n):
    genesis = Tag('/wiki/Yacc', 'yacc', 0, SEEALSO/2, 0)
    cloud = Cloud([genesis])
    cloud.start(n)
    cloud.print_tags()


if __name__ == '__main__':
    logging.config.fileConfig('logging.conf')

    opts, args = getopt.getopt(sys.argv[1:], 'l:')
    for opt, val in opts:
        if opt == '-l':
            logging.getLogger('crawler').setLevel({'d': logging.DEBUG,
                                                   'i': logging.INFO,
                                                   'e': logging.ERROR,
                                                   }[val])
    n = int(args[0])

    main(n)
    sys.exit(0)
