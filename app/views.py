import pdb
import os
from os import listdir
from os.path import abspath, join
import json

from uscode.parsexml import *

filenames = []
for fn in listdir(DATA):
	if fn.endswith('xml'):
		filenames.append(join(DATA, fn))



def titles(filenames):
	res = []
	for fn in filenames:
		print fn
		title = Title.from_filename(fn)
		res.append((title.enum, title.header))

	def sorter(t):
		return int(t[0])

	return dict(kidtype='title', 
	            kids=sorted(res, key=sorter))


def chapters()

def build():
	pass

if __name__ == "__main__":
	res = titles(filenames)
	pdb.set_trace()

