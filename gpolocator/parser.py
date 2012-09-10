# -*- coding: utf-8 -*-
'''
Usage:

>>> f = open('usc08.10')
>>> x = getlines(f)
>>> x.next()
GPOLocatorLine(code='F', arg='5800', data=u'\r\n')
>>> print x.next().data
TITLE 8–ALIENS AND NATIONALITY


Explanation:

The problem with getting structured data from the ASCII and XHTML files
provided by the house (http://uscode.house.gov/) is that you need to be
able to tokenize the statute text into distinct subsections/paragraphs
before you can reassemble them into a hierarchy.

Because the ASCCI and XHTML files were both formatted for printing in bound
volumes, they dedent paragraphs/subsections when the level of nesting gets
high enough to squish the text too close to the right margin of the page.
Because the text of the US Code (and most other statutes and regs) is littered
with internal citations, it's basically impossible to reliably work around
this difficulty across a large data set. Consider this:

§ 1. Certain Rules.
(1) Murder shall be illegal, and so shall:
  (a) Cruelty to animals, including acts described in section 123
  (b)(1) of this title.
(2) Blah Blah...

Working with GPO Locator data solves this because each subsection/paragraph
appears in its own line. You can see where the instructions are to dedent
a paragraph (look for the Q code) and other weird things and simply skip them.

So parsing this data basically means splitting each line into its code value,
any arguments, and the following text, then swapping out the escape sequences
for their unicode equivalents. You can then either process the codes somehow
or toss them and keep the unicode.

This module does that for a subset of the GPOLocator codes used in
title 8 of the US Code. It'd be easy to extend to others. Below is an example
of the same data in ASCII and GPOLocator form:


<-- ASCII data ->
                              CHAPTER 4—FREEDMEN

§§61 to 65. Omitted

                                  Codification
Section 61, R.S. 2032, related to continuation of laws then in force.
Section 62, R.S. 2033, related to enforcement of laws by former Secretary of War.
Section 63, acts Mar. 3, 1879, ch. 182, §2, 20 Stat. 402; Feb. 1, 1888, ch. 4, §1, 25 Stat. 9; July 1, 1898, ch. 546, 30 Stat. 640, related to claims for pay or bounty.
Section 64, act July 1, 1902, ch. 1351, 32 Stat. 556, related to retained bounty fund.
Section 65, R.S. §2037, related to wives and children of colored soldiers.


<-- GPO Locator data -->
I81T2CHAPTER 4_FREEDMEN

I80ÿ1A61 to 65

I89. Omitted

I76Codification

I21Section 61, R.S. 2032, related to continuation of laws then in force.

I21Section 62, R.S. 2033, related to enforcement of laws by former Secretary of War.

I21Section 63, acts Mar. 3, 1879, ch. 182, ÿ1A2, 20 Stat. 402; Feb. 1, 1888, ch. 4, ÿ1A1, 25 Stat. 9; July 1, 1898, ch. 546, 30 Stat. 640, related to claims for pay or bounty.

I21Section 64, act July 1, 1902, ch. 1351, 32 Stat. 556, related to retained bounty fund.

I21Section 65, R.S. ÿ1A2037, related to wives and children of colored soldiers.
'''
import re
from functools import partial
from collections import namedtuple


class GPOLocatorText(unicode):
    pass


class GPOLocatorLine(namedtuple('GPOLocatorLine', 'code arg data')):

    def __unicode__(self):
        return self.data

    def as_tuple(self):
        return self[:2]

    @property
    def codearg(self):
        return self.code + self.arg

    @property
    def _footnote_numbers(self, finditer=re.finditer):
        for matchobj in finditer(r'\\(\d)\\', self.data):
            # number, offset
            yield matchobj.group(1), matchobj.start()

    def footnotes(self):
        return map(self._footnote_dict.get, self._footnote_numbers)

    @property
    def text(self):
        text = self.data
        for number, offset in self._footnote_numbers:
            text = text.replace(r'\\%d\\' % number, '')

        text.notes = self.footnotes
        return text

#-----------------------------------------------------------------------------
# Step 1: Identify bell codes and their arguments.
codes = {

    # Mapping of "bell" code values to patterns matching numeric arguments.
    # Example: '\x07F5880Blah blah blah...'
    'G': '\d',
    'I': '\d{2}',
    'Q': '\d{2}',
    'R': '\d{2}',
    'T': '\d',
    'U': '\d',
    'Y': '\d',
    'a': '\d{3}',
    'g': '\d{3}',
    'h': '\d',
    'q': '\d{2}',
    'F': '\d{4,5}',
    'S': '\d{4,5}',

    # These ones never have numeric arguments.
    'K': None,
    'gs': None,
    '\d{2}': None,
    'j': None,
    'e': None,

    # Code 'c' signals data for a complex table. Match the whole line.
    'c': '.+',
    }


# Compile a pattern to match code values.
re_code = re.compile('|'.join(sorted(codes, reverse=True, key=len)))

# Compile functions to match code arguments.
for k, v in codes.items():
    if v:
        codes[k] = re.compile(v).match

#-----------------------------------------------------------------------------
# Step 2: Convert escape sequences to unicode

specialchars = {
    # These are the unicode equivalents of the GPOLocator
    # escape sequences.
    '\x06': u'§',
    '\x0A': u'\n',
    '\x0B': u'¢',
    '\x0C': u'¶',
    '\x10': u"'",
    '\x13': u'[',
    '\x14': u']',
    '\x18': u'\u2003',
    '\x19': u'\u2002',
    '\x1B': u'±',
    '\x1C': u'',
    '\x1E': u'†',
    '\x27': u'“',
    '\x3C': u'<',
    '\x3E': u'>',
    '\x5E': u'-',
    '\x5F': u'–',
    '\x60': u'”',
    '\xAB': u'º',
    '\xBD': u'‡',
    '\xBE': u'n',
    '\xBF': u'□',
    '\xff1A': u' ',
    '\xff09': u'–',
    '\xff0A': u'×',
    '\xff08': u'\u2009',
    '\xffAF': u'©',
    '\xffAE0': u'˘',
    '\xffAE1': u'΄',
    '\xffAE2': u'`',
    '\xffAE3': u'^',
    '\xffAE4': u'¨',
    '\xffAE5': u'ˇ',
    '\xffAE6': u'~',
    '\xffAE7': u'˚',
    '\xffAE8': u'ˉ',
    '\xffAE9': u'¸',
    }

# Compile the keys into a big regex.
_ = map(re.escape, specialchars)
_ = '|'.join(sorted(_, key=len, reverse=True))
_ = re.compile('(%s)' % _)

# Example: swap('1 USC \x06\x06 234') --> '1 USC §§ 234'
swap = partial(_.sub, lambda m: specialchars[m.group()])


#-----------------------------------------------------------------------------
# Step 3: Chop each line of the file into code, args, and data.

def getlines(fp, argmatchers=codes, codematcher=re_code.match, swap=swap,
             GPOLocatorLine=GPOLocatorLine):

    for line in fp:
        if line.strip():

            # Get the code value.
            startpos = 1
            matchobj = codematcher(line, startpos)
            if matchobj:
                code = matchobj.group()
            else:
                continue

            # Get the argument value (if any)
            len_code = len(code)
            argmatcher = argmatchers[code]
            if not argmatcher:
                arg = None
                len_arg = 0
            else:
                startpos += len_code
                arg = argmatcher(line, startpos).group()
                len_arg = len(arg)

            # Get the data.
            startpos += len_arg
            data = line[startpos:]

            yield GPOLocatorLine(code, arg, swap(data))


if __name__ == "__main__":

    import urllib2
    import zipfile
    from StringIO import StringIO

    # Download some GPO Locator data to play with, Title 8 of th US Code.
    print 'Get comfy...this takes a sec...'
    resp = urllib2.urlopen('http://uscode.house.gov/zip/2010/usc08.zip')
    data = StringIO(resp.read())
    fp = zipfile.ZipFile(data).open('usc08.10')

    for line in getlines(fp):
        print line
        raw_input('Press enter to see next line: ')
