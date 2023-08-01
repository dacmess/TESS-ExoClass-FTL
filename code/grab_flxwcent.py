# -*- coding: utf-8 -*-
"""
The routine gets the flux weighted centroids for sectors
Supports multi sector
Will also be used to gather PDC goodness statistics when
I can talk with Jeff Smith.
The Time re-sampling of these is on an hour time scale

AUTHOR: Christopher J. Burke
"""

import numpy as np
import pickle
from gather_tce_fromdvxml import tce_seed
import os
import math
import h5py
from statsmodels import robust
import matplotlib.pyplot as plt
from astropy.io import fits
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



if __name__ == '__main__':
    
    # get run parameters
    run_name            = tecrp.run_name
    multi_sector_flag   = tecrp.multi_sector_flag
    sector_number       = tecrp.sector_number
    tec_root            = tecrp.tec_root
    tec_run_name        = tecrp.tec_run_name
    data_root_dir       = tecrp.data_root_dir
    light_curve_dir	= tecrp.light_curve_dir
    lc_file_prefix      = tecrp.lc_file_prefix
    lc_file_postfix     = tecrp.lc_file_postfix
    ftl_10min           = tecrp.ftl_10min
    ftl_200sec          = tecrp.ftl_200sec
    tgt_2min            = tecrp.tgt_2min

    dirOutputs = tec_root + tec_run_name +'/'
    if multi_sector_flag:
        SECTOR = -1
    else:
        SECTOR = sector_number

    # Resample centroid time series to ~ 60 min  ###  USE AN ODD NUMBER ###
    if tgt_2min:
        RESAMP = 31 
    elif ftl_10min:
        RESAMP = 7
    elif ftl_200sec:
        RESAMP = 19
    else:
        raise Exception(__name__,': Error cadence type not properly defined')

    
    ### Not sure how to parameterize Multi-sector case -DAC 16 Jun 2022
    #  Directory list for Sector light curve files
    # This block is for the multi-sector case
# In the case of a single sector One needs dummy entries for
#  every sector
#    fileInputPrefixList = ['/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-001-20210219/ftl-light-curve/tess2018206045859-s0001-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-002-20210219/ftl-light-curve/tess2018234235059-s0002-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-003-20210219/ftl-light-curve/tess2018263035959-s0003-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-004-20210219/ftl-light-curve/tess2018292075959-s0004-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-005-20210219/ftl-light-curve/tess2018319095959-s0005-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-006-20210219/ftl-light-curve/tess2018349182459-s0006-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-007/ftl-light-curve/tess2019006130736-s0007-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-008/ftl-light-curve/tess2019032160000-s0008-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-009/ftl-light-curve/tess2019058134432-s0009-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-010/ftl-light-curve/tess2019085135100-s0010-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-011/ftl-light-curve/tess2019112060037-s0011-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-012/ftl-light-curve/tess2019140104343-s0012-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-013/ftl-light-curve/tess2019169103026-s0013-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-014-reprocessed/ftl-light-curve/tess2019198215352-s0014-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-015-reprocessed/ftl-light-curve/tess2019226182529-s0015-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-016-reprocessed/ftl-light-curve/tess2019253231442-s0016-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-017-reprocessed/ftl-light-curve/tess2019279210107-s0017-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-018-reprocessed/ftl-light-curve/tess2019306063752-s0018-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-019-reprocessed/ftl-light-curve/tess2019331140908-s0019-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-020/ftl-light-curve/tess2019357164649-s0020-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-021/ftl-light-curve/tess2020020091053-s0021-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-022/ftl-light-curve/tess2020049080258-s0022-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-023/ftl-light-curve/tess2020078014623-s0023-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-024/ftl-light-curve/tess2020106103520-s0024-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-025/ftl-light-curve/tess2020133194932-s0025-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-026/ftl-light-curve/tess2020160202036-s0026-', \
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-027/ftl-light-curve/tess2020186164531-s0027-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-028/ftl-light-curve/tess2020212050318-s0028-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-029/ftl-light-curve/tess2020238165205-s0029-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-030/ftl-light-curve/tess2020266004630-s0030-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-031/ftl-light-curve/tess2020294194027-s0031-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-032/ftl-light-curve/tess2020324010417-s0032-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-033/ftl-light-curve/tess2020351194500-s0033-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-034/ftl-light-curve/tess2021014023720-s0034-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-035/ftl-light-curve/tess2021039152502-s0035-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-036/ftl-light-curve/tess2021065132309-s0036-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-037/ftl-light-curve/tess2021091135823-s0037-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-038/ftl-light-curve/tess2021118034608-s0038-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-039/ftl-light-curve/tess2021146024351-s0039-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-040/ftl-light-curve/tess2021175071901-s0040-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-041/ftl-light-curve/tess2021204101404-s0041-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-042/ftl-light-curve/tess2021232031932-s0042-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-043/ftl-light-curve/tess2021258175143-s0043-',\
#                          '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-044/ftl-light-curve/tess2021284114741-s0044-',\
#			  '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-045/ftl-light-curve/tess2021310001228-s0045-',\
#			  '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-046/ftl-light-curve/hlsp_tess-spoc_tess_phot_'
#]

#    fileInputSuffixList = ['-0120-s_lc.fits.gz', \
#                           '-0121-s_lc.fits.gz', \
#                           '-0123-s_lc.fits.gz', \
#                           '-0124-s_lc.fits.gz', \
#                           '-0125-s_lc.fits.gz', \
#                           '-0126-s_lc.fits.gz', \
#                           '-0131-s_lc.fits.gz', \
#                           '-0136-s_lc.fits.gz', \
#                           '-0139-s_lc.fits.gz', \
#                           '-0140-s_lc.fits.gz', \
#                           '-0143-s_lc.fits.gz', \
#                           '-0144-s_lc.fits.gz', \
#                           '-0146-s_lc.fits.gz',\
#                           '-0150-s_lc.fits.gz',\
#                           '-0151-s_lc.fits.gz',\
#                           '-0152-s_lc.fits.gz',\
#                           '-0161-s_lc.fits.gz',\
#                           '-0162-s_lc.fits.gz',\
#                           '-0164-s_lc.fits.gz',\
#                           '-0165-s_lc.fits.gz',\
#                           '-0167-s_lc.fits.gz',\
#                           '-0174-s_lc.fits.gz',\
#                           '-0177-s_lc.fits.gz',\
#                           '-0180-s_lc.fits.gz',\
#                           '-0182-s_lc.fits.gz',\
#                           '-0188-s_lc.fits.gz',\
#                           '-0189-s_lc.fits.gz',\
#                           '-0190-s_lc.fits.gz',\
#                           '-0193-s_lc.fits.gz',\
#                           '-0195-s_lc.fits.gz',\
#                           '-0198-s_lc.fits.gz',\
#                           '-0200-s_lc.fits.gz',\
#                           '-0203-s_lc.fits.gz',\
#                           '-0204-s_lc.fits.gz',\
#                           '-0205-s_lc.fits.gz',\
#                           '-0207-s_lc.fits.gz',\
#                           '-0208-s_lc.fits.gz',\
#                           '-0209-s_lc.fits.gz',\
#                           '-0210-s_lc.fits.gz',\
#                           '-0211-s_lc.fits.gz',\
#                           '-0212-s_lc.fits.gz',\
#                           '-0213-s_lc.fits.gz',\
#                           '-0214-s_lc.fits.gz',\
#                           '-0215-s_lc.fits.gz',\
#			   '-0216-s_lc.fits.gz',\
#			   '-s0048_tess_v1_lc.fits.gz'
#]


# Single sector block of file prefixes fill with fake values
    fileInputPrefixList = []
    for i in np.arange(1,SECTOR):
        fileInputPrefixList.append('/foo{0:d}'.format(i))
    fileInputPrefixList.append(data_root_dir + light_curve_dir + '/' + lc_file_prefix)
    #fileInputPrefixList.append('/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-48/ftl-light-curve/hlsp_tess-spoc_tess_phot_')
    fileInputSuffixList = []
    for i in np.arange(1,SECTOR):
        fileInputSuffixList.append('/foo{0:d}'.format(i))
    fileInputSuffixList.append(lc_file_postfix + '_lc.fits.gz')
    #fileInputSuffixList.append('-s0048_tess_v1_lc.fits.gz')

    nSector = len(fileInputPrefixList)    

    #fileOut = 'spoc_pdcstats_' + run_name + '.txt'
    #fom = open(fileOut, 'w')
    vetFile = 'spoc_fluxtriage_' + run_name + '.txt'
    #vetFile = 'junk.txt'

    # Load the tce data h5
    tceSeedInFile = run_name + '_tce.h5'
    tcedata = tce_seed()
    all_tces = tcedata.fill_objlist_from_hd5f(tceSeedInFile)
    
    alltic = np.array([x.epicId for x in all_tces], dtype=np.int64)
    allpn = np.array([x.planetNum for x in all_tces], dtype=int)
    allatvalid = np.array([x.at_valid for x in all_tces], dtype=int)
    allrp = np.array([x.at_rp for x in all_tces])
    allrstar = np.array([x.rstar for x in all_tces])
    alllogg = np.array([x.logg for x in all_tces])
    allper = np.array([x.at_period for x in all_tces])
    alltmags = np.array([x.tmag for x in all_tces])
    allmes = np.array([x.mes for x in all_tces])
    allsnr = np.array([x.at_snr for x in all_tces])
    alldur = np.array([x.at_dur for x in all_tces])
    allsolarflux = np.array([x.at_effflux for x in all_tces])
    allatdep = np.array([x.at_depth for x in all_tces])
    allatepoch = np.array([x.at_epochbtjd for x in all_tces])
    alltrpvalid = np.array([x.trp_valid for x in all_tces])
    allatrpdrstar = np.array([x.at_rpDrstar for x in all_tces])
    allatrpdrstare = np.array([x.at_rpDrstar_e for x in all_tces])
    allatadrstar = np.array([x.at_aDrstar for x in all_tces])

    # Load the  flux vetting
    dataBlock = np.genfromtxt(vetFile, dtype=[int,int,int,'S1'])
    fvtic = dataBlock['f0']
    fvpn = dataBlock['f1']
    fvvet = dataBlock['f2']
    
    allvet = np.zeros_like(allpn)
    for i in range(len(allvet)):
        idx = np.where((alltic[i] == fvtic) & (allpn[i] == fvpn))[0]
        if len(idx) > 0:
            allvet[i] = fvvet[idx]
    # only keep tces with both valid dv and trapezoid fits
    # and flux vetted pass
    idx = np.where((allatvalid == 1) & (alltrpvalid == 1) & (allsolarflux > 0.0) & \
                   (allvet == 1))[0]
    alltic, allpn, allatvalid, allrp, allrstar, alllogg, allper, alltmags, \
            allmes, allsnr, alldur, allsolarflux, allatdep, allatepoch, \
            allatrpdrstar, allatrpdrstare, allatadrstar = idx_filter(idx, \
            alltic, allpn, allatvalid, allrp, allrstar, alllogg, allper, alltmags, \
            allmes, allsnr, alldur, allsolarflux, allatdep, allatepoch, \
            allatrpdrstar, allatrpdrstare, allatadrstar)
            
    # Get flux weighted centroids  and PDC stats over flux triage passing TCEs
    for i, curTic in enumerate(alltic):
        print('{:d} of {:d}'.format(i, len(alltic)))
        curPn = allpn[i]
        hasSector = np.zeros((nSector,), dtype=int)
        pdcTot = np.zeros((nSector,), dtype=float)
        pdcNoise = np.zeros((nSector,), dtype=float)
        pdcCor = np.zeros((nSector,), dtype=float)
        
        # Find files for each sector
        for k in range(nSector):
            fileInput = '{0}{1:016d}{2}'.format(fileInputPrefixList[k], curTic, fileInputSuffixList[k])
            fileOutput = os.path.join(make_data_dirs(dirOutputs, SECTOR, curTic), 'tess_flxwcent_{0:016d}_{1:02d}_{2:02d}.h5d'.format(curTic,curPn, k+1))
            if os.path.isfile(fileInput):
                hdulist = fits.open(fileInput)
                
                # Get some PDC statistics
                hasSector[k] = 1
                try:
                    pdcTot[k] = hdulist[1].header['PDC_TOT']
                except:
                    print('Cannot find PDC_TOT {0:d} sec: {1:d}'.format(curTic, k))
                pdcNoise[k] = hdulist[1].header['PDC_NOI']
                pdcCor[k] = hdulist[1].header['PDC_COR']
                pdcStats = np.array([pdcTot[k], pdcNoise[k], pdcCor[k]], dtype=float)
                flxw_centr1 = hdulist[1].data['MOM_CENTR1']
                flxw_centr2 = hdulist[1].data['MOM_CENTR2']
                time = hdulist[1].data['TIME']
                dqflgs = hdulist[1].data['QUALITY']
                nImage = len(time)
                newNImage = int(np.floor(nImage / RESAMP))
                oldNImage = newNImage*RESAMP
                # trim off the excess images not integral into resamp
                idx = np.arange(0,oldNImage)
                flxw_centr1, flxw_centr2, time, dqflgs = idx_filter(idx, \
                    flxw_centr1, flxw_centr2, time, dqflgs)
        
                # Do downsampling of data stream
                time = np.mean(np.reshape(time, (newNImage, RESAMP)), axis=1)
                flxw_centr1 = np.median(np.reshape(flxw_centr1, (newNImage, RESAMP)), axis=1)
                flxw_centr2 = np.median(np.reshape(flxw_centr2, (newNImage, RESAMP)), axis=1)
                dqflgs = np.bitwise_or.reduce(np.reshape(dqflgs, (newNImage, RESAMP)), axis=1)
    
                # Identify data that is missing or NaN
                idx = np.where((np.isfinite(time)) & (np.isfinite(flxw_centr1)) & (np.isfinite(flxw_centr2)))[0]
                valid_data_flag = np.zeros((newNImage,), dtype=np.bool_)
                valid_data_flag[idx] = True
                idx = np.where(dqflgs == 0)[0]
                valid_data_flag[idx] = True 
                # Now save data as h5py 
                f = h5py.File(fileOutput, 'w')
                tmp = f.create_dataset('time', data=time, compression='gzip') 
                tmp = f.create_dataset('flxw_centr1', data=flxw_centr1, compression='gzip')
                tmp = f.create_dataset('flxw_centr2', data=flxw_centr2, compression='gzip')
                tmp = f.create_dataset('dqflgs', data=dqflgs, compression='gzip')
                tmp = f.create_dataset('valid_data_flag', data=valid_data_flag, compression='gzip')
                tmp = f.create_dataset('pdc_stats', data=pdcStats)
                
                print(curTic, 'alpha')                


#        fo = open(fileOutput, 'w')
#        # Write out the best fit parameters as a header
#        #for j in range(len(ioblk.physvals)): 
#        #    fo.write('# {:s} {:f}\n'.format(ioblk.physval_names[j], ioblk.bestphysvals[j]))
#
#        for j in range(len(ioblk.normts)):
#            strout = '{:f} {:f} {:f}\n'.format(ioblk.normts[j], ioblk.normlc[j]-1.0, ioblk.modellc[j]-1.0)
#            fo.write(strout)
#        fo.close()
#        
#
#    fom.close()
