#!/home/pi/berryconda3/bin/python3
import sys
import IMU

def read_sensor():
	#Read the accelerometer,gyroscope and magnetometer values
	GYRx = IMU.readGYRx()
	GYRy = IMU.readGYRy()
	GYRz = IMU.readGYRz()
	ACCx = IMU.readACCx()
	ACCy = IMU.readACCy()
	ACCz = IMU.readACCz()
	MAGx = IMU.readMAGx()
	MAGy = IMU.readMAGy()
	MAGz = IMU.readMAGz()

	return [ACCx, ACCy, ACCz, GYRx, GYRy, GYRz, MAGx, MAGy, MAGz]

# MAG_LPF_FACTOR = 0.4 	# Low pass filter constant magnetometer
# ACC_LPF_FACTOR = 0.4 	# Low pass filter constant for accelerometer
# ACC_MEDIANTABLESIZE = 9	# Median filter table size for accelerometer. Higher = smoother but a longer delay
# MAG_MEDIANTABLESIZE = 9	# Median filter table size for magnetometer. Higher = smoother but a longer delay

# oldXMagRawValue = 0
# oldYMagRawValue = 0
# oldZMagRawValue = 0
# oldXAccRawValue = 0
# oldYAccRawValue = 0
# oldZAccRawValue = 0

# #Setup the tables for the mdeian filter. Fill them all with '1' so we dont get devide by zero error 
# acc_medianTable1X = [1] * ACC_MEDIANTABLESIZE
# acc_medianTable1Y = [1] * ACC_MEDIANTABLESIZE
# acc_medianTable1Z = [1] * ACC_MEDIANTABLESIZE
# acc_medianTable2X = [1] * ACC_MEDIANTABLESIZE
# acc_medianTable2Y = [1] * ACC_MEDIANTABLESIZE
# acc_medianTable2Z = [1] * ACC_MEDIANTABLESIZE
# mag_medianTable1X = [1] * MAG_MEDIANTABLESIZE
# mag_medianTable1Y = [1] * MAG_MEDIANTABLESIZE
# mag_medianTable1Z = [1] * MAG_MEDIANTABLESIZE
# mag_medianTable2X = [1] * MAG_MEDIANTABLESIZE
# mag_medianTable2Y = [1] * MAG_MEDIANTABLESIZE
# mag_medianTable2Z = [1] * MAG_MEDIANTABLESIZE

# def read_sensor():
# 	# global variables
# 	global MAG_LPF_FACTOR	
# 	global ACC_LPF_FACTOR	
# 	global ACC_MEDIANTABLESIZE
# 	global MAG_MEDIANTABLESIZE

# 	global oldXMagRawValue
# 	global oldYMagRawValue
# 	global oldZMagRawValue
# 	global oldXAccRawValue
# 	global oldYAccRawValue
# 	global oldZAccRawValue

# 	global acc_medianTable1X
# 	global acc_medianTable1Y
# 	global acc_medianTable1Z
# 	global acc_medianTable2X
# 	global acc_medianTable2Y
# 	global acc_medianTable2Z
# 	global mag_medianTable1X
# 	global mag_medianTable1Y
# 	global mag_medianTable1Z
# 	global mag_medianTable2X
# 	global mag_medianTable2Y
# 	global mag_medianTable2Z

# 	############################################### 
# 	#### Apply low pass filter ####
# 	###############################################
# 	MAGx =  MAGx  * MAG_LPF_FACTOR + oldXMagRawValue*(1 - MAG_LPF_FACTOR);
# 	MAGy =  MAGy  * MAG_LPF_FACTOR + oldYMagRawValue*(1 - MAG_LPF_FACTOR);
# 	MAGz =  MAGz  * MAG_LPF_FACTOR + oldZMagRawValue*(1 - MAG_LPF_FACTOR);
# 	ACCx =  ACCx  * ACC_LPF_FACTOR + oldXAccRawValue*(1 - ACC_LPF_FACTOR);
# 	ACCy =  ACCy  * ACC_LPF_FACTOR + oldYAccRawValue*(1 - ACC_LPF_FACTOR);
# 	ACCz =  ACCz  * ACC_LPF_FACTOR + oldZAccRawValue*(1 - ACC_LPF_FACTOR);

# 	oldXMagRawValue = MAGx
# 	oldYMagRawValue = MAGy
# 	oldZMagRawValue = MAGz
# 	oldXAccRawValue = ACCx
# 	oldYAccRawValue = ACCy
# 	oldZAccRawValue = ACCz

# 	######################################### 
# 	#### Median filter for accelerometer ####
# 	#########################################
# 	# cycle the table
# 	for x in range (ACC_MEDIANTABLESIZE-1,0,-1 ):
# 		acc_medianTable1X[x] = acc_medianTable1X[x-1]
# 		acc_medianTable1Y[x] = acc_medianTable1Y[x-1]
# 		acc_medianTable1Z[x] = acc_medianTable1Z[x-1]

# 	# Insert the lates values
# 	acc_medianTable1X[0] = ACCx
# 	acc_medianTable1Y[0] = ACCy
# 	acc_medianTable1Z[0] = ACCz

# 	# Copy the tables
# 	acc_medianTable2X = acc_medianTable1X[:]
# 	acc_medianTable2Y = acc_medianTable1Y[:]
# 	acc_medianTable2Z = acc_medianTable1Z[:]

# 	# Sort table 2
# 	acc_medianTable2X.sort()
# 	acc_medianTable2Y.sort()
# 	acc_medianTable2Z.sort()

# 	# The middle value is the value we are interested in
# 	ACCx = acc_medianTable2X[ACC_MEDIANTABLESIZE//2];
# 	ACCy = acc_medianTable2Y[ACC_MEDIANTABLESIZE//2];
# 	ACCz = acc_medianTable2Z[ACC_MEDIANTABLESIZE//2];



# 	######################################### 
# 	#### Median filter for magnetometer ####
# 	#########################################
# 	# cycle the table
# 	for x in range (MAG_MEDIANTABLESIZE-1,0,-1 ):
# 		mag_medianTable1X[x] = mag_medianTable1X[x-1]
# 		mag_medianTable1Y[x] = mag_medianTable1Y[x-1]
# 		mag_medianTable1Z[x] = mag_medianTable1Z[x-1]

# 	# Insert the latest values
# 	mag_medianTable1X[0] = MAGx
# 	mag_medianTable1Y[0] = MAGy
# 	mag_medianTable1Z[0] = MAGz

# 	# Copy the tables
# 	mag_medianTable2X = mag_medianTable1X[:]
# 	mag_medianTable2Y = mag_medianTable1Y[:]
# 	mag_medianTable2Z = mag_medianTable1Z[:]

# 	# Sort table 2
# 	mag_medianTable2X.sort()
# 	mag_medianTable2Y.sort()
# 	mag_medianTable2Z.sort()

# 	# The middle value is the value we are interested in
# 	MAGx = mag_medianTable2X[MAG_MEDIANTABLESIZE//2];
# 	MAGy = mag_medianTable2Y[MAG_MEDIANTABLESIZE//2];
# 	MAGz = mag_medianTable2Z[MAG_MEDIANTABLESIZE//2];

# 	return [GYRx, GYRy, GYRz, ACCx, ACCy, ACCz, MAGx, MAGy, MAGz]