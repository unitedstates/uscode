'''
.. moduleauthor:: Thom Neale <twneale@gmail.com>


This module exports an API for modeling the enumerations (aka "enums") found
in documents that contain numbered paragraphs that are hierarchically related.

Example Use
+++++++++++++++

Use it like this:

>>> Token('a') < Token('b')
>>> True
>>>
>>> Enum('3-a') < Enum('3-b')
>>> True
'''
import re
import operator
import itertools
import collections


#-----------------------------------------------------------------------------
#  Prepare schemes data.
#-----------------------------------------------------------------------------
_alphabet = 'abcdefghijklmnopqrstuvwxyz'
_alphabet_upper = _alphabet.upper()
_digits = '123456789'


def romans():
    '''Produce data for roman numeral schemes.'''
    ones = ('', 'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix')
    tens = ('', 'x', 'xx', 'xxx', 'l')
    res = []
    for x in tens:
        res += [x + y for y in ones]
    return filter(None, res)
_romans = romans()
del romans

# List (rather than set) versions of the schemes sets. Necessary to
# compare ordinality of tabs.
_schemes_lists = {
    'lower':         list(_alphabet),
    'upper':         list(_alphabet_upper),
    'lower_doubles': [c * 2 for c in _alphabet],
    'upper_doubles': [c * 2 for c in _alphabet_upper],
    'lower_triples': [c * 3 for c in _alphabet],
    'upper_triples': [c * 3 for c in _alphabet_upper],
    'lower_quads':   [c * 4 for c in _alphabet],
    'upper_quads':   [c * 4 for c in _alphabet_upper],
    'lower_roman':   _romans,
    'upper_roman':   map(str.upper, _romans),
    'digits':        map(str, range(1, 200)),
    }

del _alphabet
del _alphabet_upper
del _digits

# The same dict as _schemes_lists, only with sets. Helpful for fast
# membership testing.
_schemes = dict(
    (k, set(v)) for k, v in _schemes_lists.items()
    )

# Used for testing whether tab is first-in-scheme.
_first_scheme_tokens_dict = {}
for k, v in _schemes_lists.items():
    _first_scheme_tokens_dict[v[0]] = set([k])

_first_scheme_tokens = set(_first_scheme_tokens_dict)

_all_scheme_tokens = reduce(operator.or_, _schemes.values())

# If these aren't the same length, one was modified without
# corresponding changes to the other, so complain and fail.
assert len(_schemes) == len(_first_scheme_tokens)


#-----------------------------------------------------------------------------
#  Scheme identification helpers.
#-----------------------------------------------------------------------------
class UnrecognizedSchemeError(Exception):
    '''
    If an enum's scheme can't be determined using simple
    techniques, the tab warrants an inspection, so raise
    an error.
    '''
    pass


def get_common_schemes(*entities):
    '''
    Given an arbitrary list of instances supporting the "get_schemes"
    method, return all common schemes that apply.
    '''
    return reduce(operator.and_, (e.get_schemes() for e in entities))


class SchemeEntity(object):
    '''
    This class exists simply as a way to allow its inheritants to share
    the schemes data. Its inheritants are "Token" and "Enum".
    '''
    # Schemes data.
    _schemes_lists = _schemes_lists
    _schemes = _schemes
    _first_scheme_tokens = _first_scheme_tokens
    _all_scheme_tokens = _all_scheme_tokens

    # Defaults.
    schemes = None
    ordinality = None


class Token(SchemeEntity):

    def __init__(self, t):

        self.text = t

    def __repr__(self):
        return self.text

    def __eq__(self, other):

        try:
            # Other is a Token.
            return self.text == other.text
        except AttributeError:
            # Other is subtype of basestring.
            return self.text == other

    def __ne__(self, other):
        try:
            # Other is a Token.
            return not self.text == other.text
        except AttributeError:
            # Other is subtype of basestring.
            return not self.text == other

    def __and__(self, other):
        return self.get_schemes() & other.get_schemes()

    def get_schemes(self):
        '''
        Get a set of names of all schemes that could apply to this token.

        This function is lengthy in an attempt to optimize it, it possibly
        being worst performing aspect of parsing statutes.
        '''
        if self.schemes:
            return self.schemes

        t = self.text
        tlen = len(t)
        schemes = _schemes

        # Tab is only 1 char. No need to test for doubles, etc.
        # Most tabs fall into this branch, so this ought
        # to speed things up.
        if tlen == 1:

            if t.isalpha():

                case = ('upper' if t.isupper() else 'lower')
                tset = set(list(t))
                res = set([case])
                roman = '%s_roman' % case

                if tset & schemes[roman]:
                    res.add(roman)

                self.schemes = res
                return res

            elif t.isdigit():
                res = set(['digits'])

                self.schemes = res
                return res

        # More than one char. Conduct additional tests.
        else:

            if t.isalpha():

                case = ('upper' if t.isupper() else 'lower')
                tset = set(list(t))
                tsetlen = len(tset)
                res = []

                # Test if it's multiple.
                if (tsetlen == 1) and (tsetlen < tlen):
                    res.append('%s_%s' % (
                        case,
                        {2: 'doubles', 3: 'triples', 4: 'quads'}[tlen]
                        ))

                # Test if it's upper_roman.
                if t in schemes['%s_roman' % case]:
                    res.append('%s_roman' % case)

                res = set(res)
                self.schemes = res
                return res

            elif t.isdigit():
                res = set(['digits'])
                self.schemes = res
                return res

        msg = 'Couldn\'t determine scheme type of "%s"' % t
        raise UnrecognizedSchemeError(msg)

    def is_first_in_scheme(self):
        '''
        Determine whether this token is the first token in any scheme.
        '''
        return self.text in self._first_scheme_tokens

    def get_ordinality(self):
        '''
        Return a dict with this token's schemes as keys and the token's
        ordinality within each scheme as the corresponding value.
        '''
        _ord = self.ordinality
        if _ord:
            return _ord
        else:
            t = self.text
            _ord = {}
            _schemes_lists = self._schemes_lists
            for sc in self.get_schemes():
                _ord[sc] = _schemes_lists[sc].index(t)
            self.ordinality = _ord
            return _ord

    def could_be_next_after(self, other):
        '''
        Determine whether this token "could be next" after other
        in a scheme.

        :param other: another token
        :type other: statutils.Token
        '''
        if self == other:
            return 'equal'

        common_schemes = self & other
        if not common_schemes:
            return False
        else:
            for c in common_schemes:
                ord1 = other.get_ordinality()
                ord2 = self.get_ordinality()
                if ord2[c] - ord1[c] == 1:
                    return 'consecutive'
            return False


#-----------------------------------------------------------------------------
#  Main Enum class
#-----------------------------------------------------------------------------
class Enum(list, SchemeEntity):
    '''
    This class models a single enumeration character, such as "a" or "3"
    or "viii". It can model complex enums like "a-3" as long as each component
    is a valid scheme token. That means numbers can't have decimals, but
    an assumption underlying this API is no scheme token will ever be a
    decimal number. It might for a section number, but not a mere scheme token.
    '''

    class UnrecognizedTokenError(Exception):
        '''
        Prevent this class from being instantiated with text containing
        any scheme tokens not in the set _all_scheme_tokens. So in other
        words, raise an error for any like these:

            * Enum('$')
            * Enum('1-a*')

        If the statute's enumerations do contain any of these characters, they
        probably indicate something of importance, such as a note, and
        should be stripped from the enum text before passing it to the
        Enum class.
        '''
        pass

    #-------------------------------------------------------------------------
    #  Token extraction regexes.
    #-------------------------------------------------------------------------
    rgxs = (
        re.compile(r'[A-Z]+', re.I),    # alphas
        re.compile(r'[\d.]+'),          # numbers
        re.compile(r'[-]+'),            # connectors
        re.compile(r'^\(.+\)$'),        # parens
        re.compile(r'\.$'),             # points
        )

    def __init__(self, text, **kwargs):
        '''
        :param text: the enum text (not stripped of punctuation)
        :type text: str or unicode
        :param kwargs: any other information to cache in the instance dict

        This method does the following:

          * Screen the input to make sure no invalid scheme tokens are present
          * Cache arbitrary kwargs for later use
          * Cache the passed-in text as ``self.original_text`` for use in
            later substitutions
          * Cache any parenthesis or punctuation surrounding the enum tokens
            for use in later comparison and formatting operations, since some
            statutes incorporate enum style in defining the document hierarchy
          * Find all match objects for self.rgxs and sort them by start()
          * Extend self, a list, with the sorted matches
          * Cache self.text, which appears to be redundant of original text.
        '''
        # A quick test to verify that no unrecognized tokens are present,
        # (like "$")
        unrec = set(text) - (self._all_scheme_tokens | set('-0.()'))
        if unrec:
            msg = (
                'Can\'t instantiate Enum from text %s with'
                'unrecognized tokens "%s"'
                ) % (text, unrec)

            raise self.UnrecognizedTokenError(msg)

        # Cache any info passed in.
        # Aug 31, 2010 - Enable caching of info helpful in parse.
        for k, v in kwargs.items():
            setattr(self, k, v)

        # Cache the original text
        self.original_text = text

        # Cache any parens or periods surrounding the tokens.
        # These can be reused to recreate the style of the enum.
        text = text.strip()
        format_left = []
        format_right = []

        if text:
            first_char = text[0]
            while first_char in '(':
                format_left.append(first_char)
                text = text[1:]
                first_char = text[0]

            last_char = text[-1]
            while last_char in '.)':
                format_right.append(last_char)
                text = text[:-1]
                last_char = text[-1]

        self.format_left = format_left
        self.format_right = format_right

        # Get all match strings.
        matches = itertools.chain.from_iterable(
            m.finditer(text) for m in self.rgxs
            )

        # Sort by start position and wrap in Token class.
        matches = [Token(m.group()) for m in
                   sorted(matches, key=lambda m: m.start())]

        super(Enum, self).__init__(matches)

        # Cache text in instance.
        self.text = text

    def __repr__(self):
        return 'Enum(\'%s\')' % self.text

    def __eq__(self, other):
        return self.text == other.text

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        '''
        <  less than

        This actually tests whether self COULD BE less than
        other under any of the schemes they share.
        '''
        ord1 = self.get_ordinality()
        ord2 = other.get_ordinality()
        common_schemes = set(ord1) & set(ord2)
        if common_schemes:
            return any((ord1[s] < ord2[s]) for s in common_schemes)
        else:
            return False

    def __le__(self, other):
        '''
        <= less than/equal
        '''
        return (self == other) or (self < other)

    def __gt__(self, other):
        ord1 = self.get_ordinality()
        ord2 = other.get_ordinality()
        common_schemes = set(ord1) & set(ord2)
        if common_schemes:
            return any((ord1[s] > ord2[s]) for s in common_schemes)
        else:
            return False

    def __ge__(self, other):
        '''
        => greater than/equal
        '''
        return (self == other) or (self > other)

    def __lshift__(self, other):
        return other.could_be_next_after(self)

    def __rshift__(self, other):
        return self.could_be_next_after(other)

    def __and__(self, other):
        return self.get_common_schemes(other)

    def __nonzero__(self):
        return bool(self.text)

    def _itertokens(self):
        return (x for x in self if x.text != '-')

    def get_schemes(self):
        '''
        Get a set of names of all schemes that
        could apply to the provided tabtext.

        Note that for compound tabs, this function
        bails after determining the scheme of the first token.
        '''
        if self.schemes:
            return self.schemes
        else:
            for t in self:
                res = t.get_schemes()
                self.schemes = res
                return res

    def get_common_schemes(self, *others):
        '''
        Get common schemes between ``self`` and ``other``.
        Can also do this: self & other
        '''
        tabs = [self] + list(others)
        return reduce(operator.and_, (t.get_schemes() for t in tabs))

    def get_ordinality(self):
        '''
        Figure out what this tab's possible scheme orders are.
        '''

        # Try returning cached value.
        ordinality = self.ordinality
        if ordinality:
            return ordinality

        text = self.text

        # Calculate ordinality.
        ordinality = collections.defaultdict(lambda: [])
        for s in self.get_schemes():
            try:
                ord_ = _schemes_lists[s].index(text)
            except ValueError:
                pass
            else:
                ordinality[s].append(ord_)
                continue
            # Not in the schemes list; probably a compound tab like "4-a".
            # Repeat the test with each token in the tab.
            # Break on success?
            tokens = list(self._itertokens())
            if len(tokens) == 1:
                continue
            for t in tokens:
                for sc in t.get_schemes():
                    try:
                        ord_ = _schemes_lists[sc].index(t.text)
                    except ValueError:
                        continue
                    ordinality[s].append(ord_)
        self.ordinality = ordinality
        return ordinality

    def is_first_in_scheme(self):
        '''
        Determine whether this Tab instance is first in any scheme.
        '''
        return self.text in self._first_scheme_tokens

    def could_be_next_after(self, other):
        '''
        Determine whether self would be
        a valid consecutive tab following other
        per any scheme.

        Alternatively: other << self
        '''
        if self == other:
            return False

        extra_tokens = filter(lambda x: x != '-', self[len(other):])
        if extra_tokens:
            if not all(t.is_first_in_scheme() for t in extra_tokens):
                return False

        comparisons = (x.could_be_next_after(y) for x, y in
                       zip(self, other))

        consecutive = False
        for c in comparisons:
            if not c:
                return False
            elif c == 'equal':
                continue
            elif consecutive:
                # Here the tabs must be like '4-a' and 5-b'.
                # Only one consecutive result allowed; all
                return False
            else:
                consecutive = True
                continue
        return True

    @property
    def was_nested(self):
        try:
            was_nested = self._was_nested
        except AttributeError:
            return False
        else:
            if was_nested:
                return True

if __name__ == '__main__':
    
    import pdb;pdb.set_trace()

##class TabbedSequence(list):
##    '''
##    This class models a sequence of tabs or tabbed elements, each having
##    a "tab" attribute. 
##    '''
##    _ERROR_PROTOCOL = {
##        'strict': 0,
##        'lax': 1,
##        'forceappend': 2,
##        }
##
##    class SequenceError(Exception): pass
##    class SchemeMismatch(SequenceError): pass
##    class TabNotFirstInScheme(SequenceError): pass
##    class TabNotConsecutive(SequenceError): pass
##    class TabNotGreaterThan(SequenceError): pass
##
##    _first_scheme_tokens_dict = _first_scheme_tokens_dict
##
##    def appendsingle(self, tabbed_item, error_protocol="strict"):
##        '''
##        :param tab: A schemeutils.Tab instance
##        :type tab: schemeutils.Tab
##
##        :param error_protocol: "strict", "lax", or "forceappend"
##        :type error_protocol: str
##
##        :param recurse: On failure, try to append to TabSequence.parent?
##        :type recurse: bool
##        
##        
##        Performs a normal list append but first checks to see whether
##        item added has a "tab" attribute (which is an instance of the
##        Tab class) that is valid within the current scheme.
##
##        Depending on the error_protocol selected, this function follows
##        different procedures for appending the tab:
##
##          * If error_protocol is "strict", the append will fail unless
##            tab could be next after the last tab in the sequence.
##          * If error_protocol is "lax",  the append will succeed if the
##            the tab is simply "greater than" the last tab in the sequence.
##            In other words, the tab doesn't have to be a valid consecutive
##            tab.
##        '''
##        # --------------------------------------------------------------------
##        #  Sort out locals.
##        # --------------------------------------------------------------------
##        ep = error_protocol
##        error_protocol = self._ERROR_PROTOCOL.get(ep, ep)
##
##        try:
##            # Item has a tab.
##            tab = tabbed_item.tab
##        except AttributeError:
##            # Item is a tab.
##            tab = tabbed_item
##
##        # --------------------------------------------------------------------
##        #  Commence append attempt.
##        # -------------------------------------------------------------------- 
##            
##        if len(self) == 0:
##            if not tab.is_first_in_scheme():
##                raise self.TabNotFirstInScheme('Purported first tab %s isn\'t'
##                                       ' first in scheme.' % tab)
##
##            else:
##                # The scheme of the first Tab in the sequence determines
##                # the scheme for the entire TabSequence.
##                scheme = self._first_scheme_tokens_dict[tab.text]
##                self.scheme = scheme
##                list.append(self, tab)
##
##        else:
##            # Could the item be a member of this scheme?
##            scheme = self.scheme
##            if not scheme & tab.get_schemes():
##                raise self.SchemeMismatch("Item with tab %s doesn't fit in "
##                                       "this sequence's scheme, which is %s."
##                                       % (tab, scheme,))
##            else:
##                # Here add first could be next, then the fallback
##                # of allowing nonconsecutive but greater tabs.
##                
##                if error_protocol == 0:
##                    # strict: append only if tab could be next.
##                    if self[-1] << tab:
##                        list.append(self, tab)
##                    else:                    
##                        raise self.TabNotConsecutive(
##                            "%s isn't consecutive after %s" \
##                            % (tab, self[-1],))
##
##                elif error_protocol == 1:
##                    # lax: append if tab is greater than last in sequence.
##                    if self[-1] < tab:
##                        list.append(self, tab)
##                    else:                    
##                        raise self.TabNotGreaterThan(
##                            "%s isn't greatern than %s" \
##                            % (tab, self[-1],))
##        
##                if error_protocol == 2:
##                    # Force the append.
##                    list.append(self, tab)
##
##    def append(self, tab, error_protocol='strict'):
##
##
##class TabbedDocument(TabbedSequence):
##
##    def build(self):
##        
##        previous = self
##
##        # SequenceError locals
##        WasNotFirstInScheme = TabbedSequence.WasNotFirstInScheme
##        SchemeMismatch = TabbedSequence.SchemeMismatch
##        TabNotConsecutive = TabbedSequence.TabNotConsecutive
##        TabNotGreaterThan = TabbedSequence.TobNotGreaterThan
##
##        def append(previous, current, error_protocol='strict'):
##                
##            try:
##                # First, try to add current as a sibling of previous.
##                previous.parent.append(current, error_protocol)
##                previous = current
##                return
##            
##            except (TabNotConsecutive, AttributeError):
##                # --------------------------------------------------------
##                # Try to make current a child of previous.
##                #
##                # If AttributeError, previous.parent was None. Usually
##                # in that situation "previous" is the root element.
##                # --------------------------------------------------------
##
##                try:
##                    previous.append(current, error_protocol)
##                except WasNotFirstInScheme:
##                    append(previous.parent.parent, current, error_protocol)
                    

                    
                
                        
            
