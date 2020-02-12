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
    

header = ["time_ms"] + pdata.get_header()
duration_s = 1.5

while True:
    input("Press 'Enter' to start tracing...")
    start = datetime.datetime.now()
    elapsed_ms = 0
    data = []

    while elapsed_ms < duration_s * 1000:
        print("tracing...")

        row = [elapsed_ms] + read_sensor()
        data.append(row)
        elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000

    df = pd.DataFrame(data, columns=header)
    features = pdata.get_model_features(df)
    features = scaler.transform(np.reshape(features, (1, -1)))
    prediction = model.predict(features)[0]
    print(prediction)



# CHECK_TIME_INCREMENT_MS = 400
# SAMPLE_SIZE_MS = 850

# header = ["time_ms"] + pdata.get_header()
# data = collections.deque(maxlen=int(SAMPLE_SIZE_MS / 10)) #10 Hz

# start = datetime.datetime.now()
# elapsed_ms = 0
# last_classified = 0
# last_classification = "negative"

# while True:
#     row = [elapsed_ms] + read_sensor()
#     data.append(row)

#     if elapsed_ms - last_classified >= CHECK_TIME_INCREMENT_MS and len(data) == data.maxlen:
#         df = pd.DataFrame(list(data), columns=header)
#         features = pdata.get_model_features(df)
#         features = scaler.transform(np.reshape(features, (1, -1)))
#         prediction = model.predict(features)[0]

#         print(int(elapsed_ms), prediction)
#         if prediction != 'negative':# and last_classification != prediction:
#             print("========================>", prediction)
#             input("press 'Enter' to continue...")
#             # return prediction
#         data.clear()

#         last_classified = elapsed_ms
#         last_classification = prediction

#     elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000


   