#!/home/pi/berryconda3/bin/python3
import time
import datetime
import pandas as pd
import collections
from sklearn.externals import joblib
from sensor import *
import process_data as pdata
import numpy as np

def gesture_setup(member, model_name="model4", scaler_name="scaler4", prefix=""):
    model = joblib.load(prefix + 'models/' + member + '/' + model_name + ".joblib")
    scaler = joblib.load(prefix + 'models/' + member + '/' + scaler_name + ".joblib")

    IMU.detectIMU()
    IMU.initIMU()
    return model, scaler

def get_gesture(model, scaler, duration_s=1.5):
    header = ["time_ms"] + pdata.get_header()
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
    return prediction

def get_gesture2(model, scaler, max_time=4):
    CHECK_TIME_INCREMENT_MS = 200
    THRESHOLD = 300

    header = ["time_ms"] + pdata.get_header()

    start = datetime.datetime.now()
    counter = 0
    elapsed_ms = 0
    last_check_ms = 0
    record = False
    stop = False
    accel_x = []
    accel_y = []
    accel_z = []
    data = []

    while True:
        row = [elapsed_ms] + read_sensor()
        data.append(row)
        counter += 1

        # Checks for movement
        if record is False and elapsed_ms - last_check_ms >= CHECK_TIME_INCREMENT_MS:
            if check_movement(data, THRESHOLD):
                print("Movement detected")
                record = True
            else:
                print("No movement detected")
                data = []
                counter = 0
            last_check_ms = elapsed_ms

        # Check for no movement
        if record is True and elapsed_ms - last_check_ms >= CHECK_TIME_INCREMENT_MS:
            if check_movement(data[-counter:], THRESHOLD):
                print("tracing...")
                counter = 0
            else: 
                print("Movement stopped")
                stop = True
            last_check_ms = elapsed_ms

        # Predicts traced gesture
        if stop:
            df = pd.DataFrame(list(data), columns=header)
            features = pdata.get_model_features(df)
            features = scaler.transform(np.reshape(features, (1, -1)))
            prediction = model.predict(features)[0]

            print("========================>", prediction)
            return prediction

        # timeout 
        if elapsed_ms > max_time * 1000:
            print("Timeout")
            return "block" # have it as pass?

        elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000

# def get_gesture(model, scaler, max_time=3):
#     CHECK_TIME_INCREMENT_MS = 200
#     SAMPLE_SIZE_MS = 840

#     header = ["time_ms"] + pdata.get_header()
#     data = collections.deque(maxlen=int(SAMPLE_SIZE_MS / 10)) #10 Hz

#     start = datetime.datetime.now()
#     elapsed_ms = 0
#     last_classified = 0
#     last_classification = "negative"

#     while True:
#         row = [elapsed_ms] + read_sensor()
#         data.append(row)

#         if elapsed_ms - last_classified >= CHECK_TIME_INCREMENT_MS and len(data) == data.maxlen:
#             df = pd.DataFrame(list(data), columns=header)
#             features = pdata.get_model_features(df)
#             features = scaler.transform(np.reshape(features, (1, -1)))
#             prediction = model.predict(features)[0]

#             print(int(elapsed_ms), prediction)
#             if prediction != 'negative':# and last_classification != prediction:
#                 print("========================>", prediction)
#                 # input("press 'Enter' to continue...")
#                 return prediction
#             data.clear()

#             last_classified = elapsed_ms
#             last_classification = prediction

#         elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000

#         if elapsed_ms > max_time * 1000:
#             break

#     return "negative"