## Parsing the US Code

A parser for the US Code's structure, and a work-in-progress parser for the US Code's full content.


### Setup

Create a virtual environment:

    virtualenv virt
    source virt/bin/activate
    pip install -r requirements.txt


### Getting the structure of the Code

To output the hierarchy of the US Code to STDOUT, in JSON:

```bash
./run structure
```

The script will first download the 

Options:

* `--year`: "uscprelim" (the default), or a specific year version of the Code (e.g. "2011")
* `--title`: Do only a specific title (e.g. "5", "5a", "25")
* `--sections`: Return a flat hierarchy of only titles and sections (no intervening layers)
* `--debug`: Output debug messages only, and no JSON output (dry run)
* `--force`: Force a re-download of the US Code. Use this flag if you're automatically running the script at an interval.

Example:

```json
[
  {
    "level": "title", 
    "name": "GENERAL PROVISIONS", 
    "number": "1", 
    "subparts": [
      {
        "level": "chapter", 
        "name": "RULES OF CONSTRUCTION", 
        "number": "1", 
        "subparts": [
          {
            "citation": "usc/1/1", 
            "level": "section", 
            "name": "Words denoting number, gender, and so forth", 
            "number": "1"
          }, 
          {
            "citation": "usc/1/2", 
            "level": "section", 
            "name": "\u201cCounty\u201d as including \u201cparish\u201d, and so forth", 
            "number": "2"
          },
          ...
        ]
      }
    ]
  }
]
```

### Getting the content of the Code (work-in-progress)

To get at the content of the Code:

* Run `download/gpolocator.sh 2011` to download all GPO Locator files for 2011.
* Run download/pdf.sh to download all pdf files for 2011.

Run the debug script with the title as the first argument and the offset of the parsed node in the parsed title (yes, that makes no sense--just enter a number, like 3).

    source virt/bin/activate # if not already activated
    ./run debug title=[title] offset=[offset]

So to view title 11, section 1, which is the definitions section of the bankruptcy code, run:

    ./run debug title=11 offset=3