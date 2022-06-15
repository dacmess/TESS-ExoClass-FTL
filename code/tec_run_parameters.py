# Run Parameter file for TEC-FTL (https://github.com/dacmess/TESS-ExoClass-FTL)
# a TESS-SPOC FFI pipeline version of the original TEC distribution
# (https://github.com/christopherburke/TESS-ExoClass)
# The intent is to be fully compatible with TEC for use on 2-minute data
# and extensible to 200-sec FFI data.
#
# Edit this file to setup TEC-FTL for a specific run. TEC-FTL python code
# will import and use these definitions
# 
# Mods from: Douglas Caldwell based on initial TEC code by Christopher Burke
# 15 June 2022 - initial use, working for FTL, 2-min single sector
# 
# test file for setting run parameters using an imported file

## Sector and Run parameters
######## changes here ########
sector_number 	= 51
run_date	= '20220614'	# select a date string to idenfity the run
sector_name	= 'sector51'
######## end change section ########
run_name 	= sector_name + '_' + run_date

## Single-sector vs multi-sector parameters
######## changes here ########
start_sector 	= 51
end_sector 	= 51
multi_sector_flag = False # use for sector_number in multi-sector run
# sector_number	= multi_sector_flag
######## end change section ########

## TEC run path parameters
######## changes here ########
tec_root 	= '/nobackupp15/dacaldwe/git/tec/'  # root directory for all TEC checkouts
tec_run_name 	= 'sector51FTL' # top directory in current TEC run distribution
######## end change section ########

## Local data path parameters
######## changes here ########
data_root_dir 	= '/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-48/' 	# data_root to locate export products

# note: for 2-min runs remove the initial 'ftl-' 
light_curve_dir	= 'ftl-light-curve'
target_pixel_dir = 'ftl-target-pixel'
dv_results_dir	= 'ftl-dv-results'
dv_reports_dir	= 'ftl-dv-reports'
dv_time_series_dir = 'ftl-dv-time-series'
######## end change section ########

## Data file name parameters (2-min vs FTL)
######## changes here ########
lc_file_prefix	= 'hlsp_tess-spoc_tess_phot_'	# FTL style
lc_file_postfix	= '-s0051_tess_v1'		# FTL style
#lc_file_prefix	= 'tess2021336043614-s0046-'	# 2-min style
#lc_file_postfix = '-0217-s'			# 2-min style

dv_file_prefix	= 'hlsp_tess-spoc_tess_phot_'	# FTL style
dv_file_postfix	= '-s0051-s0051_tess_v1'	# FTL style
#dv_file_prefix	= 'tess2018206190142'		# 2-min style
#dv_file_postfix = '-00555'			# 2-min style

######## end change section ########

## Run type parameters (2-min vs FTL) 
######## changes here ########
      ## one of these should be "True" and the others "False" ##
ftl_10min	= True	# FTL 10-min FFIs
ftl_200sec	= False	# FTL 200-second FFIs
tgt_2min	= False # 2-min data


######## end change section ########
if tgt_2min:
    cadPerHr	= 30
elif ftl_10min:
    cadPerHr	= 6
elif ftl_200sec:
    cadPerHr	= 18
else:
    raise Exception(__name__,': Error cadence type not properly defined')
    
