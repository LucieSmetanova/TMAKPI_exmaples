import pandas as pd
import os
from datetime import datetime
import time

# ACTION: change to correct airport and year
start_time = time.time()
year = '2019'
airport_icao = "ESSA"

#function to import data
def get_all_states(csv_input_file):
    df = pd.read_csv(csv_input_file, sep=',', header=0)
    df = df[['flightID', 'sequence', 'timestamp', 'baroAltitude', 'velocity', 'endDate']]
    df.rename(columns={"baroAltitude": "altitude"},inplace=True)
    df.set_index(['flightID', 'sequence'], inplace=True)
    return df

#function to calculate vertical flight efficiency
#ACTION: change paths/file names
def calculate_vfe(month, week):
    input_filename = "ex_subset_ESSA_2019.csv"
    try:
        os.mkdir('PIs')
    except FileExistsError:
        print("Directory PIs already exists.")
    output_filename = "ESSA_ver_PIs_by_flight.csv"
    full_output_filename = os.path.join('PIs', output_filename)
    
    states_df = get_all_states(input_filename)
    # minimum seconds on level to be considered as level flight
    min_level_time = 30
    #Y/X = 300 feet per minute
    rolling_window_Y = (300*(min_level_time/60))/ 3.281 # feet to meters

    #descent part ends at 1800 feet
    descent_end_altitude = 1800 / 3.281
    vfe_df = pd.DataFrame(columns=['flight_id', 'date', 'begin_hour', 'end_hour', 
                                   'number_of_levels',
                                   'time_on_levels', 'time_on_levels_percent',
                                   'TMA_time',
                                   'distance_on_levels', 'distance_on_levels_percent',
                                   'cdo_altitude'])
    number_of_levels_lst = []
    distance_on_levels_lst = []
    distance_on_levels_percent_lst = []
    time_on_levels_lst = []
    time_on_levels_percent_lst = []
    
    flight_id_num = len(states_df.groupby(level='flightID'))
    count = 0
    for flight_id, flight_id_group in states_df.groupby(level='flightID'):
        
        count = count + 1
        print(year, month, week, flight_id_num, count, flight_id)
        
        number_of_levels = 0
        time_sum = 0
        time_on_levels = 0
        time_on_level = 0
        distance_sum = 0
        distance_on_levels = 0
        distance_on_level = 0
        level = 'false'
        altitude1 = 0 # altitude at the beginning of rolling window
        altitude2 = 0 # altitude at the end of rolling window
        cdo_altitude = 0
        seq_level_end = 0
        seq_min_level_time = 0

        df_length = len(flight_id_group)
        cdo_altitude = flight_id_group.loc[flight_id, :]['altitude'].values[0]
        for seq, row in flight_id_group.groupby(level='sequence'):

            if (seq + min_level_time) >= df_length:
                break
            
            time_sum = time_sum + 1
            distance_sum = distance_sum + row['velocity'].values[0]

            #print("row", row) 
            #print("row[altitude]", row['altitude'])

            altitude1 = row['altitude'].values[0]
            
            altitude2 = flight_id_group.loc[flight_id, seq+min_level_time-1]['altitude']
            
            #print('altitude1', altitude1)
            #print('altitude2', altitude2)

            # do not calculate as levels climbing in go around
            if altitude2 > altitude1:
                continue
     
            if altitude2 < descent_end_altitude:
                break


            if level == 'true':

                if seq < seq_level_end:
                    if altitude1 - altitude2 < rolling_window_Y: #extend the level
                        seq_level_end = seq_level_end + 1
                    if seq < seq_min_level_time: # do not count first 30 seconds
                        continue
                    else:
                        time_on_level = time_on_level + 1
                        distance_on_level = distance_on_level + row['velocity'].values[0]
                else: # level ends
                    if seq_level_end >= seq_min_level_time:
                        number_of_levels = number_of_levels + 1
                    level = 'false'
                    time_on_levels = time_on_levels + time_on_level
                    distance_on_levels = distance_on_levels + distance_on_level
                    time_on_level = 0
                    distance_on_level = 0
                    
                    cdo_altitude = altitude1
            else: #not level
                if altitude1 - altitude2 < rolling_window_Y: # level begins
                    level = 'true'
                    seq_min_level_time = seq + min_level_time
                    seq_level_end = seq + min_level_time - 1
                    time_on_level = time_on_level + 1
                    distance_on_level = distance_on_level + row['velocity'].values[0]

        if (time_sum == 0) or (distance_sum == 0):
        #if (time_sum == 0):
            print(flight_id, time_sum, distance_sum)
            #print(type(time_sum))
            #print(type(distance_sum))            
            continue

        number_of_levels_str = str(number_of_levels)

        number_of_levels_lst.append(number_of_levels)

        # convert distance to NM and time to munutes
        distance_on_levels = distance_on_levels * 0.000539957   #meters to NM
        distance_sum = distance_sum * 0.000539957   #meters to NM
        time_on_levels = time_on_levels / 60    #seconds to minutes

        distance_on_levels_lst.append(distance_on_levels)
        distance_on_levels_str = "{0:.3f}".format(distance_on_levels)

        distance_on_levels_percent = distance_on_levels / distance_sum *100
        distance_on_levels_percent_lst.append(distance_on_levels_percent)
        distance_on_levels_percent_str = "{0:.1f}".format(distance_on_levels_percent)


        time_on_levels_lst.append(time_on_levels)
        time_on_levels_str = "{0:.3f}".format(time_on_levels)

        time_on_levels_percent = time_on_levels / time_sum *100
        time_on_levels_percent_lst.append(time_on_levels_percent)
        time_on_levels_percent_str = "{0:.1f}".format(time_on_levels_percent)

        date_str = states_df.loc[flight_id].head(1)['endDate'].values[0]
        
        #end_timestamp = states_opensky_df.loc[flight_id]['timestamp'].values[-1].item(0)
        end_timestamp = states_df.loc[flight_id]['timestamp'].values[-1]
        end_datetime = datetime.utcfromtimestamp(end_timestamp)
        end_hour_str = end_datetime.strftime('%H')
        
        TMA_time = len(flight_id_group)/60  #seconds to minutes
        
        #print(date_str)
        #print(number_of_levels_str)
        #print(distance_on_levels_str)
        #print(distance_on_levels_percent_str)
        #print(time_on_levels_str)
        #print(time_on_levels_percent_str)

        date_str = states_df.loc[flight_id].head(1)['endDate'].values[0]
        
        begin_timestamp = states_df.loc[flight_id]['timestamp'].values[0]
        begin_datetime = datetime.utcfromtimestamp(begin_timestamp)
        begin_hour_str = begin_datetime.strftime('%H')

        end_timestamp = states_df.loc[flight_id]['timestamp'].values[-1]
        end_datetime = datetime.utcfromtimestamp(end_timestamp)
        end_hour_str = end_datetime.strftime('%H')
        
        TMA_time = len(flight_id_group)/60  #seconds to minutes
        
        # vfe_df = vfe_df.append({'flight_id': flight_id, 'date': date_str, 
        #                         'begin_hour': begin_hour_str,
        #                         'end_hour': end_hour_str,
        # #                        'entry_point': entry_point,
        #                         'number_of_levels': number_of_levels_str,
        #                         'distance_on_levels': distance_on_levels_str,
        #                         'distance_on_levels_percent': distance_on_levels_percent_str,
        #                         'time_on_levels': time_on_levels_str,
        #                         'time_on_levels_percent': time_on_levels_percent_str,
        #                         'TMA_time': TMA_time,
        #                         'cdo_altitude': cdo_altitude}, ignore_index=True)
        vfe_df = pd.concat([vfe_df,pd.Series({'flight_id': flight_id, 'date': date_str, 
                                'begin_hour': begin_hour_str,
                                'end_hour': end_hour_str,
        #                        'entry_point': entry_point,
                                'number_of_levels': number_of_levels_str,
                                'distance_on_levels': distance_on_levels_str,
                                'distance_on_levels_percent': distance_on_levels_percent_str,
                                'time_on_levels': time_on_levels_str,
                                'time_on_levels_percent': time_on_levels_percent_str,
                                'TMA_time': TMA_time,
                                'cdo_altitude': cdo_altitude})],ignore_index=True)

    vfe_df.to_csv(full_output_filename, sep=' ', encoding='utf-8', float_format='%.3f', header=True, index=False)



def main():
    
    for week in range (1,5):
        calculate_vfe(10, week)
    
    
main()    

print("--- %s minutes ---" % ((time.time() - start_time)/60))