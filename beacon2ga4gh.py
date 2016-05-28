#!flask/bin/python
"""
This module will provide a glue layer between the Beacon server and the
standard GA4GH APIs provided by a compliant GA4GH server.
"""
from __future__ import division
from __future__ import unicode_literals
import logging
import ConfigParser

import ga4gh.client as client

serverURL =""
debugLevel=""

def setup_ga4gh_client():
    """
    Return the client library to use for searching the data on the GA4GH
    server specified in the config file.

    This function reads the config file and then
    it initializes the ga4gh client library
    """
    global serverURL
    global debugLevel

    config = ConfigParser.ConfigParser()
    try:
        config.read('beacon2ga4gh.cfg')
        serverURL = config.get('refServer', 'url')
        debugLevel = config.get('refServer', 'debugLevel')
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
    if referenceSet != requestedReferenceSet:
        logging.warning("returning False for ref set, {} != {}".format(referenceSet, requestedReferenceSet))
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
    for alt in foundVariant.alternateBases:
        logging.debug("looking for {} in alt string {} at string offset {}".format(allele, alt, offset))
        if alt.startswith("<"):
            continue
        if len(alt) > offset:
            foundHere = (allele == alt[offset])
            if foundHere:
                alleleFound |= foundHere
                logging.debug("FOUND allele {}".format(allele))
    return alleleFound

def search_in_variantset(cl, pos, chrom, allele, variantSet):
    """
    This function searches inside a single variant set for the conditions passed in
    :param cl: GA4GH Client lib to use
    :param pos: position opn chromosome to search
    :param chrom: Which chromosome to search
    :param allele: Single base to search for
    :param variantSet: variant set to search in
    :return: nothing, but uses global alleleFound
    """

    # this function does the actual search
    # fix up chrom
    if chrom.startswith("chr"):
        chrom = chrom.replace("chr","")
    # OK, now search from pos-1 to pos on chrom
    alleleFound = False  #start every search by setting this to false
    logging.debug("VariantSet.id is {}".format(variantSet.id))
    logging.debug("ReverenceName is {}".format(chrom))
    for foundVariant in cl.searchVariants(variantSet.id, start=pos, end=pos+1, referenceName=chrom, callSetIds=[]):
        logging.debug("Variant names: {}".format(foundVariant.names))
        logging.debug("Start: {}, End: {}".format(foundVariant.start, foundVariant.end))
        logging.debug("Reference bases: {}".format(foundVariant.referenceBases))
        logging.debug("Alternate bases: {}".format(foundVariant.alternateBases))
        alleleFound = findAlleleMatch(allele, foundVariant, pos)
        logging.debug(foundVariant)
        if alleleFound:
            break
    return alleleFound

def search_variants(cl, pos, chrom, allele):
    """
    This function itterates through all the variant sets on the server and calls
        a subfunc to do the actual search in eact set found
    :param cl: GA4GH Client lib to use
    :param pos: position opn chromosome to search
    :param chrom: Which chromosome to search
    :param allele: Single base to search for
    :return: returns the global alleleFound
    """
    # This function searches all varaiant sets on this server.
    alleleFound = False  #initialize to False before each series of searches
    observedF = 0
    # pos is the 1-based beacon location on the chrom to search
    # chrom is the string that holds the alleles to look for
    logging.debug("search_variants, pos= %s, chrom= %s, allele= %s", pos, chrom, allele)

    # which data set am I supposed to search? should this be passed in to this function
    dataset = cl.searchDatasets().next()
    logging.debug("dataset %s", dataset)
    for variantSet in cl.searchVariantSets(datasetId=dataset.id):
        logging.debug("---> looping on variant sets, current Name={}".format(variantSet.name))
        alleleFound = search_in_variantset(cl, pos, chrom, allele, variantSet)
    return alleleFound


def fill_beacon(cl, beacon):
    """
    This function fills in the beacon data structure from the information in the dataset
    residing on the GA4GH server
    :param cl: handle for the GA4GH Client library
    :param beacon: beacon data structure to fill in
    :return: nothing
    """
    # TODO I should iterate here and fill in all the beacon info about each of the datasets that this server has
    dataset = cl.searchDatasets().next()
    logging.debug(dataset)
    beacon['id'] = dataset.name
    beacon['name'] = dataset.name
    beacon['description'] = dataset.description
    beacon['organization'] = dataset.name  # TODO: Get from config file

    # TODO need to fill in the ref sets in the beacon data struct
    # Check the reference set match, do we need to search for it?
    referenceSet = cl.searchReferenceSets().next()
    logging.debug(referenceSet)
