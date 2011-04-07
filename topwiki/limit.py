#coding: utf8

import time
import unittest
import logging


logger = logging.getLogger('crawler.mylib.limit')


class Limit(object):

    def __init__(self, obj_or_func, seconds, maxn, interval=None):
        '''
        在seconds秒内，最对可以调用maxn次，且每次之间的间隔时间不小于interval。
        '''
        self.obj_or_func = obj_or_func
        self.seconds = seconds
        self.maxn = maxn
        self.interval = interval
        self.hist = []

        if hasattr(self.obj_or_func, '__name__'):
            n = self.obj_or_func.__name__
        elif hasattr(self.obj_or_func, '__class__'):
            n = self.obj_or_func.__class__.__name__
        else:
            n = 'anonym'
        self.name = n

    def check(self):
        def sleep(t):
            logger.info('%s exceed limit: go to sleep for %.1f seconds'%(self.name, t))
            time.sleep(t)

        now = time.time()
        hist = [ i for i in self.hist if i>=now-self.seconds ]
        if self.interval and hist:
            last = hist[-1]
            t = now-last-self.interval
            if t<0:
                sleep(abs(t))
                now = time.time()

        if len(hist) >= self.maxn:
            t = hist[0]+self.seconds-now
            if t>0:
                sleep(t)
        self.hist = hist+[time.time()]

    def __getattr__(self, name):
        self.check()
        return object.__getattribute__(self.obj_or_func, name)

    def __call__(self, *args, **kw):
        self.check()
        return self.obj_or_func(*args, **kw)


class LimitTest(unittest.TestCase):
    def setUp(self):
        self.obj = {}
        self.func = lambda:0

    def test_obj1(self):
        l = Limit(self.obj, .1, 2)
        t1 = time.time()
        for i in range(1):
            l.keys
        self.assertTrue(time.time()-t1<.1)

    def test_obj2(self):
        l = Limit(self.obj, .1, 2)
        t1 = time.time()
        for i in range(3):
            l.keys
        self.assertTrue(time.time()-t1>.1)

    def test_obj3(self):
        l = Limit(self.obj, .1, 2)
        t1 = time.time()
        for i in range(5):
            l.keys
        self.assertTrue(time.time()-t1>.2)

    def test_func(self):
        l = Limit(self.func, .1, 2)
        t1 = time.time()
        for i in range(3):
            l()
        self.assertTrue(time.time()-t1>.1)

    def test_interval(self):
        l = Limit(self.func, .1, 2, .07)
        t1 = time.time()
        for i in range(2):
            l()
        self.assertTrue(.1>time.time()-t1>.07)


if __name__ == '__main__':
    unittest.main()
