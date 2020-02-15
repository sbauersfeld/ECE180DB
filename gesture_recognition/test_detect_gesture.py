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

input("Press 'Enter' to start...")

start = datetime.datetime.now()
elapsed_ms = 0
last_check = 0
record = False
accel_x = []
accel_y = []
accel_z = []

while True:
    row = [elapsed_ms] + read_sensor()
    data.append(row)

    # Check for changes every CHECK_TIME_INCREMENT_MS
    if elapsed_ms - last_check >= CHECK_TIME_INCREMENT_MS and record is False:
        data_len = range(len(data))
        accel_x = [data[i][1] for i in data_len]
        accel_y = [data[i][2] for i in data_len]
        accel_z = [data[i][3] for i in data_len]

        x_range = max(accel_x) - min(accel_x)
        y_range = max(accel_y) - min(accel_y)
        z_range = max(accel_z) - min(accel_z)

        # if two out of three ranges of sensor values overpases the threshold, start tracing
        if (x_range >= THRESHOLD and y_range >= THRESHOLD) or \
        (x_range >= THRESHOLD and z_range >= THRESHOLD) or \
        (y_range >= THRESHOLD and z_range >= THRESHOLD):
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
        data.clear()
        record = False
        input("Press 'Enter' to continue...")
        elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000
        last_check = elapsed_ms

    elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000