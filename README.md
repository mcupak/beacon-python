#Python Beacon Development Kit (PBDK) [![GitHub license](https://img.shields.io/badge/license-mit-blue.svg)](https://raw.githubusercontent.com/mcupak/beacon-python/develop/LICENSE)

##Contents

* [What it is](#what-it-is)
* [System requirements](#system-requirements)
* [How to run it](#how-to-run-it)
* [How it works](#how-it-works)
* [Technologies](#technologies)

##What it is
This project contains BDK (beacon development kit) for Python developers. It provides a skeleton of a simple beacon allowing the developers to plug in their own data/functionality. The API makes sure the response produced is compatible with the [Beacon API](https://github.com/ga4gh/beacon-team/).

##System requirements
All you need to build this project is Python 2 and Flask web framework. If you're running Linux, OS X or Windows with cygwin support, the following commands should be enough to set up Flask (the process is a bit different with the native version of Python on Windows):

    $ pip install virtualenv
    $ virtualenv flask
    $ flask/bin/pip install flask

##How to run it
Launch beacon.py:

    $ chmod a+x beacon.py
    $ ./beacon.py

This starts an embedded server. By default, the application will be available at <http://127.0.0.1:5000>

##How it works
In order to implement a beacon, simply override beacon details and query function in beacon.py (marked with TODO in the source code).

The API takes care of the rest and provides the following endpoints when you start your beacon:

    http://127.0.0.1:5000/beacon-python - information about your beacon
    http://127.0.0.1:5000/beacon-python/query - access to query service

Query example:

    GET http://127.0.0.1:5000/beacon-python/query?referenceName=1&start=1000&referenceBases=A&alternateBases=T&assemblyId=GRCh37&datasetIds=&includeDatasetResponses=true

##Technologies
Python 2, Flask.
