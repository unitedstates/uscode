code
====

A parser for the US Code, and USCprelim. From GPO locator codes to JSON.


To Download the Data
====================

* Run download/gpolocator.sh to download all GPO Locator files for 2011.
* Run download/pdf.sh to download all pdf files for 2011.


To Test out the Parser
======================

Run the debug script with the title as the first argument and the offset of the parsed node in the parsed title (yes, that makes no sense--just enter a number, like 3).

    python gpolocator-debug.py [title] [offset]

So to view title 11, section 1, which is the definitions section of the bankruptcy code, run:
    python gpolocator-debug.py 11 3


