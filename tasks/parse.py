import utils
from utils import log

import uscode

def run(options):
  title = options.get('title', None)
  section = options.get('section', None)

  if not title or not section:
    utils.log("Supply a 'title' and 'section' argument to parse a title.")

  