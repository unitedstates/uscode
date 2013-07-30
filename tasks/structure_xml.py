# Downloads and uses the XML version of the US Code to extract a table of contents.
# 
# Outputs JSON to STDOUT. Run and save with:
#  ./run structure_xml > structure.json 
#
# options:
#   title: Do only a specific title (e.g. "5", "5a", "25")
#   sections: Return a flat hierarchy of only titles and sections (no intervening layers)
#   debug: Output debug messages only, and no JSON output (dry run)
#   force: Force a re-download of the US Code

import glob, re, lxml.etree, lxml.html, json, sys, os, os.path, urllib, zipfile

import utils

import HTMLParser
pars = HTMLParser.HTMLParser()

section_symbol = u'\xa7'

ns = {
  "uslm": "http://xml.house.gov/schemas/uslm/1.0"
}

def run(options):
  # optional: don't print json out, just --debug information
  debug = options.get('debug', False)

  # optional: limit to a specific --title
  title = options.get("title", None)
  if not title:
    title = "*"
  else:
    title = "xml_usc" + title + "@*"

  # sync XML to disk as needed (cache by default)
  download_usc(options)

  filenames = glob.glob("data/uscode.house.gov/xml/%s.zip" % title)
  filenames.sort()
  
  # optional: --limit to a number of titles
  limit = options.get("limit", None)
  if limit:
    filenames = filenames[0:int(limit)]

  # optional: only retrieve titles and --sections, nothing in between
  sections_only = options.get("sections", False)

  # process titles

  TOC = [ ]
  
  for fn in filenames:
    zf = zipfile.ZipFile(fn, "r")
    xmlbody = zf.read(os.path.basename(fn).replace("xml_", "").replace(".zip", ".xml"))
    #print xmlbody
    dom = lxml.etree.fromstring(xmlbody)
    titlenode = dom.xpath("uslm:main/uslm:title", namespaces=ns)[0]
    proc_node(titlenode, TOC, None, sections_only)

  # Sort the titles (take into account appendix notation).
  TOC.sort(key = lambda title : (int(title["number"].replace("a", "")), title["number"]))
  
  # Write output in JSON to stdout.
  if debug:
    print "\n(dry run only, not outputting)"
  else:
    json.dump(TOC, sys.stdout, indent=2, sort_keys=True, check_circular=False)
  
def proc_node(node, parent, title, sections_only):
  # Form the node for this title/chapter/.../section.
  
  remove_footnotes(node.xpath("uslm:heading", namespaces=ns)[0])
  entry = {
    "level": lxml.etree.QName(node.tag).localname,
    "number": unicode(node.xpath("string(uslm:num/@value)", namespaces=ns)),
    "name": unicode(node.xpath("string(uslm:heading)", namespaces=ns)),
  }
  if entry["level"] == "level": entry["level"] = "heading"
  
  # TODO: For comparison to HTML version only. Remove me.
  entry["name"] = entry["name"].replace(u"\u2019", "'") # curly right apostrophe => straight apostrophe (it's inconsistent, so for diffs: sed -i "s/\\\\u2019/'/g" structure_html.json)
  entry["name"] = entry["name"].replace(u"\u202f", u"\u00a0") # narrow no-break space => no-break space (probably convert this to a space later on)
  entry["name"] = entry["name"].replace(u"\u2013", "-") # replace en-dashes with simple hyphens

  # Text reformatting.
  entry["name"] = entry["name"].strip() # TODO: Flag upstream, remove this line when fixed.
  entry["name"] = entry["name"].replace(u"\u00ad", "") # remove soft hyphens
  entry["number"] = entry["number"].strip() # TODO: Flag upstream, remove this line when fixed.
  entry["number"] = entry["number"].replace(u"\u2013", "-") # replace en-dashes with simple hyphens
  if entry["number"] == "": entry["number"] = None
  
  # Don't record structure of phantom parts.
  if entry["name"] in ("Repealed", "Reserved", "Omitted", "Omitted]", "Transferred", "Transferred]", "Omitted or Transferred", "Vacant]"):
    return
  if re.match(r"(Repealed.*|Transferred|Omitted|Renumbered .*\])(\.|$)", entry["name"]):
    return

  if entry["level"] == "title":
    # for passing into children
    title = entry["number"]
  elif entry["level"] == "section":
    entry["citation"] = "usc/%s/%s" % (title, entry["number"])
    
  # Debugging helper.
  #if entry.get("citation") == "usc/4/107":
  #  print lxml.etree.tostring(node)
  #  print entry
    
  # Recurse into children.
  
  children = []
  
  for child in node.xpath("uslm:title|uslm:subtitle|uslm:chapter|uslm:subchapter|uslm:part|uslm:subpart|uslm:division|uslm:level|uslm:section", namespaces=ns):
    proc_node(child, children, title, sections_only)

  if len(children):
    entry["subparts"] = children

  # TODO: For comparison to HTML version only. Remove me.
  if not len(children) and entry["level"] != "section":
    # don't include parts with no sections
    return

  # Pop back up.

  if sections_only and entry["level"] not in ['title', 'section']:
    # We're only interested in these two levels. Flatten the hierarchy.
    parent.extend(children)
  else:
    # Add this entry to the parent's list of children.
    parent.append(entry)
  
def remove_footnotes(node):
  # Remove footnote text and footnote markers from the heading text.
  # lxml makes removing nodes tricky because the tail text gets removed too, but it needs to be moved.
  def filter_nbsp(t):
    if not t: return ""
    if t[-1] in (u"\u00a0", u"\u202f"): t = t[:-1] # footnotes are often preceded by a non-breaking space which we can remove
    return t
  for n in node.xpath("uslm:note|uslm:ref[@class='footnoteRef']", namespaces=ns):
    if n.tail:
      if n.getprevious() != None:
        n.getprevious().tail = filter_nbsp(n.getprevious().tail) + n.tail
      else:
        n.getparent().text = filter_nbsp(n.getparent().text) + n.tail
    n.getparent().remove(n)
  
def download_usc(options):
  debug = options.get("debug", False)
  
  dest_dir = "data/uscode.house.gov/xml"
  utils.mkdir_p(dest_dir)
  
  base_url = "http://uscode.house.gov/download/"
  index_page = lxml.html.parse(urllib.urlopen(base_url + "download.shtml")).getroot()
  for anode in index_page.xpath('//a[.="[XML]"]'):
    if "uscAll@" in anode.get("href"): continue # skip the all-titles archive
    if "xml_usc34@" in anode.get("href"): continue # title 34 doesn't exist (was repealed)
    source_url = base_url + anode.get("href")
    dest_path = dest_dir + "/" + os.path.basename(anode.get("href"))
    if os.path.exists(dest_path) and not options.get("force", False):
      continue
    os.system("wget -O %s %s" % (dest_path, source_url))
