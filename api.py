# modified from http://api.brain-map.org/examples/doc/lines/api.py.html
# main change: translation from Python 2 to Python 3

import json
import urllib.request
# import urllib
# import urllib2
import zipfile
import re
import numpy as np
import matplotlib.pyplot as plt
	
API_SERVER = "http://api.brain-map.org/"
API_DATA_PATH = API_SERVER + "api/v2/data/"
FIBER_TRACT_VOLUME_URL = API_SERVER + "api/v2/well_known_file_download/197646984"
STRUCTURE_GRAPH_ID = 1
REFERENCE_SPACE_ID = 10

GRID_FMT = API_SERVER + "grid_data/download/%d?include=%s"
LINES_FMT = "http://api.brain-map.org/api/v2/data/query.json?criteria=service::mouse_connectivity_target_spatial[seed_point$eq%d,%d,%d][section_data_set$eq%d]"

# for QueryAPI() only
MOUSE_PRODUCT_ID = 1 # aba
PLANE_ID = 1 # coronal
DATA_SET_QUERY_URL = ("%s/SectionDataSet/query.json" +\
                          "?criteria=[failed$eq'false'][expression$eq'true']" +\
                          ",products[id$eq%d]" +\
                          ",plane_of_section[id$eq%d]") \
                          % (API_DATA_PATH, MOUSE_PRODUCT_ID, PLANE_ID)
                          
def DownloadFiberTractVolume():
    url = API_SERVER + "/api/v2/well_known_file_download/197646984"
    return DownloadVolume(url, 'annotationFiber')

def DownloadDataSetVolume(dataSetId, volume='density'):
    url = GRID_FMT % (dataSetId, volume)
    return DownloadVolume(url, volume)

def DownloadTargetLines(target_coordinate, injection_data_set_id):
    url = LINES_FMT % (target_coordinate[0], target_coordinate[1], target_coordinate[2], injection_data_set_id)
    try:
        connection = urllib.request.urlopen(url)
        response_text = connection.read()
        response = json.loads(response_text)

        if response['success'] == True:
            return response['msg']
        else:
            return []
    except urllib.error.HTTPError as e:
        return []
    
def DownloadVolume(url, volume):

    fh = urllib.request.urlretrieve(url) # download the .zip file from the url

    zf = zipfile.ZipFile(fh[0]) # fh[0] is the .zip file path

    header = zf.read(volume + '.mhd')
    raw = zf.read(volume + '.raw') # the 3D data is stored here

    arr = np.frombuffer(raw, dtype=np.float32)
   
    metaLines = str(header).split('\\n')
    
    if metaLines[0][0]=='b':
        metaLines[0] = metaLines[0][1:]
    
    if metaLines[-1]=="'":
        metaLines = metaLines[:-1]
    
    metaInfo = dict(line.split(' = ') for line in metaLines if line)

	
    for k in metaInfo:
        v = metaInfo[k]
        if re.match("^[\d\s]+$",v): # convert numerical values into floats and integers
            nums = v.split(' ')
            if len(nums) > 1:
                if k=='DimSize':
                    metaInfo[k] = list(map(int, v.split(' ')))
                else:
                    metaInfo[k] = list(map(float, v.split(' ')))
            else:
                metaInfo[k] = int(nums[0])
                
	
    arr = np.reshape(arr, metaInfo['DimSize'], order='F') # reshape vector into tensor
    
    return (header,arr,metaInfo)

	
def QueryAPI(url):
    start_row = 0
    num_rows = 2000
    total_rows = -1
    rows = []
    done = False
    
	
    while not done:
        pagedUrl = url + '&start_row=%d&num_rows=%d' % (start_row,num_rows)

        print(pagedUrl)
        source = urllib.request.urlopen(pagedUrl).read()
        response = json.loads(source)
        rows += response['msg']
        
        if total_rows < 0:
            total_rows = int(response['total_rows'])

        start_row += len(response['msg'])

        if start_row >= total_rows:
            done = True

    return rows

if __name__ == "__main__":
    myResult = QueryAPI(DATA_SET_QUERY_URL)
    print(len(myResult))
    print(myResult[0]) # print an example result