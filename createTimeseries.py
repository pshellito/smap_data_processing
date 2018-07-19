# This script will read in SMAP data and write out time series.
# The number of days of SMAP data to be read in is limited by computer memory and spatial extent requested.
# The locations of the time series to be written out is defined by a separate python file that contains a 2-column array of all the lon/lat pairs we want. That file is created by a separate script, named, "createDomain.py"
# P. Shellito, Jul 19, 2018

# Date range to read

# Number of days to read at once

# Lon/Lat to write out
domainFile = 'nldasDomain.txt'
