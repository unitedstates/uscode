# Download and unzip all uscode files for 2010. 
DIR=~/data/uscode/xml
mkdir -p $DIR
wget -P $DIR http://uscode.house.gov/xml/USC_TEST_XML.zip
unzip -d $DIR ~/data/uscode/xml/USC_TEST_XML.zip 

