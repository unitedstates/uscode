from os import chdir as cd
from os.path import dirname, abspath
import subprocess

if __name__ == "__main__":

	# Compile the templates.
	cd(dirname(__file__))
	subprocess.call([
		'java', '-jar', 
		'SoyToJsSrcCompiler.jar',
		'--outputPathFormat',
		abspath('../build/uscode/js/templates.js'),
		'templates.soy',
		])