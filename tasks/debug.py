#! /home/thom/ve/2.7/bin/python
import sys

from logbook import Logger

from gpolocator import File
from gpolocator.utils import title_filename


logger = Logger('debug')


def main():
    filename = title_filename(int(sys.argv[1]), '2011')
    fp = open(filename)

    gpo_file = File(fp)
    succeeded = 0
    failed = 0
    for section in gpo_file.sections():
        logger.info('Trying to parse %r' % section)
        try:
            tree = section.as_tree()
        except Exception as e:
            logger.warning('  .. parse failed: %r' % e)
            failed += 1
        else:
            succeeded += 1

    logger.info('Number that succeeded: %d' % succeeded)
    logger.info('Number that failed: %d' % failed)
    logger.info('Percent success: %f' % (1 - (1.0 * failed / succeeded)))





    # ss = ff[int(sys.argv[2])].instance
    # bb = ss.body_lines()
    # xx = GPOLocatorParser(bb)
    # qq = xx.parse()
    # qq.tree()
    # js = qq.json()

    import pdb;pdb.set_trace()

    # xx = [x.instance for x in gg]

    # import pdb;pdb.set_trace()
    # for doc in gg:
    #     x = doc.instance
    #     print x
    #     import pdb;pdb.set_trace()


if __name__ == '__main__':
    main()
