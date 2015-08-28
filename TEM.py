# Python module for dealing with TEM diagnostics 
# Lisa Neef, 26 Aug 2015

# load the required packages  
#import numpy as np
#import datetime
import os.path
from netCDF4 import Dataset

def load_Wang_TEM_file(E,datetime_in,ensemble_member,hostname='taurus',verbose=False):

	"""
	Load the file of TEM diagnostics computed for a certain experiment and a 
	given month, 
	 using code by Wuke Wang. 


	Inputs:  
	E		: experiment dictionary 
	datetime_in  	: datetime.datetime object for the file to load 
	ensemble_member	: number of the ensemble member to load 
	hostname	: default is taurus  
	verbose		: default is False  

	"""
	# if the variable given in E isn't a TEM diagnostic, change it to the default variable 
	# wstar (residual vertical velocity)
	tem_variables_list = ['VSTAR','WSTAR','FPHI','FZ','DELF']
	variable_name = E['variable'].upper()
	if variable_name not in tem_variables_list:
		print(variable_name+' is not a TEM diagnostic -- retrieving w* instead')
		variable_name = 'WSTAR'


	# find the file path corresponding to this experiment  
	import experiment_settings as es 
	ff = es.exp_paths_TEM(E,datetime_in)

	# load the file  
        if os.path.isfile(ff):
		VV = None
		if verbose:  
			print('Loading TEM diagnostics file file '+ff)
		f = Dataset(ff,'r')
		lat = f.variables['lat'][:]
		lev = f.variables['lev'][:]
		time = f.variables['time'][:]
		VV = f.variables[variable_name][:]
		if VV is None:
			if verbose:
				print('Unable to find variable '+E['variable']+' in file '+ff)
		f.close()

		# select the vertical and lat ranges specified in E
		# if only one number is specified, find the lev,lat, or lon closest to it
		# TODO: make this an external subroutine 
		levrange=E['levrange']
		if levrange[0] == levrange[1]:
			ll = levrange[0]
			idx = (np.abs(lev-ll)).argmin()
			lev2 = lev[idx]
			k1 = idx
			k2 = idx
		else:
			k1 = (np.abs(lev-levrange[1])).argmin()
			k2 = (np.abs(lev-levrange[0])).argmin()
			lev2 = lev[k1:k2+1]

		latrange=E['latrange']
		if latrange[0] == latrange[1]:
			ll = latrange[0]
			idx = (np.abs(lat-ll)).argmin()
			lat2 = lat[idx]
			k1 = idx
			k2 = idx
		else:
			j2 = (np.abs(lat-latrange[1])).argmin()
			j1 = (np.abs(lat-latrange[0])).argmin()
			lat2 = lat[j1:j2+1]


		# now select the relevant lat, lon, and lev regions 
		# All the variables in Wuke's files have shape time x lev x lat x ensemble_member 
		Vout = VV[:,k1:k2+1,j1:j2+1,ensemble_member-1]
		
	# for file not found 
	else:
		if verbose: 
			print('Unable to find TEM diagnostic file '+ff)
		Vout = None
		lat2 = None
		lev2 = None

	return Vout,lat2,lev2
