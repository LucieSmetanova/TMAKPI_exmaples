# TMAKPI_exmaples
 Example codes for chosen metrics

 In our studies, we performed two main types of analysis, the large-scale, and the fine-grained. 
 Please note that these codes provide output for the large-scale analysis, in order to get the fine-grained analysis, the codes would have to be adjusted to iterate over each hour of the chosen time period. 

All these codes are written using Python programming language. 

# Metrics
This folder contains exmaple subset and codes for chosen metrics from the TMAKPI project.
The metrics include: 
    - Minimum Time to Final
    - Horizontal Spread
    - Distnace in TMA
    - Time in TMA
    - Additional Time
    - Spacing Deviation
    - Time Flown Level
    - Distance on Levels

The metrics listed above are working with the small example data subset from Stockholm Arlanda aiport (ex_subset_ESSA_2019.csv). The corresponding codes should be run in the order indicated in the names of the codes: 
- 01_min_time_to_final
- 02_dist_in_TMA
- 03_spacing_deviation
- 04_ESSA_vertical_PIs_by_flight

The output of these codes (csv files and figures) is directed to the same directory, the code 04_ESSA_... creates new folder "PIs" for its output.

Please note, that currently we don't have working code to provide Additional Distance in TMA for this exmaple data subset as it requires positions of Entry Points in TMA. However, we provide example code used previously to calculate the Additional Distance in TMA for Dublin airport (EIDW). This code can be adjusted to fit your needs. 
- EIDW_horizontal_PIs_by_flight

# Noise metrics
To calculate noise, we use the external tool developed by Eurocontrol, the IMPACT tool. 
To use the IMPACT tool, you need to get access to OneSky by Eurocontrol first and then request rights to use the IMPACT tool. In our studies, we used the noise calculations and noise contours using the Lden option.
Quick guide and user manual for the IMPACT tool can be accessed via Eucontrol OneSky. 

# Code adjustments
To adjust the codes for your specified airport, we include comments in the codes starting with 'ACTION:'. You can search in the document for this word and see where are some adjustments needed.
Usually it is change in some airport specifics.

One of the required changes is the Minimum Time to Final grid dimensions. In our studies, we try to keep the grid cells of 1NM size in longitude and latitude. If the study is over 50NM (or any other radius), we simply use the diameter value as both x and y dimensions. If we work with trajectories inside the actual TMA polygon (this example) we calculate the length of the sides of the smallest rectangle covering the TMA polygon and use the length in NM as x and y dimensions (to get 1NM cells).

# The data
We provide small example data subset of Stockholm Arlanda data in 2019. You can adjust the codes to work with other data formats, however, we provide short description on how to access the OpenSky data we use in our studies. 

1) Register account at OpenSky database (https://opensky-network.org/data/trino)

The historical data can be accessed various ways, we will provide guide on the one we are using. 
We use Trino credentials and the traffic library. 

2) Download and install the traffic library (https://traffic-viz.github.io/installation.html)
3) Download the data using commands specified here (https://traffic-viz.github.io/data_sources/opensky_db.html)
To download the data, the absolute minimum you need to specify is the desired time frame and location
As a location, you can provide airport ICAO and specify if you want only arrivals or departures or both (the output are full trajectories satisfying the conditions).
Instead of airport ICAO, you can also speficy the location by polygon shape of the TMA or any other shape. 

# Cleaning of the data
The Opensky data tend to be noisy, so we are using some cleaning procedures in order to get good working dataset. 
The procedures include:
- Linear interpolation to fix incorrect latitude and longitude coordinates
- Substitution of large fluctuations in altitude with the closest value
- Gaussian filter to smooth the altitude values
- Removing trajectories with inconsistent position and altitude values
- Removing of incomplete trajectories within the area of interest (TMA or circle)
- Removing go-around trajectories or the ones which landed far from runway
- If known, we remove flights with IDs corresponding to non-commerical air traffic or helicopters

Furthermore, we cure the datasets based on the needs of the current study which could be busy hours, delayed hours, day/night time, specific traffic flow, etc.

