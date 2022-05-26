#!/bin/bash

# modify to point to SPOC export directory containing ftl results
DATA_DIR='/nobackupp15/spocops/incoming-outgoing/exports/science-products-tsop-2630/sector-48'

# print out a selection of export products so user can see filename format
ls ${DATA_DIR}/ftl-dv-reports | head -4
ls ${DATA_DIR}/ftl-dv-reports/*dvm.pdf | head -2
ls ${DATA_DIR}/ftl-light-curve | head -4
ls ${DATA_DIR}/ftl-target-pixel | head -4

