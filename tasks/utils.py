import os, errno, sys, traceback
import re, htmlentitydefs
import pprint

from pytz import timezone
import datetime, time


# scraper should be instantiated at class-load time, so that it can rate limit appropriately

import scrapelib
scraper = scrapelib.Scraper(requests_per_minute=120, follow_robots=False, retry_attempts=3)


# manage input and output dirs

def output_dir():
  return "data/output"

def input_dir():
  return "data/uscode.house.gov/zip"

def title_filename(title, year=2011):
  year = str(year)
  return os.path.join(input_dir(), year, 'usc%02d.%02d' % (int(title), int(year[2:])))


# general purpose

def log(object):
  if isinstance(object, str):
    print object
  else:
    pprint.pprint(object)

def format_datetime(obj):
  if isinstance(obj, datetime.datetime):
    return obj.replace(microsecond=0, tzinfo=timezone("US/Eastern")).isoformat()
  elif isinstance(obj, str):
    return obj
  else:
    return None

def download(url, destination, force=False):
  cache = os.path.join(cache_dir(), destination)

  if not force and os.path.exists(cache):
    log("Cached: (%s, %s)" % (cache, url))
    with open(cache, 'r') as f:
      body = f.read()
  else:
    try:
      log("Downloading: %s" % url)
      response = scraper.urlopen(url)
      body = str(response)
    except scrapelib.HTTPError as e:
      log("Error downloading %s:\n\n%s" % (url, format_exception(e)))
      return None

    # don't allow 0-byte files
    if (not body) or (not body.strip()):
      return None

    # cache content to disk
    write(body, cache)

  return unescape(body)

def write(content, destination):
  mkdir_p(os.path.dirname(destination))
  f = open(destination, 'w')
  f.write(content)
  f.close()

# mdir -p in python, from:
# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc: # Python >2.5
    if exc.errno == errno.EEXIST:
      pass
    else: 
      raise

# taken from http://effbot.org/zone/re-sub.htm#unescape-html
def unescape(text):

  def remove_unicode_control(str):
    remove_re = re.compile(u'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]')
    return remove_re.sub('', str)

  def fixup(m):
    text = m.group(0)
    if text[:2] == "&#":
      # character reference
      try:
        if text[:3] == "&#x":
          return unichr(int(text[3:-1], 16))
        else:
          return unichr(int(text[2:-1]))
      except ValueError:
        pass
    else:
      # named entity
      try:
        text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
      except KeyError:
        pass
    return text # leave as is

  text = re.sub("&#?\w+;", fixup, text)
  text = remove_unicode_control(text)
  return text

# doesn't actually use the passed-in exception, but, er, I feel like I should pass it in anyway
def format_exception(exception):
  exc_type, exc_value, exc_traceback = sys.exc_info()
  return "\n".join(traceback.format_exception(exc_type, exc_value, exc_traceback))