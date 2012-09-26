from operator import itemgetter

## {{{ http://code.activestate.com/recipes/276643/ (r1)
class CachedAttribute(object):
    '''Computes attribute value and caches it in instance.

    Example:
        class MyClass(object):
            def myMethod(self):
                # ...
            myMethod = CachedAttribute(myMethod)
    Use "del inst.myMethod" to clear cache.'''

    def __init__(self, method, name=None):
        self.method = method
        self.name = name or method.__name__

    def __get__(self, inst, cls):
        if inst is None:
            return self
        result = self.method(inst)
        setattr(inst, self.name, result)
        return result


class NiceList(list):

    first = property(itemgetter(0))
    second = property(itemgetter(1))
    third = property(itemgetter(2))
    fourth = property(itemgetter(3))
    fifth = property(itemgetter(4))
    sixth = property(itemgetter(5))

    rest = property(itemgetter(slice(1, None)))