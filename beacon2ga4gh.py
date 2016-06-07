#!flask/bin/python
"""
This module will provide a glue layer between the Beacon server and the
standard GA4GH APIs provided by a compliant GA4GH server.
"""
from __future__ import division
from __future__ import unicode_literals
import logging
import ConfigParser
from datetime import date
import ga4gh.client as client

serverURL =""
debugLevel=""
organization=""

def setup_ga4gh_client():
    """
    Return the client library to use for searching the data on the GA4GH
    server specified in the config file.

    This function reads the config file and then
    it initializes the ga4gh client library
    """
    global serverURL
    global debugLevel
    global organization

    config = ConfigParser.ConfigParser()
    try:
        config.read('beacon2ga4gh.cfg')
        serverURL = config.get('refServer', 'url')
        debugLevel = config.get('refServer', 'debugLevel')
        # organization = config.get('refServer', 'organization')
    except ConfigParser.NoSectionError:
        logging.error("section not found in beacon2ga4gh.cfg file, using 1kgenomes.ga4gh.org.")
        serverURL = "http://1kgenomes.ga4gh.org"
    logging.basicConfig(level=debugLevel)
    logging.debug('using {}'.format(serverURL))
    cl = client.HttpClient(serverURL)
    return cl


def check_reference_set(cl, requestedReferenceSet):
    """
    :param cl: ga4gh client library handle to use
    :param requestedReferenceSet: The reference set to look for
    :return: boolean of if the reference set was found
    """
    dataset = cl.searchDatasets().next()
    logging.debug(dataset)

    # Check the reference set match, do we need to search for it?
    referenceSet = cl.searchReferenceSets().next()
    logging.debug(referenceSet)
    if referenceSet.name != requestedReferenceSet:
        logging.warning("returning False for ref set, {} != {}".format(referenceSet['name'], requestedReferenceSet))
        return False
    return True


def findAlleleMatch(allele, foundVariant, pos):
    """
    This function handles the logic for if the variant matches, and if so then where

    :param allele: allele to match (should be only a single char
    :param foundVariant: variant object that holds all the variant information
    :param pos: the actual location to search (may force an indexing into the actual
            variant string for the comparison
    :return: nothing, but does modify the global alleleFound

    notes: see https://github.com/maximilianh/ucscBeacon/blob/master/query line 376, readAllelesVcf(ifh)

    """
    alleleFound = False
    # the variant may start before the address we are searching so figure out
    # where in the string to look
    offset = pos - foundVariant.start
    whichAlt = 0
    for alt in foundVariant.alternateBases:
        logging.debug("looking for {} in alt string {} at string offset {}".format(allele, alt, offset))
        if alt.startswith("<"):
            continue
        if len(alt) > offset:
            foundHere = (allele == alt[offset])
            if len(allele) > 1:
                foundHere |= (allele == alt)
            if foundHere:
                alleleFound |= foundHere
                logging.debug("FOUND allele {}".format(allele))
                return alleleFound, whichAlt   # TODO: only finds the first match
        whichAlt += 1
    return alleleFound, whichAlt   # has indexed past the p[oint, only finds the first match


def search_in_variantset(cl, beaconAlleleRequest, beaconAlleleResponse, variantSet, count):
    """
    This function searches inside a single variant set for the conditions passed in
    :type beaconAlleleResponse: object
    :param cl: GA4GH Client lib to use
    :param beaconAlleleRequest: request data structure
    :param beaconAlleleResponse: response data structure returned
    :param variantSet: variant set to search in
    :param count: count of variants that have been found up to this point
    :return: total count of variants found after this
    """

    pos = beaconAlleleRequest['start']
    chrom = beaconAlleleRequest['referenceName']
    # TODO : this function does not deal with the referenceBases string yet
    # refbases = beaconAlleleRequest['referenceBases']
    allele = beaconAlleleRequest['alternateBases']
    multiReply = beaconAlleleRequest['includeDatasetResponse']

    # fix up chrom by removing "chr" if it is there
    if chrom.startswith("chr"):
        chrom = chrom.replace("chr","")

    # OK, now search from pos-1 to pos on chrom
    logging.debug("VariantSet.id is {}".format(variantSet.id))
    logging.debug("ReverenceName is {}".format(chrom))
    for foundVariant in cl.searchVariants(variantSet.id, start=pos-1, end=pos, referenceName=chrom):
        logging.debug("Variant names: {}".format(foundVariant.names))
        logging.debug("Start: {}, End: {}".format(foundVariant.start, foundVariant.end))
        logging.debug("Reference bases: {}".format(foundVariant.referenceBases))
        logging.debug("Alternate bases: {}".format(foundVariant.alternateBases))
        alleleFound, whichAlt = findAlleleMatch(allele, foundVariant, pos)
        beaconAlleleResponse['exists'] = alleleFound
        # OK, we found one so check to see if we need to search any more
        if alleleFound and not multiReply:
            return
        # implicit else means that we want to search for more, and we need to fill out this data struct
        if alleleFound:
            assert isinstance(foundVariant, object)
            logging.debug('AF = {}'.format(foundVariant.info))
            datasetAlleleResponse = {
                'exists': alleleFound,
                'callCount': len(foundVariant.calls),
                'samplecount': len(foundVariant.calls),
                # TODO : assuming that sampleCount and callCount are the same for now
                'frequency': foundVariant.info['AF'][whichAlt],
                'variantCount': 0,
                'note': '',
                'info': ''
            }
            if len(foundVariant.names) > 0:
                datasetAlleleResponse['info'] = "variantID: " + foundVariant.names[whichAlt]
            beaconAlleleResponse['datasetAlleleResponses'].append(datasetAlleleResponse)

            logging.debug('Running the multi-reply code, count={}'.format(count))
            logging.debug('response={}'.format(beaconAlleleResponse['datasetAlleleResponses'][count]))
            # foundVariant.calls is where we want to search
            for call in foundVariant.calls:
                if call.genotype[0]==(whichAlt+1) or call.genotype[1]==(whichAlt+1): #0 entry is for the reference
                    logging.debug('Count:{} alt:{} call:{}'.format(count, whichAlt, call))
                    beaconAlleleResponse['datasetAlleleResponses'][count]['note'] += ' ' + call.callSetName
                    beaconAlleleResponse['datasetAlleleResponses'][count]['variantCount'] += 1
            count += 1
    return count


def search_variants(cl, BeaconAlleleRequest, BeaconAlleleResponse):
    """
    This function itterates through all the variant sets on the server and calls
        a subfunc to do the actual search in each set found
    :param cl: GA4GH Client lib to use
    :param BeaconAlleleRequest: search data structure
    :param BeaconAlleleResponse: response structure to fill in
    :return:
    """
    """
    :return: returns the global alleleFound
    """
    # This function searches all variant sets on this server.
    count = 0 # index into the optional array of return structures
    # which data set am I supposed to search? should this be passed in to this function?
    dataset = cl.searchDatasets().next()
    logging.debug("dataset %s", dataset)
    for variantSet in cl.searchVariantSets(datasetId=dataset.id):
        logging.debug("---> looping on variant sets, current Name={}".format(variantSet.name))
        count = search_in_variantset(cl, BeaconAlleleRequest, BeaconAlleleResponse, variantSet, count)


def fill_beacon(cl, beacon):
    """
    This function fills in the beacon data structure from the information in the dataset
    residing on the GA4GH server
    :param cl: handle for the GA4GH Client library
    :param beacon: beacon data structure to fill in
    :return: nothing
    """
    global organization

    # TODO we should iterate here and fill in all the beacon info about each of the datasets that this server has
    #       Assuming just one dataset for now
    dataset = cl.searchDatasets().next()
    logging.debug(dataset)
    beacon['id'] = dataset.name
    beacon['name'] = dataset.name
    beacon['description'] = dataset.description

    beacon['createDateTime'] = date(2015, 10, 1).isoformat()
    beacon['updateDateTime'] = date(2015, 10, 1).isoformat()
    beacon['datasets'][0]['createDateTime'] = date(2015, 10, 1).isoformat()
    beacon['datasets'][0]['updateDateTime'] = date(2015, 10, 1).isoformat()
    # TODO need to fill in the ref sets in the beacon data struct
    # Check the reference set match, do we need to search for it?
    referenceSet = cl.searchReferenceSets().next()
    logging.debug(referenceSet)

