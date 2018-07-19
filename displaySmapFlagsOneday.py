#! /usr/local/other/SSS)_Ana-PyD/2.4.0_py3.5/bin/python

'''
This script will read the SMAP data for one day (AM retrieval) and display the various flags 
P. Shellito
6/14/18
Flag information found here:
https://nsidc.org/data/smap/spl3smp/data-fields
'''
import datetime as dt
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from smapUtils import *
from mpl_toolkits.basemap import Basemap
#from pjsFunctions import enlargeLonLat

# Figure directory
figDir = '../figures/'
# Figure name
figName = 'staticWater.png'
# SMAP directory
smapDir = '/discover/nobackup/projects/lis/RS_DATA/SMAP'
smapDir = '../smapData'
# Range of lon/lat to extract
minLon = -125
maxLon = -76
minLat = 25
maxLat = 50
# Range of lon/lat to display
minLonDisp = minLon
maxLonDisp = maxLon
minLatDisp = minLat
maxLatDisp = maxLat

# Day to read
readDay = dt.date(2015,4,10)
# SMAP file name from that day
fileName = getFn(date=readDay, smapDir=smapDir, type='SMP')
# SMAP soil moisture from that day
data = getSmapSm(fn=fileName,am=True)
# Replace fill values with np.nan
data = nanfill(data,nanval=-9999.,fieldName='longitude')
data = nanfill(data,nanval=-9999.,fieldName='latitude')
data = nanfill(data,nanval=-9999.,fieldName='soil_moisture')
data = nanfill(data,nanval=-9999.,fieldName='tb_v_corrected')
data = nanfill(data,nanval=-9999.,fieldName='vegetation_water_content')
# Trim the data to requested domain
trimmedData = trimData(data=data,lonData=np.nanmean(data['longitude'],axis=0),latData=np.nanmean(data['latitude'],axis=1),minLon=minLon,maxLon=maxLon,minLat=minLat,maxLat=maxLat)
# Data flagged for uncertain quality
uncertainQual = bitVal(trimmedData['retrieval_qual_flag'],qBit=0)
# Data flagged for mountainous terrain
mountains = bitVal(trimmedData['surface_flag'],qBit=9)
# Data flagged for dense vegetation
denseVeg = bitVal(trimmedData['surface_flag'],qBit=10)
# Data flagged for coastal proximity 
coastalProx = bitVal(trimmedData['surface_flag'],qBit=2)
# Data flagged for static water
staticWater = bitVal(trimmedData['surface_flag'],qBit=0)

# Set up map projection 
mm = Basemap(projection='cyl', llcrnrlat=minLatDisp, urcrnrlat=maxLatDisp, llcrnrlon=minLonDisp, urcrnrlon=maxLonDisp, resolution='l', lon_0=0) # Available 'c','l','i','h','f'  
# Convert lon and lat to proper values for plotting
pLon, pLat = processLatLon(mapObj=mm,cLon=data['longitude'],cLat=data['latitude'],minLon=minLon,maxLon=maxLon,minLat=minLat,maxLat=maxLat)

# Plot 
# Figure size
width = 10
height = 6
# Open figure
fig = plt.figure(figsize=(width, height))
# Plot data of choice
#csObj=mm.pcolormesh(pLon,pLat,trimmedData['vegetation_water_content'])
csObj=mm.pcolormesh(pLon,pLat,staticWater.astype(int))
# Draw the coastlines
mm.drawcoastlines()
# Add a colorbar
fig.colorbar(csObj)
# Print the figure
print('Printing figure ' + figDir + figName + '...')
plt.savefig(figDir+figName,bbox_inches='tight')
# Close the figure
plt.close('all')
