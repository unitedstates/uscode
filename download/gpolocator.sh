# Download and unzip all uscode files for 2011.
# Run it from the uscode folder.
DIR=`pwd`"/data"
DEST="$DIR/uscode.house.gov/zip/2011/"
#echo $DIR
#echo $DEST
mkdir -P $DIR
wget -m -l1 -P $DIR http://uscode.house.gov/zip/2011/
cd $DEST
for filename in `ls`; do unzip $filename; done
find . -type f -name "*zip" -delete
cd $DIR
