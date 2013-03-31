# Download and unzip all uscode files for a year.
# Run it from the uscode folder. Specify a year on
# the command line eg: download/gpolocator.sh 2011
DIR=`pwd`"/data"
DEST="$DIR/uscode.house.gov/zip/$1/"
#echo $DIR
#echo $DEST
mkdir -P $DIR
wget -m -l1 -P $DIR http://uscode.house.gov/zip/$1
cd $DEST
for filename in `ls`; do unzip $filename; done
find . -type f -name "*zip" -delete
cd $DIR
