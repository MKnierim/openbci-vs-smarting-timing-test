# Setup
import pandas as pd

# The xdf data is a list
# - list entry 0 = EEG; 1 = Markers (here)
# - Each entry one level below is a dict
#   - Each dict has 'info', 'footer', 'time_series', 'time_stamps'
# display(data_base[0].keys())

# Extract channel names (electrodes used as recorded in the XDF)
def getElecList(xdf_eeg_dat):
    if xdf_eeg_dat['info']['desc'][0] != None:
        elecs = xdf_eeg_dat['info']['desc'][0]['channels'][0]['channel']
        elecs = pd.DataFrame(elecs)['label'].tolist()
        elecs = [item for sublist in elecs for item in sublist] # Flatten the list
        return elecs

# Manual elec naming
# elecs_cEEGrid_Smarting = ['L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'L10', 'R8', 'R7', 'R6', 'R5', 'R1', 'R4', 'R3', 'R2', 'L1']
# print(elecs_cEEGrid_Smarting)

def extractStreamType(xdf_dat, streamType):
    stream = []
    for i in range(len(xdf_dat)):
        if xdf_dat[i]['info']['type'] == [streamType]:
            stream = xdf_dat[i]
    return stream

def extractStreamName(xdf_dat, streamName):
    stream = []
    for i in range(len(xdf_dat)):
        if xdf_dat[i]['info']['name'] == [streamName]:
            stream = xdf_dat[i]
    return stream

def makeEEGDf(xdf_eeg_dat, getElecs = True):
    if getElecs:
        df = pd.DataFrame(data=xdf_eeg_dat['time_series'], columns=getElecList(xdf_eeg_dat)) # TODO Check if elec names are correctly assigned
    else:
        df = pd.DataFrame(data=xdf_eeg_dat['time_series'])

    df.insert(0, 'time', xdf_eeg_dat['time_stamps'])
    return df

def makeExpMarkerDf(xdf_mknExp_dat):
    # Make dictionary
    datDict = {'expPhase' : [item for sublist in xdf_mknExp_dat['time_series'] for item in sublist], # Flatten the list
               'time' : xdf_mknExp_dat['time_stamps']}
    return pd.DataFrame(datDict)

def removeXML(eventStr):
    start_str = "<ecode>"
    end_str = "</ecode>"

    # slicing off after length computation
    return eventStr[eventStr.index(start_str) + len(start_str):eventStr.index(end_str)]

def makeErpEventDf(xdf_presentation_dat):
    # Extract ERP timestamps
    event_dict = {'event': [item for sublist in xdf_presentation_dat['time_series'] for item in sublist],
                  # Flatten the list
                  'time': xdf_presentation_dat['time_stamps']}

    df = pd.DataFrame(event_dict)
    # Filter where the sound stimulus information is located
    df = df[df['event'].str.contains("<etype>Sound</etype>")]

    # Simplify event information
    df['event'] = df['event'].apply(removeXML)
    # Split the cols
    df[['event', 'block', 'blockNr', 'trial', 'stimNr', 'stimulus', 'stimulusType']] = df['event'].str.split(';',
                                                                                                             expand=True)
    df.drop('event', axis=1, inplace=True)
    return df
