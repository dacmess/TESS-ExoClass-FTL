# -*- coding: utf-8 -*-
"""
This routine brings in all the TEC attributes and metrics
 for the final ranking and generates the Tier lists and the TEC reports
 
 AUTHOR: Christopher J. Burke
"""

import numpy as np
import os
from subprocess import call
import glob
from shutil import copyfile
import argparse

if __name__ == '__main__':
    # Parse the command line arguments for multiprocessing
    # With Gnu parallel with 13 cores
    # seq 0 15 | parallel --results merge_results python merge4tev.py -w {} -n 16
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", type=int,\
                        default = 0, \
                        help="Worker ID Number 0 through nWrk-1")
    parser.add_argument("-n", type=int,\
                        default = 1, \
                        help="Number of Workers")
    

    args = parser.parse_args() 
    # These are for parallel procoessing
    wID = int(args.w)
    nWrk = int(args.n)

    ###### Edit the paths and SECTOR number below ######
    sourceDir = '/nobackupp15/spocops/git/tec/sector48FTL/pdfs'
    outDir = '/nobackupp15/spocops/git/tec/sector48FTL/tevpdfs'
    #miniDir = '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2522/sector-45/ftl-dv-reports'
    miniDir = '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-48/ftl/target'
    SECTOR = 48 
    ###### End of edits, the rest should be ok for FTL ######

    miniHdr = 'hlsp_tess-spoc_tess_phot_'
    miniTail = '_tess_v1_dvm.pdf'
    #miniTail = '-s0045-s0045_tess_v1_dvm.pdf'
    multiSector = False
    
    if multiSector:
        useSector = 1000+SECTOR
    else:
        useSector = SECTOR
        
    fileList = glob.glob(os.path.join(sourceDir,'*pdf'))
    ticIds = np.array([], dtype=np.int64)
    pns = np.array([], dtype=np.int64)
    for curFilePath in fileList:
        curFile = os.path.split(curFilePath)[1]
        filePieces = curFile.split('-')
        ticIds = np.append(ticIds, int(filePieces[2]))
        pns = np.append(pns, int(filePieces[3].split('.')[0]))
        print(filePieces[2], ' ', filePieces[3])
    idx = np.lexsort((ticIds,pns))
    ticIds = ticIds[idx]
    pns = pns[idx]
    
    uniqTicIds = np.unique(ticIds)
    
    for i, curTic in enumerate(uniqTicIds):
        print('{:d} of {:d} -- {:d}'.format(i, len(uniqTicIds), curTic))
        if np.mod(i, nWrk) == wID:
            idxTic = np.where(ticIds == curTic)[0]
            outFile = os.path.join(outDir, 'tec-s{0:04d}-{1:016d}-00001_dvm.pdf'.format(useSector, curTic))
            miniList = glob.glob(os.path.join(miniDir,'{0}*{1:016d}*{2}'.format(miniHdr,curTic,miniTail)))
    #        miniFile = os.path.join(miniDir, '{0}{1:016d}{2}'.format(miniHdr,curTic,miniTail))
    #        miniExists = os.path.isfile(miniFile)
            if len(idxTic) == 1:
                curPn = pns[idxTic[0]]
                inFile = os.path.join(sourceDir, 'tec-s{0:04d}-{1:016d}-{2:02d}.pdf'.format(SECTOR, curTic, curPn))
    
    #            if miniExists:
                if len(miniList)>0:
                    comstring = 'gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile={0} {1} {2}'.format(outFile, miniList[0], inFile)
                    tmp = call(comstring, shell=True)
                else:
                    print('Warning DV mini for TIC {0:d} Does not Exist!!!'.format(curTic))
                    copyfile(inFile, outFile)
            elif len(idxTic) > 1:
                inFiles = []
    #            if miniExists:
                if len(miniList)>0:
                    inFiles.append(miniList[0])
                else:
                    print('Warning DV mini for TIC {0:d} Does not Exist!!!'.format(curTic))

                for ii in idxTic:
                    inFiles.append(os.path.join(sourceDir, 'tec-s{0:04d}-{1:016d}-{2:02d}.pdf'.format(SECTOR, curTic, pns[ii])))
                comstring = 'gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile={0} '.format(outFile)
                for ifil in inFiles:
                    comstring += ' {0} '.format(ifil)
                tmp = call(comstring, shell=True)
    
                print('help2')
print('help')
    
