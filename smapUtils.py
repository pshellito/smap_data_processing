'''
This file contains functions that are used to read and process SMAP data
P. Shellito 6/14/18
'''
import datetime as dt
import h5py as h5
import numpy as np
from pathlib import Path

# Function to enlarge lon and lat data so as to properly center the pixels created by pcolormesh
def enlargeLonLat(lons, lats, dlon, dlat):
    # Subtract 1/2 the grid size from both lon (lons) and lat (lats)
    lons = lons - dlon/2
    lats = lats - dlat/2
    # Add 1 grid spacing to the right column of lon array
    lons = np.c_[ lons, lons[:,-1]+dlon ]
    # Duplicate the bottom row of lon array and add it to the bottom
    lons = np.r_[ lons, [lons[-1,:]] ]
    # Duplicate the right-most column of lats and at it to the right
    lats = np.c_[ lats, lats[:,-1] ]
    # Add 1 grid spacing to the bottom row of lat array
    lats = np.r_[ lats, [lats[-1,:]+dlat] ]
    return lons, lats

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

# Function the read the lon/lat fields from the SMAP file (NOT enhanced
def getSmapLonLat(fn):
    # Open file
    ff = h5.File(fn, 'r')
    # Size of the SMAP data
    nLat = 406
    nLon = 964
    # Name of AM group
    amGrp = 'Soil_Moisture_Retrieval_Data_AM'
    # Names of fields to save
    lonLatFields = ['longitude',               'latitude']
    # Data types of those fields
    dataTypes = [(lonLatFields[0],np.float32), (lonLatFields[1],np.float32)]
    # Initialize a structure array to hold the data
    struc = np.empty([nLat,nLon],dtype=dataTypes)
    # Loop through required fields
    for rr in range(len(lonLatFields)):
        # Fill this field in the structured array with the SMAP data
        struc[lonLatFields[rr]][:,:] = ff[amGrp][lonLatFields[rr]][()]
    # Close file
    ff.close()
    return struc

# Function to read the soil moisture and other fields from the SMAP file (NOT enhanced)
def getSmapSm(fn, am=False, pm=False):
    # Open file
    ff = h5.File(fn, 'r')
#    # Print the dataset names
#    for nn in ff.keys():
#        print(nn)
#        print(list(ff[nn].keys()))
    # Size of the SMAP data
    nLat = 406
    nLon = 964
    # Name of AM group
    amGrp = 'Soil_Moisture_Retrieval_Data_AM'
    # Name of PM group
    pmGrp = 'Soil_Moisture_Retrieval_Data_PM'
    # Names of required fields to save
    reqFields, dataTypes = getFieldsAndDataTypes()[0:2]
    # Initialize a structure array to hold the data (am and pm)
    struc = np.empty([nLat,nLon,2],dtype=dataTypes)
    # Loop through required fields (but not the 'localTime' field)
    for rr in range(len(reqFields)-1):
        # Fill this field in the structured array with the SMAP data
        # If am data are requested
        if am:
            struc[reqFields[rr]][:,:,0] = ff[amGrp][reqFields[rr]][()]
        else:
            struc[reqFields[rr]][:,:,0] = np.nan
        # Record the localTime as AM
        struc['localTime'][:,:,0] = 'AM'
        # If pm data are requested
        if pm:
            struc[reqFields[rr]][:,:,1] = ff[pmGrp][reqFields[rr]+'_pm'][()]
        else:
            struc[reqFields[rr]][:,:,1] = np.nan
        # Record the localTime as PM
        struc['localTime'][:,:,1] = 'PM'
    # Close file
    ff.close()
    return struc

# Function to get the field names and data types of the SMAP data to be read. NOTE: this includes a field for localTime, which will be an AM/PM indicator
def getFieldsAndDataTypes():
    # Field Names
    reqFields = ['longitude', 'latitude', 'tb_time_utc', 'soil_moisture', 'soil_moisture_error', 'surface_flag', 'retrieval_qual_flag', 'tb_v_corrected', 'tb_qual_flag_v', 'vegetation_water_content', 'localTime']
    # Data types of those fields
    dataTypes = [(reqFields[0],np.float32), (reqFields[1],np.float32), (reqFields[2],np.dtype('U24')), (reqFields[3],np.float32), (reqFields[4],np.float32), (reqFields[5],np.uint16), (reqFields[6],np.uint16), (reqFields[7],np.float32), (reqFields[8],np.uint16), (reqFields[9],np.float32),  (reqFields[10],np.dtype('U2'))]
    # The formatting to use when printing (omits lon and lat: start with retrieval_qual_flag))
    printFormat = '{0:24s} {1:9f} {2:9f} {3:5n} {4:5n} {5:6.2f} {6:5n} {7:9f} {8:2s}\n'
    return reqFields, dataTypes, printFormat

# Function to trim 2d data to requested range
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

# Function to trim 3d data to requested range
def trimData3d(data,lonData,latData,minLon,maxLon,minLat,maxLat):
    # This function is the same as above but "data" is a matrix that has a third dimension
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
    return data[maxLatIdx:minLatIdx,minLonIdx:maxLonIdx,:]

# A function that will replace specific values in a data field with nan
def nanfill(data,nanval,fieldName):
    nanIdcs = data[fieldName]==nanval
    data[fieldName][nanIdcs] = np.nan
    return data

# Function that returns the index of the item closest to the pivot
def nearestIdx(items, pivot):
    idx = (np.abs(items-pivot)).argmin()
    return idx

# Function to select the smap pixel closest to the NLDAS pixel
def selectSmapPixel(lonData, latData, qLon, qLat):
    lonIdx = nearestIdx(lonData,qLon)
    latIdx = nearestIdx(latData,qLat)
    return lonIdx, latIdx

# Function to remove retrievals without lon data (indicates no overpass)
def removeNoData(smapTs):
    noDataIdcs = smapTs['longitude']==-9999.0
    smapTsClean = smapTs[~noDataIdcs]
    return smapTsClean

# Function to format the data as a string
def formatAsString(smapTs):
    # Get fields and data types
    fields, dataTypes, printFormat = getFieldsAndDataTypes()
    # Create header string
    headerStr = ''
    headerStr = fields[0] + ' {}\n'.format(smapTs[fields[0]][0]) + \
                fields[1] + ' {}\n'.format(smapTs[fields[1]][0]) + \
                ' '.join(fields[2:]) + '\n'
    # Create string with all the data in it
    bodyStr = ''
    for ll in range(len(smapTs)):
        bodyStr = bodyStr + printFormat.format(smapTs[fields[2]][ll], smapTs[fields[3]][ll], smapTs[fields[4]][ll], smapTs[fields[5]][ll], smapTs[fields[6]][ll], smapTs[fields[7]][ll], smapTs[fields[8]][ll], smapTs[fields[9]][ll], smapTs[fields[10]][ll])
    return bodyStr, headerStr

# Function to write to file
def writeToFile(fName, bodyStr, headerStr=''):
    # See if file exists
    fileName = Path(fName)
    exists = fileName.is_file()
    # Open the file in append mode
    fid = open(fileName, 'a')
    # If the file hadn't previously existed, join the header with the body string
    if not exists:
        printStr = headerStr + bodyStr
    else:
        printStr = bodyStr
    fid.write(printStr)
    fid.close()

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
