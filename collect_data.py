# import busio
import time
import datetime
# import pandas as pd
import os

# QUATERNION_SCALE = (1.0 / (1<<14))
# test = 0    # set test to 1 for test data

# i = 0
# header = ["time_ms", "delta_ms"]
# for sensor in ["accel_ms2", "mag_uT", "gyro_degs", "euler_deg", "quaternion", "lin_accel_ms2", "gravity_ms2"]:
#   if sensor is "quaternion":
#     header.append(sensor + "_w")
#   header.append(sensor + "_x")
#   header.append(sensor + "_y")
#   header.append(sensor + "_z")

###############################################################################
###					create/locate directory for storing data 				###
###############################################################################
parent_dir = "training_data" # change to test_data for testing data
filename = input("Name the folder where data will be stored: ")
path = os.path.join(parent_dir, filename)
if not os.path.exists(path):
  os.mkdir(path + '/')
starting_index = int(input("What number should we start on? "))



# duration_s = float(input("Please input how long should a sensor trace be in seconds (floats OK): "))
#
# # TODO: Add option to delete just recorded trace if it's bad
# # TODO: Add option to save notes per recorded trace
# i = starting_index
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
#
#   file_name = filename + "/" + filename + '{0:03d}'.format(i) + ".csv"
#   df = pd.DataFrame(data, columns = header)
#   df.to_csv(file_name, header=True)
#   i += 1