# This file will define the NLDAS-2 domain as a 2-column list of lons and lats, to be read in by the createTimeseries.py file.
# P. Shellito, Jul 19, 2018

import numpy as np

# Range of NDLAS-2 Lon values
lonMin=-124.9375
lonMax=-67.0625
lonMax=-121.0625
lonRes=0.125
lonN=464
lonVals = np.arange(lonMin,lonMax+lonRes/2,lonRes)
# Range of NDLAS-2 Lat values
latMin=25.0625
latMax=52.9375
latMax=28.9375
latRes=0.125
latN=224
latVals = np.arange(latMin,latMax+latRes/2,latRes)

# Name of file to save as
fileN = 'nldasDomainSection.txt'
# Open the file to write to
fid = open(fileN,'w')
# Print header
fid.write('#     Lon       Lat\n')
# Print every combination of lon/lat in a text file
for oo in range(len(lonVals)):
    for aa in range(len(latVals)):
        fid.write('{0:>9.4f} {1:>9.4f}\n'.format(lonVals[oo], latVals[aa]))

# Close the file
fid.close()
