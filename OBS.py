# THis module contaiins codes for retrieving and visualizing various observation types. 
# currently this is pretty kludge-y and contains only quick subroutines that I wrote 
# to do a few things I needed to do. 

# load the required packages  
import numpy as np
import pandas as pd  
import datetime
import experiment_settings as es
import DART as dart
#import os.path
#from netCDF4 import Dataset

def HRRS_as_DF(OBS,hostname='taurus'):

	"""
	Loop over a set of dates and a specified latitude- and longitude range, and return 
	the available high-resolution radiosonde data as a pandas data frame  
	
	Input OBS has to be a dictionary with the following entries:  
		daterange: a list of datetime objects that give the desired date range  
		latrange: a list giving the bounding latitudes of the desired range 
		lonrange: a list giving the bounding longitudes of the desired range 
	Note that OBS can be a DART experiment dictionary (see DART.py), but the DART/model 
		specific entries are ignored. 
	"""

	# first read in station information as a dataframe 
	stationdata = HRRS_station_data(hostname)
	
	# initialize an empy list which will hold the data frames for each station and time 
	DFlist=[]

	# because the HRRS data are sorted by years, loop over the years in the daterange
	DR=OBS['daterange']
	y0 = DR[0].year
	yf = DR[len(DR)-1].year
	years = range(y0,yf+1,1)
	for YYYY in years:  

		# load a list of the available stations for that year  
		Slist  = HRRS_stations_available_per_year(YYYY)

		# trim list down to the ones that fit into the latitude range 
		stations_lat = [s for s in Slist 
				if stationdata.loc[int(s)]['Lat'] >= OBS['latrange'][0] 
				and stationdata.loc[int(s)]['Lat'] <= OBS['latrange'][1] ]

		# trim list down to the ones that fit into the longitude range 
		stations_latlon = [s for s in stations_lat
				if stationdata.loc[int(s)]['Lon'] >= OBS['lonrange'][0] 
				and stationdata.loc[int(s)]['Lon'] <= OBS['lonrange'][1] ]

		# also compute the subset of the requested daterange that fits into this year. 
		year_daterange =  dart.daterange(date_start=datetime.datetime(YYYY,1,1,0,0,0), periods=365*4, DT='6H')
		DR2 = set(year_daterange).intersection(DR)
		
		# also find the dir where the station data live 
		datadir = es.obs_data_paths('HRRS',hostname)

		# now loop over available stations, and for each one, retrieve the data 
		# that fit into the requested daterange 
		for s in stations_latlon:	

			# loop over dates, and retrieve data if available 
			for dd in DR2:
				datestr = dd.strftime("%Y%m%d%H")
				ff = datadir+'/'+str(YYYY)+'/'+str(s)+'/'+str(s)+'-'+datestr+'.dat'
				if os.path.exists(ff):
					# read in the station data 
					D = read_HRRS_data(ff)
		
					# also add a column holding the date 
					D['Date'] = pd.Series(dd, index=D.index)
				
					# get rid of some unneeded columns 
					weird_number=list(D.columns.values)[1]
					useless_cols=['Time','Dewpt','RH','Ucmp','Vcmp','spd','dir', 'Wcmp',  'Ele', 'Azi', 'Qp', 'Qt', 'Qrh', 'Qu', 'Qv', 'QdZ',weird_number]
					D.drop(useless_cols,inplace=True,axis=1)


					# append to list of data frames 
					DFlist.append(D)


	# merge the list of data frames into a single DF using list comprehension 
	DFout = pd.concat(DFlist, axis=0)
	#DF = pd.merge(DF,DF2,how='outer')

	return(DFout)

def read_HRRS_data(ff):

	"""
	Read in a .dat file from SPARC high-res radiosonde data 
	Input ff is a string pointing to the full path of the desired file. 
	"""

	D= pd.read_csv(ff,skiprows=13,error_bad_lines=False,delim_whitespace=True,na_values=999.0)
	colnames=list(D.columns.values)
	obscode=list(D.columns.values)[0]
	D.rename(columns={obscode:'Obs.Code'}, inplace=True)
	D['Station.Number'] = pd.Series(obscode[0:5], index=D.index)

	# kick out the first two rows - they hold units and symbols 
	D.drop(D.index[[0,1]], inplace=True)

	# also make sure that lat, lon, pressure, altitude, and temp are numerics 
	vars_to_float = ['Press','Temp','Lat','Lon','Alt']
	D[vars_to_float] = D[vars_to_float].astype(float)

	# find bad flags and turn them into nan
	D.replace(999.0,np.nan)

	return(D)

def HRRS_stations_available_per_year(YYYY):

	"""
	Given a specific calendar year (in integer form), return a list of the available 
	high-res radiosonde stations for that year 

	TODO: so far only have 2010 coded in ...need to add others 
	"""

	stations_avail_dict={2010:['03160','04102','12850','14607','14918',
					'22536','25624','26510','26616','40308','40504',
					'40710','61705','03190','11641','13985','14684',
					'21504','25501','25713','26615','27502','40309',
					'40505','41406']
           			}

	return(stations_avail_dict[YYYY])

def HRRS_station_data(hostname):

	"""
	Read in information about the high-res radiosondes and return it as a pandas dataframe.
	"""
	
	datadir = es.obs_data_paths('HRRS',hostname)

	ff=datadir+'ListOfStations.dat'
	colnames=[ 'WBAN','Station Name','State','Country','WMO Code','Lat','Lon','Height','Transition date']
	stations = pd.read_csv(ff,delimiter=",",error_bad_lines=False,skiprows=1,names=colnames,index_col='WBAN')


	# a few columns have to be coerced to numeric 
	stations[['Lat','Lon']] = stations[['Lat','Lon']].apply(pd.to_numeric, errors='coerce')

	return(stations)
