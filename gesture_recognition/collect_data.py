#!/home/pi/berryconda3/bin/python3
import time
import datetime
import pandas as pd
import os
from sensor import *

datatype = "training" # set datatype to 'test/training' for test/training data

###############################################################################
###					create/locate directory for storing data 				###
###############################################################################
member_name = input("Enter name: ")
parent_dir = datatype + "_data/" + member_name # change to test_data for testing data
if not os.path.exists(parent_dir):
	os.mkdir(parent_dir + '/')
filename = input("Name the folder where the data will be stored: ")
path = os.path.join(parent_dir, filename)
if not os.path.exists(path):
  os.mkdir(path + '/')

###############################################################################
###									setup 									###
###############################################################################
header = ["time_ms", "delta_ms"]
for sensor in ["Accel", "Gyro", "Mag"]:
	header.append(sensor + "_x")
	header.append(sensor + "_y")
	header.append(sensor + "_z")

starting_index = int(input("Starting index: "))
duration_s = int(input("Sensor trace duration: "))
IMU.detectIMU()     #Detect if BerryIMUv1 or BerryIMUv2 is connected.
IMU.initIMU()       #Initialise the accelerometer, gyroscope and compass
sensor_data = [0,0,0,0,0,0,0,0,0]

###############################################################################
###									tracing 								###
###############################################################################
index = starting_index
while True:
	input("Trace for " + filename + "{0:03d}".format(index) + "\nPress 'Enter' to start tracing...")
	start = datetime.datetime.now()
	elapsed_ms = 0
	previous_elapsed_ms = 0
	data = []

	while elapsed_ms < duration_s * 1000:
		print("tracing...")

		sensor_data = read_sensor()
		row = [elapsed_ms, elapsed_ms - previous_elapsed_ms]
		row.extend(sensor_data)
		data.append(row)
		previous_elapsed_ms = elapsed_ms
		elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000

	# save or discard or exit or save and exit
	print("\nTracing finished:")
	while True:
		key = input("\n(d)  --> discard recorded trace\n(s)  --> save recorded trace\n(e)  --> exit\n(se) --> save and exit\n")
		if key is "e": # exit
			exit(0)
		elif key[0] is "s": # save tracing
			file_name = filename + "{0:03d}".format(index) + ".csv"
			file_name = os.path.join(path, file_name)
			df = pd.DataFrame(data, columns = header)
			df.to_csv(file_name, header=True)
			index += 1
			print("Trace saved")
			if key[1] is "e":
				exit(0)
			break
		elif key is "d": # discard tracing
			print("Trace discarded")
			break
		else:
			print("Invalid input")
# while True:
#   input("Collecting file " + str(i)+ ". Press Enter to continue...")
#   start = datetime.datetime.now()
#   elapsed_ms = 0
#   previous_elapsed_ms = 0
#
#   data = []
#   while elapsed_ms < duration_s * 1000:
#     # sys, gyro, accel, mag = bno.get_calibration_status()
#     vector = bno._read_vector(BNO055.BNO055_ACCEL_DATA_X_LSB_ADDR, 22)
#
#     accel = [s / 100. for s in vector[:3]]
#     mag = [s / 16. for s in vector[3:6]]
#     gyro = [s / 900. for s in vector[6:9]]
#     euler = [s / 16. for s in vector[9:12]]
#     quaternion = [s / QUATERNION_SCALE for s in vector[12:16]]
#     lin_accel = [s / 100. for s in vector[16:19]]
#     gravity = [s / 100. for s in vector[19:22]]
#
#     row = [elapsed_ms, int(elapsed_ms - previous_elapsed_ms)] # heading, roll, pitch, sys, gyro, accel, mag]
#     row += accel + mag + gyro + euler + quaternion + lin_accel + gravity
#
#     data.append(row)
#     previous_elapsed_ms = elapsed_ms
#     elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000



# while True:
# 	try:
# 		input("Trace for " + filename + "{0:03d}".format(index) + "\nPress 'Enter' to start tracing...")
# 		start = datetime.datetime.now()
# 		elapsed_ms = 0
# 		previous_elapsed_ms = 0
# 		data = []
# 		while True:
# 			print("tracing...")
# 			row = [elapsed_ms, elapsed_ms - previous_elapsed_ms, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# 			data.append(row)
# 			previous_elapsed_ms = elapsed_ms
# 			elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000
# 	except KeyboardInterrupt:
# 		key = input("\nTracing stopped:\n(d) --> discard recorded trace\n(s) --> save recorded trace\n(e) --> exit\n")
# 		if key is "e": # exit
# 			exit(0)
# 		elif key is "s": # save tracing
# 			file_name = filename + "{0:03d}".format(index) + ".csv"
# 			file_name = os.path.join(path, file_name)
# 			df = pd.DataFrame(data, columns = header)
# 			df.to_csv(file_name, header=True)
# 			index += 1
# 			print("trace saved")
# 		elif key is "d": # discard tracing
# 			print("trace discarded")