#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 28 11:51:04 2018
Federate/ephemeris match known confirmed planets hosted
at NExScI with the TCEs.  Must be online for the search to
work.  Also queries MAST for TIC's that may be near.

@author: Christopher J. Burke
"""

import pickle
import numpy as np
import toidb_federate as fed
from gather_tce_fromdvxml import tce_seed
import csv
import sys
import time
import json
import cjb_utils as cjb
try: # Python 3.x
    from urllib.parse import quote as urlencode
    from urllib.request import urlretrieve
except ImportError:  # Python 2.x
    from urllib import pathname2url as urlencode
    from urllib import urlretrieve
try: # Python 3.x
    import http.client as httplib 
except ImportError:  # Python 2.x
    import httplib  
import urllib
import urllib2

def mastQuery(request):

    server='mast.stsci.edu'

    # Grab Python Version 
    version = '3.6.3' #".".join(map(str, sys.version_info[:3]))

    # Create Http Header Variables
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain",
               "User-agent":"python-requests/"+version}

    # Encoding the request as a json string
    requestString = json.dumps(request)
    requestString = urlencode(requestString)
    
    # opening the https connection
    conn = httplib.HTTPSConnection(server)

    # Making the query
    conn.request("POST", "/api/v0/invoke", "request="+requestString, headers)

    # Getting the response
    resp = conn.getresponse()
    head = resp.getheaders()
    content = resp.read().decode('utf-8')

    # Close the https connection
    conn.close()

    return head,content



def genericFed(per, epc, tryper, tryepc, trydur, trypn, trytic, tStart, tEnd):
    ts = fed.timeseries(tStart, tEnd)
    federateResult = fed.federateFunction(per, epc, ts, \
                    tryper, tryepc, trydur)
    bstpn = trypn[federateResult[0]]
    bsttic = trytic[federateResult[0]]
    bstMatch = int(federateResult[1])
    bstStat = federateResult[2]
    bstPeriodRatio = federateResult[3]
    bstPeriodRatioFlag = federateResult[4]
    bstFederateFlag = federateResult[5]
    
    return bstpn, bsttic, bstMatch, bstStat, bstPeriodRatio, bstPeriodRatioFlag, bstFederateFlag

# Do cone search around TIC
def query_ticcone(curRa, curDec, searchRad):
    

    # Do cone search around this position
    startTime = time.time()
    request = {'service':'Mast.Catalogs.Filtered.Tic.Position', \
               'params':{'columns':'c.*', \
                         'filters':[ \
                                    {'paramName':'Tmag',\
                                     'values':[{'min':0, 'max':20.0}]}], \
                         'ra':'{:10.5f}'.format(curRa),\
                         'dec':'{:10.5f}'.format(curDec),\
                         'radius':'{:10.7f}'.format(searchRad/3600.0) \
                         }, \
                'format':'json', 'removenullcolumns':False}
    while True:    
        headers, outString = mastQuery(request)
        outObject = json.loads(outString)
        if outObject['status'] != 'EXECUTING':
                break
        if time.time() - startTime > 30:
                print('Working...')
                startTime = time.time()
        time.sleep(5)
     
    ticList = [x['ID'] for x in outObject['data']]


    return ticList



if __name__ == '__main__':
    fout = open('federate_knownP_sector4_20190129.txt', 'w')
    wideSearch = True
    searchRad = 180.0 # Arcsecond search radius for other TICs

    # Load known transiting planet table from NEXSCI   
    whereString = 'pl_tranflag = 1 and st_elat<0.0'
    url = 'https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI?'
    data = {'table':'planets', \
            'select':'pl_name,pl_orbper,pl_tranmid,pl_trandur,ra,dec', \
            'format':'csv', \
            'where':whereString}
    url_values = urllib.urlencode(data)
    #print url_values
    queryData = urllib2.urlopen(url + url_values)


#    url_values = urllib.parse.urlencode(data)
    #print url_values
#    queryData = urllib.request.urlopen(url + url_values)
    returnPage = queryData.read()
    dtypeseq = ['U40']
    dtypeseq.extend(['f8'] * 5)
    dataBlock = np.genfromtxt(returnPage.splitlines(), delimiter=',', skip_header=1, \
                        dtype=dtypeseq)
    gtName = dataBlock['f0']
    gtPer = dataBlock['f1']
    gtEpc = dataBlock['f2']-2457000.0
    gtDur = dataBlock['f3']*24.0 # Is in days convert to hours
    gtRa = dataBlock['f4']
    gtDec = dataBlock['f5']
    gtTIC = np.arange(len(gtName))
    gtTOI = np.arange(len(gtName))
    print("Tot # PCs: {0:d}".format(len(gtName)))


    # Load the tce data pickle    
    tceSeedInFile = 'sector4_20190129_tce.pkl'
    fin = open(tceSeedInFile, 'rb')
    all_tces = pickle.load(fin)
    fin.close()
    
    alltic = np.array([x.epicId for x in all_tces], dtype=np.int64)
    allpn = np.array([x.planetNum for x in all_tces], dtype=np.int)
    allatvalid = np.array([x.at_valid for x in all_tces], dtype=np.int)
    allrp = np.array([x.at_rp for x in all_tces])
    allper = np.array([x.at_period for x in all_tces])
    alldur = np.array([x.at_dur for x in all_tces])
    allepc = np.array([x.at_epochbtjd for x in all_tces])
    alltrpvalid = np.array([x.trp_valid for x in all_tces], dtype=np.int)
    alltrpdur = np.array([x.trp_dur for x in all_tces])
    alltrpepc = np.array([x.trp_epochbtjd for x in all_tces])
    alltcedur = np.array([x.pulsedur for x in all_tces])
    alltceepc = np.array([x.tce_epoch for x in all_tces])
    alltceper = np.array([x.tce_period for x in all_tces])
    # Go through each tce and use valid fits from dv, trpzd, tce in that order for matching
    useper = np.zeros_like(allper)
    useepc = np.zeros_like(allper)
    usedur = np.zeros_like(allper)
    idx = np.where((allatvalid == 0) & (alltrpvalid == 0) )[0]
    useper[idx] = alltceper[idx]
    useepc[idx] = alltceepc[idx]
    usedur[idx] = alltcedur[idx]
    idx = np.where((alltrpvalid == 1))[0]
    useper[idx] = alltceper[idx]
    useepc[idx] = alltrpepc[idx]
    usedur[idx] = alltrpdur[idx]
    idx = np.where((allatvalid == 1))[0]
    useper[idx] = allper[idx]
    useepc[idx] = allepc[idx]
    usedur[idx] = alldur[idx]
#    ia = np.argsort(alltic)
#    alltic, allpn, useper, useepc, usedur = cjb.idx_filter(ia, alltic, \
#                                allpn, useper, useepc, usedur)

    # write to header the inputs
    fout.write('# Match {:s}\n'.format('Exoplanet Archive Confirmed Planets'))
    fout.write('# To {:s}\n'.format(tceSeedInFile))

#    if np.min(useepc)-1.0 < uowStart:
    uowStart = np.min(useepc)-1.0
    uowEnd = np.max(useepc) + 13.0
    # Go  the ground truth data (ground truth acts like KOIs in kepler federation)
    for i in range(len(gtTIC)):
        curTic = gtTIC[i]
        curper = gtPer[i]
        curepc = gtEpc[i]
        curToi = gtTOI[i]
        curName = gtName[i]
        curRa = gtRa[i]
        curDec = gtDec[i]
        # If wideSearch True then query MAST for 
        #  all TICs within searchRad arcsec of this target
        if wideSearch:
            otherTICs = np.array(query_ticcone(curRa, curDec, searchRad), dtype=np.int64)
            #otherTICs = np.sort(otherTICs)
            idx = np.array([], dtype=np.int64)
            for ot in otherTICs:
                idxtmp = np.where(ot == alltic)[0]
                idx = np.append(idx, idxtmp)                
        else:
            # find this tic in the tces
            idx = np.where(curTic == alltic)[0]
        if len(idx) > 0:
            # Potential match
            tryper = useper[idx]
            tryepc = useepc[idx]
            trypn = allpn[idx]
            trydur = usedur[idx]
            trytic = alltic[idx]
            bstpn, bsttic, bstMatch, bstStat, bstPeriodRatio, bstPeriodRatioFlag, bstFederateFlag = \
                    genericFed(curper, curepc, tryper, tryepc, trydur, trypn, trytic, uowStart, uowEnd)
            
        else:
            #print("No match in Ground truth")
            bstpn = 0
            bstMatch = -1
            bstStat = -1.0
            bstPeriodRatio = -1.0
            bstPeriodRatioFlag = 0
            bstFederateFlag = 0
            bsttic = 0
        str = '{:12d} {:8.2f} {:s} {:12d} {:2d} {:2d} {:6.3f} {:2d} {:10.5f} {:2d}\n'.format(curTic, \
                   curToi, curName.astype('string').replace(" ",""), bsttic, bstpn, bstMatch, bstStat, bstPeriodRatioFlag, \
                   bstPeriodRatio, bstFederateFlag)
        if bstpn > 0:
            fout.write(str)
            print(str)
    fout.close()
    print('hello world')