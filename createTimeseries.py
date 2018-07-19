# This script will read in SMAP data and write out time series.
# The number of days of SMAP data to be read in is limited by computer memory and spatial extent requested.
# The locations of the time series to be written out is defined by a separate python file that contains a 2-column array of all the lon/lat pairs we want. That file is created by a separate script, named, "createDomain.py"
# P. Shellito, Jul 19, 2018

import datetime as dt
import numpy as np
from smapUtils import *

# ----------------------------------------------------------------
# Controls

# Date to start reading
dateStart = dt.date(2015,3,31)
# Date to end reading (will NOT read data on last day)
dateEnd = dt.date(2015,4,2)

# Number of days to read at once

# Lon/Lat pairs to write out
domainFile = 'nldasDomainSection.txt'
# Directory where SMAP data are held
smapDir = '../data/smapData'

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
# Convert from list to floating-point array
#domainPixelsArr = np.asarray(domainPixels,dtype=np.float32)
domainPixelsArr = np.asarray(domainPixels)
# START HERE
#domainPixelsArr = np.asarray(domainPixels,dtype=[('longitude',np.float32), ('latitude',np.float32),('pixelId',np.float32)])
# The min and max lon and lat values in the domain
minLon = np.min(domainPixelsArr[:,0])
maxLon = np.max(domainPixelsArr[:,0])
minLat = np.min(domainPixelsArr[:,1])
maxLat = np.max(domainPixelsArr[:,1])
# Trim the data to the domain (will provide the shape of the array to save)
trimmedLonLat = trimData(smapLonLat,lonData,latData,minLon,maxLon,minLat,maxLat)

# ----------------------------------------------------------------
# Read SMAP data and save to array

# Total number of days to read
totDays = (dateEnd-dateStart).days
# Fields and data types to read in
fields, dataTypes = getFieldsAndDataTypes()
# Initialize an empty array to hold this batch's data
batchSmapData = np.empty([np.shape(trimmedLonLat)[0], np.shape(trimmedLonLat)[1], totDays*2],dtype=dataTypes)
# Loop through each day
for dd in range(totDays):
    # The date of this loop
    thisDate = dateStart + dt.timedelta(days=dd)
    # The SMAP hdf file name from this day
    smapFn = getFn(date=thisDate, smapDir=smapDir, type='SMP')
    # The SMAP data from that hdf file
    fullSmapData = getSmapSm(fn=smapFn,am=True,pm=True)
    # Trim the data to the domain
    trimmedData = trimData3d(data=fullSmapData,lonData=lonData,latData=latData,minLon=minLon,maxLon=maxLon,minLat=minLat,maxLat=maxLat)
    # Write the data to this batch's data
    batchSmapData[:,:,(dd*2):(dd*2)+2] = trimmedData
# Write these data to a file corresponding to its pixel
for ff in range(np.shape(domainPixelsArr)[0]):
    print(domainPixelsArr[ff,2])
