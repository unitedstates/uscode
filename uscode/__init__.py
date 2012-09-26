from .parser import getlines
from .grouper import group
from .models import *

def title_for(filename):
    return File(open(filename))

class File(object):

    hierarchy = [
        Title,
        Subtitle,
        Chapter,
        Subchapter,
        Section,
        Part,
        Subpart,
        ]

    def __init__(self, fp):
        '''Pass it an open gpo locator file.
        '''
        self._lines = lines = getlines(fp)
        self._grouped = grouped = group(lines)
        self.instances = [g.instance for g in grouped]
        # self._build()

    def sections(self):
        return [inst for inst in self.instances if isinstance(inst, Section)]

    # def _build(self):
    #     '''Assembly the titles, chapters, headings, sections into a tree.
    #     '''
    #     instances = self.instances
    #     classmap = defaultdict(list)

    #     current = instances[0]
    #     classmap[current.__class__].append(current)

    #     # The first entry should be a title.
    #     msg = "The first entry in the file wasn't a title!"
    #     assert isinstance(head, Title), msg

    #     for inst in instances[1:]:

