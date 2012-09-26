import os
import sys
import shutil
from os.path import join
import subprocess

import fson
from gpolocator.parser import getlines
from gpolocator.grouper import group
from gpolocator.utils import title_filename
from gpolocator.structure import GPOLocatorParser


def main(argv):

    args = [
        ('2011', '2006 Edition and Supplement V (2011)'),
        ('2010', '2006 Edition and Supplement IV (2010)'),
        ('2009', '2006 Edition and Supplement III (2009)'),
        ('2008', '2006 Edition and Supplement II (2008)'),
        ('2007', '2006 Edition and Supplement I (2007)'),
        ('2006', '2006 Edition (2006)'),
        ('2005', '2000 Edition and Supplement V (2005)'),
        ('2004', '2000 Edition and Supplement IV (2004)'),
        ('2003', '2000 Edition and Supplement III (2003)'),
        ('2002', '2000 Edition and Supplement II (2002)'),
        ('2001', '2000 Edition and Supplement I (2001)'),
        ('2000', '2000 Edition (2000)'),
        ('1999', '1994 Edition and Supplement V (1999)'),
        ('1998', '1994 Edition and Supplement IV (1998)'),
        ('1997', '1994 Edition and Supplement III (1997)'),
        ('1996', '1994 Edition and Supplement II (1996)'),
        ('1995', '1994 Edition and Supplement I (1995)'),
        ('1994', '1994 Edition (1994)'),
        ]

    path = '/home/thom/code/11USC101'
    try:
        shutil.rmtree(path)
    except OSError:
        pass
    subprocess.check_call('cd /home/thom/code && mkdir 11USC101', shell=True)
    subprocess.check_call('touch %s/README' % path, shell=True)
    subprocess.check_call('cd %s && git init && git add .' % path, shell=True)

    for arg in reversed(args):
        year, msg = arg
        print 'Committing', year, '...'
        title = int(argv[0])
        offset = int(argv[1])
        filename = title_filename(title, year)
        fp = open(filename)
        lines = getlines(fp)
        gg = group(lines)

        ss = gg[offset].instance
        bb = ss.body_lines()
        xx = GPOLocatorParser(bb)
        qq = xx.parse()

        # try:
        #     shutil.rmtree(path)
        # except OSError:
        #     pass
        # os.mkdir(join(path, 'title%d' % title))
        js = qq.json()
        fson.dump(js, join(path, 'title%d' % title))
        cmd = 'cd %r && git add . && git commit -am"%s"' % (path, msg)
        print 'Running', repr(cmd)
        try:
            out = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            print e
    # subprocess.check_call('cd /home/thom/code && octogit create '
    #                       '11USC101 "11 USC 101 in git"', shell=True)
    # subprocess.check_call('cd %s && git push origin master' % path, shell=True)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
