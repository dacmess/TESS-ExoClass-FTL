#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 19:05:23 2018
The DV flux time series data is stored in h5d format after resampling 
at a coarser time sampling.  Also, some data
about the target from the header of the fits file is also kept 

@author: Christopher J. Burke
"""

import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
import h5py
import glob
import os
import math
import tec_run_parameters as tecrp


def make_data_dirs(prefix, sector, epic):
    secDir = 'S{0:02d}'.format(sector)
    localDir = os.path.join(prefix,secDir)
    if not os.path.exists(localDir):
        os.mkdir(localDir)
    epcDir = '{0:04d}'.format(int(math.floor(epic/1000.0)))
    localDir = os.path.join(prefix,secDir,epcDir)
    if not os.path.exists(localDir):
        os.mkdir(localDir)
    return localDir

def idx_filter(idx, *array_list):
    new_array_list = []
    for array in array_list:
        new_array_list.append(array[idx])
    return new_array_list

def dvts_resamp(file, dirOut, RESAMP, SECTOR=None, overwrite=True):
    """ Resample TESS dv time series file and save as h5d format
        resamp - Resample factor just make it odd okay"""    

    hdulist = fits.open(file)
    prihdr = hdulist[0].header
    nTces = prihdr['NUMTCES']

    dataSpanMax = 0.0
    # Get header information that we should keep
    if not SECTOR is None:
        keepprihdr = ['TICID','RA_OBJ', \
                  'DEC_OBJ','PMRA','PMDEC','PMTOTAL','TESSMAG','TEFF', \
                  'LOGG','RADIUS']
        formatprihdr = [np.uint32, \
                    float,float,float,float,float, \
                    float,float,float,float,float]
    else:
        keepprihdr = ['TICID','SECTOR','PXTABLE','RA_OBJ', \
                      'DEC_OBJ','PMRA','PMDEC','PMTOTAL','TESSMAG','TEFF', \
                      'LOGG','RADIUS']
        formatprihdr = [np.uint32, int, int, \
                        float,float,float,float,float, \
                        float,float,float,float,float]

    # make empty arrays
    kpCadenceNo = np.array([0], dtype=int)
    kpTimetbjd = np.array([0.0], dtype=float)
    kpQuality = np.array([0], dtype=int)
    kpPDC = np.array([0.0], dtype=float)
    for ii in range(nTces):
        # Check if already done
        epic = hdulist[0].header['TICID']
        if SECTOR is None:
            sec = hdulist[0].header['SECTOR']
        else:
            sec = SECTOR
        pn = ii+1
        fileoutput = os.path.join(make_data_dirs(dirOut,sec,epic), 'tess_dvts_{0:016d}_{1:02d}.h5d'.format(epic,pn))
        fileExists=os.path.isfile(fileoutput)
        if (not fileExists) or overwrite:

            extname = 'TCE_{0:d}'.format(ii+1)
            arr = hdulist[extname].data['TIME']
            nImage = len(arr)
    
            cadenceNo = hdulist[extname].data['CADENCENO']
            kpCadenceNo = cadenceNo
            timetbjd = hdulist[extname].data['TIME']
            kpTimetbjd = timetbjd
            lc_init = hdulist[extname].data['LC_INIT']
            lc_init_err = hdulist[extname].data['LC_INIT_ERR']
            lc_white = hdulist[extname].data['LC_WHITE']
            lc_med_detrend = hdulist[extname].data['LC_DETREND']
            lc_model = hdulist[extname].data['MODEL_INIT']
            lc_white_model = hdulist[extname].data['MODEL_WHITE']
            lc_phase = hdulist[extname].data['PHASE']
            pdc_flux = hdulist['statistics'].data['PDCSAP_FLUX']
            pdc_flux_err = hdulist['statistics'].data['PDCSAP_FLUX_ERR']
            deweights = hdulist['statistics'].data['DEWEIGHTS']
            kpQuality = hdulist['statistics'].data['QUALITY']
            kpPDC = hdulist['statistics'].data['PDCSAP_FLUX']

            # Fix the issue of having times close to zero
            # First get time stamps on valid data
            idx = np.where((np.isfinite(timetbjd)) & (np.isfinite(lc_init)) & (np.isfinite(pdc_flux)))[0]
            # minimum time on valid data
            minGdTime = np.min(timetbjd[idx])
            idx = np.where(timetbjd < minGdTime-30.0)[0]
            timetbjd[idx] = np.nan
    
            newNImage = int(np.floor(nImage / RESAMP))
            oldNImage = newNImage*RESAMP
            # trim off the excess images not integral into resamp
            idx = np.arange(0,oldNImage)
            cadenceNo, timetbjd, lc_init, lc_init_err, lc_white, lc_med_detrend, \
                lc_model, lc_white_model, lc_phase, pdc_flux, pdc_flux_err, \
                deweights = idx_filter(idx, cadenceNo, timetbjd, lc_init, lc_init_err, lc_white, lc_med_detrend, \
                                       lc_model, lc_white_model, lc_phase, pdc_flux, pdc_flux_err, \
                                       deweights)
        
            # Do downsampling of data stream
            cadenceNoBeg = np.min(np.reshape(cadenceNo, (newNImage, RESAMP)), axis=1)
            cadenceNoEnd = np.max(np.reshape(cadenceNo, (newNImage, RESAMP)), axis=1)
            cadenceNo = np.mean(np.reshape(cadenceNo, (newNImage, RESAMP)), axis=1, dtype=int)
            timetbjd = np.mean(np.reshape(timetbjd, (newNImage, RESAMP)), axis=1)
            lc_init = np.mean(np.reshape(lc_init, (newNImage, RESAMP)), axis=1)
            lc_init_err = np.mean(np.reshape(lc_init_err, (newNImage, RESAMP)), axis=1)
            lc_white = np.mean(np.reshape(lc_white, (newNImage, RESAMP)), axis=1)
            lc_med_detrend = np.mean(np.reshape(lc_med_detrend, (newNImage, RESAMP)), axis=1)
            lc_model = np.mean(np.reshape(lc_model, (newNImage, RESAMP)), axis=1)
            lc_white_model = np.mean(np.reshape(lc_white_model, (newNImage, RESAMP)), axis=1)
            lc_phase = np.mean(np.reshape(lc_phase, (newNImage, RESAMP)), axis=1)
            pdc_flux = np.sum(np.reshape(pdc_flux, (newNImage, RESAMP)), axis=1)
            pdc_flux_err = np.mean(np.reshape(pdc_flux_err, (newNImage, RESAMP)), axis=1)
            deweights = np.mean(np.reshape(deweights, (newNImage, RESAMP)), axis=1)
    
            # Identify data that is missing or NaN
            idx = np.where((np.isfinite(timetbjd)) & (np.isfinite(lc_init)) & (np.isfinite(pdc_flux)))[0]
            valid_data_flag = np.zeros((newNImage,), dtype=np.bool_)
            valid_data_flag[idx] = True
            
            # Trim all leading in-valid data
            if not valid_data_flag[0]:
                idx = np.where(valid_data_flag)[0]
                if not len(idx) == 0:
                    idx = idx[0]
                    cadenceNoBeg = cadenceNoBeg[idx:]
                    cadenceNoEnd = cadenceNoEnd[idx:]
                    cadenceNo = cadenceNo[idx:]
                    timetbjd = timetbjd[idx:]
                    lc_init = lc_init[idx:]
                    lc_init_err = lc_init_err[idx:]
                    lc_white = lc_white[idx:]
                    lc_med_detrend = lc_med_detrend[idx:]
                    lc_model = lc_model[idx:]
                    lc_white_model = lc_white_model[idx:]
                    lc_phase = lc_phase[idx:]
                    pdc_flux = pdc_flux[idx:]
                    pdc_flux_err = pdc_flux_err[idx:]
                    deweights = deweights[idx:]
                    valid_data_flag = valid_data_flag[idx:]
                else:
                    print('No Valid data? {0:d} {1:d}'.format(ii,epic))
            
            # Get the data span in days for use in federation steps
            idx = np.where(valid_data_flag == True)[0]
            if (len(idx)>0):
                dataSpan = np.max(timetbjd[idx]) - np.min(timetbjd[idx])
                if dataSpan > dataSpanMax:
                    dataSpanMax = dataSpan
    
            # Now save data as h5py 
            f = h5py.File(fileoutput, 'w')
            tmp = f.create_dataset('cadenceNo', data=cadenceNo, compression='gzip') 
            tmp = f.create_dataset('cadenceNoBeg', data=cadenceNoBeg, compression='gzip') 
            tmp = f.create_dataset('cadenceNoEnd', data=cadenceNoEnd, compression='gzip') 
            tmp = f.create_dataset('timetbjd', data=timetbjd, compression='gzip')
            tmp = f.create_dataset('lc_init', data=lc_init, compression='gzip')
            tmp = f.create_dataset('lc_init_err', data=lc_init_err, compression='gzip')
            tmp = f.create_dataset('lc_white', data=lc_white, compression='gzip')
            tmp = f.create_dataset('lc_med_detrend', data=lc_med_detrend, compression='gzip')
            tmp = f.create_dataset('lc_model', data=lc_model, compression='gzip')
            tmp = f.create_dataset('lc_white_model', data=lc_white_model, compression='gzip')
            tmp = f.create_dataset('lc_phase', data=lc_phase, compression='gzip')
            tmp = f.create_dataset('pdc_flux', data=pdc_flux, compression='gzip')
            tmp = f.create_dataset('pdc_flux_err', data=pdc_flux_err, compression='gzip')
            tmp = f.create_dataset('deweights', data=deweights, compression='gzip')
            tmp = f.create_dataset('valid_data_flag', data=valid_data_flag, compression='gzip')
            for i in range(len(keepprihdr)):
                curval = hdulist[0].header[keepprihdr[i]]
                if np.isscalar(curval):
                    tmp = f.create_dataset(keepprihdr[i], data=np.array([hdulist[0].header[keepprihdr[i]]], dtype=formatprihdr[i]))
                else:
                    tmp = f.create_dataset(keepprihdr[i], data=np.array([-1], dtype=formatprihdr[i]))
                            
            f.close()
    return dataSpanMax, kpCadenceNo, kpTimetbjd, kpQuality, kpPDC

if __name__ == "__main__":

    # get run parameters
    tec_root 		= tecrp.tec_root
    tec_run_name	= tecrp.tec_run_name
    data_root_dir       = tecrp.data_root_dir
    dv_time_series_dir	= tecrp.dv_time_series_dir
    ftl_10min		= tecrp.ftl_10min
    ftl_200sec		= tecrp.ftl_200sec
    tgt_2min		= tecrp.tgt_2min

    dirInputs = data_root_dir + dv_time_series_dir + '/'
    #dirInputs = '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-48/ftl-dv-time-series/'
    dirOutputs = tec_root + tec_run_name + '/'
    #dirOutputs = '/nobackupp15/dacaldwe/git/tec/sector48/'

    # base resampling on cadence type, aim for ~10 minute resampling
    if tgt_2min:
        RESAMP = 5
    elif ftl_10min:
        RESAMP = 1
    elif ftl_200sec:
        RESAMP = 3
    else:
        raise Exception(__name__,': Error cadence type not properly defined')
    #RESAMP = 1  ###  USE AN ODD NUMBER HELPS WITH CADENCE NO ###

    SECTOR_OVRRIDE = None # If NOT multisector set this to None ###
    overwrite = True # Set False to keep old results and only do files that dont exist

    fileList = glob.glob(os.path.join(dirInputs, '*dvt.fits*'))
    
    # For debugging a target filter fileList to wanttic string
    #wanttic='278139637'
    #newFileList = []
    #for fil in fileList:
    #    if fil.find(wanttic) != -1:
    #        newFileList.append(fil)
    #fileList = newFileList
    # END target debugging
    
    cnt = 0
    # Keep track of max data span for use in federation
    dataSpanMax = 0.0
    gdFracMax = 0.0
    
    # Do things slightly differently for multi-sector
    minCad = 9999999999999
    maxCad = -1
    cadenceDict = {}
    
    for fil in fileList:
        cnt = cnt + 1
        if np.mod(cnt,10) == 0:
            print(cnt,' Data Span {0:f} GdFrac: {1:f}'.format(dataSpanMax, gdFracMax))
        dataSpan, cadno, timetjd, quality, pdc = dvts_resamp(fil, dirOutputs, RESAMP, SECTOR=SECTOR_OVRRIDE, overwrite=overwrite)
        # Do things differently in single sector versus multi-sector
        if SECTOR_OVRRIDE is None:
            # Single sector portion
            nData = len(quality)
            gdFrac = float(len(np.where((quality==0) & (np.isfinite(pdc)==True))[0]))/float(nData)
            if dataSpan+2.0*gdFrac > dataSpanMax+2.0*gdFracMax:
                dataSpanMax = dataSpan
                gdFracMax = gdFrac
                fout = open('cadnoVtimemap.txt','w')
                for i, cad in enumerate(cadno):
                    momdump = int(0)
                    pdcfinite = int(0)
                    if quality[i] & 32:
                        momdump = int(1)
                    if np.isfinite(pdc[i]):
                        pdcfinite = int(1)
                    fout.write('{0:d} {1:f} {2:d} {3:d} {4:d}\n'.format(int(cad), timetjd[i], int(quality[i]), momdump, pdcfinite))
                fout.close()
        else:
            # multi-sector portion
            for i, curCad in enumerate(cadno):
                cadenceDict[curCad] = timetjd[i]
            dataSpanMax = len(cadenceDict)
                
    # multisector output all times encountered
    if not SECTOR_OVRRIDE is None:    
        # split dictionary into separate cadnece and time arrays
        cadlist = [np.int32(x) for x in cadenceDict.keys()]
        timelist = [np.float64(x) for x in cadenceDict.values()]
        cadarr = np.array(cadlist, dtype=np.int32)
        timearr = np.array(timelist, dtype=float)
        ia = np.argsort(cadarr)
        fout = open('cadnoVtimemap.txt','w')
        for i in ia:
            fout.write('{0:d} {1:f} 0 0 1\n'.format(cadarr[i], timearr[i]))
        fout.close()
