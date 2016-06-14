#!flask/bin/python

"""
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
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

BeaconAlleleRequest = {
    'referenceName': u'',  # required
    'start': 0,  # required
    'referenceBases': u'',  # required
    'alternateBases': u'',  # required
    'assemblyId': '',  # required
    'datasetIds': [],  # optional
    'includeDatasetResponses': False,  # optional
}

BeaconDataset = {
    'id': u'',  # required
    'name': u'',  # required
    'description': u'',  # optional
    'assemblyId': u'',  # required
    'createDateTime': u'',  # required
    'updateDateTime': u'',  # required
    'version': u'',  # optional
    'variantCount': 1,  # optional
    'callCount': 1,  # optional
    'sampleCount': 1,  # optional
    'externalUrl': u'',  # optional
    'info': {}  # optional
}

BeaconOrganization = {
    'id': u'',  # required
    'name': u'',  # required
    'description': u'',  # optional
    'address': u'',  # optional
    'welcomeUrl': u'',  # optional
    'contactUrl': u'',  # optional
    'logoUrl': u'',  # optional
    'info': {}  # optional
}

Beacon = {
    'id': u'',  # required
    'name': u'',  # required
    'apiVersion': u'0.3',  # required
    'organization': BeaconOrganization,  # required
    'description': u'',  # optional
    'version': u'',  # optional
    'welconeUrl': u'',  # optional
    'alternativeUrl': u'',  # optional
    'createDateTime': u'',  # optional
    'updateDateTime': u'',  # optional
    'datasets': [  # optional
        BeaconDataset
    ],
    'sampleAlleleRequests': [  # optional
        BeaconAlleleRequest  # Examples of interesting queries
    ],
    'info': {}
}

BeaconError = {
    'errorCode': 400,  # required
    'message': u''  # optional
}

BeaconDatasetAlleleResponse = {
    'datasetId': u'',  # required
    'exists': True,  # optional (required in no-error cases)
    'error': None,  # optional (required in case of an error)
    'frequency': u'',  # optional
    'variantCount': 1,  # optional
    'callCount': 1,  # optional
    'sampleCount': 1,  # optional
    'note': u'',  # optional
    'externalUrl': u'',  # optional
    'info': {}  # optional
}

BeaconAlleleResponse = {
    'beaconId': u'',  # required
    'exists': True,  # optional (required in no-error cases)
    'error': None,  # optional (required in case of an error)
    'alleleRequest': BeaconAlleleRequest,  # optional
    'datasetAlleleResponses': [  # optional
        BeaconDatasetAlleleResponse
    ]
}


# info function
# TODO: override with the details of your beacon (see https://github.com/ga4gh/beacon-team/ for more details)
@app.route('/beacon-python/', methods=['GET'])
def info():
    return jsonify(Beacon)


# query function
# TODO: plug in the functionality of your beacon (see https://github.com/ga4gh/beacon-team/ for more details)
@app.route('/beacon-python/query', methods=['GET'])
def query():
    # parse query
    BeaconAlleleRequest['referenceName'] = request.args.get('referenceName')
    BeaconAlleleRequest['start'] = int(request.args.get('start'))
    BeaconAlleleRequest['referenceBases'] = request.args.get('referenceBases')
    BeaconAlleleRequest['alternateBases'] = request.args.get('alternateBases')
    BeaconAlleleRequest['assemblyId'] = request.args.get('assemblyId')
    BeaconAlleleRequest['datasetIds'] = request.args.getlist('datasetIds')
    BeaconAlleleRequest['includeDatasetResponses'] = bool(request.args.get('includeDatasetResponses'))

    return jsonify(BeaconAlleleResponse)


# page not found
@app.errorhandler(404)
def not_found(error):
    return 'Page not found (Bad URL)', 404


if __name__ == '__main__':
    app.run()
