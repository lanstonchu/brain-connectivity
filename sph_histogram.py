
import json
import urllib.request
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import random
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

wall_names = [' (i.e. Inner Wall)',' (i.e. Middle Wall)',' (i.e. Outer Wall)']

def reg_to_sph(reg_coord):
    # to convert retangular coordinates to WebGL's spherical coordinates
    
    # theory: https://en.wikipedia.org/wiki/Spherical_coordinate_system
    # format modification: elevation angle is from y-axis: https://threejs.org/docs/#api/en/math/Spherical    
    x = reg_coord[:,0]
    y = reg_coord[:,1]
    z = reg_coord[:,2]
        
    r_xz_square = x**2 + z**2 # for atan2
    r = np.sqrt(r_xz_square + y**2)
    
    theta = np.arctan2(np.sqrt(r_xz_square), y) % np.pi # elevation angle from y-axis; belongs to [0, pi)
    phi = (np.arctan2(-z, x) + np.pi) % (2*np.pi)
   
    sph_coord = np.transpose(np.vstack((r, theta, phi)))    
    return sph_coord # (r, elevation, angle_xy)

def sph_to_reg(sph_coord):
    # to convert spherical coordinates to retangular coordinates
    
    r = sph_coord[:,0]
    theta = sph_coord[:,1]
    phi = sph_coord[:,2]
  
    y = r*np.cos(theta)
    x = -r*np.cos(phi)*np.sin(theta)
    z = r*np.sin(phi)*np.sin(theta)
    
    reg_coord = np.transpose(np.vstack((x, y, z)))
    return reg_coord

def determine_closest_points_of_walls(lines, radii):
    # to convert retangular coordinates of paths to spherical coordinates
    # only keep closest 2 points (i.e. inside and outside) for each wall
    
    if len(radii)!=3:
        raise Exception("There should be 3 walls.")
        
    r0 = radii[0]
    r1 = radii[1]
    r2 = radii[2]
    
    if r0 > r1 or r1 > r2:
        raise Exception("The walls' distance should be in ascending order.")
        
    num_lines = len(lines)
    
    closest_points_all_paths = np.zeros([num_lines,6,3])
    closest_points_idx = np.ones([num_lines, 4])*-1 # first 3 columns: indices before passing wall; last column: total number of points in path
    for j in range(len(lines)):
        
        line = lines[j]        
        path = np.array([pt['coord'] for pt in line['path']]) # extract path coordinates from the data
        path_recentered = (path - path[0,:]) # recentered the path for radius calculation
        path_sph = reg_to_sph(path_recentered)        
        r_points = path_sph[:,0]
        r_far = np.max(r_points)
        
        r_wall_contain = next(r for r in [r0, r1, r2, np.inf] if r >= r_far) # r_wall_contain will indicate whether r_far is inside all walls
        
        closest_points_idx[j, 3] = len(path)
        closest_points = np.ones([6,3])*-1 # default values = -1 if the path doesn't passing through the wall        
        if r_wall_contain > r0: # if r_far is outside wall0
            i0 = next(i for i in range(len(r_points)) if r_points[i] >= r0)
            closest_points[0,:] = path_sph[i0-1,:]
            closest_points[1,:] = path_sph[i0,:]   
            closest_points_idx[j, 0] = i0 - 1
            
        if r_wall_contain > r1: # if r_far is outside wall1
            i1 = next(i for i in range(len(r_points)) if r_points[i] >= r1)
            closest_points[2,:] = path_sph[i1-1,:]
            closest_points[3,:] = path_sph[i1,:]
            closest_points_idx[j, 1] = i1 - 1
            
        if r_wall_contain > r2: # if r_far is outside wall2
            i2 = next(i for i in range(len(r_points)) if r_points[i] >= r2)
            closest_points[4,:] = path_sph[i2-1,:]
            closest_points[5,:] = path_sph[i2,:]
            closest_points_idx[j, 2] = i2 - 1
            
        closest_points_all_paths[j,:,:] = closest_points
            
    return closest_points_all_paths, closest_points_idx

def compute_binStat2D(closest_points_all_paths, selected_indices, wall_i, bin_num):
    
    row_start = wall_i*2
    total_indices = range(len(closest_points_all_paths))
    
    # Part A: remove invalid points; only paths passing through the wall is valid
    indices_valid0 = np.where(closest_points_all_paths[:,row_start + 1,0]!=-1) # filter 1
    indices_valid = np.array([idx for idx in total_indices if idx in indices_valid0[0] and idx in selected_indices]) # filter 2

    thetas_valid = closest_points_all_paths[indices_valid, row_start:(row_start+2),1].flatten()
    phis_valid  = closest_points_all_paths[indices_valid, row_start:(row_start+2),2].flatten()
    
    if (-1 in thetas_valid) or (-1 in phis_valid):
        raise Exception("The number of valid r/theta/phi don't match.")
    
    # Part B: histogram construction and statistics visualization
    edges_theta = np.linspace(0, np.pi, num=bin_num+1)
    edges_phi = np.linspace(0, 2*np.pi, num=2*bin_num+1)    
    
    binStat2D = stats.binned_statistic_2d(thetas_valid, phis_valid, None, 'count', bins=[edges_theta, edges_phi], expand_binnumbers=True)
   
    stat2D = binStat2D.statistic
    bin_points = binStat2D.binnumber
    bin_theta_minus_1, bin_phi_minus_1 = np.where(stat2D == np.max(stat2D))

    print(np.flip(stat2D, axis=0))
    
    # Part C: plot visualization
    plot_histogram_scatter(phis_valid, thetas_valid, bin_num, wall_i)  
    
    # Part D: Clustering
    clustering(phis_valid, thetas_valid, bin_num, wall_i)
    
    # Ensure there is no points exceeding lower/upper boundaries
    if not(all((bin_points.flatten()!=0)) and all((bin_points[0]!=len(edges_theta))) and all((bin_points[1]!=len(edges_phi)))):
        raise Exception("Not all points are within lower/upper bin-boundaries.")
    
    if len(bin_theta_minus_1)!=len(bin_phi_minus_1):
        raise Exception("The length of theta-bins and phi-bins don't match.")
        
    # In case there are more than 1 max. bin, select a random one
    if len(bin_theta_minus_1)>=2:
        
        random.seed(123)
        myIdx = random.randint(0, len(bin_theta_minus_1) - 1)
        
        bin_theta_minus_1 = bin_theta_minus_1[myIdx]
        bin_phi_minus_1 = bin_phi_minus_1[myIdx]
        
    bin_theta = int(bin_theta_minus_1+1)
    bin_phi = int(bin_phi_minus_1+1)
    
    indices_flatten = np.where((np.transpose(bin_points) == (bin_theta, bin_phi)).all(axis=1))
    # only keep odd number points (i.e. outside of wall)    
    indices_points = [int((idx - 1)/2) for idx in indices_flatten[0] if idx % 2 == 1]
    
    range_theta = [edges_theta[bin_theta - 1], edges_theta[bin_theta]]
    range_phi = [edges_phi[bin_phi - 1], edges_phi[bin_phi]]
   
    selected_indices_out = [int(indices_valid[idx]) for idx in indices_points]
    
    return range_theta, range_phi, selected_indices_out

def plot_histogram_scatter(phis, thetas, bin_num, wall_i):
    fig, ax = plt.subplots()
    plt.hist2d(phis, thetas, bins=[2*bin_num, bin_num], range = [[0, 2*np.pi], [0, np.pi]],cmap='Blues')
    ax.set_title('Histogram of Flow of Wall ' + str(wall_i) + wall_names[wall_i])
    ax.set_ylabel(r"$\theta$")
    ax.set_xlabel(r"$\phi$")
    
    plt.twinx()
    plt.scatter(phis, thetas)
    plt.xlim(0, 2*np.pi)
    plt.ylim(0, np.pi)

    plt.show()   
    return

def clustering(phis, thetas, bin_num, wall_i):
    
    min_num_cluster = 2
    max_num_cluster = 10
    
    ph_th = np.transpose(np.vstack((phis, thetas)))

    sil_score_max = -1 # minimum possible score
    for n_clusters in range(min_num_cluster, max_num_cluster):
         model = KMeans(n_clusters = n_clusters, init='k-means++', max_iter=100, n_init=1) 
         labels = model.fit_predict(ph_th)
         sil_score = silhouette_score(ph_th, labels)
         # print("The average silhouette score for %i clusters is %0.2f" %(n_clusters,sil_score))
         if sil_score > sil_score_max:
             sil_score_max = sil_score
             best_n_clusters = n_clusters

    model = KMeans(n_clusters=best_n_clusters)
    model.fit(ph_th)
    
    yhat = model.predict(ph_th)
    clusters = np.unique(yhat)
    
    fig, ax = plt.subplots()
    # plt.hist2d(phis, thetas, bins=[2*bin_num, bin_num], range = [[0, 2*np.pi], [0, np.pi]],cmap='Blues')
    ax.set_title('Clustering Result at Wall ' + str(wall_i) + wall_names[wall_i])
    ax.set_ylabel(r"$\theta$")
    ax.set_xlabel(r"$\phi$")
    
    plt.twinx()
    
    for cluster in clusters:
    	# get row indexes for samples with this cluster
    	row_ix = np.where(yhat == cluster)
    	# create scatter of these samples
    	plt.scatter(ph_th[row_ix, 0], ph_th[row_ix, 1])

    plt.xlim(0, 2*np.pi)
    plt.ylim(0, np.pi)

    plt.show() 
    
    return

def subset_check(closest_points_idx, selected_indices_i, wall_i):
    
    myColumn = closest_points_idx[:, wall_i]
    valid_indices = np.where(myColumn != -1)
    
    for idx in selected_indices_i:
        if idx not in valid_indices[0]:
            raise Exception("closest_points_idx (i.e. pre-histogram filter) should contain more valid paths than selected_indices_i (i.e. post-histogram filter) .")
    return
    
# Part I: Download lines coordinate
 
injection_data_set_id = 156394513

# destination coordinate: LGd (Dorsal part of the lateral geniculate complex)
x = 7400 # unit: 1 μm
y = 3300
z = 3300

# =============================================================================
# # destination coordinate: IG (Innduseum Griseum)
# x = 4500 # unit: 1 μm
# y = 3200
# z = 5700
# =============================================================================

# =============================================================================
# # destination coordinate: MO1 (Somatomotor areas, Layer 1)
# x = 4400 # unit: 1 μm
# y = 1500
# z = 5600
# =============================================================================

LINES_FMT = "http://api.brain-map.org/api/v2/data/query.json?criteria=service::mouse_connectivity_target_spatial[seed_point$eq%d,%d,%d]"
url = LINES_FMT % (x, y, z)

connection = urllib.request.urlopen(url)
response_text = connection.read()

# =============================================================================
# htmlResponseFilename = 'htmlResponseSample_' + str(x) + '_' + str(y) + '_' + str(z) + '.html'
# # htmlResponseFilename = 'htmlResponseSample.html'
# with open(htmlResponseFilename, 'r') as f:
#     response_text = f.read() # read htmlResponseSample.html instead of using api for debugging purpose
# =============================================================================

response = json.loads(response_text)

lines = response['msg']

# Part II: Determine distances of walls

start_points = np.array([line['path'][0]['coord'] for line in lines])
start_point = np.mean(start_points, axis = 0)

end_points_recentered = np.array([line['path'][-1]['coord'] - start_point for line in lines])
end_points_sph = reg_to_sph(end_points_recentered)
r_end_points = end_points_sph[:,0]
percent_paths_not_passing_outer = 0.75*100
adj_ratio = 0.9
r_outer = np.percentile(r_end_points, percent_paths_not_passing_outer)*adj_ratio
r_middle = r_outer*2/3
r_inner = r_outer*1/3

# Part III: Transform all paths into 6 rows for 3 walls only

radii = [r_inner, r_middle, r_outer]
closest_points_all_paths, closest_points_idx = determine_closest_points_of_walls(lines, radii)

# Part IV: Construct 2D histogram
selected_indicesX = range(len(closest_points_all_paths))
range_theta0, range_phi0, selected_indices0 = compute_binStat2D(closest_points_all_paths, selected_indicesX, 0, 180/90)
range_theta1, range_phi1, selected_indices1 = compute_binStat2D(closest_points_all_paths, selected_indices0, 1, 180/45)
range_theta2, range_phi2, selected_indices2 = compute_binStat2D(closest_points_all_paths, selected_indices1, 2, 180/22.5)

subset_check(closest_points_idx, selected_indices0, 0)
subset_check(closest_points_idx, selected_indices1, 1)
subset_check(closest_points_idx, selected_indices2, 2)
    
# Part V: Save Json file
data = {"lines": lines,
    "destinationCoordinates": [[x, y, z]],
    "wallRadii": radii,
    "wallThetaPhi":[[range_theta0, range_phi0], [range_theta1, range_phi1], [range_theta2, range_phi2]],
    "selected_indices0":selected_indices0,
    "selected_indices1":selected_indices1,
    "selected_indices2":selected_indices2,
    "closest_points_idx":closest_points_idx.tolist()
    }

with open('data.json', 'wb') as f:
    f.write(json.dumps(data).encode())
