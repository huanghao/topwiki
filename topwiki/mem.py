import os
import hashlib
import urllib2
import logging


logger = logging.getLogger('crawler.mylib.mem')


class DoesNotExist(Exception): pass



class Cache(object):

    def __init__(self, func):
        self.func = func
        self.funcname = func.__name__

    def __call__(self, *args, **kw):
        hash = self.hash(self.funcname, args, kw)
        try:
            return self.query(hash)
        except DoesNotExist:
            data = self.func(*args, **kw)
            self.save(hash, data)
            return data


class StringCache(Cache):

    def __init__(self, func, repo):
        super(StringCache, self).__init__(func)
        self.repo = repo

    def query(self, hash):
        if not os.path.exists(self.path(hash)):
            raise DoesNotExist()
        return open(self.path(hash)).read()

    def save(self, hash, data):
        try:
            with open(self.path(hash), 'w') as f:
                f.write(data)
        except:
            os.unlink(self.path(hash))
            raise

    def hash(self, funcname, args, kw):
        s = funcname + \
            ''.join(map(str, args)) + \
            ''.join([ str(k)+str(v) for k,v in sorted(kw.iteritems(), lambda i,j: cmp(i[0], j[0])) ])
        h = hashlib.md5(s).hexdigest()
        return h

    def path(self, hash):
        return os.path.join(self.repo, hash)


def _GET(url, *args, **kw):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204 Safari/534.16')
    logger.info('urlopen '+url)
    f = urllib2.urlopen(req, *args, **kw)
    return f.read()

#GET = StringCache(Limit(curl, 10, 3, 3), 'cache_wiki')


