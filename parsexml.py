from os.path import join, expanduser
import re

from lxml import etree
import pdb

DATA = expanduser('~/data/uscode/xml/USC_TEST_XML/')

def title_filename(title):
    return join(DATA, '%02d.xml' % title)

def titledata(title):
    with open(title_filename(title)) as f:
        return f.read()


def _gettext(element, recurse=True):
    '''
    Extract text from this element, any child element, and the tail.
    '''
    
    if element.tag == 'quote':
        yield '"%s"' % element.text
    else:
        yield element.text

    if recurse:
        for child in element.getchildren():
            for t in _gettext(child):
                yield t

    tail = element.tail
    if tail and tail.strip():
        yield tail

def gettext(element, recurse=True, join=''.join):
    return join(_gettext(element, recurse))
    

        
#----------------------------------------------------------------------------
#
class SectionMixin(object):
    
    def _kids(self, types='text subsection paragraph subparagraph'.split()):
        kids = self.element.getchildren()
        if kids is not None:
            kids = kids[1:]
            for k in kids:
                if k.tag in types:
                    yield classes[k.tag](k)

    @property
    def kids(self):
        return list(self._kids())

    def getnote(self, header_or_tag):
        for note in self.notes:
            if note.tag == header_or_tag:
                return note
            if note.header == header_or_tag:
                return note


class Node(object):

    def __init__(self, element):
        self.element = element
        self.find = element.find
        self.findall = element.findall

    @property
    def tag(self):
        '''paragraph, subsection, etc.'''
        return self.element.tag
    type_ = tag

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
        return self.element.attrib['ref-id']
        
    @property
    def id(self):
        return self.element.attrib['id']

    @property
    def notes(self):
        return map(Note, self.element.find('usc-notes'))

    @property
    def text(self):
        return gettext(self.element)

    @property
    def inline(self):
        attrib = self.element.attrib
        try:
            return not attrib['display-inline'] == 'no-display-inline'
        except KeyError:
            return False

    @property
    def sub(self, class_cache={}):
        for w in ('subtitle', 'part', 'subpart', 'chapter', 'subchapter', 'section'):
            res = self.findall(w)
            if res:
                bases = [self.__class__]
                if w == 'section':
                    bases.append(SectionMixin)
                cls = type(w, tuple(bases), {self.tag: self.enum})
                return map(cls, res)

    def _get_nodes(self, name):
        def f(s):
            if s.sub:
                for s in s.sub:
                    if s.tag == name:
                        yield s
                    else:
                        for _s in f(s):
                            yield _s
        return list(f(self))


    @property
    def sections(self):
        return self._get_nodes('section')


                                    


    def __repr__(self):
        if self.enum:
            return '<%s %s>' % (self.tag, self.enum)
        else:
            return '<%s>' % self.tag
             
        


#----------------------------------------------------------------------------
#
class Note(Node):

    @property
    def paragraphs(self):
        return map(gettext, self.element.findall('note-text'))






class Subsection(Node):
    '''
    The Subsection won't recurse into its child notes when we get its text.
    '''
    @property
    def text(self):
        return gettext(self.element, recurse=False)

class Paragraph(Subsection):
    pass

class Subparagraph(Subsection):
    pass

class Text(Subsection):
    pass

classes = {

    'subsection': Subsection,
    'paragraph': Paragraph,
    'subparagraph': Subparagraph,
    'text': Text,
    }

#----------------------------------------------------------------------------
#
class Chapter(Node):

    @property
    def sections(self):
        return map(Section, self.findall('section'))



#----------------------------------------------------------------------------
#

def title(element):
    cls = type('title', (Node,), {'title': Node(element).enum})
    return cls(element)





if __name__ == "__main__":

    for n in range(1, 50):

        try:
            t = title(etree.fromstring(titledata(n)))
        except IOError:
            continue

        def printtree(e, indent=0):
            print " " * indent, e
            if e.sub:
                for s in e.sub:
                    printtree(s, indent=indent + 2)
        
        printtree(t)
                    
        # for ss in t.sections:
        #     print ss, ss.kids
        # ss = t.sections[-1]
        # k = ss._kids()
        # k.next()
        # pdb.set_trace()
    # nn = t9.chapters[0].sections[1].notes
    # ss = t9.sections
    # sss = ss[9]
    # xx = sss.kids
    # hh = sss.find('header')
    # pdb.set_trace()
