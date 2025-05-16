import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn.preprocessing
import seaborn as sns
from itertools import product
from datetime import datetime
import math

# data import
# ACTION: choose input
flights = pd.read_csv('ex_subset_ESSA_2019.csv', 
header=0,
sep=','
) 

# converting unix timestamp to time object
flights_filtered = flights.copy()
flights_filtered['time_obj'] = flights_filtered['timestamp'].transform(lambda x: datetime.utcfromtimestamp(x))
flights_filtered['time'] = flights_filtered['time_obj'].transform(lambda x: int(x.strftime('%H%M%S')))


# adding border values for correct normalization of coordinates
# ACTION: change based on chosen TMA
ATM = flights_filtered
df1 = pd.DataFrame({"flightID":['xxx'],"sequence":[0],"timestamp":[0],"lat":[60.2994], "lon":[19.8281],"rawAltitude":[0],"baroAltitude":[0],"velocity":[0],"endDate":[0]})
ATM = pd.concat([ATM,df1],ignore_index=True)
df2 = pd.DataFrame({"flightID":['xxx'],"sequence":[0],"timestamp":[0],"lat":[58.5831], "lon":[16.2678],"rawAltitude":[0],"baroAltitude":[0],"velocity":[0],"endDate":[0]})
ATM = pd.concat([ATM,df2],ignore_index=True)

# the grid dimensions (approx 1NM), calculated based on the width and height of rectangle tightly surroundinig TMA
# if the boundary of the data is not TMA but xNM circle around airport, just use the diameter for both x and y 
#ACTION: change based on chosen TMA
grid_x = 103
grid_y = 109

lon = np.array(ATM['lon'])
lat = np.array(ATM['lat'])

# First, creating list of X and Y for min.time plots (list creating function, used later)
def createList(r1, r2): 
    return [item for item in range(r1, r2+1)] 


def distance(p11,p12,p21,p22):
    return math.hypot(p11-p21, p12-p22)

# Normalization of the coordinates into grid
ATM['lon_norm'] = sklearn.preprocessing.minmax_scale(lon, feature_range=(0, grid_x),copy=True)
ATM['lat_norm'] = sklearn.preprocessing.minmax_scale(lat, feature_range=(0, grid_y),copy=True)

### calculated to plot with the TMA polygons, otherwise just circle can be plotted
#function to choose the closest number to the specified one
def takeClosest(num,collection):
   return min(collection,key=lambda x:abs(x-num))

# coordinates for ESSA TMA polygon
#ACTION: change to chosen TMA
polygon_lat = [60.2994,60.2661,59.8828,60.0353,59.6736,59.5994,59.2550,59.0419,58.8325,58.7525,58.5831,58.6164,58.9661,58.9786,59.0119,59.0494,59.3239,59.7494,60.2328,60.2994]
polygon_lat_norm = pd.Series([])
polygon_lon = [18.2131,18.5547,18.8469,19.3136,19.8281,19.2736,18.9683,18.7547,18.5394,18.4572,17.9328,17.4569,17.4078,17.2233,16.7078,16.2678,16.3183,16.4467,17.5967,18.2131]
polygon_lon_norm = pd.Series([])

#changing the geo coordinates to normalized ones
for i in polygon_lat:
    if ATM.loc[(ATM['lat'] == i)].empty == True:
        i = takeClosest(i, ATM['lat'])
        value = ATM.loc[(ATM['lat'] == i)]['lat_norm'].head(1).item()
    else:
        value = ATM.loc[(ATM['lat'] == i)]['lat_norm'].head(1).item()
    # polygon_lat_norm = polygon_lat_norm.append(pd.Series([value]))
    polygon_lat_norm = pd.concat([polygon_lat_norm,pd.Series([value])],ignore_index=True)
    
for i in polygon_lon:
    if ATM.loc[(ATM['lon'] == i)].empty == True:
        i = takeClosest(i, ATM['lon'])
        value = ATM.loc[(ATM['lon'] == i)]['lon_norm'].head(1).item()
    else:
        value = ATM.loc[(ATM['lon'] == i)]['lon_norm'].head(1).item()
    # polygon_lon_norm = polygon_lon_norm.append(pd.Series([value]))
    polygon_lon_norm = pd.concat([polygon_lon_norm,pd.Series([value])],ignore_index=True)

ESSA_polygon = pd.concat([polygon_lat_norm, polygon_lon_norm], axis=1)
ESSA_polygon.columns = ['lat_norm','lon_norm']
ESSA_polygon = ESSA_polygon.reset_index(drop = True)

#calculation of the area, used later for horizontal spread metric
#ACTION: change the c point, it is one random point inside the chosen TMA used as a reference point when calculating the polygon area (triangles using waypoints)
area_fin = pd.Series([])
for i in range(len(ESSA_polygon)-1):
    a1 = ESSA_polygon['lon_norm'][i]
    a2 = ESSA_polygon['lat_norm'][i]
    b1 = ESSA_polygon['lon_norm'][i+1]
    b2 = ESSA_polygon['lat_norm'][i+1]
    c1 = 60.7944
    c2 = 46.882
    side_a = distance(a1, a2, b1, b2)
    side_b = distance(b1,b2,c1,c2)
    side_c = distance(c1,c2,a1,a2)
    s = 0.5 * ( side_a + side_b + side_c)
    area_triangle = math.sqrt(s * (s - side_a) * (s - side_b) * (s - side_c))
    # area_fin = area_fin.append(pd.Series([area_triangle]))
    area_fin = pd.concat([area_fin,pd.Series([area_triangle])],ignore_index=True)
total_TMA = area_fin.sum()

ATM['lat_norm_round'] = ATM['lat_norm'].transform(lambda x: round(x))
ATM['lon_norm_round'] = ATM['lon_norm'].transform(lambda x: round(x))
wrong_flights = ATM.loc[(ATM['lon_norm_round'] >= 44) & (ATM['lon_norm_round'] <= 46)]
wrong_flights = wrong_flights.loc[(wrong_flights['lat_norm_round'] >= 52)]
wrong_flights_IDs = wrong_flights.groupby('flightID')['flightID'].head(1)

#ACTION: change name of the file  
pd.DataFrame(ESSA_polygon).to_csv('ESSA_polygon.csv')
print('POLYGONS DONE')

# ==================================== SELECTING SUBSET OF DATA ========================================='
# can be used for subset selection or iteration over hours of the dataset to get fine-grained analysis
#this code is set to provide the large-scale analysis (whole dataset)

#drops the lines with boundaries used above
ATM.drop(ATM[ATM['flightID'] == 'xxx'].index, inplace = True)
ATM = ATM.reset_index()
Grid_frame = ATM
print('DATA SELECTION DONE')
# ================================= PLOT OF FLIGHT TRAJECTORIES ============================================
# plot of flight trajectories
fig, ax = plt.subplots(figsize=(10,9))
for i, g in Grid_frame.groupby(['flightID','endDate']):
    g.plot(x='lon_norm', y='lat_norm', ax=ax, label=str(i))
ax.xaxis.set_ticks(np.arange(0, grid_x+1, 5))  ## GRID CHANGE !!! 
ax.yaxis.set_ticks(np.arange(0, grid_y+1, 5))
plt.xlabel('X - coordinates')
plt.ylabel('Y - coordinates')
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)    
plot1 = ESSA_polygon.plot(x="lon_norm", y="lat_norm",color = 'black', linewidth=2,kind="line",ax=ax)
axes = plt.gca()
axes.legend().set_visible(False)
axes.grid()
plt.savefig('trajectories')

#================================= CALCULATION OF MINIMUM TIME TO GO FOR EACH CELL ===========================================
# using ceil() function to get rounded up calues of normalized coordinates (the X and Y grid cells)
Grid_frame['X'] = [math.ceil(x) for x in Grid_frame['lon_norm']]
Grid_frame['Y'] = [math.ceil(x) for x in Grid_frame['lat_norm']]

# extracting only columns which I am going to use in the next steps to ensure lower CPU usage during computation
Grid_frame2 = Grid_frame[['flightID', 'timestamp','endDate','X','Y']].copy()  

# getting time in final and entering time values for each flight
Grid_frame2['time_in_final'] = Grid_frame2.groupby(['flightID','endDate'])['timestamp'].transform('max')
Grid_frame2['entering_time'] = Grid_frame2.groupby(['flightID','endDate'])['timestamp'].transform('min')
number_of_flights = Grid_frame2['flightID'].nunique()

# time to final for each flight and each of its recording (position)
Grid_frame2['time_to_final'] = Grid_frame2['time_in_final'] - Grid_frame2['timestamp']
print('TIME TO/IN FINAL DONE')

#computing the minimum time ot final for each grid cell (the minimum value of time to final from all recordings inside)
grouped = Grid_frame2.groupby(['X', 'Y'],as_index=False)
min_time = grouped.agg({'time_to_final': 'min'})
min_time = min_time.rename(columns={"time_to_final": "min_time"})
min_time_result = min_time

#calculation for the horizontal spread
occupancy_count = len(min_time_result)
print('MIN TIME DONE')


# finding overlaps for each flight (which aircraft were present during flight of a given aircraft)  
# for spacing deviation calculation  
flight = Grid_frame2.groupby(['flightID','endDate']).head(1)
flight.index=range(0,len(flight))

# ============================ MINIMUM TIME VISUALISATION=================================================
# making dataset with all combinations of x,y to assure good plots
X = createList(1,grid_x)
Y = createList(1,grid_y)
min_time_list = pd.DataFrame(list(product(X, Y)), columns=['X', 'Y'])

min_time = pd.merge(min_time, min_time_list, on=['X', 'Y'],how='outer')
# filling nan values with very high value (for white background)
#ACTION: if the background is not white, change 450 to higher (or lower the max value on the min time plot)
fillnans = min_time.min_time.max() + 450
min_time = min_time.fillna(fillnans)

#horizontal spread calculation
total_area = len(min_time)
occupancy_percent = round(occupancy_count/(total_TMA/100),2)

# rounding minimum time values to nearest 50
min_time_rounded = pd.Series([])
min_time_rounded = min_time.min_time*2

for i in range(len(min_time_rounded)):
    min_time_rounded[i] = (min_time_rounded[i].round(-2))/2
    
min_time.insert(3,"min_time_rounded",min_time_rounded)

# decreasing values x,y by 0.5 for the heatmap to have all cells filled and not shifted the filling (build in function fills another way)
X_half = pd.Series([])
Y_half = pd.Series([])
X_half = min_time.X - 0.5
Y_half = min_time.Y - 0.5


min_time.insert(4,"x_half",X_half)
min_time.insert(5,"y_half",Y_half)


# making pivot tables for plotting (Y values are on the y axis, X values are at x-axis and min_time values are as Z (assigned values for color))
min_times = min_time.pivot(index="y_half",columns= "x_half",values= "min_time_rounded")

# using another axis labels than the plot gives
x_labels = range(0,grid_x+1,5)
y_labels = range(0,grid_y+1,5)
new_ticks_X = np.linspace(0,grid_x,5)
new_ticks_Y = np.linspace(0,grid_y,5)

min_min_time = min_time_result.min_time.min()
max_min_time = min_time_result.min_time.max()
avg_min_time = round(min_time_result.min_time.mean())
s2_min_time = round(min_time_result.min_time.std())


# making my own colormaps (choose your own)
import matplotlib.colors
cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["midnightblue","navy","teal","darkcyan","mediumseagreen","limegreen","yellowgreen","yellow","white","white"])
cmap2 = matplotlib.colors.LinearSegmentedColormap.from_list("", ["black","maroon","darkred","firebrick","red","r","darkorange","orange","gold","yellow","white","white"])
cmap3 = matplotlib.colors.LinearSegmentedColormap.from_list("", ["black","maroon","darkred","firebrick","red","r","darkorange","orange","gold","yellow","white","white","lightcyan","paleturquoise","powderblue","lightblue","lightskyblue","skyblue","skyblue","darkturquoise","c","c","darkcyan","darkcyan","teal","darkslategrey","white","white"])
cmap4 = matplotlib.colors.LinearSegmentedColormap.from_list("", ['white','yellow','gold','orange','darkorange','r','red','firebrick','darkred','maroon','black',"black"])
cmap5 = matplotlib.colors.LinearSegmentedColormap.from_list("", ['crimson','orangered','orange','lemonchiffon','lightyellow','greenyellow','palegreen','mediumturquoise','cornflowerblue','royalblue','rebeccapurple','white'])

#heatmap plot of minimum time to final
fig, ax = plt.subplots(figsize=(10,9))
sns.heatmap(min_times,cmap=cmap5,cbar_kws={'label': 'Minimum time [seconds]'},yticklabels=5,xticklabels=5,vmin=0, vmax=1250, ax=ax)
ax.invert_yaxis()
ax.set_xlim([0,grid_x])                                                               #setting limits for axes
ax.set_ylim([0,grid_y])
plot1 = ESSA_polygon.plot(x="lon_norm", y="lat_norm",color = 'black', linewidth=2,kind="line",ax=ax)
axes = plt.gca()
ax.grid()
ax.legend().set_visible(False)
ax.set_xticklabels([*range(0, grid_x-2, 5)]) 
ax.set_yticklabels([*range(0, grid_y-2, 5)]) 
plt.savefig('heatmap')

pd.DataFrame(min_time).to_csv('min_time_ESSA.csv', sep=',', encoding='utf-8', float_format='%.4f', index = False, header = True)
pd.DataFrame(Grid_frame).to_csv('Grid_frame_ESSA.csv', sep=',', encoding='utf-8', float_format='%.4f', index = False, header = True)
pd.DataFrame(Grid_frame2).to_csv('Grid_frame2_ESSA.csv', sep=',', encoding='utf-8', float_format='%.4f', index = False, header = True)
pd.DataFrame(min_times).to_csv('min_times_ESSA.csv', sep=',', encoding='utf-8', float_format='%.4f', index = False, header = True)
pd.DataFrame(min_time_result).to_csv('min_time_result_ESSA.csv', sep=',', encoding='utf-8', float_format='%.4f', index = False, header = True)
pd.DataFrame(flight).to_csv('flight_ESSA.csv', sep=',', encoding='utf-8', float_format='%.4f', index = False, header = True)

# check output to see the horizontal spread values (occupancy percent)
print ('ALL DONE')
print ('OCCUPANCY TOTAL')
print(total_TMA)
print('OCCUPANCY PERCENT')
print(occupancy_percent)