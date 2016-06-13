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


class IncompleteQuery(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None, ErrorResource=None, query=None, beacon_id=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
        self.ErrorResource = ErrorResource
        self.query = query
        self.beacon_id = beacon_id

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["beacon"] = self.beacon_id
        rv["query"] = self.query
        rv['error'] = self.ErrorResource
        return rv


app = Flask(__name__)

# --------------- Information endpont (start) --------------------#

# TODO: override with the details of your beacon

########### QueryResource for beacon details ###############

# required field(s): allele, chromosome, position, reference
QueryResource = {
    "allele": '',
    "chromosome": '',
    "position": 0,
    "reference": '',
    'dataset_id': ''
}

################### Beacon details #########################

BeaconAlleleRequest = {
    'referenceName': u'',
    'start': u'',
    'referenceBases': u'',
    'alternateBases': u'',
    'assemblyId': '',
    'datasetIds': [],
    'includeDatasetResponse': False,
}

BeaconDataset = {
    'id': u'',
    'name': u'',
    'description': u'',
    'assemblyId': u'',
    'createDateTime': u'',
    'updateDateTime': u'',
    'version':u'',   #version of the beacon
    'variantCount': -1,
    'callCount': -1,
    'sampleCount': -1,
    'externalUrl': u'',
    'info': u''
}

BeaconOrganization = {
    'id': u'',
    'name': u'',
    'apiVersion': u'0.3',
    'description': u'',
    'address': u'',
    'welcomeUrl': u'',
    'contactUrl': u'',
    'logoUrl': u'',
    'info': u''
}

# required field(s): id, name, organization, api
Beacon = {
    'id': u'',
    'name': u'',
    'apiVersion': u'0.3',
    'BeaconOrganization': [
        BeaconOrganization
        ],
    'description': u'',
    'version':u'',   #version of the beacon
    'welconeUrl': u'',
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
@app.route('/beacon-python/info', methods=['GET'])
def info():
    return jsonify(Beacon)


# query function
# TODO: plug in the functionality of your beacon
@app.route('/beacon-python/query', methods=['GET'])
def query():
    # parse query
    BeaconAlleleRequest['referenceName'] = request.args.get('referenceName')
    BeaconAlleleRequest['start'] = long(request.args.get('start'))
    BeaconAlleleRequest['referenceBases'] = request.args.get('referenceBases')
    BeaconAlleleRequest['alternateBases'] = request.args.get('alternateBases')
    BeaconAlleleRequest['assemblyId'] = request.args.get('assemblyId')
    #BeaconAlleleRequest['includeDatasetResponse'] = request.args.get('includeDatasetResponse')

    # ---- TODO: override with the necessary response details  ----#

    if BeaconAlleleRequest['referenceName'] is None \
            or BeaconAlleleRequest['start'] is None \
            or BeaconAlleleRequest['alternateBases'] is None \
            or BeaconAlleleRequest['assemblyId'] is None:
            ErrorResource['description'] = 'Required parameters are missing'
            ErrorResource['name'] = 'Incomplete Query'
            raise IncompleteQuery('IncompleteQuery', status_code=410, ErrorResource=ErrorResource, query=BeaconAlleleRequest,
                                  beacon_id=Beacon["id"])

    # --------------------------------------------------------------#

    return jsonify({"response": BeaconAlleleResponse, "beacon": Beacon['id']})


# info function
@app.route('/beacon-python/', methods=['GET'])
def welcome():
    return 'WELCOME!!! Beacon of Beacons Project (BoB) provides a unified REST API to publicly available GA4GH Beacons. BoB standardizes the way beacons are accessed and aggregates their results, thus addressing one of the missing parts of the Beacon project itself. BoB was designed with ease of programmatic access in mind. It provides XML, JSON and plaintext responses to accommodate needs of all the clients across all the programming languages. The API to use is determined using the header supplied by the client in its GET request, e.g.: "Accept: application/json".'


# required parameters missing
@app.errorhandler(IncompleteQuery)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    return response


# page not found
@app.errorhandler(404)
def not_found(error):
    return 'Page not found (Bad URL)', 404


if __name__ == '__main__':
    app.run()
