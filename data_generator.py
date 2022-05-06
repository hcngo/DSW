from tracemalloc import start
from xml.dom.minidom import CharacterData
import pandas as pd
import numpy as np
import json
from datetime import datetime
from constants import ICUID, HID, CHARTTIME, NUMBER_OF_INTERVALS, TIME_STEP, MAPPING, ALL_MAPPING, LABS, GCS, UO, VITALS
import sys

option = sys.argv[1] if len(sys.argv) > 1 else None

if option == "treatments" or option is None:

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
  vaso_df = pd.read_csv('./data/vaso_durations.csv', parse_dates=["starttime"])
  vent_df = pd.read_csv('./data/vent_durations.csv', parse_dates=["starttime"])
  # prune to sepsis3 cohort only
  vaso_df = vaso_df[vaso_df[ICUID].isin(icu_id_sepsis)]
  vent_df = vent_df[vent_df[ICUID].isin(icu_id_sepsis)]
  # add HID
  vaso_df[HID] = vaso_df[ICUID].map(icu2hadm)
  vent_df[HID] = vent_df[ICUID].map(icu2hadm)

  treatment_hids = {"vaso": set(vaso_df[HID]), "vent": set(vent_df[HID])}

  # save each patient demographic details to static.npy file
  for treatment_option, df in [('vaso', vaso_df), ('vent', vent_df)]:
    print(f"processing {len(treatment_hids[treatment_option])} treatment records treatment_option={treatment_option}")
    for id in treatment_hids[treatment_option]:
      patient = df[df[HID] == id]

      first_treatment_time = patient["starttime"].min().replace(minute=0, second=0, microsecond=0)

      vals = []

      for i in range(NUMBER_OF_INTERVALS):
        start_time = (first_treatment_time + i * TIME_STEP)
        end_time = (first_treatment_time + (i + 1) * TIME_STEP)
        time_interval_data = patient[(patient["starttime"] >= start_time) & (patient["starttime"] < end_time)]
        v = time_interval_data["duration_hours"].sum()
        if np.isnan(v):
          v = 0
        vals.append(v)

      np.save('./data/treatment/{}/{}.npy'.format(treatment_option, id), np.array(vals))
      print(f"record hid={id} treatment is saved to data folder")

# hadm ids for sepsis patient in MIMIC-III
icu2hadm = pd.read_json('./data/icu_hadm_dict.json', typ='series').to_dict()
hadm2icu = {icu2hadm[icu]:icu for icu in icu2hadm.keys()}
icu_id_sepsis = list(icu2hadm.keys())
hadm_id_sepsis = list(icu2hadm.values())

if option == "static" or option is None:

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
  detail_df['white'] = detail_df['ethnicity_grouped'].apply(lambda x: 1 if x =='white' else 0)
  detail_df['black'] = detail_df['ethnicity_grouped'].apply(lambda x: 1 if x =='black' else 0)
  detail_df['hispanic'] = detail_df['ethnicity_grouped'].apply(lambda x: 1 if x =='hispanic' else 0)
  detail_df['asian'] = detail_df['ethnicity_grouped'].apply(lambda x: 1 if x =='asian' else 0)
  detail_df['other'] = detail_df['ethnicity_grouped'].apply(lambda x: 1 if not (x =='asian' or x=='hispanic' or x=='black' or x=='white') else 0)
  detail_df.drop(columns=['ethnicity_grouped'], inplace=True)

  detail_df["gender"] =  detail_df["gender"].apply(lambda x: 1 if x == "M" else 0 if x == "F" else -1)

  # calculate bmi variable
  height_weight_df['bmi'] = height_weight_df['weight_first'] / (height_weight_df['height_first']/100)**2

  # merging all time varying data into one df
  static_df = detail_df.merge(comorbid_df, on=HID, how='inner')
  static_df = static_df.merge(height_weight_df, on=HID, how='inner')

  # save each patient demographic details to static.npy file
  for id in list(static_df[HID]):
    patient = static_df[static_df[HID] == id]
    patient = patient.loc[:, patient.columns!=HID]
    np.save('./data/static/{}.static.npy'.format(id), patient.to_numpy()[0])

if option == "variables" or option is None:
  start_idx = int(sys.argv[2]) if len(sys.argv) > 2 else None
  end_idx = int(sys.argv[3]) if len(sys.argv) > 3 else None

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

  data_bag = {LABS: labs_df, VITALS: vitals_df, GCS: gcs_df, UO: uo_df}
  data_means = {}  
  # Use HID as the index
  for type, whole_df in data_bag.items():
    whole_df.set_index(HID)
    whole_df.sort_index()
    data_means[type] = whole_df.mean(numeric_only=True)



  # list of hids in the vitals df. We use vitals as it contains the most frequently gathered ICU data
  labs_hids = list(set(vitals_df[HID]))
  labs_hids.sort()
  print("Number of Hospital Admission IDS: " + str(len(labs_hids)))
  if start_idx is None:
    start_idx = 0
  if end_idx is None:
    end_idx = len(labs_hids)
  print(f"Process sample from start index {start_idx} to end index {end_idx} for {end_idx - start_idx} samples")

  for record_idx in range(start_idx, end_idx):
    hid = labs_hids[record_idx]
    # for each hospital admission id, we want to save the patient record containing all the variables
    patient_data = {}
    patient_means = {}
    whole_period_means = {}
    for type, whole_df in data_bag.items():
      patient_data[type] = whole_df[whole_df[HID] == hid]
      patient_means[type] = patient_data[type].mean(numeric_only=True)

    # patient records corresponding to hid to be saved
    patient_record_df = pd.DataFrame()

    # variable arrays keyed by destination column names
    values = {k:[] for k in ALL_MAPPING.values()}

    # get the first charttime in vitals to get the ICU admission time
    icu_time = patient_data[VITALS][CHARTTIME].min().replace(minute=0, second=0, microsecond=0)

    # calculate the means within NUMBER_OF_INTERVALS of TIME_STEP since the first icu_time
    for type in data_bag:
      df = patient_data[type]
      whole_period_means[type] = df[(df[CHARTTIME] >= icu_time) & (df[CHARTTIME] < icu_time + NUMBER_OF_INTERVALS * TIME_STEP)].mean(numeric_only=True)

    # times
    time_array = []
    
    # Now from the ICU admission time, get the next time steps
    for i in range(NUMBER_OF_INTERVALS):
      start_time = (icu_time + i * TIME_STEP)
      end_time = (icu_time + (i + 1) * TIME_STEP)

      time_array.append(start_time)

      # data within this time interval
      interval_data = {}
      for type in patient_data:
        df = patient_data[type]
        interval_data[type] = df[(df[CHARTTIME] >= start_time) & (df[CHARTTIME] < end_time)]

      # TODO calculate all the variables within this time interval for this patient record and save to disk
      for type, mapping in MAPPING.items():
        # data = labs if data_type == "labs" else vitals if data_type == "vitals" else gcs if data_type == "gcs" else uo if data_type == "uo" else None
        # overall_mean = labs_means if data_type == "labs" else vitals_means if data_type == "vitals" else gcs_means if data_type == "gcs" else uo_means if data_type == "uo" else None
        for from_field, to_field in mapping.items():
          v = interval_data[type][from_field].mean()
          if np.isnan(v) and i > 0:
            # assume the previous value
            v = values[to_field][i - 1]
          if np.isnan(v):
            # get the mean of all the periods (NUMBER_OF_INTERVALS)
            v = whole_period_means[type][from_field]
          if np.isnan(v):
            # get the mean of all the data
            v = patient_means[type][from_field]
          if np.isnan(v):
            v = data_means[type][from_field]
          
          if np.isnan(v):
            raise Exception("v is still NaN!")

          values[to_field].append(v)
    
    patient_record_df["step"] = range(NUMBER_OF_INTERVALS)
    patient_record_df["time"] = time_array
    for to_field, val_array in values.items():
      patient_record_df[to_field] = val_array

    patient_record_df.to_csv('./data/x/{}.csv'.format(hid), index=False)
    print(f"record index={record_idx} with hid={hid} is saved to data folder")