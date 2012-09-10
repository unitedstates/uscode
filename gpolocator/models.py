import re
import itertools
from collections import namedtuple

from .utils import CachedAttribute
from .schemes import Enum


class DataQualityError(Exception):
    pass


class Registry(type):

    _classes = {}

    def __new__(meta, name, bases, attrs):
        cls = type.__new__(meta, name, bases, attrs)
        if 'applies_to' in attrs:
            meta._classes[attrs['applies_to']] = cls
        return cls


getclass = Registry._classes.get


def _subdoc_generator(key1, key2=('I', '21')):
    if key2 is None:
        key2 = key1

    def func(self):
        for doc in self.data.docs.get(key1, []):
            for line in doc.codemap[key2]:
                yield line
    return func


def jsonval(*funcs):
    '''Decorator to mark functions for
    inclusion in json conversion. *funcs is a
    list of functions to run the value through
    before it gets added to the json--i.e.,
    list for an iterator or generator.
    '''
    def decorator(f):
        f.jsonval = True
        f.jsonval_funcs = funcs
        return f

    return decorator


class Base(object):

    __metaclass__ = Registry

    class meta:
        abstract = True

    def __init__(self, data):
        self.data = data

    @property
    def codemap(self):
        return self.data['codemap']

    def json(self):
        res = {}
        for attr in dir(self):
            method = getattr(self, attr)
            if hasattr(method, 'jsonval') and method.jsonval:
                value = method()
                for func in filter(callable, method.jsonval_funcs):
                    value = func(value)
                res[attr] = value
        return res

    def extract_footnote_refs(self, text):
        '''If any footnotes[^2] are in `text`, return
        a sequence of number, offset pairs.
        '''
        for matchobj in re.finditer(r'\\(\d+)\\\x07N', text):
            offset = matchobj.start()
            number = matchobj.group(1)
            yield number, offset

    def parse_footenote_content(self, text):
        '''Given text constituting a footnote ("[^2] So in original.")
        return the footnote number and the text.
        '''
        matchobj = re.match(r'^\x07N\\(\d+)\\\s+', text)
        if matchobj:
            number = matchobj.group(1)
            text = text.replace(matchobj.group(), '', 1)
            return number, text

    def get_notes(self):
        notes = self.data['docs'][('I', '93')][0]['codemap'][('I', '28')]
        for line in notes:
            yield self.parse_footenote_content(line.data)


class Title(Base):

    applies_to = ('F', '5800')

    @CachedAttribute
    def enum_title(self):
        line = self.codemap[('I', '06')].first
        m = re.search(r'\w+ (\d+).(.+)', line.data.strip())
        if m:
            return m.groups()
        else:
            msg = 'unexpected format: %r'
            raise DataQualityError(msg % line.data)

    @jsonval()
    def enum(self):
        return self.enum_title[0]

    @jsonval()
    def name(self):
        return self.enum_title[1]


class TitleTOC(Base):
    '''Table of contents for a title. This model assumes
    a 2-column layout. See Title 8 for an example.
    '''
    applies_to = ('R', '01')

    repeals = _subdoc_generator('Repeals')
    positive_law = _subdoc_generator('Positive Law; Citation')
    census = _subdoc_generator('References To Census Office')
    separability = _subdoc_generator('Separability')
    construction = _subdoc_generator('Legislative Construction')
    effective_date = _subdoc_generator('Effective Date')

    @jsonval(list)
    def items(self, toc=namedtuple('TitleTocRow', 'chapter name section')):
        '''Returns a sequence of 4-tuples like
        (chapter, name, section, notes).
        '''

        lines = self.data['docs'][('I', '93')][0]['lines']
        lines = iter(lines[3:])
        footnote_dict = dict(self.get_notes())
        while True:
            try:
                chapter, name, section = list(itertools.islice(lines, 3))
            except ValueError:
                return

            for obj in chapter, name, section:
                obj._footnote_dict = footnote_dict

            chapter = re.sub(r'[.\s]+', '', chapter.data)
            name = name.data.strip()
            section = section.data.strip()

            yield toc(chapter, name, section)


class ChapterHeading(Base):
    '''Heading element for a chapter.
    '''
    applies_to = ('R', '10')

    amendments = _subdoc_generator('Amendments')

    @CachedAttribute
    def enum_title(self):
        line = self.codemap[('I', '81')].first
        text = line.data.strip()
        text = re.sub(r'^\x07T2', '', text)
        m = re.search(r'\w+ (\d+).(.+)', text)
        if m:
            return m.groups()
        else:
            msg = 'unexpected format: %r'
            raise DataQualityError(msg % line.data)

    @jsonval()
    def enum(self):
        return self.enum_title[0]

    @jsonval()
    def name(self):
        return self.enum_title[1]

    def toc_items(self, toc=namedtuple('ChapterTocRow', 'section name')):
        lines = self.data.docs[('I', '70')].first.lines.rest
        lines = iter(lines)
        while True:
            try:
                section, name = list(itertools.islice(lines, 2))
            except ValueError:
                return
            section = re.sub(r'[.\s]+', '', section.data)
            name = name.data.strip()
            yield toc(section, name)


class Section(Base):
    applies_to = ('I', '80')

    def enum(self):
        _, id_ = self.codemap[('I', '80')].first.data.split(' ', 1)
        return id_.strip()

    history = _subdoc_generator(('I', '53'), ('I', '53'))
    amendments = _subdoc_generator('Amendments')
    derivation = _subdoc_generator('Derivation')
    refs = _subdoc_generator('References In Text')
    codification = _subdoc_generator('Codification')

    def name(self):
        name = self.data.docs[('I', '89')].first.lines.first
        return re.sub(r'^[\s.]+', '', name.data).strip()

    def body_lines(self):

        # Test some assumptions...
        assert len(self.data.docs[('I', '89')]) == 1

        lines = self.data.docs[('I', '89')].first.lines.rest
        for line in lines:
            if line.code != 'I':
                continue
            text = line.data
            if not text.startswith('('):
                body = text
                enum = None
                yield (enum, body, line)
            else:
                enum_text, body = re.split(r'\s+', text, 1)
                enums = re.findall(r'\((\S+?)\)', enum_text)
                enums = map(Enum, enums)
                for enum in enums[1:]:
                    enum._was_nested = True

                # In the case of "(B)(i)(1) blah blah" yield data like:
                #  (B, None, None)
                #  (i, None, None)
                #  (1, blah blah, GPOLocatorCode(...))
                enums = enums[::-1]
                while enums:
                    enum = enums.pop()
                    if not enums:
                        yield (enum, body, line)
                    else:
                        yield (enum, None, None)

    def misc(self):
        ignored = '''Amendments, Derivation, References In Text,
                     Codification'''
        ignored = re.split(r'[,\s+]+', ignored)
        print set(self.data.docs) - set(ignored)
        for k in set(self.data.docs) - set(ignored):
            if isinstance(k, basestring):
                yield k, list(_subdoc_generator(k)(self))
