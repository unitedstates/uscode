import os
import sys
import shutil
from os.path import join
import subprocess

from logbook import Logger
from gpolocator import File
import utils


logger = Logger('debug')

def run(options):
    argv = options["argv"]

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

    path = '/home/thom/code/uscode-git'
    try:
        logger.info('Removing tree: %r' % path)
        shutil.rmtree(path)
    except OSError:
        pass

    # Create the repo again.
    logger.info('Creating the git repo.')
    subprocess.check_call('cd /home/thom/code && mkdir -p ' + path, shell=True)
    subprocess.check_call('touch %s/README' % path, shell=True)
    subprocess.check_call('cd %s && git init && git add .' % path, shell=True)
    subprocess.check_call('cd %s && git remote add origin git@github.com:unitedstates/uscode-git.git' % path, shell=True)

    succeeded = 0
    failed = 0
    failed_objs = []
    for title in range(1, 51):

        for arg in reversed(args):

            year, commit_msg = arg
            logger.info('Writing files for %s ...' % year)
            filename = utils.title_filename(title, year)

            title_path = join(path, str(title))

            try:
                os.mkdir(title_path)
            except OSError:
                pass
            else:
                logger.info('created dir %s' % title_path)

            try:
                fp = open(filename)
            except IOError as e:
                logger.warning('No such file: %r: %r' % (filename, e))

            try:
                gpo_file = File(fp)
            except Exception as e:
                logger.critical('The parser failed on %r' % filename)

            for section in gpo_file.sections():
                try:
                    msg = 'Trying to parse %r' % section
                    # logger.info(msg)
                except Exception as e:
                    logger.warning('Something terrible happend.')
                    failed_objs.append((section, e))
                    continue
                try:
                    tree = section.as_tree()
                except Exception as e:
                    logger.critical('Parse failed! %r' % e)
                    failed += 1
                    failed_objs.append((section, e))
                else:
                    succeeded += 1

                section_path = join(title_path, '%s.txt' % str(section.enum()))
                with open(section_path, 'w') as f:
                    tree.filedump(f)

        # import pdb;pdb.set_trace()

        # try:
        #     shutil.rmtree(path)
        # except OSError:
        #     pass
        # os.mkdir(join(path, 'title%d' % title))
        #js = qq.json()
        #fson.dump(js, join(path, 'title%d' % title))
        cmd = 'cd %r && git add . && git commit -am"%s"' % (path, msg)
        print 'Running', repr(cmd)
        try:
            out = subprocess.check_output(commit_msg, shell=True)
        except subprocess.CalledProcessError as e:
            print e
    # subprocess.check_call('cd /home/thom/code && octogit create '
    #                       '11USC101 "11 USC 101 in git"', shell=True)
    # subprocess.check_call('cd %s && git push origin master' % path, shell=True)


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
