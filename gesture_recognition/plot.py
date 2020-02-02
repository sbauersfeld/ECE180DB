#!/home/pi/berryconda3/bin/python3
import time
import datetime
import os
import matplotlib
matplotlib.use('Agg') # for rpi OS
import matplotlib.pyplot as plt
plt.subplots_adjust(hspace = 0.5)


###############################################################################
###					create/locate directory for storing data 				###
###############################################################################
parent_dir = "data_plots"
if not os.path.exists(parent_dir):
	os.mkdir(parent_dir + '/')
filename = input("Name the gesture that will be traced: ")
path = os.path.join(parent_dir, filename)
if not os.path.exists(path):
  os.mkdir(path + '/')

###############################################################################
###									setup 									###
###############################################################################
starting_index = int(input("Starting index: "))
duration_s = int(input("Sensor trace duration: "))
sensor_data = [0,0,0,0,0,0,0,0,0]

###############################################################################
###									tracing 								###
###############################################################################
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

		#TODO: track sensor values
			# sensor returns list gyro(x/y/z), accl(x/y/z), mag(x/y/z)
		for i in range(len(sensor_data)):
			sensor_data[i] += i
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
			sensors = ["Gyroscope", "Accelerometer", "Magnetometer"]
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
			if key[1] is "e": #exit
				exit(0)
			break
		elif key is "d": # discard plot
			print("Trace discarded")
			break
		else:
			print("Invalid input")