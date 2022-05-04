import pandas as pd
import numpy as np
import json
from datetime import datetime
from constants import ICUID, HID, CHARTTIME, NUMBER_OF_INTERVALS, TIME_STEP

#------- generating ICU Stay ID files ---------#
sepsis3_df = pd.read_csv('./data/sepsis3-df.csv')

icustay_ids = sepsis3_df[ICUID]
icustay_ids.to_csv('./data/icustay_ids.txt', index=False)

icu2hadm_df = sepsis3_df[[ICUID, HID]]
icu2hadm_dict = icu2hadm_df.set_index(ICUID).to_dict()[HID]
icu2hadm_json = json.dumps(icu2hadm_dict)
dict_file = open('./data/icu_hadm_dict.json', "w")
dict_file.write(icu2hadm_json)
dict_file.close()

# hadm ids for sepsis patient in MIMIC-III
icu2hadm = pd.read_json('./data/icu_hadm_dict.json', typ='series').to_dict()
hadm2icu = {icu2hadm[icu]:icu for icu in icu2hadm.keys()}
icu_id_sepsis = list(icu2hadm.keys())
hadm_id_sepsis = list(icu2hadm.values())

#------- generating treatment/{treatment_option}/{ID}.npy files ------#
vaso_df = pd.read_csv('./data/vaso_durations.csv')
vent_df = pd.read_csv('./data/vent_durations.csv')
# prune to sepsis3 cohort only
vaso_df = vaso_df[vaso_df[ICUID].isin(icu_id_sepsis)]
vent_df = vent_df[vent_df[ICUID].isin(icu_id_sepsis)]
# add HID
vaso_df[HID] = vaso_df[ICUID].map(icu2hadm)
vent_df[HID] = vent_df[ICUID].map(icu2hadm)

# save each patient demographic details to static.npy file
for treatment_option, df in [('vaso', vaso_df), ('vent', vent_df)]:
  for ID in list(vaso_df[HID]):
    patient = df[df[HID] == ID]
    patient = patient['duration_hours'].to_numpy()
    # adjust length of arr st it matches the expected A format
    if len(patient) < 10:
      zeros = np.zeros(10-len(patient))
      patient = np.append(patient, zeros)
    elif len(patient) > 10:
      patient = patient[:10]
    patient = patient.reshape((10, 1))
    np.save('./data/treatment/{}/{}.npy'.format(treatment_option, ID), patient)

#------- generating /static/{ID}.static.npy files ------#
detail_df = pd.read_csv('./data/detail.csv')
comorbid_df = pd.read_csv('./data/comorbid.csv')
height_weight_df = pd.read_csv('./data/height_weight.csv')

# prune to sepsis3 cohort only
detail_df = detail_df[detail_df[HID].isin(hadm_id_sepsis)]
comorbid_df = comorbid_df[comorbid_df[HID].isin(hadm_id_sepsis)]
height_weight_df = height_weight_df[height_weight_df[ICUID].isin(icu_id_sepsis)]

#add HID
height_weight_df[HID] = height_weight_df[ICUID].map(icu2hadm)

# calculate race variable
detail_df['white'] = detail_df['ethnicity_grouped']=='white'
detail_df['black'] = detail_df['ethnicity_grouped']=='black'
detail_df['hispanic'] = detail_df['ethnicity_grouped']=='hispanic'
detail_df['asian'] = detail_df['ethnicity_grouped']=='asian'
detail_df['other'] = ~(detail_df['white'] | detail_df['black'] | detail_df['hispanic'] | detail_df['asian'])
detail_df.drop(columns=['ethnicity_grouped'], inplace=True)

# calculate bmi variable
height_weight_df['bmi'] = height_weight_df['weight_first'] / (height_weight_df['height_first']/100)**2

# merging all time varying data into one df
static_df = detail_df.merge(comorbid_df, on=HID, how='inner')
static_df = static_df.merge(height_weight_df, on=HID, how='inner')

# save each patient demographic details to static.npy file
for ID in list(static_df[HID]):
  patient = static_df[static_df[HID] == ID]
  patient = patient.loc[:, patient.columns!=HID]
  np.save('./data/static/{}.static.npy'.format(ID), patient.to_numpy()[0])

# # ------- generating time variable x/{ID}.csv files ------#
vitals_df = pd.read_csv('./data/pivoted_vitals.csv', parse_dates=[CHARTTIME])
labs_df = pd.read_csv('./data/pivoted_labs.csv', parse_dates=[CHARTTIME])
gcs_df = pd.read_csv('./data/pivoted_gcs.csv', parse_dates=[CHARTTIME])
uo_df = pd.read_csv('./data/urine_output.csv', parse_dates=[CHARTTIME])

# keep only sepsis cohort for all data (vitals, labs, gcs, uo)
vitals_df = vitals_df[vitals_df[ICUID].isin(icu_id_sepsis)]
labs_df = labs_df[labs_df[HID].isin(hadm_id_sepsis)]
gcs_df = gcs_df[gcs_df[ICUID].isin(icu_id_sepsis)]
uo_df = uo_df[uo_df[ICUID].isin(icu_id_sepsis)]

# Add HID
vitals_df[HID] = vitals_df[ICUID].map(icu2hadm)
gcs_df[HID] = gcs_df[ICUID].map(icu2hadm)
uo_df[HID] = uo_df[ICUID].map(icu2hadm)

# list of hids in the vitals df. We use vitals as it contains the most frequently gathered ICU data
labs_hids = list(vitals_df[HID])
for hid in labs_hids:
  # for each hospital admission id, we want to save the patient record containing all the variables
  vitals = vitals_df[vitals_df[HID] == hid]
  labs = labs_df[labs_df[HID] == hid]
  gcs = gcs_df[gcs_df[HID] == hid]
  uo = uo_df[uo_df[HID] == hid]

  # get the first charttime in vitals to get the ICU admission time
  icu_time = vitals.min(axis=CHARTTIME).replace(minute=0, second=0, microsecond=0)
  # Now from the ICU admission time, get the next time steps
  for i in range(NUMBER_OF_INTERVALS):
    start_time = icu_time + i * TIME_STEP
    end_time = start_time + TIME_STEP
    # TODO calculate all the variables within this time interval for this patient record and save to disk



# # merging all time varying data into one df
# all_labs_df = labs_df.merge(gcs_df, on=HID, how='left')
# all_labs_df = all_labs_df.merge(uo_df, on=HID, how='left')
# time_var_df = vitals_df.merge(all_labs_df, on=HID, how='inner')
# var_rename = {'charttime':'time','HEMOGLOBIN':'hemoglobin','HeartRate':'heartrate','CREATININE':'creatinine','HEMATOCRIT':'hematocrit','SysBP':'sysbp','TempC':'tempc','PT':'pt','SODIUM':'sodium','DiasBP':'diasbp', 'GCS':'gcs_min','PLATELET':'platelet','PTT':'ptt','CHLORIDE':'chloride','RespRate':'resprate','GLUCOSE':'glucose','BICARBONATE':'bicarbonate','BANDS':'bands', 'BUN':'bun','value':'urineoutput','INR':'inr','LACTATE':'lactate','ANIONGAP':'aniongap','SpO2':'spo2','WBC':'wbc','MeanBP':'meanbp'}
# time_var_df.rename(columns=var_rename, inplace=True)

# # saving each patient data to a file
# for ID in list(time_var_df[HID]):
#   patient = time_var_df[time_var_df[HID] == ID]
#   patient = patient.loc[:, patient.columns!=HID]
#   # prune to only first 30 hours of a patient's stay
#   times_str = set(patient['time'])
#   times = []
#   for time_str in times_str:
#     times.append(datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S'))
#   times = sorted(times)
#   times = times[1:32:3]
#   sorted_str_times = []
#   for time in times:
#     sorted_str_times.append(time.strftime('%Y-%m-%d %H:%M:%S'))
#   times_dict = dict(zip(sorted_str_times, list(range(1, 32, 3))))
#   patient = patient[patient['time'].isin(sorted_str_times)]
#   patient = patient.replace({'time':times_dict})
#   # fill NULL values with mean of column
#   means = patient.mean(axis=0)
#   for col in patient.columns:
#     patient[col] = patient[col].fillna(means[col])
#   patient.to_csv('./data/x/{}.csv'.format(ID), index=False)