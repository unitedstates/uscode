#!/usr/bin/python
import os, sys 
import httplib2
from lxml import etree
from StringIO import StringIO
import re
import simplejson

# Table Three Scraper http://uscode.house.gov/table3/table3years.htm
# The scrapers grab the URLs for each year from 1789 to 2011, go one directory down to grab the directory, then go one directory below and grab the whole page.  THIS CODE TAKES A WHILE TO RUN.  It may be better to tweak just for the years you want.  Also, could use some refactoring, e.g. merge some of the functions.

# This script downloads files into the current directory

# GLOBAL VARIABLES

# Specify the years you want in a set
years = { 1950 }

# for testing purposes, the number of files downloaded can be limited.
LIMIT_SUBSUBRELEASES = False
LIMIT = 5

def mainscraper(content): #function to parse Table 3 website
	doc = etree.parse(StringIO(content), parser=etree.HTMLParser())
	releases = []
	subreleases = []
	for element in doc.xpath('//div[@class="alltable3years"]'):   #Could also use "alltable3statutesatlargevolumes"
		for d_element in element.xpath('span'):
			text = d_element.xpath('a')[0].text
			unitext = unicode(text).encode(sys.stdout.encoding, 'replace')
			for m_element in d_element.xpath('a'):
				addy = m_element.attrib['href']
				year = addy.replace( 'year', '' )
				year = year.replace( '.htm', '' )
				if int( year ) in set( years ): 
					url = "http://uscode.house.gov/table3/" + addy
				        #print unitext, url
				        #releases += [(unitext, url)]
					subreleases += add_subrelease(url)
					#return subreleases
				else:
					pass
	return subreleases #releases, subreleases

def subscraper(content): #function to parse Table 3 website
	doc = etree.parse(StringIO(content), parser=etree.HTMLParser())
	subsubreleases = []	
	releases = []
	for element in doc.xpath('//div[@class="yearmaster"]'):   #Could also use "statutesatlargevolumemasterhead"
		for d_element in element.xpath('span'):
			text = d_element.xpath('a')[0].text
			unitext = unicode(text).encode(sys.stdout.encoding, 'replace')
			for m_element in d_element.xpath('a'):
				addy = m_element.attrib['href']
				url = "http://uscode.house.gov/table3/" + addy
				print addy
				#print text, url
				#releases += [(text, url)]
				subsubreleases.append( add_subsubrelease(url) )
				if LIMIT_SUBSUBRELEASES and len( subsubreleases ) == LIMIT:
					return subsubreleases


	return	subsubreleases

def add_release(url): #function grab main page data
	http = httplib2.Http('/tmp/httpcache')
	response, content = http.request(url)
	if response.status != 200:
	    sys.stderr.write('Error, returned status: %s\n' % response.status)
	    sys.exit(1) #bomb out, non-zero return indicates error
	#print content
	return mainscraper(content)
	
def add_subrelease(url): #function to grab sub page data
	http = httplib2.Http('/tmp/httpcache')
	response, content = http.request(url)
	if response.status != 200:
	    sys.stderr.write('Error, returned status: %s\n' % response.status)
	    sys.exit(1) #bomb out, non-zero return indicates error
	#print content
	return subscraper(content)

def add_subsubrelease(url): #function to grab sub, sub page data
	http = httplib2.Http('/tmp/httpcache')
	response, content = http.request(url)
	if response.status != 200:
	    sys.stderr.write('Error, returned status: %s\n' % response.status)
	    sys.exit(1) #bomb out, non-zero return indicates error
	# print content
	return url, content

def main():
	dataset = []
	x = add_release("http://uscode.house.gov/table3/table3years.htm") #Could also use "/alltable3statutesatlargevolumes.html"
	for filename, html_string in x:
		final_pagename = filename.split('/')[-1]
		with open( final_pagename, 'w' ) as f:
			f.write( html_string )
		sys.stderr.write( "Wrote %s\n" % ( final_pagename ) )
		

if __name__ == '__main__':
	main()
