# Download all XHTML uscode files for a year.
# Run it from the uscode folder. Specify a year on
# the command line eg: download/xhtml.sh 2011
DIR=`pwd`"/data"
DEST="$DIR/uscode.house.gov/xhtml/$1/"
#echo $DIR
#echo $DEST
mkdir -P $DIR
wget -m -l1 -P $DIR http://uscode.house.gov/xhtml/$1

