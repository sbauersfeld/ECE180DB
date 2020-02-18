#!/home/pi/berryconda3/bin/python3
import time
import datetime
import pandas as pd
import collections
from sklearn.externals import joblib
from sensor import *
import process_data as pdata
import numpy as np

model = joblib.load('models/scott/ft2.joblib')
scaler = joblib.load('models/scott/sft2.joblib')

IMU.detectIMU()
IMU.initIMU()

CHECK_TIME_INCREMENT_MS = 150
THRESHOLD = 300

header = ["time_ms"] + pdata.get_header()
data = []

input("Press 'Enter' to start...")

start = datetime.datetime.now()
counter = 0
elapsed_ms = 0
last_check_ms = 0
record = False
stop = False
sensor_x = []
sensor_y = []
sensor_z = []

while True:
    row = [elapsed_ms] + read_sensor()
    data.append(row)
    counter += 1

    # Check for changes every CHECK_TIME_INCREMENT_MS
    if record is False and elapsed_ms - last_check_ms >= CHECK_TIME_INCREMENT_MS:
        if check_movement(data, THRESHOLD):
            print("Movement detected")
            record = True
        else:
            print("No movement detected")
            data = []
            counter = 0
        last_check_ms = elapsed_ms

    if record is True and elapsed_ms - last_check_ms >= CHECK_TIME_INCREMENT_MS:
        if check_movement(data[-counter:], THRESHOLD):
            print("tracing...")
            counter = 0
        else: 
            print("Movement stopped")
            stop = True
        last_check_ms = elapsed_ms

    if stop:
        df = pd.DataFrame(list(data), columns=header)
        features = pdata.get_model_features(df)
        features = scaler.transform(np.reshape(features, (1, -1)))
        prediction = model.predict(features)[0]

        print("========================>", prediction)
        data = []
        record = False
        stop = False
        counter = 0
        input("Press 'Enter' to continue...")
        elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000
        last_check_ms = elapsed_ms

    elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000


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

# CHECK_TIME_INCREMENT_MS = 100
# SAMPLE_SIZE = 84
# THRESHOLD = 300

# header = ["time_ms"] + pdata.get_header()
# data = collections.deque(maxlen=SAMPLE_SIZE) #10 Hz

# input("Press 'Enter' to start...")

# start = datetime.datetime.now()
# elapsed_ms = 0
# last_check_ms = 0
# record = False
# stop = False
# sensor_x = []
# sensor_y = []
# sensor_z = []

# while True:
#     row = [elapsed_ms] + read_sensor()
#     data.append(row)

#     # Check for changes every CHECK_TIME_INCREMENT_MS
#     if elapsed_ms - last_check_ms >= CHECK_TIME_INCREMENT_MS and record is False:
#         if check_movement(data, THRESHOLD):
#             print("Changes detected")
#             record = True
#         else:
#             print("No changes detected")
#             data.clear()
#         last_check_ms = elapsed_ms

#     if len(data) == data.maxlen and record is True:
#         df = pd.DataFrame(list(data), columns=header)
#         features = pdata.get_model_features(df)
#         features = scaler.transform(np.reshape(features, (1, -1)))
#         prediction = model.predict(features)[0]

#         print("========================>", prediction)
#         data.clear()
#         record = False
#         input("Press 'Enter' to continue...")
#         elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000
#         last_check_ms = elapsed_ms

#     elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000
