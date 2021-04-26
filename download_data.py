# modified from api.brain-map.org/examples/doc/lines/download_data.py.html
# main change: translation from Python 2 to Python 3

import api
import numpy as np
import json

DATA_SET_ID = 566244185 # injection site at LGd
# =============================================================================
# DENSITY_RANGE = [0.04, 0.04001] # density requirement
# =============================================================================
DENSITY_RANGE = [0.04, 0.0400] # density requirement
INJECTION_MASK_THRESHOLD = 0.5

def DownloadLines(dataSetId, densityRange):
    print("downloading density volume")
    densityHeader, densityArr, densityMeta = api.DownloadDataSetVolume(dataSetId, 'density')
    densitySpacing = np.array(densityMeta['ElementSpacing']) # unit = 100μm, i.e. lower resolution

    print("downloading fiber tract volume")
    ftHeader, ftArr, ftMeta = api.DownloadFiberTractVolume()
    ftSpacing = np.array(ftMeta['ElementSpacing']) # unit = 25μm, i.e. higher resolution

    ftScale = densitySpacing / ftSpacing.astype(np.float32)  # ftArr's size (e.g. [528, 320, 456]) to densityArr's size (e.g. [132, 80, 114]) ratio
    ftDims = ftArr.shape    

    indices = np.argwhere((densityArr >= densityRange[0]) & (densityArr <= densityRange[1])) # extract indices that is within the density requirement

    dataSetLines = []
    
    count = 0
    for index in indices:
        
        if count % 10 == 0:
            print("count = " + str(count) + " / " + str(len(indices)))
        count+=1
        
        ftIndex = np.array(index * ftScale, dtype=np.int64) # index rescaling
        try:
            ftVal = ftArr[ftIndex[0], ftIndex[1], ftIndex[2]]
        except IndexError as e:
            print(index + "outside fiber tract mask")
            continue

        if ftVal == 0: # download lines that are outside the fiber tract mask (i.e. axon mask)
            coord = index * densitySpacing # coordinates in μm
            lines = api.DownloadTargetLines(coord, dataSetId)

            dataSetLines += lines # union the new lines set to the original lines set
            
        else:
            print(str(index) + "inside fiber tract mask")

    return dataSetLines

	
def DownloadInjectionCoordinates(dataSetId, injectionMaskThreshold):
    print("downloading injection mask coordinates")
    header, arr, meta = api.DownloadDataSetVolume(dataSetId, 'injection') # note: most values in arr are just simply 0

	
    spacing = np.array(meta['ElementSpacing'])
    coords = np.argwhere(arr > injectionMaskThreshold) * spacing
    
    return coords.tolist() # injection coordinates in μm

if __name__ == "__main__":

    data = {
        "lines": DownloadLines(DATA_SET_ID, DENSITY_RANGE),
# =============================================================================
#         "injectionCoordinates": DownloadInjectionCoordinates(DATA_SET_ID, INJECTION_MASK_THRESHOLD)
# =============================================================================
        "destinationCoordinates": DownloadInjectionCoordinates(DATA_SET_ID, INJECTION_MASK_THRESHOLD)
    }

    with open('data.json', 'wb') as f:
        f.write(json.dumps(data).encode())