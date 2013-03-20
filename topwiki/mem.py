import os


def wget(url):
    '''fetch url page, if it's cached, return the cached version
    '''
    cache = Cache(url)
    if not cache.is_cached():
        path = os.path.abspath(cache.key)
        _wget(url, path)
    return cache.get()


class Cache(object):
    '''file cache contained in {rootdir}.
    cache key is the relative path to {rootdir}
    just remove file to clean cache
    '''

    rootdir = 'cache'

    def __init__(self, url):
        self.key = os.path.join(self.rootdir, url2path(url))

    def is_cached(self):
        return os.path.exists(self.key)

    def get(self):
        with open(self.key) as fp:
            return fp.read()


def url2path(url):
    pos = url.find('://')
    return url[pos+3:] if pos > 0 else url


def _wget(url, outpath):
    '''wget url and save into outpath'''
    cmd = "mkdir -p '%s'; wget -nv '%s' -O '%s'" % \
        (os.path.dirname(outpath), url, outpath)
    os.system(cmd)
