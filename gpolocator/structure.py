import re
import logbook

from .utils import CachedAttribute
from .schemes import Enum


logger = logbook.Logger()


class Token(object):

    def __init__(self, enum, text, linedata):
        self.enum = enum
        self.text = text
        self.linedata = linedata

    def __iter__(self):
        for x in (self.enum, self.text, self.linedata):
            yield x

    def __repr__(self):
        return 'Token(%r, %r, %r)' % (self.enum, self.text, self.linedata)

    @classmethod
    def make(cls, tpl):
        return cls(*tpl)


class Stream(object):

    def __init__(self, iterable):
        self._stream = map(Token.make, iterable)
        self.i = 0

    def __iter__(self):
        self.i = -1
        while True:
            self.i += 1
            try:
                yield self._stream[self.i]
            except IndexError:
                raise StopIteration

    def next(self):
        i = self.i + 1
        try:
            yield self._stream[i]
        except IndexError:
            raise StopIteration

    def previous(self):
        return self.behind(1)

    def this(self):
        return self._stream[self.i]

    def ahead(self, n):
        return self._stream[self.i + n]

    def behind(self, n):
        return self._stream[self.i - n]


class TextNode(list):
    '''A text node can (sometimes) have children.'''

    def __init__(self, content):
        self.content = content

    def __repr__(self):
        return 'TextNode(%r)' % self.content


class Node(list):

    def __init__(self, enum, linedata, text):
        self.enum = enum
        self.linedata = linedata
        self.footnotes = []
        self.extend([TextNode(text)])
        self.logger = logbook.Logger(level='DEBUG')

    def __repr__(self):
        return 'Node(%r, %s)' % (self.enum, list.__repr__(self))

    @CachedAttribute
    def _new_child(self):
        '''Return a subclass of this class where the attribute `parent`
        points back to this class, enabling `append` to recursively
        move back up the tree structure if necessary.
        '''
        self_cls = self.__class__
        attrs = dict(parent=self)
        cls = type(self_cls.__name__, (self_cls,), attrs)
        return cls

    def _force_append(self, token, listappend=list.append):
        '''Append a child node without attempting to judge whether it
        fits or propagating it back up the tree.'''
        enum, text, linedata = token
        new_node = self._new_child(enum, linedata, text)

        # Append the new node to the parent.
        listappend(self, new_node)

        # Make the new node accessible via the token inside the parser.
        token.node = new_node
        return new_node

    def append(self, token,
               h=Enum('h'), H=Enum('H'),
               i=Enum('i'), I=Enum('I'),
               j=Enum('j'), J=Enum('J')):

        enum, text, linedata = token
        self_enum = self.enum

        try:
            is_root = self.is_root
        except AttributeError:
            pass
        else:
            if is_root:
                if enum:
                    return self._force_append(token)

        if enum is None:
            return self._force_append(token)

        if enum.is_first_in_scheme():

            # Disambiguate roman and alpahabetic 'i' and 'I'
            if enum == i and self_enum == h:
                # If the next enum is 'ii', the scheme is probably
                # 'lower_roman'.
                next_ = self.parser.stream.ahead(1)
                if next_.enum.could_be_next_after(enum):
                    return self.parent._force_append(token)

                # Else if it's 'j', it's probably just 'lower'.
                if next_.enum == j:
                    return self.parent._force_append(token)

            elif enum == I and self_enum == H:

                # If the next enum is 'II', the scheme is probably
                # 'upper_roman'.
                next_ = self.parser.stream.ahead(1)
                if next_.enum.could_be_next_after(enum):
                    return self.parent._force_append(token)

                # Else if it's 'J', it's probably just 'upper'.
                if next_.enum == J:
                    return self.parent._force_append(token)

            return self._force_append(token)

        if enum.was_nested:
            return self._force_append(token)

        if self_enum is None:
            self.parent._force_append(token)

        elif enum.could_be_next_after(self_enum):
            return self.parent._force_append(token)

        # If we get here, the previous append attempts all failed,
        # so propagate this node up to the current node's parent
        # and start over.
        return self.parent.append(token)

    def tree(self, indent=0):
        if self.linedata:
            print ' ' * indent, self.enum  # '[{0}, {1}]'.format(*self.linedata)
            # if 16 < int(self.linedata.arg):
            #     import pdb;pdb.set_trace()
        else:
            print ' ' * indent, self.enum
        if self.footnotes:
            for note in self.footnotes:
                print 'NOTE:', note['number'], note['offset'],repr(note['text'])
        for node in self:
            if isinstance(node, Node):
                node.tree(indent=indent + 2)
            elif isinstance(node, TextNode):
                if node.content is not None:
                    print ' ' * indent, node.content.encode('utf-8')


class Parser(object):

    SKIP = 1

    def __init__(self, stream):
        stream = Stream(stream)
        node_cls = type('Node', (Node,), dict(stream=stream, parser=self))
        root = node_cls(None, None, None)
        root.is_root = True
        self.root = root
        self.stream = stream

    def parse(self):

        this = self.root
        before_append = self.before_append
        after_append = self.after_append
        SKIPPED = 1

        for token in self.stream:

            # Try and execute beford_append.
            appended_to = before_append(token)
            if appended_to is not None:
                pass
            else:
                appended_to = this.append(token)

            after_append(token)

            # Change the parser's state.
            if appended_to is not SKIPPED and appended_to.enum:
                this = appended_to

        return self.root

    def before_append(self, token):
        raise NotImplemented

    def after_append(self, token):
        raise NotImplemented


class GPOLocatorParser(Parser):

    def __init__(self, *args, **kwargs):

        super(GPOLocatorParser, self).__init__(*args, **kwargs)

        # The parser needs to remember the last token it saw for
        # each gpo locator code encountered.
        self.codemap = {}

        # Mapping of encountered footnote numbers to nodes in which
        # they appear.
        self.footnotes = {}

    def before_append(self, token, finditer=re.finditer):

        SKIPPED = 1
        codemap = self.codemap

        # Keep track of the most recent token for each codearg.
        linedata = token.linedata
        if linedata is not None:
            # Nested enums have no linedata.
            codemap[linedata.codearg] = token

        # I13 tail text is denoted with I32.
        linedata = token.linedata
        if linedata is not None:

            codearg = token.linedata.codearg
            if codearg == 'I32':

                # Get the most recent I13 node.
                node = self.codemap['I13'].node
                return node.parent._force_append(token)

            if codearg == 'I17':
                node = self.codemap['I12'].node
                return node.parent._force_append(token)

            if codearg == 'I28':
                return SKIPPED

        # Associate nodes with footnotes they contain.
        if token.text:
            for matchobj in finditer(r'\\(\d+)\\\x07N', token.text):
                number, offset = self.matchobj_to_notedata(token, matchobj)
                self.footnotes[number] = (token, offset)

    def after_append(self, token):

        # Match footnotes to their annotations in node text.
        linedata = token.linedata
        if linedata and linedata.codearg == 'I28':
            target_token, note = self.token_to_note(token)
            target_token.node.footnotes.append(note)

    #  methods.
    def matchobj_to_notedata(self, token, matchobj):
        offset = matchobj.start()
        number = matchobj.group(1)
        return number, offset

    def token_to_note(self, token):
        text = token.text

        # If the text doesn't start with\x07, it's not a note.
        assert text[0] == '\x07'

        number = text[3]
        target_token, offset = self.footnotes[number]
        text = re.sub(r'^\x07N\\(\d+)\\\s+', '', text)
        note = dict(offset=offset, text=text, number=number)
        return target_token, note

