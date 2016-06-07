#!flask/bin/python

'''
The MIT License

Copyright 2014 DNAstack.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

from flask import Flask, jsonify, request
import logging
from beacon2ga4gh import setup_ga4gh_client, check_reference_set, search_variants, fill_beacon

"""
If we want to add Oauth2 support then see the code example in this other beacon on top of
GA4GH example  https://github.com/Genecloud/simplebeacon/blob/master/beacon_rp.py
"""

app = Flask(__name__)
#global GA4GH client lib
cl=""

########### QueryResource for beacon details ###############

# required field(s): allele, chromosome, position, reference
QueryResource = {
    "allele": "A",
    "chromosome": "chr17",
    "position": 35098007,
    "reference": "NCBI37",
    'dataset_id': ""
}

################### Beacon details #########################

BeaconAlleleRequest = {
    'referenceName': u'',
    'start': u'',
    'referenceBases': u'',
    'alternateBases': u'',
    'assemblyId': '',
    'datasetIds': [],
    'includeDatasetResponse': True,
}

BeaconDataset = {
    'id': u'1kgenomes',
    'name': u'1000Genomes',
    'description': u'Variants from the 1000 Genomes project and GENCODE genes annotations',
    'assemblyId': u'NCBI37',
    'createDateTime': u'',
    'updateDateTime': u'',
    'version':u'0.1',   #version of the beacon
    'variantCount': -1,
    'callCount': -1,
    'sampleCount': -1,
    'externalUrl': u'',
    'info': u''
}

BeaconOrganization = {
    'id': u'Sanger',
    'name': u'Sanger Institute',
    'apiVersion': u'0.3',
    'description': u'',
    'address': u'',
    'welcomeUrl': u'http://www.1000genomes.org',
    'contactUrl': u'',
    'logoUrl': u'',
    'info': u''
}

# required field(s): id, name, organization, api
Beacon = {
    'id': u'1000Genomes',
    'name': u'1000Genomes',
    'apiVersion': u'0.3',
    'BeaconOrganization': [
        BeaconOrganization
        ],
    'description': u'Variants from the 1000 Genomes project and GENCODE genes annotations',
    'version':u'0.1',   #version of the beacon
    'welconeUrl': u'http://1kgenomes.ga4gh.org',
    'alternativeUrl': u'',
    'createDateTime': u'',
    'updateDateTime': u'',
    'datasets': [
        BeaconDataset
    ],
    'queries': [
        QueryResource  # Examples of interesting queries
    ],
    'info': u''
}

BeaconDatasetAlleleResponse = {
    'datasetId': u'',
    'exists': u'',
    'error': u'',
    'frequency': u'',
    'variantCount': -1,
    'callCount': -1,
    'sampleCount': -1,
    'note': u'',
    'externalUrl': u'',
    'info': u''
}

BeaconAlleleResponse = {
    'beaconId': u'',
    'exists': u'',
    'error': u'',
    'alleleRequest': [
        BeaconAlleleRequest
    ],
    'datasetAlleleResponses': [
        #BeaconDatasetAlleleResponse
    ]
}


# --------------- Information endpoint (end) ----------------------#

# info function
@app.route('/beacon/info', methods=['GET'])
def info():
    return jsonify(Beacon)


# query function
@app.route('/beacon/query', methods=['GET'])
def query():
    global cl


    ############# ErrorResource for response #################

    # required field(s): name
    ErrorResource = {
        'name': u'error name/code',
        'description': u'error message'
    }

    # parse query
    BeaconAlleleRequest['referenceName'] = request.args.get('referenceName')
    BeaconAlleleRequest['start'] = long(request.args.get('start'))
    BeaconAlleleRequest['referenceBases'] = request.args.get('referenceBases')
    BeaconAlleleRequest['alternateBases'] = request.args.get('alternateBases')
    BeaconAlleleRequest['assemblyId'] = request.args.get('assemblyId')
    #BeaconAlleleRequest['includeDatasetResponse'] = request.args.get('includeDatasetResponse')

    logging.debug(BeaconAlleleRequest)

    # search for the reference first
    # search variant set
    if not check_reference_set(cl, BeaconAlleleRequest['assemblyId']):
        ErrorResource['description'] = 'Unknown assembly ID'
        ErrorResource['name'] = 'Incomplete Query'
        raise IncompleteQuery('IncompleteQuery', status_code=410, ErrorResource=ErrorResource, query=BeaconAlleleRequest,
                              beacon_id=Beacon["id"])

    # make sure the array is cleared before each call to the search
    BeaconAlleleResponse['datasetAlleleResponses'] = []
    logging.debug('Starting with resonse{}'.format(BeaconAlleleResponse))
    search_variants(cl, BeaconAlleleRequest, BeaconAlleleResponse)

    if BeaconAlleleRequest['referenceName'] is None \
            or BeaconAlleleRequest['start'] is None \
            or BeaconAlleleRequest['alternateBases'] is None \
            or BeaconAlleleRequest['assemblyId'] is None:
            ErrorResource['description'] = 'Required parameters are missing'
            ErrorResource['name'] = 'Incomplete Query'
            raise IncompleteQuery('IncompleteQuery', status_code=410, ErrorResource=ErrorResource, query=BeaconAlleleRequest,
                                  beacon_id=Beacon["id"])

    # --------------------------------------------------------------#
    # fill in the rest of the response:
    BeaconAlleleResponse['beaconId'] = Beacon['id']
    return jsonify({"response": BeaconAlleleResponse, "beacon": Beacon['id']})

class IncompleteQuery(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None, ErrorResource=None, query=None, beacon_id=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
        self.ErrorResource = ErrorResource
        self.query = BeaconAlleleRequest
        self.beacon_id = Beacon['id']

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["beacon"] = Beacon
        rv["query"] = BeaconAlleleRequest
        rv['error'] = self.ErrorResource
        return rv

# info function
@app.route('/beacon/', methods=['GET'])
def welcome():
    welcome_message = "Welcome to the Beacon service for the 1000 Genomes GA4GH server. Here is a sample query that can be made against this server (schema version 0.3)."
    url="http://127.0.0.1:5000/beacon/query?referenceName=chr17&start=35098007&alternateBases=A&assemblyId=NCBI37"
    return jsonify({"Greeting": welcome_message, "QueryResource": QueryResource, "URL": url})


# required parameters missing
@app.errorhandler(IncompleteQuery)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    return response


# page not found
@app.errorhandler(404)
def not_found(error):
    return 'Page not found (Bad URL)', 404

def main():
    global cl

    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', filename='gb.log', level=logging.DEBUG)
    logging.debug('Beacon starting')
    cl = setup_ga4gh_client()
    fill_beacon(cl, Beacon)
    app.run()


if __name__ == '__main__':
    main()