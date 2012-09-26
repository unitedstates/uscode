import utils
from utils import log

import uscode

def run(options):
  title_number = options.get('title', None)
  section = options.get('section', None)
  year = options.get('year', 2011) # default to 2011 for now

  if not title_number:
    utils.log("Supply a 'title' argument to parse a title.")
    return

  filename = utils.title_filename(title_number, year)
  title = uscode.title_for(filename)

  print title