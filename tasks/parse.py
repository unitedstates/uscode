import utils
from utils import log

import uscode
import json

def run(options):
  title_number = options.get('title', None)
  # section = options.get('section', None)
  year = options.get('year', 2011) # default to 2011 for now

  if not title_number:
    utils.log("Supply a 'title' argument to parse a title.")
    return

  filename = utils.title_filename(title_number, year)
  title = uscode.title_for(filename)

  sections = title.sections()

  for section in sections:
    section_number = section.enum()
    print "[%s USC %s] Parsing..." % (title_number, section_number)
    bb = section.body_lines()
    xx = uscode.GPOLocatorParser(bb)
    qq = xx.parse()
    output = qq.json()
    
    utils.write(
      json.dumps(output, sort_keys=True, indent=2), 
      uscode_output(year, title_number, section_number)
    )


def uscode_output(year, title, section):
  return "%s/%s/%s/%s.json" % (utils.output_dir(), year, title, section)