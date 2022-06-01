*FTL version - contains mods to work on draco with local SPOC products plus mods to work on FTL*
# This document describes the procedure for running TEC for a single sector SPOC run.

# A. Environment Setup
Use your normal means of connecting to draco (e.g., vnc) and open terminal windows. Generally, 2 or 3 terminals is sufficient for 
running things in parallel and keeping track of intermedidiate results.
*If you are running as SPOCOPS user you will need to login as spocops and do the python setup below on each of these terminals*

> When running as spocops user, change python-conda source path by sourcing 
> 
>        $ source ~/server-config/bin/conda-for-tec.sh
>
>Then select conda environment:
>
>        $ conda activate tec-env

TEC runs with the conda environment **tec-env** tools (with one optional exception).

The following python modules used by TEC are available in the tec-env environment: numpy, matplotlib, scipy, astropy, h5py, statsmodels, spectrum

The following system commands should be available on you local machine: c++ compiler (g++), pdftotext, grep, gs, seq, parallel

*Note: on draco, **parallel** was installed for spocops user using the basic local install described in the README file. This installs parallel in ~/bin and documentation & man pages in ~/share/*. Go to Gnu Parallel to get the latest stable version: https://www.gnu.org/software/parallel/.*

One time you need to compile the modshift test c++ code. After downloading the TEC source code (see below) in the [install-dir]/TESS-ExoClass/code directory.

A compiled version of modshift is located in /nobackupp15/spocops/git/tec/modshift. If you need to recompile use the command line:

        $ g++ -std=c++11 -Wno-unused-result -O3 -o modshift -O modshift.cpp

In modshift_test.py *near* Line 536 the syscall variable needs to point to the compiled modshift (as described  below in Step 12).

I created git/tec/tec_startup to add the definitions below. Before running tec step 10 you should source this file: 

        $ source /nobackupp15/spocops/git/tec/tec_startup
        
Note: sedcsvfix is used in step 10 to remove commas in the comment section from the TOI csv file. The teccd function is for convenience and not required; it can be used like “teccd 45FTL” for a code directory under the sector45FTL root.

> Contents of tec_startup
> 
>        ### TEC
>        alias sedcsvfix="sed -e 's/\"\"//g' -e 's/,\"[^\"]*/,\"NOCOMMENT/g'"
>    
>        function teccd { cd $NFS/git/tec/sector"$1"/TESS-ExoClass-FTL/code; }
>
>        export -f teccd
>    
>        ### TEC items
>    
>The alias is used to remove commas in the TEV output TOI listing .csv and the function is used to quickly change to the working code directory of a sector. For instance ‘teccd 48FTL’ will change to the TEC code route in sector48FTL. Alter the path for where you are running TEC.


# B. Directory and code setup

If running as spocops user, run TEC on /nobackupp15/git/tec. Setup the directories for the current run with the commands below, where \## is the sector number for this run:

    $ cd /nobackupp15/spocops/git/tec/ 
        
    $ mkdir sector##FTL  
    
    $ cd sector##FTL
    
    $ mkdir S## (do not include the “FTL” in this dir name)
    
    $ mkdir pdfs
    
    $ mkdir tevpdfs
    
Clone from github the TEC codebase

    $ git clone https://github.com/dacmess/TESS-ExoClass-FTL.git
    
    $ cd TESS-ExoClass-FTL/code
    
This is the main working directory for all TEC commands and all of the subsequent commands are run from within this code directory.

Edit showfilenumbers.sh such that the DATA_DIR variable points to the spoc data directory for the sector you are working on. Note: This is where the DV results, LC & TP files live. On draco this is: /nobackupp15/spocops/exports/science-products-tsop-####. 

To edit this file you will need the name of the export directory, including the Sector-NN directory. For example, the changes for Sector 40 FTL look like:

> DATA_DIR='/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2369/sector-40'

Run the showfilenumbers.sh bash script

    $ ./showfilenumbers.sh
    
It will show the filenames for the current sector. You will need these filename prefixes in the next step.

Edit **update_filenames.sh** - There are a series of OLD and NEW variables that need to be updated. This bash script will update all the python codes such that paths and variables get set for the current directory. Copy the NEW variables to the OLD and then replace the NEW variables with values appropriate for the current sector.

- NEW_NAME - the 8 digit number at the end is just the current date in year month day format
- For FTL runs NEW4 should include FTL if you used it in the tec install directory name: e.g., NEW4 = “sector45FTL”
- DV report prefix and LC prefix - follow the pattern for the filename prefixes from the SPOC data products. Note: this is the part before the zero-padded TIC ID in the export file names. For FTL results, these change to something like “hlsp_tess-spoc_tess_phot_”  
- The DV postfix changes to something like “-s0045-s0045_tess_v1” 
- The LC postfix changes to something like “-s0045_tess_v1” (see outputs from showfilenumbers.sh step above).
- NEW1=”SECTOR = -1”; NEW2=”SECTOR1 = #min”; NEW3=”SECTOR2 = #max”, where #min and #max are the minimum and maximum sector numbers, respectively.
- DV report prefix filenames should be updated to match multi-sector run output; LC prefix filenames should be set to maximum sector number’s light curve files

Run the bash script

    $ ./update_filenames.sh
    
Edit the script **update_local_paths.sh** to change the output path roots from the OLD_PATH to the NEW_PATH and the data path roots; e.g.

>OLD_PATH=”\\/pdo\\/users\\/cjburke\\/spocvet” 
>
>NEW_PATH=”\\/nobackupp15\\/dacaldwe\\/git\\/tec”). 
>
>OLD_DATA_PATH="\\/pdo\\/spoc-data", 
>
>NEW_DATA_PATH= "\\/nobackupp15\\/spocops\\/incoming-outgoing\\/exports\\/science-products-tsop-####"

*Note: need to escape the directory separators with “\” for use in the sed command. Also update the tsop number to point to the exports for this sector.*

Then run the bash script 
    
    $ ./update_local_paths.s

If running on FTL, run the script: 

    $ /nobackupp15/spocops/git/tec/update_for_ftl.sh 

to change data subdirectory names to “ftl-*”.
                          

For TEC there are various times when commands are run in parallel and serially. It can be helpful to have multiple terminals open to run commands in parallel and check on progress and results. The command *teccd <sector number>* lets you quickly navigated to the TEC working directory for each ssh connection.
You should now be setup to run TEC commands

# C. TEC Commands

TEC commands are run from the TESS-ExoClass/code directory for the sector you are working on. The bashrc function ‘teccd #’ will take you there quickly. Some commands are run serially and some are run in parallel. For each command I will try to summarize what it calculates, when you should wait for command to complete before moving to next command, and what it outputs. For the outputs I am giving an example from Sector 33, the filenames will be different for the sector you are working on. A helper routine ‘python tec_status.py’ exists that shows that the datafiles it expects for a TEC run are complete. Use ‘python tec_status.py’ to help diagnose if a command is working or completed as expected.
      
0.  Run in conda python 3.x environment: conda activate tec-env (had to install several packages & ran into some dependency issues, but fixed after uninstall then conda install)

1. Read in the DV xml files for the SPOC TCEs and store the TCE data in a convenient format. Prereq: None. Wait until finished. Output: sector33_20200208_tce.h5 (can check # of TCEs is as expected by checking DAWG ticket)
python  gather_tce_fromdvxml.py Note: for FTL need to change “*_dvr.xml*” to “*-dv.xml*” since the FLT DV xml filenames differ. I guess we could use *dvr.xml*  that would work for both and (I don’t think) cause any problems.

2. Output the TCE data in a human friendly .txt file. Prereq: Step 1. Wait until finished. Output: sector33_20200208_tce.txt
python dump_tce_info.py

3. Bin all light curve files from 2min to 10minute. Prereq: None. Continue to next step while this is running. Output: Under the S# directories each light curve will be stored in .h5 format. for TIC 141122198 planet number 2 ~/spocvet/sector33/S33/141122/tess_dvts_0000000141122198_02.h5d
        MS only near line 201: SECTOR_OVRRIDE = -1 Change to None
        For FTL the RESAMP factor on line 200 should be changed from RESAMP = 5 to RESAMP = 1 with 10 minute FFIs (RESAMP = 3 with 200 second FFIs); 
python dvts_bulk_resamp.py
**If after multi-sector near Line 201: SECTOR_OVERRIDE = None

4. Find cadences where many transit ephemerides overlap such that the transits should be deweighted when recalculating significance. Prereq: None. Continue to next step while this is running. Output: Will bring up a figure window. Close figure window. skyline_data_sector33_20200208.txt
python skyline_spoc.py

5. Match TCE ephemerides to the known planet ephemerides at the exoplanet archive. This routine takes a long time since it needs to query MAST as well. This step can be a bit finicky. Every once in a while the queries to MAST will just hang and/or it will error out. Usually just rerunning the command will result in it working. Prereq: None. Continue to next step while this is running. Output: federate_known_sector33_20200208.txt
python federate_knownPWtce.py
***If TESS changes the ecliptic hemisphere then Ln 144 st_elat filter in the known planet query needs to be adjusted NOTE: change to st_elat>0.0 for Northern hemisphere; Commented out ecliptic latitude line for ecliptic plane sectors

6. Match TCE ephemeride list to itself. This finds matches in common indicating systematics. Prereq: None. Continue to next step while this runs. Output: selfMatch_sector33_20200208.txt
python selfMatch_spoc.py

7. Rip the difference image pages from the DV report. When running this command can sometimes produce ‘GPL Ghostscript…’ warnings and error messages. Those are actually ok. You can run tec_status to see that the DV report pages are actually being generated. Prereq: None. Takes a long time to run so continue to next step while this is running. Output: Difference images in their own pdf for each TCE ~/spocvet/sector33/S33/141122/tess_diffImg_0000000141122198_02_33.pdf
        Needs multiple instances run (rec 3) manually adjust wID & nWrk for each instance
    For FTL need to edit the search string line (near Line 143) to be:       
srchstr = '{0}{1:016d}{2}'.format(summaryPrefix,curTic,'*dvr.pdf')


python get_dv_report_page.py
**if after multi-sector Ln 31: Reset wID=0; nWrk=1;

8. [OPTIONAL] Parse the target pixel files to bin them to 10minute cadence in order to perform centroid analysis. Prereq: *Step 3, light curves must be rebinned before doing this. Takes a long time to run so continue to next step while this runs. Output: target pixel file data in h5 format for every TCE ~/spocvet/sector33/S33/141122/tess_tpf_0000000141122198_33.h5d
Edit tpf_bulk_resamp.py
Variables fileInputPrefixList & fileInputSuffixList need to be modified in order to add a fake directory ‘/foo#’ for the previous sector. The reason for this has to do with supporting multi-sector runs, but for a single sector these need filling in. If you were working on Sector 33, then the ‘/foo32’ directory would not be present, add it to the python list.
MS Only - Consult tpf_bulk_resamp.py from previous sectors to fill directory and file prefixes and suffixes for all sectors that have data in the search.
Modify TPF prefix & suffix for FTL use **should already be done during setup step above with update_for_ftl.sh
Modify RESAMP = 1 for FTL
python  tpf_bulk_resamp.py

9. Calculate the main statistics that will be used for the triage cut. Prereq: Step 3 complete. The will use multiple cores and processes. The example below uses 20 processes. There is nothing special about 20 processes you can use more or less, but you have to change both the last number in the command and the 2nd number in the command, and the 2nd number in the command is one less than the last number. For instance if you want to run 5 processes the command should be ‘seq 0 4…-n 5’. Go to step 10 and wait until this completes before doing step 11. Output: SES light curve for every TCE ~/spocvet/sector33/S33/141122/tess_sesmes_0000000141122198_02.h5d
seq 0 19 | parallel --results ses_mes_results python ses_mes_stats.py -w {} -n 20
Used 60 tasks. **Note: when running S45 FTL, I did not have to make the changes described next** Had to hack fluxts_conditioning.py to prevent preYStd, postYStd from being <0, which was causing an error in numpy call. Added max(1.0, preYStd) to line 77; max(1.0, postYStd) to line 91. Specifically:  Line 77: preFill = np.random.normal(scale=max(1.0,preYStd), size=(nW,)); Line 91: postFill = np.random.normal(scale=max(1.0,postYStd), size=(nW,))
Note: line 312 has cadPerHr = 6 hard-coded to be 10 minute sampling. This must (presumably) match the RESAMP parameter in dvts_bulk_resamp.py.

10. Match the TOI ephemerides to the TCEs. Prereq: Wait until Step 5 completes. Output: federate_toiWtce_sector33_20200208.txt
From tev.mit.edu download the latest toi catalog ‘TOI+ List’ csv file. Transfer the toi csv file to pdo
    Alternative on pdo: ‘curl https://tev.mit.edu/data/collection/193/csv/6/ > csv-file-toi-catalog.csv’ directly on pdo to download the toi list
Remove the commas in the comments from the csv file using the sed alias
sedcsvfix csv-file-toi-catalog.csv  > csv-file-toi-catalog-FIXED-20200208.csv
Edit federate_toiWtce.py . Line 174 variable qlpfile should point to the corrected TOI csv file.
python federate_toiWtce.py

11. Run the triage filter. Prereq: Step 9. Wait until this completes but it is quick. Output: spoc_fluxtriage_sector33_20200208.txt
python flux_triage.py

12. Perform a trapezoid model fit and run the modshift test for the DV median detrended light curve. Prereq: Step 11. Continue with next step while this runs. Output: Modshift plot outputs for every triage passing TCE and trapezoid fit parameters. ~/spocvet/sector33/S33/140900/tess_0000000140900726_01_med-modshift.pdf & ~/spocvet/sector33/S33/140900/tess_trpzdfit_0000000140900726_01.txt
Run modshift_test.py with input argument = 1: use DV median detrended time series
Edit modshift_test.py. Make sure Lines 292 & 293 are commented out. You want 294 & 295 uncommented ; medianInputFlux = True ; fileOut = 'spoc_modshift_med_sector33_20200208.txt'
Edit modshift_test.py (2 places, near lines 514, 536) to make sure syscall points to compiled modshift:    syscall = '/nobackupp15/spocops/git/tec/modshift. Note: this is the default from the TESS-ExoClass-FTL repo.
python modshift_test.py 1

13. Perform the sweet test. Prereq: Step 11. Continue with next step while this runs. Output: spoc_sweet_sector33_20200208.txt
python sweet_test.py

14. Gather the flux weighted centroid time series and some PDC statistics about the quality of the light curve. Prereq: Step 11. Continue with next step while this runs. Output: ~/spocvet/sector33/S33/140900/tess_flxwcent_0000000140900726_01.h5d
Edit grab_flxwcent.py. Need to add the ‘/foo#’ directories in the same manner as in Step 8. For multisector need all the directories. Also need to convert target-pixel -> light_curve in directory and lc for filenames; Should be ok for single-sector runs (including FTL).
Edit grab_flxwcent.py to set RESAMP = 7 near line 44 (Note: set at 31 for 2-min data so setting at odd number near 31/5 for 10 minute FTL data).
python grab_flxwcent.py

15. Check whether the TCE events line up with momentum dumps. Prereq: Step 11. Continue with next step while this runs. Output: spoc_modump_sector33_20200208.txt
python modump_check.py

16. Generate the twexo page that has convenient URL links and GAIA data. Unfortunately this needs to run under a python 3 environment. So, I have a separate python environment installed on PDO which I can help install if you want to run this. Prereq: Step 11. Continue with next step while this runs.
python gen_twexo.py

17. Run modshift test again, but using the TEC detrended light curve. You may be tempted to start this right after Step 12, but do not do this. There are some temporary files created in modshift that if the two modshift runs work on the same target causes problems. Just run this now after getting the other steps 13-16 started and the Step 12 gets far enough along that this issue won’t happen. Prereq: Step 11. Now we wait for steps 12-17 to finish.
Run modshift_test.py with input argument = 2: use TEC detrended time series
Edit modshift_test.py. Make sure Lines 294 & 295 are Commented out. You want 292 & 293 uncommented ; medianInputFlux = False ; fileOut = 'spoc_modshift_sector33_20200208.txt'
python modshift_test.py 2

18. Generate TEC centroid difference image figures. So far this is not that useful other than egregious centroid offsets. This is a multi-core step. Prereq: Step 11,12, & 17. If you run this step, wait until it finishes until moving onto step 19. Adjust the second number after the “seq” command to be one less than the -n option (that is seq counts the number of tasks from 0 to n-1). Output: Difference image figures ~/spocvet/sector33/S33/140900/tess_bsc_diffImg_0000000140900726_01_33.pdf
seq 0 19 | parallel --results centroid_basic_results python centroid_form_basic.py -w {} -n 20

19. Make the TEC Tier files. This is where we bring all the information together for the final ranking. Prereq: Wait until all steps 1-17 (optionally 18 as well) are complete. Before running this step I run ‘python tec_status.py’ to ensure that I have all the tests completed. Also, ‘ls -l *txt’ to make sure there aren’t any zero length files. This step is very quick. Output: spoc_ranking_Tier1_sector33_20200208.txt as well as Tier2 and Tier3 file.
python rank_tces.py

20. Generate the TEC reports. Prereq: Step 19. This uses multiple processes, adjust number of workers as needed with “seq 0 N-1” & “-n N” command line options. Outputs: ~/spocvet/sector33/pdfs/  Note: rank_tces.py generates the Tier files and also the reports on this run.
FTL DV summary report name change means some edits are required for rank_tces.py:
Near line 99 change to: summaryPostfix = ‘_tess_v1_dvs-’
Near line 552 change to: inputFile = os.path.join(summaryFolder,'{0}{1:016d}-s{2:04d}-s{3:04d}{4}{5:02d}.pdf'.format(summaryPrefix,alltic[j],SECTOR1,SECTOR2,summaryPostfix,allpn[j]))
Near line 578 change (note inputFile1): inputFile1 = os.path.join(summaryFolder,'{0}{1:016d}-s{2:04d}-s{3:04d}{4}{5:02d}.pdf'.format(summaryPrefix,alltic[j],SECTOR1,SECTOR2,summaryPostfix,allpn[j]))
seq 0 19 | parallel --results rank_tces_results python rank_tces.py -w {} -n 20
After this is done I run ‘python tec_status.py’ to make sure all the TEC reports are generated. Also, check to make sure there aren’t too small files; ‘ls -Shlr *pdf | head’. They should all be > several MB in size

21. Formally TEC is complete. There is another step that is not in the TEC codebase that does the merging of DV mini reports with the TEC report for the ingest to TEV. This code is at /pdo/users/cjburke/spocvet/merge4tev.py. Note: there is an FTL appropriate version of this code in /nobackupp15/spocops/git/tec/merge4tev.py. It will need to be copied to the current sector’s code directory and edited near lines 35-38. 
Make a copy of merge4tev.py into your working directory.
Alter the variables
    sourceDir = '/pdo/users/cjburke/spocvet/sector33/pdfs'
    outDir = '/pdo/users/cjburke/spocvet/sector33/tevpdfs'
    miniDir = '/pdo/spoc-data/sector-033/dv-reports/'
    miniHdr = 'tess2020353052510-'
    miniTail = '-00430_dvm.pdf'
    multiSector = False
    SECTOR = 33
To point to where various things live and then run it with multiple processes
seq 0 19 | parallel --results merge_results python merge4tev.py -w {} -n 20

I run tec_status.py again to make sure the TEV merged reports are generated.


How to diagnose a problem step that uses the parallel command to launch routines
parallel creates a directory for every process launched to store the stdout and stderr.  The directory names that store the outputs match what is given after the ‘--results’ flag in the parallel command. For instance ‘--results ses_mes_results’ means look in the ses_mes_results directory for the outputs. There is one more level of directory as well with name ‘1’. So, in summary ‘cd ses_mes_results/1’ will get you to the directory containing a separate directory for every process. Each process directory is numbered. From the ‘ses_mes_results/1’ directory, run the command ‘tail -n 100 */stdout | less’. This will list the last 100 lines of stdout for every process. A lot of times the error is actually in stdout. You can also try ‘tail -n 100 */stderr | less’ if you don’t find anything useful in stdout.

