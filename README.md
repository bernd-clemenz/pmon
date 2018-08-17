# Simple HTTP process monitor
This module allows to scan for responses of certain HTTP
addresses.

[License](./LICENSE)

## Method
Very simple: a series of URLs for GET requests is defined and
queried. the results are stored in a JSON data file.

## Requirements
- Python 3 installed. [Python](http://www.python.org)
- Module requirements are resolved by **setup.py**
- Internet connection for setup

## Installation
The tool is a simple Python 3 module it can be installed
manually into the local Python 3 environment by switching to
the directory with **pmon** files and executing

    python setup.py
    
After installation it can be executed with the command

    python -m pmon [--conf=config-file-name]
    
If one does not want to install it, it can be run just by
switching to the directory and executing:

    python -m pmon
   
## Configuration
The module is configured via an traditional ini file. If no name
is given the config file name defaults to _pmon.ini_.

### Section 'pmon'
The general configuration of the tool.

| Name | Description |
|------|-------------|
| **id** | Identifies the instance of the monitor. Set it to a unique number |
| **data.file** | Name of the file, to store the results for further evaluation |
| **log.file** | Name of log output file |
| **timeout** | Wait for response in seconds until fail | 

### Section 'urls'
A dynamic section where the URLs for GET access are configured.
The entries follow the pattern **url.XX** where XX is a
number, unique to the section.

### Example
    [pmon]
    id=isc_001
    data.file = pmon.json

    [urls]
    url.1 = https://some-valid-url.io
    url.2 = http://invalid.url.io
    
## Result
Every execution adds to the URL-named lists. The result codes are:

| Code | Description |
|------|-------------|
| SUCCESS | All good |
| EXCEPTION_ERROR | Some thing in the environment went wrong, like network or system unavailable. |
| APPLICATION_ERROR | Service is there, but could not respond error-free to the request |
The rest of the entries is self-explanatory.

```javascript
{
    "http://invalid.url.io": [
        {
            "message": "HTTPConnectionPool(host='invalid.url.io', port=80):",
            "result": "EXCEPTION_ERROR",
            "time": "2018-07-17 00:16:53.259895"
        }
    ],
    "https://some-valid-url.io": [
        {
            "message": "OK",
            "result": "SUCCESS",
            "time": "2018-07-17 00:16:45.709041"
        }
    ],
    "https://some-valid-url.io/invalid-file.html": [
        {
            "message": 404,
            "result": "APPLICATION_ERROR",
            "time": "2018-07-17 00:16:55.263712"
        }
    ]
}
```