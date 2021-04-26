

import api
import numpy as np
import json

DATA_SET_ID = 479670988 # injection site at LGd
	
def DownloadInjectionCoordinates(dataSetId, injectionMaskThreshold):
    print("downloading injection mask coordinates")
    header, arr, meta = api.DownloadDataSetVolume(dataSetId, 'injection') # note: most values in arr are just simply 0

	
    spacing = np.array(meta['ElementSpacing'])
    coords = np.argwhere(arr > injectionMaskThreshold) * spacing
    
    return coords.tolist() # injection coordinates in μm

data = {
    "lines": [],
    "destinationCoordinates": DownloadInjectionCoordinates(DATA_SET_ID, INJECTION_MASK_THRESHOLD)
}

abc = data['destinationCoordinates']

with open('data.json', 'wb') as f:
    f.write(json.dumps(data).encode())