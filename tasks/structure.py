# Uses the XHTML files to extract a table of contents for the US Code.
# run with: ./run xhtml_to_structure year=2011 > structure.json 

import glob, re, lxml.html, json, sys
import HTMLParser

pars = HTMLParser.HTMLParser()
section_symbol = u'\xa7'

def run(options):
  year = options.get("year", "uscprelim") # default to USCprelim


  # Output data structure.
  TOC = [ ]
  path = None
  

  # optional: don't print json out, just --debug information
  debug = options.get('debug', False)

  # optional: limit to a specific --title
  title = options.get("title", None)
  if title:
    title = "*usc%02d" % int(title) # doesn't handle appendix titles e.g. 5a :/
  else:
    title = "*usc*"

  filenames = glob.glob("data/uscode.house.gov/xhtml/" + year + "/%s.htm" % title)
  filenames.sort()

  # optional: --limit to a number of titles
  limit = options.get("limit", None)
  if limit:
    filenames = filenames[0:int(limit)]

  # Loop through all titles of the code...
  for fn in filenames:
    match = re.search(r"usc(\d+a?)\.htm$", fn, re.I)
    if not match: continue
    
    title = match.groups(1)[0]
    if debug:
      print "[%s] Processing title..." % title

    # Parse the XHTML file...
    dom = lxml.html.parse(fn)
    
    # The file structure is flat. Loop through the XML
    # nodes in this title.
    for n in dom.find("body/div"):
      # Look for comments of the form <!-- expcite:... -->
      # This tells us the current table of contents location for the following <h3>.
      m = re.match(ur"<!-- expcite:(.*\S)\s*-->", unicode(n))
      if m:
        # This is a "!@!"-separated string giving the table-of-contents
        # path to each section as we see it.
        expcite = m.group(1)
        
        # These comments have HTML entities. Replace them with unicode.
        expcite = expcite.replace("&nbsp;", " ")
        expcite = pars.unescape(expcite)
        
        # Parse the table of contents path.
        path = parse_expcite(expcite)
            
      elif n.tag == "h3":
        # All headings are h3s. Check if it starts with the curly S section symbol.
        h3 = n.text_content()
        if not h3.startswith(section_symbol): continue
        
        # The most recent expcite path is the TOC location of this section.
        if not path: raise Exception("h3 without path")
        
        # Insert the section into our TOC structure.
        parse_h3(path, h3, TOC)
        
        # Clear so we don't reuse the path on the next h3.
        path = None

  # Sort the titles (take into account appendix notation).
  TOC.sort(key = lambda title : (int(title[0][1].replace("a", "")), title[0][1]))
  
  # Reformat the output.
  TOC = [reformat_structure(title) for title in TOC]

  # Write output in JSON to stdout.
  if debug:
    print "\n(dry run only, not outputting)"
  else:
    json.dump(TOC, sys.stdout, indent=True, sort_keys=True, check_circular=False)
  
def parse_expcite(expcite):
  path = expcite.split("!@!")
  
  # Parse each part of the path:
  for i in xrange(len(path)):
    if re.match(r"\[.*-(REPEALED|RESERVED|OMITTED|TRANSFERRED)\]\s*$", path[i], re.I):
      # This part is repealed. No need to process this path at all.
      path = None
      break
    
    m = re.match(r"(TITLE|SUBTITLE|CHAPTER|SUBCHAPTER|PART|SUBPART|DIVISION) ([^\-]+)-(.*)$|Secs?\. (.*)", path[i], re.I)
    if not m:
      # Some random text string. It's a part of a title with no level specifier.
      # We'll call it a "heading" level. In Title 50a, there are just names of
      # acts under the title, no apparent chapter.
      path[i] = ("heading", None, path[i])
      
    elif m.group(1):
      # Matches TITLE|CHAPTER...
      # Store as (TITLE|CHAPTER, NUMBER, NAME)
      # Replace en-dashes in the number with simple dashes, as we do with section numbers.
      path[i] = (m.group(1).lower(), m.group(2).replace(u"\u2013", "-"), m.group(3))
      
      # Reformat title appendices: XXX, APPENDIX => XXXa.
      if i == 0 and path[i][0] == "title" and ", APPENDIX" in path[i][1]:
        path[i] = (path[i][0], path[i][1].replace(", APPENDIX", "a"), path[i][2] + " (APPENDIX)")
      elif i == 0 and path[i][0] == "title" and path[i][2] == "APPENDIX": # titles 5, 18 look like this
        path[i] = (path[i][0], path[i][1] + "a", path[i][2])
      
    elif m.group(4) and i == len(path) - 1:
      # Matches a section number or range of sections.
      # We'll get this information from the next <h3> element, which also has the
      # section title.
      path.pop() 
      
    else:
      raise Exception("Invalid expcite?")  
      
  return path
  
def parse_h3(path, h3, TOC):
  # Skip sections that are just placeholders.
  if re.match(section_symbol + section_symbol + r"?(.*?)\. (Repealed.*|Transferred|Omitted)(\.|$)", h3):
    # This is for multiple sections, which are always repealed, or
    # repealed/transferred sections.
    return
    
  # Reformat section numbers. Replace en-dashes with simple dashes, as we do with chapter etc. numbers.
  h3 = h3.replace(u"\u2013", "-")
    
  # Parse the section number and description, and add that to the path.
  m = re.match(section_symbol + r"(.*?)\.? (.*)", h3)
  if not m: raise Exception("Could not parse: " + h3)
  path.append( ("section", m.group(1), m.group(2)) )
  
  # Add the new path into the TOC, making a structure like:
  #  [ ( (title, 17, Copyright), [
  #       ... sub parts ..
  #      ])
  #  ]
  _toc = TOC
  for p in path:
    if len(_toc) == 0 or _toc[-1][0] != p:
      _toc.append( (p, []) )
    _toc = _toc[-1][1] # move in  

def reformat_structure(entry):
  ret = {
    "level": entry[0][0],
    "number": entry[0][1],
    "name": entry[0][2],
  }
  if len(entry[1]):
    ret["subparts"] = [reformat_structure(e) for e in entry[1]]
  return ret
  
