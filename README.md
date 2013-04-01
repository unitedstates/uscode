## Parsing the US Code

A parser for the US Code's structure, and a work-in-progress parser for the US Code's full content.

### Setup

Create a virtual environment:

    virtualenv virt
    source virt/bin/activate
    pip install -r requirements.txt

### Getting the structure of the Code

To get a `structure.json` file of the Code - its hierarchy but not its content - you can parse the most recent XHTML version of the Code (USCprelim)

First, download the XHTML to disk:

```bash
./download/xhtml.sh uscprelim
```

Then, run the script, which defaults to USCprelim:

```bash
./run xhtml_to_structure
```


### Getting the content of the Code (alpha)

To get at the content of the Code:

* Run `download/gpolocator.sh 2011` to download all GPO Locator files for 2011.
* Run download/pdf.sh to download all pdf files for 2011.

Run the debug script with the title as the first argument and the offset of the parsed node in the parsed title (yes, that makes no sense--just enter a number, like 3).

    source virt/bin/activate # if not already activated
    ./run debug title=[title] offset=[offset]

So to view title 11, section 1, which is the definitions section of the bankruptcy code, run:

    ./run debug title=11 offset=3