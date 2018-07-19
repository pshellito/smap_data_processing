'''
This file contains functions that are used to read and process SMAP data
P. Shellito 6/14/18
'''
import datetime as dt
import h5py as h5
import numpy as np
from pjsFunctions import enlargeLonLat

# Function to return the file name of the SMAP file from a specific date
def getFn(date, smapDir, type):
    if type == 'SMP':
        typeDir = '/SPL3SMP/'
        filePrefix = 'SMAP_L3_SM_P_'
    else:
        raise NameError("Requested SMAP type not supported.")
    if not isinstance(date, dt.date):
        raise TypeError("Requested day must be of type datetime.date")
    if not isinstance(smapDir, str):
        raise TypeError("SMAP directory must be provided as a string")
    fn = smapDir + typeDir + date.strftime('%Y.%m.%d/') + filePrefix + date.strftime('%Y%m%d.h5')
    return fn

# Function to read the soil moisture field from the SMAP file
def getSmapSm(fn, am=False, pm=False):
    # Open file
    ff = h5.File(fn, 'r')
    # Print the dataset names
    #for nn in ff.keys():
        #print(nn)
        #print(list(ff[nn].keys()))
    # Size of the SMAP data
    nLat = 406
    nLon = 964
    # Name of AM group
    amGrp = 'Soil_Moisture_Retrieval_Data_AM'
    # Names of required fields to save
    reqFields = ['longitude',               'latitude',                'retrieval_qual_flag',    'tb_v_corrected',          'soil_moisture',           'soil_moisture_error',     'tb_qual_flag_v',         'surface_flag',           'vegetation_water_content', 'tb_time_utc']
    # Data types of those fields
    dataTypes = [(reqFields[0],np.float32), (reqFields[1],np.float32), (reqFields[2],np.uint16), (reqFields[3],np.float32), (reqFields[4],np.float32), (reqFields[5],np.float32), (reqFields[6],np.uint16), (reqFields[7],np.uint16), (reqFields[8],np.float32),  (reqFields[9],np.dtype('U24'))]
    # Initialize a structure array to hold the data
    struc = np.empty([nLat,nLon],dtype=dataTypes)
    # Loop through required fields
    for rr in range(len(reqFields)):
        print(reqFields[rr])
        # This field
        struc[reqFields[rr]] = ff[amGrp][reqFields[rr]][()]
        # Replace -9999. with nan START HERE
        #struc[reqFields[rr]][struc[reqFields[rr]]==-9999.] = np.nan
    # Close file
    ff.close()
    return struc

# Function to trim the data to requested range
def trimData(data,lonData,latData,minLon,maxLon,minLat,maxLat):
    # Difference between longitudes and requested min and max lons
    lonDiffMin = lonData-minLon
    lonDiffMax = maxLon-lonData
    # Difference between latitudes and requested min and max lats
    latDiffMin = latData-minLat
    latDiffMax = maxLat-latData
    # Closest postive differences
    minLonVal = min(lonDiffMin[lonDiffMin>=0])
    maxLonVal = min(lonDiffMax[lonDiffMax>=0])
    minLatVal = min(latDiffMin[latDiffMin>=0])
    maxLatVal = min(latDiffMax[latDiffMax>=0])
    # Indices of those values
    minLonIdx = lonDiffMin.tolist().index(minLonVal)
    maxLonIdx = lonDiffMax.tolist().index(maxLonVal)+1
    minLatIdx = latDiffMin.tolist().index(minLatVal)+1
    maxLatIdx = latDiffMax.tolist().index(maxLatVal)
    # Return trimmed data
    return data[maxLatIdx:minLatIdx,minLonIdx:maxLonIdx]

# A function that will replace specific values in a data field with nan
def nanfill(data,nanval,fieldName):
    nanIdcs = data[fieldName]==nanval
    data[fieldName][nanIdcs] = np.nan
    return data

# A function that will trim vectors down to only include values within a specific range
def trim1d(data,minn,maxx):
    idcsInBounds = (data>=minn) & (data<=maxx)
    trimmedData = data[idcsInBounds]
    return trimmedData

# A function that will do the processing necessary to fill in lon and lat values and enlarge them
def processLatLon(mapObj,cLon,cLat,minLon,maxLon,minLat,maxLat):
    # cLon and cLat are the "complete' lon and lat fields (not trimmed). The ranges provided by min/max lon/lat indicate what we intend to plot)
    # 1-dimensional lon and lat fields
    lon1d=np.nanmean(cLon ,axis=0)
    lat1d=np.nanmean(cLat ,axis=1)
    #print(lon1d)
    #print(lat1d)
    # Trim the lon and lat down
    trimmedLon = trim1d(lon1d,minLon,maxLon)
    trimmedLat = trim1d(lat1d,minLat,maxLat)
    #print(trimmedLon)
    #print(trimmedLat)
    # Create filled 2-d lon and lat fields
    lon2d=np.tile(trimmedLon,(len(trimmedLat),1))
    lat2d=np.transpose(np.tile(trimmedLat,(len(trimmedLon),1)))
    # Grid spacing of lon and lat
    dLon = np.mean(np.diff(trimmedLon))
    dLat = np.mean(np.diff(trimmedLat))
    # Enlarge the grids for plotting with pcolormesh
    eLons, eLats = enlargeLonLat(lon2d,lat2d,dLon,dLat)
    return eLons, eLats

# A function to return the value of specific bits in a 16-bit unsigned integer.
def bitVal(intArr,qBit):
    '''
    Given array of whole, positive, decimal integers, return the boolean corresponding to whether or not the qBit-th bit associated with the binary equivalent is raised.
    '''
    # Divide by 2 the number of times as bits requested
    for nn in range(qBit):
        intArr = intArr // 2
    # Return a boolean that indicates whether the resulting values have a remainder when divided by two. This indicates that the flag is raised
    raised = (intArr % 2).astype(bool)
    return raised
