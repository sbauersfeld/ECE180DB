#!/home/pi/berryconda3/bin/python3
import time
import datetime
import pandas as pd
import collections
from sklearn.externals import joblib
from sensor import *
import process_data as pdata
import numpy as np

#temp
from sklearn.preprocessing import StandardScaler

# model = joblib.load('/home/pi/ECE180DB/gesture_recognition/models/s100_q63model.joblib') 

# IMU.detectIMU()     #Detect if BerryIMUv1 or BerryIMUv2 is connected.
# IMU.initIMU()       #Initialise the accelerometer, gyroscope and compass

# CHECK_TIME_INCREMENT_MS = 200
# SAMPLE_SIZE_MS = 1500

# header = ["time_ms"] + pdata.get_header()
# data = collections.deque(maxlen=int(SAMPLE_SIZE_MS / 10)) #10 Hz

# input("Press any key to start...")
# print('Starting operation')

# start = datetime.datetime.now()
# elapsed_ms = 0
# last_classified = 0
# last_classification = "negative"

# while True:
#   row = [elapsed_ms] + read_sensor()
#   data.append(row)

#   if elapsed_ms - last_classified >= CHECK_TIME_INCREMENT_MS and len(data) == data.maxlen:
#     df = pd.DataFrame(list(data), columns=header)
#     features = pdata.get_model_features(df)
#     prediction = model.predict([features])[0]

#     print(int(elapsed_ms), prediction)
#     if prediction != 'negative':# and last_classification != prediction:
#         #print("========================>", prediction)
#         #input("press 'Enter' to continue...")
#         data.clear()

#     last_classified = elapsed_ms
#     last_classification = prediction

#   elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000

#   #if elapsed_ms > 10000:
#   #  break

model = joblib.load('models/wilson/model.joblib') 
scaler = joblib.load('models/wilson/scaler.joblib') 

IMU.detectIMU()     #Detect if BerryIMUv1 or BerryIMUv2 is connected.
IMU.initIMU()       #Initialise the accelerometer, gyroscope and compass

duration_s = float(input("Sensor trace duration: "))

header = ["time_ms"] + pdata.get_header()

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

	print(len(data))
	df = pd.DataFrame(data, columns=header)
	features = pdata.get_model_features(df)
	features = scaler.transform(np.reshape(features, (1, -1)))
	prediction = model.predict(features)[0]
	print(prediction)

def GetGesture(scaler, model):
  duration_s = 1.5
  start = datetime.datetime.now()
  elapsed_ms = 0
  data = []

  while elapsed_ms < duration_s * 1000:
	  row = [elapsed_ms] + read_sensor()
	  data.append(row)
	  elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000

  df = pd.DataFrame(data, columns=header)
  features = pdata.get_model_features(df)
  features = scaler.transform(np.reshape(features, (1, -1)))
  prediction = model.predict(features)[0]
  return prediction