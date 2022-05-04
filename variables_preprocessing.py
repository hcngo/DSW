import pandas as pd
from constants import HID, ICUID

# hadm ids for sepsis patient in MIMIC-III
icu2hadm = pd.read_json('./data/icu_hadm_dict.json', typ='series').to_dict()
icu_id_sepsis = list(icu2hadm.keys())
hadm_id_sepsis = list(icu2hadm.values())

# PREPROCESS vitals data to keep only sepsis cohort and to map icustay_id to hadm_id
vitals_df = pd.read_csv('./data/pivoted_vitals.csv')
vitals_df = vitals_df[vitals_df[ICUID].isin(icu_id_sepsis)]
vitals_df = vitals_df.replace({ICUID: icu2hadm})
vitals_df.rename(columns={ICUID:HID}, inplace=True)
vitals_df['charttime'] = vitals_df['charttime'].str.replace('\S{6}$', ':00:00', regex=True)
vitals_df['charttime'] = pd.to_datetime(vitals_df['charttime'], format='%Y-%m-%d %H:%M:%S')
# convert all datetime to every 3 hrs
def convertToInterval(date_obj):
  hr = date_obj.hour
  rem = hr%3
  if rem != 0:
    new_hour = min(hr+3-rem, 23)
    date_obj = date_obj.replace(hour=new_hour)
  return date_obj
vitals_df['charttime'] = vitals_df['charttime'].apply(convertToInterval)
# aggregate rows w/ same id and charttime by mean
grouped_vitals = vitals_df.groupby(['hadm_id', 'charttime']).agg(dict(zip(vitals_df.columns[2:], ['mean']*len(vitals_df.columns))))
grouped_vitals = grouped_vitals.reset_index()
# if all values are null use mean of first 30
all_vitals = pd.DataFrame({}, columns=vitals_df.columns) # empty df to store final values
hadm_ids = set(grouped_vitals['hadm_id'])
for hadm_id in hadm_ids:
  patient = grouped_vitals[grouped_vitals['hadm_id'] == hadm_id]
  patient = patient.sort_values(by=['charttime'])
  means = patient.iloc[:32, 2:].mean(axis=0)
  for col in patient.columns[2:]:
    patient[col] = patient[col].fillna(means[col])
  all_vitals = pd.concat([all_vitals, patient])
vitals_df.to_csv('./data/processed_pivoted_vitals.csv', index=False)
del vitals_df
vitals_df = None

# PREPROCESS labs data to keep only sepsis cohort
labs_df = pd.read_csv('./data/pivoted_labs.csv')
labs_df = labs_df[labs_df[HID].isin(hadm_id_sepsis)]
labs_df.to_csv('./data/processed_pivoted_labs.csv', index=False)
del labs_df
labs_df = None

# PREPROCESS gcs data to keep only sepsis cohort and to map icustay_id to hadm_id
gcs_df = pd.read_csv('./data/pivoted_gcs.csv')
gcs_df = gcs_df[gcs_df[ICUID].isin(icu_id_sepsis)]
gcs_df = gcs_df.replace({ICUID: icu2hadm})
gcs_df.rename(columns={ICUID:HID}, inplace=True)
gcs_df.to_csv('./data/processed_pivoted_gcs.csv', index=False)
del gcs_df
gcs_df = None

# PREPROCESS urine data to keep only sepsis cohort and to map icustay_id to hadm_id
uo_df = pd.read_csv('./data/urine_output.csv')
uo_df = uo_df[uo_df[ICUID].isin(icu_id_sepsis)]
uo_df = uo_df.replace({ICUID: icu2hadm})
uo_df.rename(columns={ICUID:HID}, inplace=True)
uo_df.to_csv('./data/processed_urine_output.csv', index=False)
del uo_df
uo_df = None