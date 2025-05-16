import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def takeClosest(num,collection):
   return min(collection,key=lambda x:abs(x-num))
#data import
flight = pd.read_csv('flight_ESSA.csv', 
header=0,
sep=','
) 


flight = flight.sort_values(by=['time_in_final'])
flight.insert(7,"flight_nr",range(1,len(flight)+1))
flight.index=range(0,len(flight))
## ordering the flights by time in final and giving them id numbers


# making a/c pairs respectively by time in final (pairs= a1:a2, a2:a3 ...)
column_names = ["leader","leader_nr", "trailer", "trailer_nr"]
pairs = pd.DataFrame(columns = column_names)
for i in range(len(flight)):
    if i == (len(flight) - 1): #last flight does not have any to be paired with
        pass
    else:
        pair=pd.DataFrame({"leader":[flight.flightID[i]],"leader_nr":[flight.flight_nr[i]],"trailer":[flight.flightID[i+1]],"trailer_nr":[flight.flight_nr[i+1]]})
        pairs = pd.concat([pairs,pair],ignore_index=True)
pairs['pair_nr'] = range(1,len(pairs)+1,1)

# ataching also interval start and end for the spacing deviation calculation 
# starts at the time trailer enters the TMA and ends when trailer arrives
interval_start = pd.Series([])
for i in range(len(pairs)):
    interval_start[i] = int(flight.loc[(flight.flight_nr == pairs.trailer_nr[i])]['entering_time'])
interval_start.index = range(0,len(interval_start))
interval_end = pd.Series([])
for i in range(len(pairs)):
    interval_end[i] = int(flight.loc[(flight.flight_nr == pairs.trailer_nr[i])]['time_in_final'])
pairs['interval_start'] = interval_start
pairs['interval_end'] = interval_end 
print('PAIRS DONE')

# calculation of spacing deviation
# timestamps for this calculation will be existing timestamps from trailer and for a leader will be used "takeClosest" function
column_names = ["pair_ID","time_to_final", "leader_X", "leader_Y","trailer_X","trailer_Y"]
spacing_dev2 = pd.DataFrame(columns = column_names)

#import of other needed frames
Grid_frame = pd.read_csv('Grid_frame_ESSA.csv', 
header=0,
sep=','
) 
Grid_frame2 = pd.read_csv('Grid_frame2_ESSA.csv', 
header=0,
sep=','
) 
min_time = pd.read_csv('min_time_ESSA.csv', 
header=0,
sep=','
) 

n = Grid_frame.groupby('flightID').size().min()
err = 5

#min time to final bins to calculate (until 15 minutes to final = 900s)
timestamps_2 = list(range(0, 910,10)) 
timestamps_2 = pd.Series(timestamps_2, name='timestamp').reset_index(drop=True)
timestamps_2 = timestamps_2.sort_values(ascending = False).reset_index(drop=True)

print('TIMESTAMPS DONE')

for i in range(len(pairs)):
    for j in timestamps_2:
        leader_time = takeClosest(j,Grid_frame2.loc[(Grid_frame2['flightID'] == str(pairs.leader[i]))]['time_to_final'])
        trailer_time = takeClosest(j,Grid_frame2.loc[(Grid_frame2['flightID'] == str(pairs.trailer[i]))]['time_to_final'])
        leader_x = Grid_frame2.loc[((Grid_frame2['time_to_final']==int(leader_time)) & (Grid_frame2['flightID']==str(pairs.leader[i])))]['X']
        leader_y = Grid_frame2.loc[((Grid_frame2['time_to_final']==int(leader_time)) & (Grid_frame2['flightID']==str(pairs.leader[i])))]['Y']
        trailer_x = Grid_frame2.loc[((Grid_frame2['time_to_final']==int(trailer_time)) & (Grid_frame2['flightID']==str(pairs.trailer[i])))]['X']
        trailer_y = Grid_frame2.loc[((Grid_frame2['time_to_final']==int(trailer_time)) & (Grid_frame2['flightID']==str(pairs.trailer[i])))]['Y']
        df1 = pd.DataFrame({"pair_ID":[pairs.pair_nr[i]],"time_to_final":[j],"leader_X":[int(leader_x.values[0])],"leader_Y":[int(leader_y.values[0])],"trailer_X":[int(trailer_x.values[0])],"trailer_Y":[int(trailer_y.values[0])]})
        spacing_dev2 = pd.concat([spacing_dev2,df1],ignore_index=True)

print('X/Y DONE')

# calculation of spacing deviation for each pair   
spacing_dev2.insert(6,"sp_d_sec","")        
for i in range(len(spacing_dev2)):
    min_time_trailer = int(min_time.loc[((min_time['X'] == spacing_dev2['trailer_X'][i]) & (min_time['Y'] == spacing_dev2['trailer_Y'][i]))]['min_time'])  
    min_time_leader = int(min_time.loc[((min_time['X'] == spacing_dev2['leader_X'][i]) & (min_time['Y'] == spacing_dev2['leader_Y'][i]))]['min_time'])
    spacing_dev2.sp_d_sec[i] = int(min_time_trailer - min_time_leader) 

print('CALCULATION DONE')

# numbering intervals for easier orientation in the dataframe
spacing_dev2.insert(7,"interval_nr","")
spacing_dev2.interval_nr = spacing_dev2.groupby(['pair_ID'])['pair_ID'].cumcount()

#final deviations to zero
last_dev = pd.Series([])
zyx = spacing_dev2.groupby('pair_ID').tail(1)[['pair_ID', 'sp_d_sec']]
zyx.index=range(0,len(zyx))

#assignment of final time to each row
for i in range(len(spacing_dev2)):
    for j in range(len(zyx)):
        if spacing_dev2.pair_ID[i] == zyx.pair_ID[j]:
            last_dev[i] = zyx.sp_d_sec[j]
spacing_dev2['last_dev'] = last_dev

#recalculating the spacing deviation values according to the last deviation
recalculated_dev = pd.Series([])
for i in range(len(spacing_dev2)):
    recalculated_dev[i] = spacing_dev2.sp_d_sec[i] - spacing_dev2.last_dev[i]
spacing_dev2['recalculated_dev'] = recalculated_dev

# calculation of 90% confidence intervals, medians and means for intervals of spacing deviation (100 second interval)
# making range for intervals
time_to_final_groups = range(0,1100,100)
intervals = pd.Series([])

# making a dataframe with intervals
for i in range(len(time_to_final_groups)-1):
   intervals[i] = pd.Interval(time_to_final_groups[i],time_to_final_groups[i+1],closed='both')
intervals[10] = pd.Interval(0,0,closed='both')
intervals = intervals.sort_values()
intervals = intervals.reset_index()
intervals = intervals.drop(list(intervals)[0], axis=1)
spacing_dev2['quantile05'] = spacing_dev2.groupby(['time_to_final'])['recalculated_dev'].transform(lambda x: x.quantile(.05))
spacing_dev2['quantile95'] = spacing_dev2.groupby(['time_to_final'])['recalculated_dev'].transform(lambda x: x.quantile(.95))

#statistics
max_dev = abs(spacing_dev2.loc[(spacing_dev2.time_to_final <= 900)]['recalculated_dev'].max())
min_dev = spacing_dev2.loc[(spacing_dev2.time_to_final <= 900)]['recalculated_dev'].min()
avg_dev = round(spacing_dev2.loc[(spacing_dev2.time_to_final <= 900)]['recalculated_dev'].mean(),2)
s2_dev = round(spacing_dev2.loc[(spacing_dev2.time_to_final <= 900)]['recalculated_dev'].std(),2)

# calculation of quantile width
spacing_dev2['quantile_width'] = spacing_dev2.quantile95 - spacing_dev2.quantile05
quantile_width = spacing_dev2.loc[(spacing_dev2.time_to_final <= 900)]['quantile_width'].max()

########### SPACINGT DEVIATION VISUALIZATION ###################
# scatter plot (not smoothed)
new_ticks_X = np.linspace(0,900,10)
new_ticks_Y = np.linspace(-600,600,13)
spacing_dev2 = spacing_dev2.sort_values(by=['time_to_final'])
fig, ax = plt.subplots(1, 1)
plot = spacing_dev2.plot.scatter(x='time_to_final',y='recalculated_dev',c='pair_ID',colorbar = False,colormap='gist_rainbow',figsize=(8,6),ax=ax)
spacing_dev2.plot(x='time_to_final',y='quantile95',color='black',linewidth=2.5,ax=ax)
spacing_dev2.plot(x='time_to_final',y='quantile05',color='black',linewidth=2.5,ax=ax)
plot.set_xlabel("Time to final trailer [seconds]",fontsize=19)
plot.set_ylabel("Spacing deviation [seconds]",fontsize=19)
plot.xaxis.tick_top()
ax.set_xticks(new_ticks_X)
ax.set_yticks(new_ticks_Y)
ax.set_xlim(0,900)
ax.set_ylim(-600,600)
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
plt.legend(fontsize=17)
ax.grid()
fig = plot.get_figure()
#fig.savefig('Spacing_dev_scatter_ESSA .jpg',bbox_inches="tight")
#ACTION: uncomment if you want to save the plots


# SMOOTHED LINE PLOT
# smoothing procedure
new_dev = spacing_dev2.copy()
new_dev.set_index('time_to_final', inplace=True)
xx = new_dev.groupby(['pair_ID'])['recalculated_dev'].rolling(15).mean().reset_index(drop = True)
xx2 = new_dev.groupby(['pair_ID'])['recalculated_dev'].rolling(10).mean().reset_index(drop = True)
xx3 = new_dev.groupby(['pair_ID'])['recalculated_dev'].rolling(5).mean().reset_index(drop = True)
new_dev = new_dev.sort_values(by=['pair_ID','interval_nr'],ascending=[True, False]).reset_index()
new_dev['moving_average'] = xx
new_dev['moving_average_2'] = xx2
new_dev['moving_average_3'] = xx3
moving_av_final = pd.Series([])
for i in range(len(new_dev)):
    if new_dev['time_to_final'][i] > 130:
        moving_av_final[i] = new_dev['moving_average'][i]
    elif new_dev['time_to_final'][i] < 130 and new_dev['time_to_final'][i] > 80:
        moving_av_final[i] = new_dev['moving_average_2'][i]
    elif new_dev['time_to_final'][i] < 80 and new_dev['time_to_final'][i] > 30:
        moving_av_final[i] = new_dev['moving_average_3'][i]
    elif new_dev['time_to_final'][i] == 30:
        moving_av_final[i] = new_dev['moving_average_3'][i+1]
    else:
        moving_av_final[i] = new_dev['recalculated_dev'][i] 
        
new_dev['moving_av_final'] = moving_av_final
new_dev.set_index('time_to_final', inplace=True)

plt.figure(figsize=(8,6))  
new_dev.groupby('pair_ID')['moving_av_final'].plot()
plt.plot()
axes = plt.gca()
axes.set_xticks(new_ticks_X)
axes.set_yticks(new_ticks_Y)
axes.set_xlabel("Time to final trailer [seconds]",fontsize=19)
axes.set_ylabel("Spacing deviation [seconds]",fontsize=19)
axes.set_ylim(-600,600)
axes.set_xlim([0,900])
axes.grid()
# plt.savefig('Spacing_dev_line_smoothed.jpg',bbox_inches="tight")


pd.DataFrame(pairs).to_csv('pairs_ESSA.csv')
pd.DataFrame(spacing_dev2).to_csv('spacing_dev2_ESSA.csv')
