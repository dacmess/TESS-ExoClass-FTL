# -*- coding: utf-8 -*-
"""
Generate twexo pdfs for all targets
"""

import math
import os
from subprocess import Popen, PIPE
import numpy as np
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
    sector_number       = tecrp.sector_number
    tec_root            = tecrp.tec_root
    tec_run_name        = tecrp.tec_run_name

    #  Directory storing the ses mes time series
    sesMesDir = tec_root + tec_run_name
    SECTOR = sector_number

    doPDFs = True
    vetFile = 'spoc_fluxtriage_' + run_name + '.txt'
    overwrite = False

    # Load the  flux vetting
    dataBlock = np.genfromtxt(vetFile, dtype=[int,int,int,'S1'])
    fvtic = dataBlock['f0']
    fvpn = dataBlock['f1']
    fvvet = dataBlock['f2']

    # Generate html for triage passing TICs
    idx = np.where(fvvet == 1)[0]
    useTic = np.unique(fvtic[idx])
    nTic = len(useTic)
    for i,curTic in enumerate(useTic):
        if np.mod(i, 20) == 0:
            print('Done {0:d} of {1:d}'.format(i, nTic))
        htmlOutput = os.path.join(make_data_dirs(sesMesDir, SECTOR, curTic), 'twexo_{0:016d}'.format(curTic))
        if not os.path.isfile(htmlOutput + '.pdf') or overwrite:
            # Build argument list
            syscall = 'python twexo.py -t {0:d} -of {1} -nw'.format(\
                                curTic, htmlOutput)
            print(syscall)
            p = Popen(syscall.split(), stdin=None, stdout=PIPE, stderr=PIPE)
            sysreturn, err = p.communicate()
            if os.path.isfile(htmlOutput + '.html'):
                syscall = 'wkhtmltopdf {0}.html {0}.pdf'.format(htmlOutput)
                print(syscall)
                p = Popen(syscall.split(), stdin=None, stdout=PIPE, stderr=PIPE)
                sysreturn, err = p.communicate()
            else:
                print(syscall + ' failed to produce output')
                print(sysreturn)
                print(err)
            #rc = p.returncode
            #print('alpha')
