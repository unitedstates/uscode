# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 19:24:15 2014
The purpose of this script is to parse the mapping of Public Law sections to U.S. Code sections.
This file parses HTML files such as http://uscode.house.gov/table3/111_148.htm
The output is a list of references, currently printing to standard output.
@author: Pablo, @williampli
"""

from __future__ import division
from bs4 import BeautifulSoup
import re
import sys

def parseTable(f):
   
    soup = BeautifulSoup(f)
    f.close()
    
    t = soup.find('table')
    t3 = t.find_all('tr')


    sections = []
    for row in t3:
        cols = map(lambda x: x.get_text(),row.find_all("td"))
        if len(cols) > 4:
            sections.append((cols[2],cols[3]))
    return sections
                
                

if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        print 'Usage: python ParseTable.py inputHTMLfile.htm'
        sys.exit()
    filename = sys.argv[1]
    f = file(filename,'r')
    sections = parseTable(f)
    print sections
