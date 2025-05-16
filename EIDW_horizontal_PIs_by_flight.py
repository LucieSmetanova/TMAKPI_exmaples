import pandas as pd
import os

import pyproj

from datetime import datetime
import calendar

import time
start_time = time.time()


#ACTION: change to your constants
year = '2019'
airport_icao = "EIDW"
from constants_EIDW import *
#months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '12', '12']
months = ['10']

DATA_DIR = os.path.join("data", airport_icao)
DATA_DIR = os.path.join(DATA_DIR, year)

geod = pyproj.Geod(ellps='WGS84')   # to determine runways via azimuth
#fwd_azimuth, back_azimuth, distance = geod.inv(lat1, long1, lat2, long2)
rwy10R_azimuth, rwy28L_azimuth, distance = geod.inv(rwy10R_lat[0], rwy10R_lon[0], rwy10R_lat[1], rwy10R_lon[1])
rwy16_azimuth, rwy34_azimuth, distance = geod.inv(rwy16_lat[0], rwy16_lon[0], rwy16_lat[1], rwy16_lon[1])

print(rwy10R_azimuth, rwy28L_azimuth, rwy16_azimuth, rwy34_azimuth)
# ~ -3.15 176.85 -54.07 125.93

def get_all_states(csv_input_file):

    df = pd.read_csv(csv_input_file, sep=' ',
                    names = ['flightId', 'sequence', 'timestamp', 'lat', 'lon', 'rawAltitude', 'altitude', 'velocity', 'endDate'],
                    dtype={'flightId':str, 'sequence':int, 'timestamp':int, 'lat':float, 'lon':float, 'rawAltitude':float, 'altitude':float, 'velocity':float, 'endDate':str})
    
    df.set_index(['flightId', 'sequence'], inplace=True)
    
    return df

# ACTION: change to your paths
def determine_entry_points_and_runways(month, week):
    
    DATA_INPUT_DIR = os.path.join(DATA_DIR, "osn_"+ airport_icao + "_states_TMA_" + year)
    input_filename = "osn_"+ airport_icao + "_states_TMA_" + year + '_' + month + "_week" + str(week) + ".csv"
    full_input_filename = os.path.join(DATA_INPUT_DIR, input_filename)
         
    DATA_OUTPUT_DIR = os.path.join(DATA_DIR, "PIs")
    if not os.path.exists(DATA_OUTPUT_DIR):
        os.makedirs(DATA_OUTPUT_DIR)
    output_filename = "entry_points_and_runways_" + year + '_' +  month + "_week" + str(week) + ".csv"
    full_output_filename = os.path.join(DATA_OUTPUT_DIR, output_filename)

    states_df = get_all_states(full_input_filename)
    
    number_of_flights = len(states_df.groupby(level='flightId'))
    print(number_of_flights)
        
    entry_points_and_runways_df = pd.DataFrame(columns=['flight_id', 'date', 'hour', 
                                   'entry_point', 'runway'
                                   ])

    
    flight_id_num = len(states_df.groupby(level='flightId'))

    count = 0
    for flight_id, flight_id_group in states_df.groupby(level='flightId'):
        
        count = count + 1
        print(year, month, week, flight_id_num, count, flight_id)

        date_str = states_df.loc[flight_id].head(1)['endDate'].values[0]
        
        end_timestamp = states_df.loc[flight_id]['timestamp'].values[-1]
        end_datetime = datetime.utcfromtimestamp(end_timestamp)
        end_hour_str = end_datetime.strftime('%H')
        
        # Determine Entry Point based on lat, lon
        entry_point = ""
        entry_point_lon = flight_id_group['lon'][0]
        entry_point_lat = flight_id_group['lat'][0]
    
# ACTION: change for your chosen airport (can be found in AIP)
        if entry_point_lon > -6 : # "NIMAT", "BOYNE", "BAGSO", "LIPGO", "ABLIN", "VATRY"
                              # lat: 53.9650, 53.7671, 53.6800, 53.0639, 52.7828, 52.5544
            if entry_point_lat > 53.86:
                entry_point = "NIMAT"
            elif entry_point_lat > 53.72:
                entry_point = "BOYNE"
            elif entry_point_lat > 53.37:
                entry_point = "BAGSO"
            elif entry_point_lat > 53.0:
                entry_point = "LIPGO"
            elif entry_point_lat > 52.77:
                entry_point = "ABLIN"
            else:
                entry_point = "VATRY"            
        else: # lon <= -6 => "BAMLI", "OLAPO", "OSGAR", "SUTEX", "BUNED"
                       # lat: 54.1412, 53.7803, 53.0494, 52.8244, 52.6228
            if entry_point_lat > 53.96:
                entry_point = "BAMLI"
            elif entry_point_lat > 53.41:
                entry_point = "OLAPO"
            elif entry_point_lat > 52.93:
                entry_point = "OSGAR"
            elif entry_point_lat > 52.72:
                entry_point = "SUTEX"
            else:
                entry_point = "BUNED"

        
#ACTION: change based on your airport     
        # Determine Runway based on lat, lon
        
        runway = ""
        trajectory_point_last = [flight_id_group['lat'][-1], flight_id_group['lon'][-1]]
        # 30 seconds before:
        trajectory_point_before_last = [flight_id_group['lat'][-30], flight_id_group['lon'][-30]]
        
        #fwd_azimuth, back_azimuth, distance = geod.inv(lat1, long1, lat2, long2)
        trajectory_azimuth, temp1, temp2 = geod.inv(trajectory_point_before_last[0],
                                                    trajectory_point_before_last[1],
                                                    trajectory_point_last[0],
                                                    trajectory_point_last[1])

        # ~ -3.15 176.85 -54.07 125.93
        if (trajectory_azimuth > -24) and (trajectory_azimuth <= 61):
            runway = '10R'
        elif (trajectory_azimuth > -136) and (trajectory_azimuth <= -24):
            runway = '16'
        elif (trajectory_azimuth > 61) and (trajectory_azimuth <= 152):
            runway = '34'
        else: # 28L
            runway = '28L'
        #print(runway)
        
        entry_points_and_runways_df = entry_points_and_runways_df.append({'flight_id': flight_id, 'date': date_str, 'hour': end_hour_str,
                                'entry_point': entry_point,
                                'runway': runway}, ignore_index=True)

    entry_points_and_runways_df.to_csv(full_output_filename, sep=' ', encoding='utf-8', float_format='%.3f', header=True, index=False)
#ACTION: change paths
def create_entry_points_and_runways_files(month, week):
    
    DATA_INPUT_DIR1 = os.path.join(DATA_DIR, "osn_"+ airport_icao + "_states_TMA_" + year)
    input_filename1 = "osn_"+ airport_icao + "_states_TMA_" + year + '_' + month + "_week" + str(week) + ".csv"
    full_input_filename1 = os.path.join(DATA_INPUT_DIR1, input_filename1)
    
    states_df = get_all_states(full_input_filename1)
    
    number_of_flights = len(states_df.groupby(level='flightId'))
    
    DATA_INPUT_DIR2 = os.path.join(DATA_DIR, "PIs")
    input_filename2 = "entry_points_and_runways_" + year + '_' +  month + "_week" + str(week) + ".csv"
    full_input_filename2 = os.path.join(DATA_INPUT_DIR2, input_filename2)
    
    entry_points_and_runways_df = pd.read_csv(full_input_filename2, sep=' ')
    entry_points_and_runways_df.set_index(['flight_id'], inplace=True)
                     
    NIMAT_rwy10_df = pd.DataFrame()
    NIMAT_rwy28_df = pd.DataFrame()
    NIMAT_rwy16_df = pd.DataFrame()
    NIMAT_rwy34_df = pd.DataFrame()
    BOYNE_rwy10_df = pd.DataFrame()
    BOYNE_rwy28_df = pd.DataFrame()
    BOYNE_rwy16_df = pd.DataFrame()
    BOYNE_rwy34_df = pd.DataFrame()
    BAGSO_rwy10_df = pd.DataFrame()
    BAGSO_rwy28_df = pd.DataFrame()
    BAGSO_rwy16_df = pd.DataFrame()
    BAGSO_rwy34_df = pd.DataFrame()
    LIPGO_rwy10_df = pd.DataFrame()
    LIPGO_rwy28_df = pd.DataFrame()
    LIPGO_rwy16_df = pd.DataFrame()
    LIPGO_rwy34_df = pd.DataFrame()
    ABLIN_rwy10_df = pd.DataFrame()
    ABLIN_rwy28_df = pd.DataFrame()
    ABLIN_rwy16_df = pd.DataFrame()
    ABLIN_rwy34_df = pd.DataFrame()
    VATRY_rwy10_df = pd.DataFrame()
    VATRY_rwy28_df = pd.DataFrame()
    VATRY_rwy16_df = pd.DataFrame()
    VATRY_rwy34_df = pd.DataFrame()
    BAMLI_rwy10_df = pd.DataFrame()
    BAMLI_rwy28_df = pd.DataFrame()
    BAMLI_rwy16_df = pd.DataFrame()
    BAMLI_rwy34_df = pd.DataFrame()
    OLAPO_rwy10_df = pd.DataFrame()
    OLAPO_rwy28_df = pd.DataFrame()
    OLAPO_rwy16_df = pd.DataFrame()
    OLAPO_rwy34_df = pd.DataFrame()
    OSGAR_rwy10_df = pd.DataFrame()
    OSGAR_rwy28_df = pd.DataFrame()
    OSGAR_rwy16_df = pd.DataFrame()
    OSGAR_rwy34_df = pd.DataFrame()
    SUTEX_rwy10_df = pd.DataFrame()
    SUTEX_rwy28_df = pd.DataFrame()
    SUTEX_rwy16_df = pd.DataFrame()
    SUTEX_rwy34_df = pd.DataFrame()
    BUNED_rwy10_df = pd.DataFrame()
    BUNED_rwy28_df = pd.DataFrame()
    BUNED_rwy16_df = pd.DataFrame()
    BUNED_rwy34_df = pd.DataFrame()
    
    count = 0
    for flight_id, flight_id_group in states_df.groupby(level='flightId'):
        count = count + 1
        print(year, month, week, number_of_flights, count, flight_id)

        runway = entry_points_and_runways_df.loc[flight_id][['runway']].values[0]
    
        entry_point = entry_points_and_runways_df.loc[flight_id][['entry_point']].values[0]
    
        # "NIMAT", "BOYNE", "BAGSO", "LIPGO", "ABLIN", "VATRY", "BAMLI", "OLAPO", "OSGAR", "SUTEX", "BUNED"
        if entry_point == "NIMAT":
            if runway == "10R":
                NIMAT_rwy10_df = NIMAT_rwy10_df.append(flight_id_group)
            elif runway == "28L":
                    NIMAT_rwy28_df = NIMAT_rwy28_df.append(flight_id_group)
            elif runway == "16":
                NIMAT_rwy16_df = NIMAT_rwy16_df.append(flight_id_group)
            else:
                NIMAT_rwy34_df = NIMAT_rwy34_df.append(flight_id_group)
        elif entry_point == "BOYNE":
            if runway == "10R":
                BOYNE_rwy10_df = BOYNE_rwy10_df.append(flight_id_group)
            elif runway == "28L":
                BOYNE_rwy28_df = BOYNE_rwy28_df.append(flight_id_group)
            elif runway == "16":
                BOYNE_rwy16_df = BOYNE_rwy16_df.append(flight_id_group)
            else:
                BOYNE_rwy34_df = BOYNE_rwy34_df.append(flight_id_group)
        elif entry_point == "BAGSO":
            if runway == "10R":
                BAGSO_rwy10_df = BAGSO_rwy10_df.append(flight_id_group)
            elif runway == "28L":
                BAGSO_rwy28_df = BAGSO_rwy28_df.append(flight_id_group)
            elif runway == "16":
                BAGSO_rwy16_df = BAGSO_rwy16_df.append(flight_id_group)
            else:
                BAGSO_rwy34_df = BAGSO_rwy34_df.append(flight_id_group)
        elif entry_point == "LIPGO":
            if runway == "10R":
                LIPGO_rwy10_df = LIPGO_rwy10_df.append(flight_id_group)
            elif runway == "28L":
                LIPGO_rwy28_df = LIPGO_rwy28_df.append(flight_id_group)
            elif runway == "16":
                LIPGO_rwy16_df = LIPGO_rwy16_df.append(flight_id_group)
            else:
                LIPGO_rwy34_df = LIPGO_rwy34_df.append(flight_id_group)
        elif entry_point == "ABLIN":
            if runway == "10R":
                ABLIN_rwy10_df = ABLIN_rwy10_df.append(flight_id_group)
            elif runway == "28L":
                ABLIN_rwy28_df = ABLIN_rwy28_df.append(flight_id_group)
            elif runway == "16":
                ABLIN_rwy16_df = ABLIN_rwy16_df.append(flight_id_group)
            else:
                ABLIN_rwy34_df = ABLIN_rwy34_df.append(flight_id_group)
        elif entry_point == "VATRY":
            if runway == "10R":
                VATRY_rwy10_df = VATRY_rwy10_df.append(flight_id_group)
            elif runway == "28L":
                VATRY_rwy28_df = VATRY_rwy28_df.append(flight_id_group)
            elif runway == "16":
                VATRY_rwy16_df = VATRY_rwy16_df.append(flight_id_group)
            else:
                VATRY_rwy34_df = VATRY_rwy34_df.append(flight_id_group)
        elif entry_point == "BAMLI":
            if runway == "10R":
                BAMLI_rwy10_df = BAMLI_rwy10_df.append(flight_id_group)
            elif runway == "28L":
                BAMLI_rwy28_df = BAMLI_rwy28_df.append(flight_id_group)
            elif runway == "16":
                BAMLI_rwy16_df = BAMLI_rwy16_df.append(flight_id_group)
            else:
                BAMLI_rwy34_df = BAMLI_rwy34_df.append(flight_id_group)
        elif entry_point == "OLAPO":
            if runway == "10R":
                OLAPO_rwy10_df = OLAPO_rwy10_df.append(flight_id_group)
            elif runway == "28L":
                OLAPO_rwy28_df = OLAPO_rwy28_df.append(flight_id_group)
            elif runway == "16":
                OLAPO_rwy16_df = OLAPO_rwy16_df.append(flight_id_group)
            else:
                OLAPO_rwy34_df = OLAPO_rwy34_df.append(flight_id_group)
        elif entry_point == "OSGAR":
            if runway == "10R":
                OSGAR_rwy10_df = OSGAR_rwy10_df.append(flight_id_group)
            elif runway == "28L":
                OSGAR_rwy28_df = OSGAR_rwy28_df.append(flight_id_group)
            elif runway == "16":
                OSGAR_rwy16_df = OSGAR_rwy16_df.append(flight_id_group)
            else:
                OSGAR_rwy34_df = OSGAR_rwy34_df.append(flight_id_group)
        elif entry_point == "SUTEX":
            if runway == "10R":
                SUTEX_rwy10_df = SUTEX_rwy10_df.append(flight_id_group)
            elif runway == "28L":
                SUTEX_rwy28_df = SUTEX_rwy28_df.append(flight_id_group)
            elif runway == "16":
                SUTEX_rwy16_df = SUTEX_rwy16_df.append(flight_id_group)
            else:
                SUTEX_rwy34_df = SUTEX_rwy34_df.append(flight_id_group)
        elif entry_point == "BUNED":
            if runway == "10R":
                BUNED_rwy10_df = BUNED_rwy10_df.append(flight_id_group)
            elif runway == "28L":
                BUNED_rwy28_df = BUNED_rwy28_df.append(flight_id_group)
            elif runway == "16":
                BUNED_rwy16_df = BUNED_rwy16_df.append(flight_id_group)
            else:
                BUNED_rwy34_df = BUNED_rwy34_df.append(flight_id_group)

    DATA_OUTPUT_DIR = os.path.join(DATA_DIR, "osn_"+ airport_icao + "_states_TMA_" + year)
    DATA_OUTPUT_DIR = os.path.join(DATA_OUTPUT_DIR, "osn_"+ airport_icao + "_states_TMA_" + year + "_" + month + "_week" + str(week) + "_by_entry_points_and_runways")
    if not os.path.exists(DATA_OUTPUT_DIR):
        os.makedirs(DATA_OUTPUT_DIR)
    output_filename = "osn_"+ airport_icao + "_states_TMA_" + year + '_' + month + "_week" + str(week)
    full_output_filename = os.path.join(DATA_OUTPUT_DIR, output_filename)

    NIMAT_rwy10_df.to_csv(full_output_filename + "_NIMAT_rwy10.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    NIMAT_rwy28_df.to_csv(full_output_filename + "_NIMAT_rwy28.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    NIMAT_rwy16_df.to_csv(full_output_filename + "_NIMAT_rwy16.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    NIMAT_rwy34_df.to_csv(full_output_filename + "_NIMAT_rwy34.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    BOYNE_rwy10_df.to_csv(full_output_filename + "_BOYNE_rwy10.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    BOYNE_rwy28_df.to_csv(full_output_filename + "_BOYNE_rwy28.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    BOYNE_rwy34_df.to_csv(full_output_filename + "_BOYNE_rwy34.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    BAGSO_rwy10_df.to_csv(full_output_filename + "_BAGSO_rwy10.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    BAGSO_rwy28_df.to_csv(full_output_filename + "_BAGSO_rwy28.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    BAGSO_rwy16_df.to_csv(full_output_filename + "_BAGSO_rwy16.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    BAGSO_rwy34_df.to_csv(full_output_filename + "_BAGSO_rwy34.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    LIPGO_rwy10_df.to_csv(full_output_filename + "_LIPGO_rwy10.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    LIPGO_rwy28_df.to_csv(full_output_filename + "_LIPGO_rwy28.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    LIPGO_rwy16_df.to_csv(full_output_filename + "_LIPGO_rwy16.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    LIPGO_rwy34_df.to_csv(full_output_filename + "_LIPGO_rwy34.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    ABLIN_rwy10_df.to_csv(full_output_filename + "_ABLIN_rwy10.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    ABLIN_rwy28_df.to_csv(full_output_filename + "_ABLIN_rwy28.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    ABLIN_rwy16_df.to_csv(full_output_filename + "_ABLIN_rwy16.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    ABLIN_rwy34_df.to_csv(full_output_filename + "_ABLIN_rwy34.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    VATRY_rwy10_df.to_csv(full_output_filename + "_VATRY_rwy10.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    VATRY_rwy28_df.to_csv(full_output_filename + "_VATRY_rwy28.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    VATRY_rwy16_df.to_csv(full_output_filename + "_VATRY_rwy16.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    VATRY_rwy34_df.to_csv(full_output_filename + "_VATRY_rwy34.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    BAMLI_rwy10_df.to_csv(full_output_filename + "_BAMLI_rwy10.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    BAMLI_rwy28_df.to_csv(full_output_filename + "_BAMLI_rwy28.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    OLAPO_rwy10_df.to_csv(full_output_filename + "_OLAPO_rwy10.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    OLAPO_rwy28_df.to_csv(full_output_filename + "_OLAPO_rwy28.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    OLAPO_rwy16_df.to_csv(full_output_filename + "_OLAPO_rwy16.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    OLAPO_rwy34_df.to_csv(full_output_filename + "_OLAPO_rwy34.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    OSGAR_rwy10_df.to_csv(full_output_filename + "_OSGAR_rwy10.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    OSGAR_rwy28_df.to_csv(full_output_filename + "_OSGAR_rwy28.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    OSGAR_rwy16_df.to_csv(full_output_filename + "_OSGAR_rwy16.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    OSGAR_rwy34_df.to_csv(full_output_filename + "_OSGAR_rwy34.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    SUTEX_rwy10_df.to_csv(full_output_filename + "_SUTEX_rwy10.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    SUTEX_rwy28_df.to_csv(full_output_filename + "_SUTEX_rwy28.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    SUTEX_rwy16_df.to_csv(full_output_filename + "_SUTEX_rwy16.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    SUTEX_rwy34_df.to_csv(full_output_filename + "_SUTEX_rwy34.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    BUNED_rwy10_df.to_csv(full_output_filename + "_BUNED_rwy10.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    BUNED_rwy28_df.to_csv(full_output_filename + "_BUNED_rwy28.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    BUNED_rwy16_df.to_csv(full_output_filename + "_BUNED_rwy16.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    BUNED_rwy34_df.to_csv(full_output_filename + "_BUNED_rwy34.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)


def create_runways_files(month, week):
    
    DATA_INPUT_DIR1 = os.path.join(DATA_DIR, "osn_"+ airport_icao + "_states_TMA_" + year)
    input_filename1 = "osn_"+ airport_icao + "_states_TMA_" + year + '_' + month + "_week" + str(week) + ".csv"
    full_input_filename1 = os.path.join(DATA_INPUT_DIR1, input_filename1)
    
    states_df = get_all_states(full_input_filename1)
    
    number_of_flights = len(states_df.groupby(level='flightId'))
    
    DATA_INPUT_DIR2 = os.path.join(DATA_DIR, "PIs")
    input_filename2 = "entry_points_and_runways_" + year + '_' +  month + "_week" + str(week) + ".csv"
    full_input_filename2 = os.path.join(DATA_INPUT_DIR2, input_filename2)
    
    entry_points_and_runways_df = pd.read_csv(full_input_filename2, sep=' ')
    entry_points_and_runways_df.set_index(['flight_id'], inplace=True)

    rwy10_df = pd.DataFrame()
    rwy28_df = pd.DataFrame()
    rwy16_df = pd.DataFrame()
    rwy34_df = pd.DataFrame()

    count = 0
    for flight_id, flight_id_group in states_df.groupby(level='flightId'):
        
        count = count + 1
        print(year, month, week, number_of_flights, count, flight_id)

        runway = entry_points_and_runways_df.loc[flight_id][['runway']].values[0]

        if runway == "10R":
            rwy10_df = rwy10_df.append(flight_id_group)
        elif runway == "28L":
            rwy28_df = rwy28_df.append(flight_id_group)
        elif runway == "16":
            rwy16_df = rwy16_df.append(flight_id_group)
        else:
            rwy34_df = rwy34_df.append(flight_id_group)

    DATA_OUTPUT_DIR = os.path.join(DATA_DIR, "osn_"+ airport_icao + "_states_TMA_" + year)
    DATA_OUTPUT_DIR = os.path.join(DATA_OUTPUT_DIR, "osn_"+ airport_icao + "_states_TMA_" + year + "_" + month + "_week" + str(week) + "_by_runways")
    if not os.path.exists(DATA_OUTPUT_DIR):
        os.makedirs(DATA_OUTPUT_DIR)
    output_filename = "osn_"+ airport_icao + "_states_TMA_" + year + '_' + month + "_week" + str(week)
    full_output_filename = os.path.join(DATA_OUTPUT_DIR, output_filename)

    rwy10_df.to_csv(full_output_filename + "_rwy10.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    rwy28_df.to_csv(full_output_filename + "_rwy28.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    rwy16_df.to_csv(full_output_filename + "_rwy16.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    rwy34_df.to_csv(full_output_filename + "_rwy34.csv", sep=' ', encoding='utf-8', float_format='%.3f', index = True, header = False)
    
    
def main():
    
    for month in months:
        number_of_weeks = (5, 4)[month == '02' and not calendar.isleap(int(year))]
        #number_of_weeks = 1
        
        for week in range(0, number_of_weeks):
        #for week in range(1, number_of_weeks):
        
            determine_entry_points_and_runways(month, week+1)
            
            create_entry_points_and_runways_files(month, week+1)
            
            create_runways_files(month, week+1)
    
    
main()    

print("--- %s minutes ---" % ((time.time() - start_time)/60))