from fnmatch import fnmatch, filter
from random import randint
from time import time

print "Creating random data..."
a = {}
for _ in xrange(2000):
    x = "".join([ chr(randint(0, 128)) for _ in xrange(1000) ])
    a[x] = x

print "Benchmarking fnmatch and filter..."
t1 = time()
b = { k:v for k,v in a.iteritems() if fnmatch(k, "*") }
t2 = time()
c = { k:a[k] for k in filter(a.iterkeys(), "*") }
t3 = time()

print "Using fnmatch: %f seconds" % (t2 - t1)
print "Using filter:  %f seconds" % (t3 - t2)
