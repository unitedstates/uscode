#! /home/thom/ve/2.7/bin/python
import sys
import pprint

from gpolocator.parser import getlines
from gpolocator.grouper import group
from gpolocator.utils import title_filename
from gpolocator.structure import GPOLocatorParser


def main():
    filename = title_filename(int(sys.argv[1]), 11)
    fp = open(filename)
    lines = getlines(fp)
    gg = group(lines)
    pprint.pprint(gg[1].instance.json())

    ss = gg[int(sys.argv[2])].instance
    bb = ss.body_lines()
    xx = GPOLocatorParser(bb)
    qq = xx.parse()
    qq.tree()
    # import pdb;pdb.set_trace()

    # xx = [x.instance for x in gg]

    # import pdb;pdb.set_trace()
    # for doc in gg:
    #     x = doc.instance
    #     print x
    #     import pdb;pdb.set_trace()


if __name__ == '__main__':
    main()
