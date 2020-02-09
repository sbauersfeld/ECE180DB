import time
import datetime
import pandas as pd
import utils
import collections
from sklearn.externals import joblib
import sensor
import process_data

# CHANGE HERE
model = joblib.load('/home/pi/dev/gesture/models/167pt_model.joblib') 

CHECK_TIME_INCREMENT_MS = 200
SAMPLE_SIZE_MS = 1500

header = ["time_ms"] + process_data.get_header()
data = collections.deque(maxlen=int(SAMPLE_SIZE_MS / 10)) #10 Hz

print('Starting operation')

start = datetime.datetime.now()
elapsed_ms = 0
last_classified = 0
last_classification = "negative_trim" # set it as pass

while True:
  row = [elapsed_ms] + sensor.read_sensor()
  data.append(row)

  if elapsed_ms - last_classified >= CHECK_TIME_INCREMENT_MS and len(data) == data.maxlen:
    df = pd.DataFrame(list(data), columns=header)
    features = utils.get_model_features(df)
    prediction = model.predict([features])[0]

    #print(int(elapsed_ms), prediction)
    # CHANGE HERE
    if prediction != 'negative_trim':# and last_classification != prediction:
        print("========================>", prediction)
        data.clear()

    last_classified = elapsed_ms
    last_classification = prediction

  elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000

  #if elapsed_ms > 10000:
  #  break