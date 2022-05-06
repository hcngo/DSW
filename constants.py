import datetime
HID = "hadm_id"
ICUID = "icustay_id"
CHARTTIME = "charttime"

LABS = "labs"
VITALS = "vitals"
GCS = "gcs"
UO = "uo"

NUMBER_OF_INTERVALS = 10 # number of time steps
TIME_STEP = datetime.timedelta(hours=3) # time interval for each step in hour
STATIC_VARIABLES = ["admission_age", "gender", "white", "black", "hispanic", "asian", "other", "metastatic_cancer", "diabetes_complicated", "height_first", "weight_first", "bmi"]
MAPPING = {
    LABS: {
        'HEMOGLOBIN':'hemoglobin',
        'CREATININE':'creatinine',
        'HEMATOCRIT':'hematocrit',
        'PT':'pt',
        'SODIUM':'sodium',
        'PLATELET':'platelet',
        'PTT':'ptt',
        'WBC':'wbc',
        'CHLORIDE':'chloride',
        'GLUCOSE':'glucose',
        'BICARBONATE':'bicarbonate',
        'BANDS':'bands',
        'BUN':'bun',
        'INR':'inr',
        'LACTATE':'lactate',
        'ANIONGAP':'aniongap',
    },
    VITALS: {
        'HeartRate':'heartrate',
        'SysBP':'sysbp',
        'DiasBP':'diasbp',
        'MeanBP':'meanbp',
        'RespRate':'resprate',
        'TempC':'tempc',
        'SpO2':'spo2',
    },
    GCS: {
        'GCS':'gcs_min',
    },
    UO: {
        'value':'urineoutput',
    }
}
ALL_MAPPING = {k:v for mapping in MAPPING.values() for k, v in mapping.items() }