# This script will read in SMAP data and write out time series.
# The number of days of SMAP data to be read in is limited by computer memory and spatial extent requested.
# The locations of the time series to be written out is defined by a separate python file that contains a 2-column array of all the lon/lat pairs we want. That file is created by a separate script, named, "createDomain.py"
# P. Shellito, Jul 19, 2018

import datetime as dt
import numpy as np
import math
from smapUtils import *

# ----------------------------------------------------------------
# Controls

# Date to start reading
dateStart = dt.date(2015,3,31)
# Date to end reading (will NOT read data on last day)
dateEnd = dt.date(2015,4,8)
#dateEnd = dt.date(2015,4,2)

# Number of days to read at once
batchDays = 4

# Lon/Lat pairs to write out
domainFile = 'nldasDomainSection.txt'
# Directory where raw SMAP data are held
smapDir = '../../data/smapData'
# Directory where processed SMAP time series will be written
smapOutDir = '../../data/smapTs'

# Total number of days to read
totDays = (dateEnd-dateStart).days
# Number of batches of data to go through
nBatches = math.ceil(totDays/batchDays)
# Fields and data types to read in
fields, dataTypes = getFieldsAndDataTypes()[:2]

# ----------------------------------------------------------------
# Get domain data

# The first file's name
firstFn = getFn(date=dateStart, smapDir=smapDir, type='SMP')
# Read the lon/lat data from the first file
smapLonLat = getSmapLonLat(fn=firstFn)
# Replace -9999.0 with np.nan
smapLonLat['longitude'][smapLonLat['longitude']==-9999.0]=np.nan
smapLonLat['latitude'][smapLonLat['latitude']==-9999.0]=np.nan
# Extract a 1-d array of lon and lat data
lonData = np.nanmean(smapLonLat['longitude'],axis=0)
latData = np.nanmean(smapLonLat['latitude'],axis=1)

# Read file containing domain data
with open(domainFile) as fid:
    # Initialize vars to keep
    domainPixels = []
    # Skip the header
    next(fid)
    # Read the rest of the data
    for line in fid:
        thisLine = line.split()
        domainPixels.append(thisLine)
# Initialize a structured array to hold the pixel lat/lon and IDs
domainPixelsArr = np.empty([len(domainPixels)],dtype=[('longitude',np.float32), ('latitude',np.float32), ('pixelId',np.dtype('U9'))])
# Write the list data into the structured array
for ll in range(len(domainPixels)):
    domainPixelsArr[ll] = tuple(domainPixels[ll])
# The min and max lon and lat values in the domain. Allow some extra space to ensure the closest SMAP pixel is mapped to the NLDAS pixel, not just the closest in bounds SMAP pixel.
minLon = np.min(domainPixelsArr['longitude'])-0.5
maxLon = np.max(domainPixelsArr['longitude'])+0.5
minLat = np.min(domainPixelsArr['latitude'])-0.5
maxLat = np.max(domainPixelsArr['latitude'])+0.5
# Trim the lon and lat data to the domain 
trimmedLon = trim1d(lonData,minLon,maxLon)
trimmedLat = trim1d(latData,minLat,maxLat)

# ----------------------------------------------------------------
# Read SMAP data and save to array
# Separate the total days into discrete batches to avoid running out of memory. We'll write each batch to disk before clearing that data from memory and going to the next one.

# Initialize a value for the number of days left to read
daysLeft = totDays

# Loop through each batch
for bb in range(nBatches):
    # Print batch number
    print('Reading batch ' + str(bb+1) + ' of ' + str(nBatches) + '...')
    # Initialize an empty array the same size as the lon/lat (plus an extra dimension for time) to hold this batch's data
    batchSmapData = np.empty([len(trimmedLat), len(trimmedLon), np.min([batchDays, daysLeft])*2],dtype=dataTypes)
    # Loop through each day in the batch
    for dd in range(np.min([batchDays, daysLeft])):
        # The date of this loop
        thisDate = dateStart + dt.timedelta(days=dd+bb*batchDays)
        print('Reading date ' + thisDate.isoformat() + '...')
        # The SMAP hdf file name from this day
        smapFn = getFn(date=thisDate, smapDir=smapDir, type='SMP')
        # The SMAP data from that hdf file
        fileSmapData = getSmapSm(fn=smapFn,am=True,pm=True)
        # Trim the data to the domain
        trimmedData = trimData3d(data=fileSmapData,lonData=lonData,latData=latData,minLon=minLon,maxLon=maxLon,minLat=minLat,maxLat=maxLat)
        # Write the data to this batch's data
        batchSmapData[:,:,(dd*2):(dd*2)+2] = trimmedData
    # Write these data to a file corresponding to its pixel
    for ff in range(len(domainPixelsArr)):
        if ff <1:#% 1000 == 0:
            #print('writing pixel ' + str(ff) + ' of ' + str(len(domainPixelsArr)))
            #print(domainPixelsArr['pixelId'][ff])
            # Name of file to write to
            fName = smapOutDir + '/' + domainPixelsArr['pixelId'][ff] + '.txt'
            # Select the appropriate SMAP pixel to pull data from
            lonIdx, latIdx = selectSmapPixel(trimmedLon, trimmedLat, domainPixelsArr['longitude'][ff], domainPixelsArr['latitude'][ff])
            # Pull data from SMAP array 
            smapTs = batchSmapData[lonIdx,latIdx,:]
            # Remove data without a lon value (indicates no retrieval)
            smapTsClean = removeNoData(smapTs)
            # Format data into a string 
            bodyStr, headerStr = formatAsString(smapTsClean)
            # Write the data to the file. Open with append 'a' mode. Close when done.(include header if first time writing--if file did not exist)
            writeToFile(fName,bodyStr,headerStr)

            # Clear smapData from memory

    # Update daysLeft variable
    daysLeft -= batchDays
