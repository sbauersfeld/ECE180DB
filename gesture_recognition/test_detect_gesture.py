#!/home/pi/berryconda3/bin/python3
import time
import datetime
import pandas as pd
import collections
from sklearn.externals import joblib
from sensor import *
import process_data as pdata
import numpy as np


model = joblib.load('models/wilson/model3.joblib')
scaler = joblib.load('models/wilson/scaler3.joblib')

IMU.detectIMU()
IMU.initIMU()
    

# header = ["time_ms"] + pdata.get_header()
# duration_s = 1.5

# while True:
#     input("Press 'Enter' to start tracing...")
#     start = datetime.datetime.now()
#     elapsed_ms = 0
#     data = []

#     while elapsed_ms < duration_s * 1000:
#         print("tracing...")

#         row = [elapsed_ms] + read_sensor()
#         data.append(row)
#         elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000

#     df = pd.DataFrame(data, columns=header)
#     features = pdata.get_model_features(df)
#     features = scaler.transform(np.reshape(features, (1, -1)))
#     prediction = model.predict(features)[0]
#     print(prediction)



CHECK_TIME_INCREMENT_MS = 100
SAMPLE_SIZE = 84
THRESHOLD = 300

header = ["time_ms"] + pdata.get_header()
data = collections.deque(maxlen=SAMPLE_SIZE) #10 Hz

start = datetime.datetime.now()
elapsed_ms = 0
last_check = 0
record = False

while True:
    row = [elapsed_ms] + read_sensor()
    data.append(row)

    # Check for changes every CHECK_TIME_INCREMENT_MS
    if elapsed_ms - last_check == CHECK_TIME_INCREMENT_MS and record is False:
        x_range = max(data[1]) - min(data[1])
        y_range = max(data[2]) - min(data[2])
        z_range = max(data[3]) - min(data[3])

        # if range of sensor values overpases the threshold, start tracing
        if x_range >= THRESHOLD or y_range >= THRESHOLD or z_range >= THRESHOLD:
            print("Changes detected")
            record = True
        else:
            print("No changes detected")
            data.clear()

        last_check = elapsed_ms


    if len(data) == data.maxlen and record is True:
        df = pd.DataFrame(list(data), columns=header)
        features = pdata.get_model_features(df)
        features = scaler.transform(np.reshape(features, (1, -1)))
        prediction = model.predict(features)[0]

        print("========================>", prediction)
        input("Press 'Enter' to continue...")
        data.clear()
        last_check = elapsed_ms

    elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000