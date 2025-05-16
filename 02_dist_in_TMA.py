import pandas as pd

#import needed dataframes
min_time_result = pd.read_csv('min_time_result_ESSA.csv', 
header=0,
sep=','
) 
Grid_frame = pd.read_csv('Grid_frame_ESSA.csv', 
header=0,
sep=','
) 
 
Grid_frame2 = pd.read_csv('Grid_frame2_ESSA.csv', 
header=0,
sep=','
) 

# joining the grid cell values to each row in Grid_Frame2
Grid_frame2 = pd.merge(Grid_frame2,min_time_result,how='left',on=['X','Y'])
Grid_frame2 = Grid_frame2.rename(columns={'min_time': 'min_time_to_final'})

#taking only first recording of each (enough for add time calculation)
frame_head = Grid_frame2.groupby(['flightID']).head(1)
# calculation of additional time
frame_head['additional_time'] = frame_head['time_to_final'] - frame_head['min_time_to_final']

#statistics for add time (output printed in the console)
max_add_time = frame_head['additional_time'].max()
min_add_time = frame_head['additional_time'].min()
avg_add_time = frame_head['additional_time'].mean()
median_add_time = frame_head['additional_time'].median()
s2_add_time = frame_head['additional_time'].std()

print('Additional time stats')
print(max_add_time,min_add_time,avg_add_time,median_add_time,s2_add_time)
pd.DataFrame(frame_head).to_csv('additional_time_ESSA.csv', sep=',', encoding='utf-8', float_format='%.4f', index = False, header = True)

#TIME IN TMA (CIRCLE)
Grouped_data=Grid_frame2.groupby(by='flightID')['timestamp'].agg(['first','last'])
Grouped_data['time_in_TMA']=Grouped_data['last']-Grouped_data['first'] 
pd.DataFrame(Grouped_data).to_csv('time_in_TMA_ESSA.csv')
print('TIME IN TMA stats')
time_in_TMA_min = Grouped_data['time_in_TMA'].min()
time_in_TMA_max = Grouped_data['time_in_TMA'].max()
time_in_TMA_avg = round(Grouped_data['time_in_TMA'].mean(),2)
time_in_TMA_median = round(Grouped_data['time_in_TMA'].median(),2)
time_in_TMA_std = round(Grouped_data['time_in_TMA'].std(),2)


# DISTANCE IN TMA (CIRCLE)
#calculation of the distance flown in TMA based on geo-coordinates
from geopy.distance import great_circle
Grid_frame['point'] =  Grid_frame[['lat','lon']].values.tolist()
   
distance = pd.Series([])
for i in range(len(Grid_frame2)-1):
    distance[i] = great_circle(Grid_frame['point'][i],Grid_frame['point'][i+1]).nm
Grid_frame['distance'] = distance
Grid_frame.loc[Grid_frame.groupby('flightID')['distance'].tail(1).index, 'distance'] = 0
Grid_frame["cum_sum_dist"]=Grid_frame.groupby(['flightID'])['distance'].transform(pd.Series.cumsum)
dist_in_TMA = Grid_frame.groupby(['flightID'])[['flightID','cum_sum_dist']].tail(1)
pd.DataFrame(dist_in_TMA).to_csv('distance_in_TMA_ESSA.csv')
print('DISTANCE IN TMA stats')

dist_in_TMA_min = dist_in_TMA['cum_sum_dist'].min()
dist_in_TMA_max = dist_in_TMA['cum_sum_dist'].max()
dist_in_TMA_avg = round(dist_in_TMA['cum_sum_dist'].mean(),2)
dist_in_TMA_median = round(dist_in_TMA['cum_sum_dist'].median(),2)
dist_in_TMA_std = round(dist_in_TMA['cum_sum_dist'].std(),2)




