#!/home/pi/berryconda3/bin/python3
# duration = 1.5s
# starting position for all gestures: hand right next to hips
# Gestures:
# 	shoot: extend arm forward
# 	shield: bent both arms with hand pointing upwards (moving just the arm with the sensor is enough)
# 	reload: move hand behind butt

import time
import datetime
import os
import matplotlib
from sensor import *
matplotlib.use('Agg') # for rpi OS
import matplotlib.pyplot as plt
plt.subplots_adjust(hspace = 0.5)
import glob


###############################################################################
###					create/locate directory for storing data 				###
###############################################################################
member_name = input("Enter name: ")
parent_dir = "data_plots/" + member_name
if not os.path.exists(parent_dir):
	os.mkdir(parent_dir + '/')
filename = input("Name the gesture that will be traced: ")
path = os.path.join(parent_dir, filename)
if not os.path.exists(path):
  os.mkdir(path + '/')

###############################################################################
###									setup 									###
###############################################################################
duration_s = float(input("Sensor trace duration: "))

#look for gestures latest index
file_list = glob.glob(path + '/*.png')
if not file_list:
	starting_index = 0
else:
	newest_file = max(file_list)
	starting_index = int(newest_file[-12:-9]) + 1

IMU.detectIMU()     #Detect if BerryIMUv1 or BerryIMUv2 is connected.
IMU.initIMU()       #Initialise the accelerometer, gyroscope and compass

###############################################################################
###									tracing 								###
###############################################################################
sensor_data = [0,0,0,0,0,0,0,0,0]
index = starting_index
while True:
	input("Trace for " + filename + "{0:03d}".format(index) + "\nPress 'Enter' to start tracing...")
	start = datetime.datetime.now()
	elapsed_ms = 0

	# Create list of for each sensor and each sensor has a list of their corresponding axis values
	data = [[] for i in range(len(sensor_data))]
	time = []

	while elapsed_ms < duration_s * 1000:
		print("tracing...")

		sensor_data = read_sensor()

		for i in range(len(sensor_data)):
			data[i].append(sensor_data[i])
		time.append(elapsed_ms)
		elapsed_ms = (datetime.datetime.now() - start).total_seconds() * 1000

	# save or discard or exit or save and exit
	print("\nTracing finished:")
	while True:
		key = input("\n(d)  --> discard plot\n(s)  --> save plot\n(e)  --> exit\n(se) --> save and exit\n")
		if key is "e": # exit
			exit(0)
		elif key[0] is "s": # save plot
			sensors = ["Accelerometer", "Gyroscope", "Magnetometer"]
			axis = ['x', 'y', 'z']
			for i in range(len(sensors)):
				for j in range(len(axis)): # for x,y,z axis
					plt.plot(time, data[i * len(axis) + j], label=axis[j])
					plt.title(sensors[i])
				plt.xlabel("Time [ms]")
				plt.grid()
				plt.legend()
				file_name = filename + "{0:03d}_".format(index) + sensors[i][:4] + ".png"
				file_name = os.path.join(path, file_name)
				plt.savefig(file_name)
				plt.cla()
			
			index += 1
			print("Trace saved")
			if len(key) > 1 and key[1] is "e": #exit
				exit(0)
			break
		elif key is "d": # discard plot
			print("Trace discarded")
			break
		else:
			print("Invalid input")
