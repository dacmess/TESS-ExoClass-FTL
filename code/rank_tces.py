# -*- coding: utf-8 -*-
"""
This routine brings in all the TEC attributes and metrics
 for the final ranking and generates the Tier lists and the TEC reports
 
 AUTHOR: Christopher J. Burke
"""

import numpy as np
import pickle
from gather_tce_fromdvxml import tce_seed
import os
from subprocess import call
import math
import h5py
import argparse
import glob
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


def mstar_from_stellarprops(rstar, logg):
    """Gives stellar mass from the rstar and logg
       INPUT:
         rstar - Radius of star [Rsun]
         logg - log surface gravity [cgs]
       OUTPUT:
         mstar - stellar mass [Msun]
    """
    # Convert logg and rstar into stellar mass assuming logg_sun=4.437
    mstar = 10.0**logg * rstar**2. / 10.0**4.437
    return mstar

def transit_duration(rstar, logg, per, ecc):
    """Transit duration
       assuming uniform distribution of cos(inc) orbits,
       assuming rstar/a is small, and assuming rp/rstar is small.
       INPUT:
        rstar - Radius of star [Rsun]
        logg - log surface gravity [cgs]
        per - Period of orbit [day]
        ecc - Eccentricity; hardcoded to be < 0.99 
       OUTPUT:
        durat - Transit duration [hr]
       COMMENTS:  example:  x=transit_duration(1.0,4.437,365.25,0.0)
                            x=10.19559 [hr] duration for planet in 1 year orbit
                            around sun
    """
    # Replace large ecc values with 0.99
    ecc = np.where(ecc > 0.99, 0.99, ecc)
    # Convert logg and rstar into stellar mass
    mstar = mstar_from_stellarprops(rstar, logg)
    # Semi-major axis in AU
    semia = mstar**(1.0/3.0) * (per/365.25)**(2.0/3.0)
    # transit duration e=0 including pi/4 effect of cos(inc) dist
    r_sun = 6.9598e10 # cm
    au2cm = 1.49598e13 # 1 AU = 1.49598e13 cm
    durat = (per*24.0) / 4.0 * (rstar*r_sun) / (semia*au2cm)
    #transit duration e > 0
    durat = durat * np.sqrt(1.0-ecc**2);

    return durat

def idx_filter(idx, *array_list):
    new_array_list = []
    for array in array_list:
        new_array_list.append(array[idx])
    return new_array_list

if __name__ == '__main__':
    # Parse the command line arguments for multiprocessing
    # With Gnu parallel with 13 cores
    # seq 0 12 | parallel --results rank_tces_results python rank_tces.py -w {} -n 13
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

    # get run parameters
    run_name            = tecrp.run_name
    multi_sector_flag   = tecrp.multi_sector_flag
    sector_number       = tecrp.sector_number
    start_sector        = tecrp.start_sector
    end_sector          = tecrp.end_sector
    tec_root            = tecrp.tec_root
    tec_run_name        = tecrp.tec_run_name
    data_root_dir       = tecrp.data_root_dir
    dv_reports_dir      = tecrp.dv_reports_dir
    dv_file_prefix      = tecrp.dv_file_prefix
    dv_file_postfix     = tecrp.dv_file_postfix
    ftl_10min           = tecrp.ftl_10min
    ftl_200sec          = tecrp.ftl_200sec
    tgt_2min            = tecrp.tgt_2min


    summaryFolder = data_root_dir + dv_reports_dir
    summaryPrefix = dv_file_prefix
    # Note: DV report file names differ between 2-min & FTL outputs
    if tgt_2min:
        summaryPostfix = dv_file_postfix + '_dvs.pdf'
    elif ftl_10min:
        summaryPostfix = dv_file_postfix + '_dvs-'
    elif ftl_200sec:
        summaryPostfix = dv_file_postfix + '_dvs-'
    else:
        raise Exception(__name__,': Error cadence type not properly defined')

    #summaryPrefix = 'hlsp_tess-spoc_tess_phot_-'
    #summaryPostfix = '_tess_v1_dvs-'
    SECTOR1 = start_sector
    SECTOR2 = end_sector

    doPNGs = False
    pngFolder = tec_root + tec_run_name + '/pngs/'
    doMergeSum = True
    if nWrk == 1:
        doMergeSum = False
    pdfFolder = tec_root + tec_run_name + '/pdfs/'
    sesMesDir = tec_root + tec_run_name
    
    if multi_sector_flag:
        SECTOR = -1
    else:
        SECTOR = sector_number

    fileOut1 =           'spoc_ranking_Tier1_' + run_name + '.txt'
    fileOut2 =           'spoc_ranking_Tier2_' + run_name + '.txt'
    fileOut3 =           'spoc_ranking_Tier3_' + run_name + '.txt'
    vetFile =            'spoc_fluxtriage_' + run_name + '.txt'
    modshiftFile =       'spoc_modshift_' + run_name + '.txt'
    modshiftFile2 =      'spoc_modshift_med_' + run_name + '.txt'
    sweetFile =          'spoc_sweet_' + run_name + '.txt'
    toiFederateFile =    'federate_toiWtce_' + run_name + '.txt'
    knowPFederateFile =  'federate_knownP_' + run_name + '.txt'
    selfMatchFile =      'selfMatch_' + run_name + '.txt'
    modumpFile =         'spoc_modump_' + run_name + '.txt'

    # Load the tce data h5
    tceSeedInFile = run_name + '_tce.h5'
    tcedata = tce_seed()
    all_tces = tcedata.fill_objlist_from_hd5f(tceSeedInFile)
    
    # Define maximum good planet radius
    maxPlanetRadiusRearth = 25.0

    ### Define test thresholds
    # Odd-Even test
    OEThreshDefault = 2.8
    OEThreshHighSNR = 4.0
    highSNROE = 30.0 # for high-SNR targets used stricter Odd-Even thresh

    # PDC Noise metric
    minPDCNoiseMetric = 0.8

    # Sweet test on Std-dev ratio
    minSweetResidRatio = 0.8

    # Momentum dump corresponding with transits
    maxMomentumDumpFraction = 0.9

    # Define rank ramp limits
    rplims = [2.0, 6.0]
    meslims = [12.0, 9.0]
    ses2meslims = [0.3, 0.6]
    tessmaglims = [9.0, 12.0]
    durratlims = [0.1, 1.5]
    solarfluxlims = [1.5, 4.0]
    snr2meslims = [0.9, 1.1]
    reldepthlims = [0.1, 0.3]
    centlims = [2.0, 3.0]
    oelims = [0.05, 5.0e-2]
    
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
    alltrpvalid = np.array([x.trp_valid for x in all_tces], dtype=int)
    alltrpdep = np.array([x.trp_depth for x in all_tces])
    allsesinmes = np.array([x.maxsesinmes for x in all_tces])
    allcentoot = np.array([x.cent_oot_offset for x in all_tces])
    allcentoote = np.array([x.cent_oot_offset_e for x in all_tces])
    allcenttic = np.array([x.cent_tic_offset for x in all_tces])
    allcenttice = np.array([x.cent_tic_offset_e for x in all_tces])
    alloesig = np.array([x.oe_signif for x in all_tces])
    allcentootsig = allcentoot/allcentoote
    allcentticsig = allcenttic/allcenttice
    allcentootsig = np.where(allcentootsig < 0.0, 99.0, allcentootsig)
    allcentticsig = np.where(allcentticsig < 0.0, 99.0, allcentticsig)


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
    alltic, allpn, allrp, allrstar, alllogg, allper, alltmags, \
            allmes, allsnr, alldur, allsolarflux, allatdep, alltrpdep, allsesinmes, \
            allcentootsig, allcentticsig, alloesig,\
            allcentoote, allcenttice = idx_filter(idx, \
            alltic, allpn, allrp, allrstar, alllogg, allper, alltmags, \
            allmes, allsnr, alldur, allsolarflux, allatdep, alltrpdep, allsesinmes, \
            allcentootsig, allcentticsig, alloesig, allcentoote, allcenttice)

    # load the modshift test information
    dtypeseq=['i4','i4']
    dtypeseq.extend(['f8']*17)
    dtypeseq.extend(['i4']*6)
    dtypeseq.extend(['f8','f8'])
    dataBlock = np.genfromtxt(modshiftFile, dtype=dtypeseq)
    modTic = dataBlock['f0']
    modPN = dataBlock['f1']
    modOESig = dataBlock['f6']
    modUniqFlg = dataBlock['f19']
    modSecFlg = dataBlock['f21']
    modSecOvrFlg = dataBlock['f23']
    modSecOvrRsn = dataBlock['f24']
    modAlbedo2s = dataBlock['f25']
    modAlbedo = dataBlock['f26']
    
    # load the modshift test information based on median detrending
    dtypeseq=['i4','i4']
    dtypeseq.extend(['f8']*17)
    dtypeseq.extend(['i4']*6)
    dtypeseq.extend(['f8','f8'])
    dataBlock = np.genfromtxt(modshiftFile2, dtype=dtypeseq)
    modTic2 = dataBlock['f0']
    modPN2 = dataBlock['f1']
    modOESig2 = dataBlock['f6']
    modUniqFlg2 = dataBlock['f19']
    modSecFlg2 = dataBlock['f21']
    modSecOvrFlg2 = dataBlock['f23']
    modSecOvrRsn2 = dataBlock['f24']
    modAlbedo2s2 = dataBlock['f25']
    modAlbedo2 = dataBlock['f26']
 
    # load the sweet test information
    dtypeseq=['i4','i4']
    dtypeseq.extend(['f8']*17)
    dataBlock = np.genfromtxt(sweetFile, dtype=dtypeseq)
    swTic = dataBlock['f0']
    swPN = dataBlock['f1']
    swResidRatio = dataBlock['f18']
    
    # load TOI federatin file
    dtypeseq=['i4','f8','U2','i4','i4','i4','f8','i4','f8','i4']
    dataBlock = np.genfromtxt(toiFederateFile, dtype=dtypeseq)
    toiFedTic = dataBlock['f3']
    toiFedPN = dataBlock['f4']
    toiFedQual = dataBlock['f9']
    # Use these to bypass federation
    #toiFedTic = np.array([0,1])
    #toiFedPN = np.array([10,10])
    #toiFedQual = np.array([0,0])
    
    # load Known Planet federation File
    dtypeseq=['i4','f8','U40','i4','i4','i4','f8','i4','f8','i4']
    dataBlock = np.genfromtxt(knowPFederateFile, dtype=dtypeseq)
    kpFedTic = dataBlock['f3']
    kpFedPN = dataBlock['f4']
    # Use these to bypass federation
    #kpFedTic = np.array([0,1])
    #kpFedPN = np.array([10,10])
    
    # load TCE vs TCE match file
    dtypeseq=['i4','i4','i4','i4','i4','f8','i4','f8','i4','f8','i4']
    dataBlock = np.genfromtxt(selfMatchFile, dtype=dtypeseq)
    smFedTic1 = dataBlock['f0']
    smFedPN1 = dataBlock['f1']
    smFedTic2 = dataBlock['f2']
    smFedPN2 = dataBlock['f3']
    smFedSep = dataBlock['f9']
    smFedMatch = dataBlock['f8']
    smFedNFed = dataBlock['f10']
# Pre MS1-6 criteria
#    idx = np.where((smFedMatch == 1) & (smFedSep<1.3))[0]
    idx1 = np.where((smFedNFed == 1) & (smFedSep<3.3))[0]
    idx2 = np.where((smFedNFed > 1))[0]
    idx = np.append(idx1, idx2)
    smFedTic1 = smFedTic1[idx]
    smFedPN1 = smFedPN1[idx]

    # Load the PDC fit goodness statistics
    pdcTic = np.array([], dtype=int)
    pdcPn = np.array([], dtype=int)
    pdcNoi = np.array([], dtype=float)
    pdcCor = np.array([], dtype=float)
    for i, curTic in enumerate(alltic):
        curPn = allpn[i]
        # For multisector run find minimum pdc added Noise
        #  Also results were only valid for sector 4 onwards
        firstSec = 4
        if SECTOR1 > firstSec:
            firstSec = SECTOR1
        minPdcNoi = 1.0
        maxPdcCor = 0.0
        for jj in np.arange(firstSec,SECTOR2+1):
            pdcResults = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic), 'tess_flxwcent_{0:016d}_{1:02d}_{2:02d}.h5d'.format(curTic,curPn, jj))
            if os.path.isfile(pdcResults):
                f = h5py.File(pdcResults,'r')
                pdcStats = np.array(f['pdc_stats'])
                if pdcStats[1] < minPdcNoi:
                    minPdcNoi = pdcStats[1]
                if pdcStats[2] > maxPdcCor:
                    maxPdcCor = pdcStats[2]
        pdcTic = np.append(pdcTic, curTic)
        pdcPn = np.append(pdcPn, curPn)
        pdcNoi = np.append(pdcNoi, minPdcNoi)
        pdcCor = np.append(pdcCor, maxPdcCor)

    # load the momentum dump transit fraction data
    dtypeseq=['i4','i4','f8']
    dataBlock = np.genfromtxt(modumpFile, dtype=dtypeseq)
    mdTic = dataBlock['f0']
    mdPN = dataBlock['f1']
    mdFrac = dataBlock['f2']

               
    # calculate expected duration
    expdur = transit_duration(allrstar, alllogg, allper, 0.0)
    durrat = np.abs(1.0 - alldur / expdur)
    ses2mes = allsesinmes/allmes
    snrrat = allsnr/allmes
    depdiff = np.abs((allatdep - alltrpdep)/allatdep)
    
    # Planet radius rank
    rprank = 1.0 - (allrp-rplims[0])/(rplims[1] - rplims[0])*0.9
    rprank[rprank<0.1] = 0.1
    rprank[rprank>1.0] = 1.0
    rprank = np.log10(rprank)

    # MES rank
    mesrank = (allmes-meslims[1])/(meslims[0]-meslims[1])*0.9 + 0.1    
    mesrank[mesrank<0.1] = 0.1
    mesrank[mesrank>1.0] = 1.0
    mesrank = np.log10(mesrank)
    
    #tess mag rank
    tmagrank = 1.0 - (alltmags-tessmaglims[0])/(tessmaglims[1]-tessmaglims[0])*0.9
    tmagrank[tmagrank<0.1] = 0.1
    tmagrank[tmagrank>1.0] = 1.0
    tmagrank = np.log10(tmagrank)

    # duration expectation
    durratrank = 1.0 - (durrat - durratlims[0])/(durratlims[1] - durratlims[0])*0.9
    durratrank[durratrank<0.1] = 0.1
    durratrank[durratrank>1.0] = 1.0
    durratrank = np.log10(durratrank)

    # earth solar flux
    solarfrank = 1.0 - (allsolarflux - solarfluxlims[0])/(solarfluxlims[1] - solarfluxlims[0])*0.9
    solarfrank[solarfrank<0.1] = 0.1
    solarfrank[solarfrank>1.0] = 1.0
    solarfrank = np.log10(solarfrank)
    
    # snr 2 mes ratio
    snr2mesrank = 1.0 - (snrrat-snr2meslims[0])/(snr2meslims[1] - snr2meslims[0])*0.9
    snr2mesrank[snr2mesrank<0.1] = 0.1
    snr2mesrank[snr2mesrank>1.0] = 1.0
    snr2mesrank = np.log10(snr2mesrank)
    
    # dv vs trapezoid depth similarity
    depsimrank = 1.0 - (depdiff - reldepthlims[0])/(reldepthlims[1] - reldepthlims[0])*0.9
    depsimrank[depsimrank<0.1] = 0.1
    depsimrank[depsimrank>1.0] = 1.0
    depsimrank = np.log10(depsimrank)
    
    # Centroid oot offset
#    centootrank = 1.0 - (allcentootsig - centlims[0])/(centlims[1] - centlims[1])*0.9
#    centootrank[centootrank<0.1] = 0.1
#    centootrank[centootrank>1.0] = 1.0
#    centootrank = np.log10(centootrank)
    
    # Centroid tic offset
#    centticrank = 1.0 - (allcentticsig - centlims[0])/(centlims[1] - centlims[1])*0.9
#    centticrank[centticrank<0.1] = 0.1
#    centticrank[centticrank>1.0] = 1.0
#    centticrank = np.log10(centticrank)
    
#    totrank = (rprank + mesrank + tmagrank + durratrank + solarfrank + snr2mesrank+\
#                depsimrank + centootrank + centticrank) / 9.0 + 1.0
    totrank = (rprank + mesrank + tmagrank + durratrank + solarfrank + snr2mesrank+\
                depsimrank) / 7.0 + 1.0

    if nWrk == 1 :
        fout1 = open(fileOut1,'w')
        fout2 = open(fileOut2, 'w')
        fout3 = open(fileOut3, 'w')              
    ia = np.argsort(-totrank)
    for i in range(len(ia)):
        if np.mod(i, nWrk) == wID:
            j = ia[i]
            # Look for a TOI match
            matchFlg = 0
            # fc is the cause flags for going to Tier 2
            fc = np.zeros((15,), dtype=int)
            fc_str = ''
            ib = np.where((alltic[j] == toiFedTic) & (allpn[j] == toiFedPN))[0]
            if len(ib)>0:
                # Was it a direct match or not
                mtch = np.max(toiFedQual[ib])
                if mtch == 1:
                    matchFlg = 1
                else:
                    matchFlg = -1
            # multiplanet systems can fall through the cracks add another flag
            #  of nearby TOI exists so one needs to investigate the relationship
            if matchFlg == 0:
                ib = np.where((alltic[j] == toiFedTic))[0]
                if len(ib)>0:
                    # has some kind of neighbor with previously identified toi
                    matchFlg = 3
            # Look to previous Planet match
            ib = np.where((alltic[j] == kpFedTic) & (allpn[j] == kpFedPN))[0]
            if len(ib)>0:
                matchFlg = 2
            # now look for a nearby previous planet was found independent of ephemeris
            if not matchFlg == 2:
                ib = np.where((alltic[j] == kpFedTic))[0]
                if len(ib)>0:
                    matchFlg = 4
            curstr = '{0:016d} {1:d} {2:f} {3:d}\n'.format(alltic[j], allpn[j], totrank[j], matchFlg)
            print(curstr)
    
            # Find modshift data to place in tier
            kidx = np.where((alltic[j] == modTic) & (allpn[j] == modPN))[0]
            kidx2 = np.where((alltic[j] == modTic2) & (allpn[j] == modPN2))[0]
            # Find sweet data 
            kswidx = np.where((alltic[j] == swTic) & (allpn[j] == swPN))[0]
            # Find self match TCE
            ksmidx = np.where((alltic[j] == smFedTic1) & (allpn[j] == smFedPN1))[0]
            # Find PDC Goodness stat data
            kpdcidx = np.where((alltic[j] == pdcTic) & (allpn[j] == pdcPn))[0]
            # Find Momentum deump data
            kmdidx = np.where((alltic[j] == mdTic) & (allpn[j] == mdPN))[0]
            # Find planet radius
            curRp = allrp[j]
            curSNR = allsnr[j]

            # Tier 1 must have no centroid issues, primary signif, no secondary (else albedo or period half),
            # and no odd/even sig
            tier1 = True
            hasSec = False
            nFlags = 0
            if allcentootsig[j] > centlims[1] or allcentoote[j] < 0.0:
                tier1 = False
                fc[0] = 1
                fc_str = fc_str + 'CenOOT_'
                #nFlags = nFlags + 1 #centroids dont count as flag
            if allcentticsig[j] > centlims[1] or allcenttice[j] < 0.0:
                tier1 = False
                fc[1] = 1
                fc_str = fc_str + 'CenTIC_'
                #nFlags = nFlags + 1 #centroids dont count as flag
            if modUniqFlg[kidx] == 0:
                tier1 = False
                fc[2] = 1
                fc_str = fc_str + 'UniqAlt_'
                nFlags = nFlags + 1
            if modUniqFlg2[kidx2] == 0:
                tier1 = False
                fc[3] = 1
                fc_str = fc_str + 'UniqDV_'
                nFlags = nFlags + 1
            if modSecFlg[kidx] == 1:
                if modSecOvrFlg[kidx] == 0:
                    tier1 = False
                    fc[4] = 1
                    hasSec = True
                    fc_str = fc_str + 'HasSecAlt_'
                    nFlags = nFlags + 1
                else:
                    tier1 = False
                    fc[12] = 1
                    fc_str = fc_str + 'HasSecAltPlanet?_'
                    #nFlags = nFlags + 1 #not flag
            if modSecFlg2[kidx2] == 1:
                if modSecOvrFlg2[kidx2] == 0:
                    tier1 = False
                    fc[5] = 1
                    hasSec = True
                    fc_str = fc_str + 'HasSecDV_'
                    nFlags = nFlags + 1
                else:
                    tier1 = False
                    fc[13] = 1
                    fc_str = fc_str + 'HasSecDVPlanet?_'
                    #nFlags = nFlags + 1 #  not flag
            OEThresh = OEThreshDefault
            if curSNR > highSNROE:
                OEThresh = OEThreshHighSNR 
            if modOESig[kidx] > OEThresh:
                tier1 = False
                fc[6] = 1
                fc_str = fc_str + 'OEAlt_'
                nFlags = nFlags + 1
            if modOESig2[kidx2] > OEThresh:
                tier1 = False
                fc[7] = 1
                fc_str = fc_str + 'OEDV_'
                nFlags = nFlags + 1
            sweetFail = False
            if len(kswidx)>0:
                # Look for sweet test results
                if swResidRatio[kswidx] < minSweetResidRatio:
                    tier1 = False
                    fc[8] = 1
                    sweetFail = True
                    fc_str = fc_str + 'Sweet_'
                    nFlags = nFlags + 1
            # Other TCE match
            if len(ksmidx)>0:
                tier1 = False
                fc[9] = 1
                fc_str = fc_str + 'OthTCEMtch_'
                nFlags = nFlags + 1
            # PDC goodness stat
            if len(kpdcidx)>0:
                if pdcNoi[kpdcidx] < minPDCNoiseMetric:# and pdcCor[kpdcidx] <:
                    # Note: not currently checking correlation metric
                    tier1 = False
                    fc[10] = 1
                    fc_str = fc_str + 'PDCsummaryPostfix_'
                    nFlags = nFlags + 1
            # Planet radius too big caution
            if curRp > maxPlanetRadiusRearth:
                tier1 = False
                fc[11] = 1
                fc_str = fc_str +'RpBig_'
                nFlags = nFlags + 1
            # Momentum dump on events caution
            if len(kmdidx)>0:
                if mdFrac[kmdidx] > maxMomentumDumpFraction:
                    tier1 = False
                    fc[12] = 1
                    fc_str = fc_str + 'MoDump_'
                    nFlags = nFlags + 1

            # undo sweet fail if sweet test is the only fail and no other flags thrown
            if sweetFail and nFlags == 1:
                sweetFail = False
                print('TIC {0:d} PN {1:d} bypass sweet fail'.format(alltic[j], allpn[j]))
            reportIt = False
            if tier1:
                if nWrk == 1:
                    fout1.write(curstr)
                mrkStr = 'Tier 1'
                reportIt = True
            if (not tier1) and (not hasSec) and (not sweetFail):
                curstr2 = ''.join(str(x) for x in fc)
                mrkStr = 'Tier 2 {}'.format(fc_str)
                if nWrk == 1:
                    fout2.write('{} {} {}\n'.format(curstr[0:-1],curstr2, fc_str))
                reportIt = True
            if (not tier1) and (not reportIt):
                mrkStr = 'Tier 3 {} {}'.format(hasSec, sweetFail)
                if nWrk == 1:
                    fout3.write('{} {} {}\n'.format(curstr[0:-1],hasSec,sweetFail))
                reportIt = True
            if doPNGs and reportIt:
                if tgt_2min:
                    inputFile = os.path.join(summaryFolder,'{0}s{1:04d}-s{2:04d}-{3:016d}-{4:02d}{5}'.format(summaryPrefix,SECTOR1,SECTOR2,alltic[j],allpn[j],summaryPostfix))
                else: # FTL DV report file name format
                    inputFile = os.path.join(summaryFolder,'{0}{1:016d}{2}{3:02d}.pdf'.format(summaryPrefix,alltic[j],summaryPostfix,allpn[j]))
                    #inputFile = os.path.join(summaryFolder,'{0}{1:016d}-s{2:04d}-s{3:04d}{4}{5:02d}.pdf'.format(summaryPrefix,alltic[j],SECTOR1,SECTOR2,summaryPostfix,allpn[j]))
                outputFile = os.path.join(pngFolder,'{0:04d}-{1:016d}-{2:02d}.png'.format(i, alltic[j], allpn[j]))
                comstring = 'gs -dBATCH -dNOPAuSE -sDEVICE=png16m -r300 -o {0} {1}'.format(outputFile, inputFile)
                tmp = call(comstring, shell=True)
            if doMergeSum and reportIt:
                curTic = alltic[j]
                curPn = allpn[j]

                # Make a temporary pdfmark file for adding Tier level and keywords to pdf
                #mrkFile = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic),'pdfmarks_{0:016d}_{1:02d}.txt'.format(curTic,curPn))
                #mrkOut = open(mrkFile,'w')
                #mrkOut.write('/pdfmark where {pop}{userdict /pdfmark /cleartomark load put} ifelse\n')
                #mrkOut.write('[ /Rect [ 15 735 500 785 ] /DA ([1 0 0] rg /Cour 20 Tf) /BS << /W 0 >> /Q 0 /Subtype /FreeText /SrcPg 1\n')
                #mrkOut.write('/Contents ({}) /ANN pdfmark\n'.format(mrkStr))
                #mrkOut.close()
                # Make a ps file for adding Tier level and keywords to pdf
                # via https://stackoverflow.com/questions/18769314/add-text-on-1st-page-of-a-pdf-file
                mrkFile = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic),'tecres_{0:016d}_{1:02d}.ps'.format(curTic,curPn))
                mrkOut = open(mrkFile,'w')
                mrkOut.write('%!\n')
                mrkOut.write('<< /EndPage {0 eq{0 eq{\n')
                mrkOut.write('/Arial findfont 22 scalefont setfont newpath 15 770 moveto 1 0 0 setrgbcolor ({0}) show\n'.format(mrkStr))
                mrkOut.write('} if true}{pop false} ifelse} >> setpagedevice\n')
                mrkOut.close()
                
                if tgt_2min:
                    inputFile1 = os.path.join(summaryFolder,'{0}s{1:04d}-s{2:04d}-{3:016d}-{4:02d}*dvs.pdf'.format(summaryPrefix,SECTOR1,SECTOR2,alltic[j],allpn[j],summaryPostfix))
                else:  # FTL file format
                    inputFile1 = os.path.join(summaryFolder,'{0}{1:016d}{2}{3:02d}.pdf'.format(summaryPrefix,alltic[j],summaryPostfix,allpn[j]))
                    #inputFile1 = os.path.join(summaryFolder,'{0}{1:016d}-s{2:04d}-s{3:04d}{4}{5:02d}.pdf'.format(summaryPrefix,alltic[j],SECTOR1,SECTOR2,summaryPostfix,allpn[j]))

                inputFileList = glob.glob(inputFile1)
                if not len(inputFileList) == 1:
                    print('Error: not found or multiple DV summaries found for {0:d} pn {1:d}'.format(alltic[j], allpn[j]))
                    exit()
                inputFile1 = inputFileList[0]
                #outputFile = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic),'tecsummary_{0:016d}_{1:02d}.pdf'.format(curTic,curPn))
                # Add TEC tier level and keywords to summary page with imagemagick convert
                #comstring = "convert -density 500 {0} -pointsize 25 -draw \"text 20,150 '{1}'\"  {2}".format(inputFile1, mrkStr, outputFile)
                #print(comstring)
                #tmp = call(comstring, shell=True)
                #inputFile1 = outputFile
                inputFile2 = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic), 'tess_{0:016d}_{1:02d}-modshift.pdf'.format(curTic,curPn))
                inputFile3 = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic), 'tess_{0:016d}_{1:02d}_med-modshift.pdf'.format(curTic,curPn))
                # Check that modshift files exist
                if not os.path.isfile(inputFile2):
                    inputFile2 = ''
                if not os.path.isfile(inputFile3):
                    inputFile3 = ''
    
                inputFileList = []
                if multi_sector_flag:
                    for curSec in np.arange(SECTOR1,SECTOR2+1):
                        inputFile4 = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic), 'tess_diffImg_{0:016d}_{1:02d}_{2:02d}.pdf'.format(curTic,curPn,curSec))
                        if os.path.isfile(inputFile4):
                            inputFileList.append(inputFile4)
                    # Summar centriod figure
                    inputFile4 = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic), 'tess_diffImg_{0:016d}_{1:02d}_centsum.pdf'.format(curTic,curPn))
                    if os.path.isfile(inputFile4):
                        inputFileList.append(inputFile4)
                    for curSec in np.arange(SECTOR1, SECTOR2+1):
                        inputFile4 = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic), 'tess_mods_diffImg_{0:016d}_{1:02d}_{2:02d}.pdf'.format(curTic,curPn,curSec))
                        if os.path.isfile(inputFile4):
                            inputFileList.append(inputFile4)
                    for curSec in np.arange(SECTOR1, SECTOR2+1):
                        inputFile4 = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic), 'tess_bsc_diffImg_{0:016d}_{1:02d}_{2:02d}.pdf'.format(curTic,curPn,curSec))
                        if os.path.isfile(inputFile4):
                            inputFileList.append(inputFile4)
                else:
                    inputFile4 = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic), 'tess_diffImg_{0:016d}_{1:02d}_{2:02d}.pdf'.format(curTic,curPn,SECTOR1))
                    inputFileList.append(inputFile4)
                    inputFile5 = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic), 'tess_mods_diffImg_{0:016d}_{1:02d}_{2:02d}.pdf'.format(curTic,curPn,SECTOR1))
                    if os.path.isfile(inputFile5):
                        inputFileList.append(inputFile5)
                    inputFile6 = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic), 'tess_bsc_diffImg_{0:016d}_{1:02d}_{2:02d}.pdf'.format(curTic,curPn,SECTOR1))
                    if os.path.isfile(inputFile6):
                        inputFileList.append(inputFile6)
    
                # Look for Twexo page
                inputFile7 = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic), 'twexo_{0:016d}.pdf'.format(curTic))
                if os.path.isfile(inputFile7):
                    inputFileList.append(inputFile7)

                outputFile = os.path.join(pdfFolder,'tec-s{3:04d}-{1:016d}-{2:02d}.pdf'.format(i, alltic[j], allpn[j], SECTOR2))
                outputFile2 = os.path.join(pdfFolder,'tec-s{3:04d}-{1:016d}-{2:02d}_mrg.pdf'.format(i, alltic[j], allpn[j], SECTOR2))
                #comstring = 'convert {0} {1} {2}'.format(inputFile1, inputFile2, outputFile)
                comstring = 'gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile={0} -dPDFSETTINGS=/prepress {4} {1} {2} {3}'.format(outputFile, inputFile1, inputFile2, inputFile3, mrkFile)
                #comstring = 'gs -dBATCH -dNOPAUSE -q -sDEVICE=pdfwrite -sOutputFile={0} {1} {2} {3}'.format(outputFile, inputFile1, inputFile2, inputFile3)
                for ifil in inputFileList:
                    comstring += ' {0} '.format(ifil)

                tmp = call(comstring, shell=True)
                # Add pdfmark text
                #print(outputFile)
                #comstring = 'gs -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -sOutputFile={0} -dPDFSETTINGS=/prepress {1} {2}'.format(outputFile2, mrkFile, outputFile)
                #print(comstring)
                #tmp = call(comstring, shell=True)
            
    print("hello world")
    if nWrk == 1:
        fout1.close()
        fout2.close()
        fout3.close()
