'''
Convert the experimental US Code XML files to json.

Usage:  

xml2json.py [path to xml files] [where to write json files]
'''

from os.path import join, expanduser
import re
from collections import defaultdict
from itertools import count
import json

from lxml import etree
import pdb



def _gettext(element, text_only=True):
    '''
    Extract text from this element, any child elements, and the tail.
    '''
    tag = element.tag

    if tag == 'quote':
        yield '"%s"' % element.text
    elif tag == 'italic':
        yield '<em>%s</em>' % element.text
    else:
        yield element.text

    for child in element.getchildren():
        if text_only:
            quote_or_text = (child.tag in ('text', 'quote', 'date', 'italic'))
            if quote_or_text:
                for t in _gettext(child):
                    yield t

    tail = element.tail
    if tail and tail.strip():
        yield tail


def gettext(element, text_only=True, join=''.join):
    return join(filter(None, _gettext(element, text_only))).strip()
    

        
#----------------------------------------------------------------------------
#


class Node(object):

    def __init__(self, element):
        self.element = element
        self.find = element.find
        self.findall = element.findall

    @property
    def tag(self):
        '''paragraph, subsection, etc.'''
        tag = self.element.tag
        if tag == 'usc-title':
            return 'title'
        else:
            return tag

    @property
    def enum(self):
        e = self.element.find('enum')
        if e is not None:
            text = e.text
            if text is not None:
                return e.text.strip('.')

    @property
    def header(self):
        header = self.find('header')
        if header is not None:
            return gettext(header)
        
    @property
    def ref_id(self):
        try:
            return self.element.attrib['ref-id']
        except KeyError:
            pass
        
    @property
    def id(self):
        try:
            return self.element.attrib['id']
        except KeyError:
            pass

    @property
    def notes(self):
        '''
        A list of `Note` instances. Note is a simple wrapper defined
        below to get paragraphs and headers from note text.
        '''
        els = self.element.find('usc-notes')
        if els is None:
            els = []
        els = filter(lambda e: e.tag.startswith('usc-note'), els)
        return map(Note, els)

    @property
    def notes_data(self):
        '''
        This node's usc-notes, converted to a list of dicts.
        '''
        res = defaultdict(list)
        for n in self.notes:
            j = {'ref-id': n.ref_id, 'id': n.id, 'paragraphs': n.paragraphs}
            header = n.header
            if header:
                res['header'] = header
            res[n.note_type].append(j)
        return dict(res)

    @property
    def meta(self):
        '''
        This is a catch-all attribute for nodes that are neither text 
        (i.e., a chapter or part) nor usc-notes.
        '''
        els = filter(lambda e: not e.tag.startswith('usc-note'), 
                     self.element.find('usc-notes'))
        return els


    @property
    def inline(self):
        '''
        Boolean indicating whether or not this node is displayed inline or
        with a newline.
        '''
        attrib = self.element.attrib
        try:
            return attrib['display-inline'] != 'no-display-inline'
        except KeyError:
            return False


    @property
    def sub(self, ignore_tags=['enum', 'header', 'usc-notes']):
        '''
        Get a list of all subelements, such a the subsections of a section,
        or the chapters under a title. 
        '''
        res = []
        kids = self.element.getchildren()
        kids = filter(lambda e: e.tag not in ignore_tags, kids)
        for k in kids:
            cls = type(self.tag, (self.__class__,), {self.tag: self.enum})
            res.append(cls(k))
        return res


    def _get_nodes(self, tag):
        '''
        Recursively get all kids with a certain tag. Return a list.
        '''
        def f(s):
            if s.sub:
                for s in s.sub:
                    if s.tag == tag:
                        yield s
                    else:
                        for _s in f(s):
                            yield _s
        return list(f(self))


    @property
    def sections(self):
        return self._get_nodes('section')

    @property
    def data(self):
        '''
        Convert this node's info to a python dict.
        '''
        res = {}

        # Add basic attrs.
        for attr in ['header', 'enum', 'inline'
                     'ref_id', 'id', 'tag']:
            val = getattr(self, attr, None)
            if val:
                res[attr] = val
        
        # Add the notes.
        notes = self.notes_data
        if notes:
            res['notes'] = notes

        # Add kids.
        sub = []
        for s in self.sub:
            if s.tag in ('text', 'proviso'):
                data = {'text': gettext(s.element)}
            else:
                data = s.data
            sub.append(data)

        if sub:
            res['sub'] = sub

        return res
             

    def __repr__(self):
        if self.enum:
            return '<%s %s>' % (self.tag, self.enum)
        else:
            return '<%s>' % self.tag
             
        


#----------------------------------------------------------------------------
#
class Note(Node):

    def __repr__(self):
        return '<note: %s>' % self.note_type

    @property
    def paragraphs(self):
        return filter(None, map(gettext, self.element.findall('note-text')))

    @property
    def note_type(self):
        return self.tag.replace('usc-note-', '')



#----------------------------------------------------------------------------
#
def title(element):
    cls = type('title', (Node,), {'title': Node(element).enum})
    return cls(element)


if __name__ == "__main__":

    import os
    import sys

    # Get the files from here.
    DATA_XML = sys.argv[1]

    # Write the json here.
    DATA_JSON = sys.argv[2]

    try:
        os.makedirs(DATA_JSON)
    except OSError:
        pass

    for n in range(1, 50):

        try:
            with open(join(DATA_XML, '%02d.xml' % n)) as f:
                data = f.read()
        except IOError:
            continue

        try:
            t = title(etree.fromstring(data))
        except IOError:
            continue
        
        with open(join(DATA_JSON, '%d.json' % n), 'w') as f:
            json.dump(t.data, f)

        