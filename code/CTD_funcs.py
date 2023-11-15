### CTD functions ###

'''
Python script defining a number of function useful for the CTD work: parsing,
switching formats, referring between different files..

Thinking that, eventually, some of this could be transferred to a more generalized module.

Sections:
- Parse .btl files


'''
# IMPORTS
import pandas as pd
import numpy as np
import re
from matplotlib.dates import date2num, num2date

#######################
### PARSE BTL FILES ###
#######################

# ----------------Dictionary mapping default SBE names to something more 
# readable (optional but nice)

colname_map = {'Sal00':'sal', 'Sbeox0ML/L':'ox', 'Sigma-é00':'sigth', 
               'SvCM':'sound_spd','PrDM':'pres', 'T090C':'temp',
               'C0S/m':'cond', 'Sbeox0V':'ox_voltage', 'FlECO-AFL':'fl'}


# ------- Support function: find start of column data
# NOTE: works for this dataset - I haven't tried to see if it generalized (yet)
def _find_start_of_data(btl_fn):
    '''
    Take a .btl file and return the row where the columnar data starts 
    (first line after header).
    '''
    start_ind_rows = 0
    with open(btl_fn, encoding = 'latin-1') as f:
        lines = f.readlines()
    for nn, line in enumerate(lines):
        if 'Time' in line:
            start_ind_rows = nn+1
    return start_ind_rows


# ------- Main parsing fuction.
# Going a bit back and forth between np arrays and pandas dataframes 
# depending on where the operations are easiest
def parse_btl_to_DataFrame(btl_fn, colname_map = colname_map):
    '''
    Take a btl file and read, clean and reorganize the data. 
    Return a more nicely formatted pandas dataframe.

    colname_map: Dictionary mapping default SBE names (e.g. "Sal00")
                 to something nicer (e.g. "sal"). Optional.
    '''
    # Find start of column data
    start_ind_rows = _find_start_of_data(btl_fn)

    # Read file to pandas line by line
    # (also reading the header, hence the -2)
    table_unwr =pd.read_fwf(btl_fn, skiprows = start_ind_rows-2, 
                delim_whitespace = True, header =None, encoding = 'latin-1')

    # Clean up whitespace and remove "(avg)", "(sdev)"
    values_flat = table_unwr.values.flatten() # Flattening the data array
    shape_orig = table_unwr.values.shape
    values_flat_cleaned = values_flat.copy()

    # Cleaning loop
    for nn, val in enumerate(values_flat):
        if isinstance(val, str):
            # Remove whitespace and "(avg)", "(sdev)"
            values_flat_cleaned[nn] = (
                val.replace('(avg)', '').replace('(sdev)', '').strip())
    
    # Reshaping back to 2D array with cleaned up fields 
    values_cleaned = values_flat_cleaned.reshape(shape_orig)
    
    # New pandas array with cleaned up fields
    pd_cleaned = pd.DataFrame(values_cleaned)
    
    # Remove the last column if that is NaN (if "(avg)", "(sdev)" 
    # were put in a separate column)
    if isinstance(pd_cleaned.values[0, -1], float):
        last_column = pd_cleaned.columns[-1]
        pd_cleaned = pd_cleaned.drop(columns = last_column)
    
    # Get column header names, replacing seabird defaults with 
    # something more human readable
    colnms = pd_cleaned.values[0]
    # thinf: leave out for now, b/c incomplete
    #for nn, colnm_orig in enumerate(colnms):
    #    if colnm_orig in colname_map:
    #        colnms[nn] =  colname_map[colnm_orig]
    
    # Make a pd dataframe with the main column (avg values)
    pd_main = pd.DataFrame(pd_cleaned.values[2::2], columns = colnms)
    
    # Add "time" # NOTE: works for this dataset, should confirm 
    # whether it works for general .btl files
    pd_main.insert(2, "Time", pd_cleaned.values[3::2, 1])

    # Read the "standard deviation line" to a pandas dataframe 
    pd_std_wo_time = (pd.DataFrame(pd_cleaned.values[3::2], columns = pd_cleaned.values[0])
        .drop(columns = 'Date').replace('', np.nan).dropna(axis=1, inplace=False))

    # Add the standard deviation columns to the main dataframe
    for stdcol in pd_std_wo_time.columns:
        pd_main[f'{stdcol}_SD'] =  pd_std_wo_time[stdcol].values

    # Return the dataframe
    return pd_main


#################################################################
### CONNECT CTD DATA/METADATA AND SALINOMETER SAMPLE METADATA ###
#################################################################

# This is pretty ad-hoc for this particular dataset.
# But should have something equivalent for the more generalized case..

def station_niskin_from_sample_nr(sample_num, df_log):
    '''
    Takes the sample number (e.g. 2527) and returns a tuple containing
    the corresponding station number, cast number, and niskin bottle number.
    (e.g. (11, 1, 3))
    '''
    df_log_sal = df_log.loc[df_log['Sample type'] == 'Salinity']
    df_sample = df_log_sal.loc[df_log_sal['Sample name'] == f'SAL-{sample_num}']

    # Get station number
    station_name = df_sample.Station.values[0]
    station_number = int(re.sub("St", "", station_name, flags=re.IGNORECASE))

    # Get cast number
    cast_number = df_sample['CTD LS number'].values[0]

    # Get bottle
    btl_number = int(df_sample['bottle #'].values[0])

    return station_number, cast_number, btl_number

    
def niskin_STP_from_sample_nr(sample_num, df_log, btl_data_dir):
    '''
    Takes the sample number (e.g. 2527) and returns the measured 
    salinity and pressure values from the corresponding ctd cast 
    '''

    station_number, cast_number, btl_number = station_niskin_from_sample_nr(sample_num, df_log)

    #TT2020/21 specific filename syntax
    #cast_fn =  f'sta{station_number:03d}_{cast_number:02d}.csv'

    #TT2022/23 specific filename syntax (more standardized)
    cast_fn =  f'{station_number:03d}.csv'

    df_cast = pd.read_csv(btl_data_dir + cast_fn)
    df_niskin = df_cast[df_cast.Bottle==btl_number]

    S1_nisk = df_niskin.Sal00.values[0]
    S2_nisk = df_niskin.Sal11.values[0]
    T1_nisk  = df_niskin.T090C.values[0]
    T2_nisk  = df_niskin.T190C.values[0]
    C1_nisk  = df_niskin['C0S/m'].values[0]
    C2_nisk  = df_niskin['C1S/m'].values[0]
    P_nisk  = df_niskin.PrDM.values[0]
    
    return S1_nisk, S2_nisk, T1_nisk, T2_nisk, C1_nisk, C2_nisk, P_nisk 


def dataframe_sal(salinometer_file, df_log, btl_data_dir):
    
    #### LOAD SALINOMETER READINGS AND CLEAN UP

    # Load salinometer csv file to Pandas DataFrame
    salm_all = pd.read_csv(salinometer_file).copy()

    # Drop the rows where we have water standard samples
    salm = salm_all[salm_all['Sample']!='std']
        
    # Drop all columns except "Sample" and "S_final"
    salm = salm[['Sample', 'S_final']]
    
    ### Sort by sample number (= in chronological order)
    salm = salm.sort_values('Sample')
    
    # Reset the index to "forget missing values"; such that 
    # e.g. [3, 4, 0, 1, 2] -> [0, 1, 2, 3, 4]
    # drop=True -> drop the previous index (don't need it)
    salm = salm.reset_index(drop=True) 

    ### ADDING CTD INFO FROM BTL FILES
    # Now, creating a copy of salm; *df_sal*.
    # Contains salinometer values; we will add the corresponding
    # CTD meta data (Station, Cast, Niskin) and S, T, P values.

    # Create a dataframe *salm* copy with new empty fields
    df_sal = salm.assign(
        CTD_station=None, CTD_cast_=None, CTD_niskin_num=None, 
        S_CTD=None, p_CTD=None, T_CTD=None).copy()

    # Loop through each sample row
    # -> Extract corresponding CTD metadata and S, T, P 
    for nn, row in df_sal.iterrows():
        
        sample_num = int(row['Sample'])
        station_number_, cast_number_, nisk_number_ = (
            station_niskin_from_sample_nr(sample_num, df_log))

        df_sal.loc[nn, 'CTD_station'] = station_number_    
        df_sal.loc[nn, 'CTD_cast'] = cast_number_    
        df_sal.loc[nn, 'CTD_niskin_num'] = nisk_number_    

        S1_CTD_, S2_CTD_, T1_CTD_, T2_CTD_, C1_CTD_, C2_CTD_, p_CTD_ = niskin_STP_from_sample_nr(
            sample_num, df_log, btl_data_dir)
        df_sal.loc[nn, 'S1_CTD'] = S1_CTD_ 
        df_sal.loc[nn, 'S2_CTD'] = S2_CTD_ 
        df_sal.loc[nn, 'T1_CTD'] = T1_CTD_ 
        df_sal.loc[nn, 'T2_CTD'] = T2_CTD_ 
        df_sal.loc[nn, 'C1_CTD'] = C1_CTD_ 
        df_sal.loc[nn, 'C2_CTD'] = C2_CTD_ 
        df_sal.loc[nn, 'p_CTD'] = p_CTD_  

    return df_sal


######################################################
### LOAD AND MANIPULATE CTD PROFILE DATA FROM .CNV ###
######################################################

# (TBW) #

'''
HERE:

- Go beetween: CTD cast num <--> profile
- Wrapper for seabird.dnv.fCNV:
    - Load to a uniform format!
    - Look into error messages!

    #NOTE: Wrote a parser in ocanograPy -> use this instead  
'''

######################################################
### CONVERT TIME TO ISO8601                        ###
######################################################
# (copied from oceanograPy)

def datetime_to_ISO8601(time_dt, zone = 'Z'):
    '''
    Convert datetime to YYYY-MM-DDThh:mm:ss<zone>

    *zone* defines the time zone. Default: 'Z' (UTC).

    (see https://wiki.esipfed.org/Attribute_Convention_for_Data_Discovery_1-3)
    '''

    time_fmt = f'%Y-%M-%dT%H:%M:%S{zone}'
    iso8601_time = time_dt.strftime(time_fmt)

    return iso8601_time

def datenum_to_ISO8601(datenum, zone = 'Z'):
    '''
    Convert datenum (time since epoch, e.g. 18634.11) to YYYY-MM-DDThh:mm:ss<zone>.

    *zone* defines the time zone. Default: 'Z' (UTC).

    (see https://wiki.esipfed.org/Attribute_Convention_for_Data_Discovery_1-3)
    '''

    time_dt = num2date(datenum)
    iso8601_time = datetime_to_ISO8601(time_dt)

    return iso8601_time
