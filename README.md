Parsing the US Code
====

A parser for the US Code. From GPO locator codes to JSON.


To Download the Data
====================

* Run `download/gpolocator.sh 2011` to download all GPO Locator files for 2011.
* Run download/pdf.sh to download all pdf files for 2011.

Setup
=====

Create a virtual environment:

    virtualenv virt
    source virt/bin/activate
    pip install -r requirements.txt

To Test out the Parser
======================

Run the debug script with the title as the first argument and the offset of the parsed node in the parsed title (yes, that makes no sense--just enter a number, like 3).

    source virt/bin/activate # if not already activated
    ./run debug title=[title] offset=[offset]

So to view title 11, section 1, which is the definitions section of the bankruptcy code, run:

    ./run debug title=11 offset=3
