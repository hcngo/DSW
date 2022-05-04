import datetime
HID = "hadm_id"
ICUID = "icustay_id"
CHARTTIME = "charttime"

NUMBER_OF_INTERVALS = 10 # number of time steps
TIME_STEP = datetime.timedelta(hours=3) # time interval for each step in hour