'''
DO NOT DELETE:
exec(open("main.py").read()) --> to run this program from shell
'''

import time
import datetime
import serial
import socket
import math
import numpy as np
import os
import django
import sys

from gps.GPS import GPSInit, saveCoor, processCoordinates, calcVelGPS
from communication.sendUDP import initSocket, sendPacket, killSocket
from altimeter.altitudeCalculation import altitudeCalc
import acceleration
from serialStuff import openSerialPort, readFromSerial
from DataObject import DataObject

# exec(open("main.py").read())
from graphs.models import Telemetry, IsLive, TimeInit
##Initiate variables
DEBUG = True
FIRST = True
oldGPSTime = 0
GPSInit()
myData = DataObject()
dropped = 0

lat2 = 0
lon2 = 0
GPSInit()
velocity = np.matrix([0, 0, 0]).T
position = np.matrix([0, 0, 0]).T

#TODO function for dynamicaly assessing calibration constants
ACCX_CALIB = 0
ACCY_CALIB = 0
ACCZ_CALIB = 0

#set positions of data in incoming csv packet
TIMESTAMP = 0
ACCELX = 1
ACCELY = 2
ACCELZ = 3
GYROX = 4
GYROY = 5
GYROZ = 6
GPSLAT = 7
GPSLONG = 8
GPSALT = 9
GPSHR = 10
GPSMIN = 11
GPSSEC = 12
TEMP = 13
PRESSURE = 14
ALTITUDE = 15
BAROTEMP = 16

tots_not_launch = 1
count = 0

# --------------------------------------------- * * * ---------------------------------------------

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reachSentinelLite.settings')
django.setup()

print("\n\n\n")
print(
	'             ||---------------------------- * * * -------------------------\\\\\n'
	'             ||   ______                    _____                           \\\\\n'
	'       ######||   | ___ \           ()     /  ___|                           \\\\\n'
	'  ###########||   | |_/ /_ __ _   _ _ _ __ \ `--. _ __   __  _  ___ ___       \\\\\n'
	"#############||   | ___ \ '__| | | | | '_ \ `--. \ '_ \ / _\| |/ __/ _ \       \\\\\n"
	'   ##########||   | |_/ / |  | |_| | | | | /\__/ / |_) | (_ | | (__| __/       //\n'
	'        #####||   \____/|_|   \__,_|_|_| |_\____/| .__/ \__/|_|\___\___|      //\n'
	'      #######||                                  | |                         //\n'
	'             ||                                  |_|                        //\n'
	'             ||---------------------------- * * * -------------------------//\n')

print("\n\n\n")

# Dabatase checks
if TimeInit.objects.count() != 0:
	for elem in IsLive.objects.all():
		elem.delete()

TimeInit.objects.create()

if Telemetry.objects.count() != 0:
	for elem in Telemetry.objects.all():
		elem.delete()

if Telemetry.objects.count() == 0:
	Telemetry.objects.create()  # zero data-point
	if (DEBUG):
		exec(open("dummyTelem.py").read())
		print("READ dummyTelem.py")

if IsLive.objects.count() != 0:  # ------------------ * * * ------------------ REQUIRES TESTING
	for elem in IsLive.objects.all():
		elem.delete()

# ----------------- * * * ----------------- INITIALLY FALSE, ON BUTTON-CLICK IN DASH, TRUE
downlink = IsLive.objects.create()

try:
	print("Opening Serial Port...")
	#initiate serial port to read data from
	SERIAL_PORT = '/dev/cu.usbmodem14101'  # '/dev/cu.usbmodem14321'
	ser = serial.Serial(
	    port=SERIAL_PORT,
	    baudrate=9600,
	    timeout=3,                         # give up reading after 3 seconds
	    parity=serial.PARITY_ODD,
	    stopbits=serial.STOPBITS_TWO,
	    bytesize=serial.SEVENBITS
	)
	print("connected to port " + SERIAL_PORT)
except Exception as ex:
	print("<== Error connecting to " + SERIAL_PORT + " ==>")
	print(ex)
	sys.exit(1)

##create plain text file to save raw data as backup for database
date = str(datetime.datetime.now())
FILENAME = 'Raw_Data/' + date
FILENAME = FILENAME.replace(':', '_')
FILENAME += '.csv'
txtfile = open(FILENAME, "w")
txtfile.write('Project Reach Raw Data starting at ' + date + '\n')

print('Telemetry initiated')

isFirst = True
dataString = ''  # --------------------- * * * ----------------------------------- EDIT!!!
# myData.calibrate(ser, txtfile, [ACCELX, ACCELY, ACCELZ])

##Main Processing Loop
while ser.isOpen():
	try:
		#get data
		print('reading...')
		dataString = ser.readline().decode()
		print(dataString)
		'''
		if(dataString == "b''"):
			dropped += 1
		'''
	except:
		print("could not read")
		continue

	try:
		print('Writing to textfile')
		txtfile.write(dataString)
		txtfile.flush()
	except:
		pass

	try:
		dataString = dataString[2:len(dataString)-5]
		print('Received: ' + dataString)
		data = dataString.split(",")
		#had problems with only reading in a few data
		if (len(data) < 6):
			print("not enough data")
			continue

		#adjust for NANs
		print('Checking for NANs')
		nans = 0
		for i in range(len(data)):
			if "NAN" in data[i]:
				data[i] = float('nan')
				nans += 1
				continue
			data[i] = float(data[i])
		print('NANs: ' + str(nans))

		#Populate data object
		print('Populating data object...')
		myData.timestamp = data[TIMESTAMP]
		myData.accel_x = data[ACCELX]
		myData.accel_y = data[ACCELY]
		myData.accel_z = data[ACCELZ]
		myData.gyro_x = data[GYROX]
		myData.gyro_y = data[GYROY]
		myData.gyro_z = data[GYROZ]
		myData.gps_lat = data[GPSLONG]
		myData.gps_lon = data[GPSLAT]
		myData.gps_alt = data[GPSALT]
		myData.gps_hour = data[GPSHR]
		myData.gps_min = data[GPSMIN]
		myData.gps_sec = data[GPSSEC]
		myData.temp = data[TEMP]
		myData.press = data[PRESSURE]
		myData.altitude = data[ALTITUDE]
		myData.baro_temp = data[BAROTEMP]
		#myData.mag_x = data[MAGX]
		#myData.mag_y = data[MAGY]
		#myData.mag_z = data[MAGZ]
		#myData.mag_head = data[MAGHEAD]

		print(data)

		# if (isFirst):
		# 	TimeInit.objects.get().timeInit = datetime.datetime.now() - data[TIMESTAMP]
		# 	isFirst = False

		print("Timestamp:", data[TIMESTAMP])

		print('--------')

		new_data = Telemetry.objects.create(  # -------------- * * * -------------- SAVE TO DATABASE
                    timestamp=data[TIMESTAMP],
                    accel_x=data[ACCELX],
                    accel_y=data[ACCELY],
                    accel_z=data[ACCELZ],
                    gyro_x=data[GYROX],
                    gyro_y=data[GYROY],
                    gyro_z=data[GYROZ],
                    barometer=data[ALTITUDE],
                    temp=data[TEMP]
		)
		new_data.save()

		#for the first few iterations, just take the
		#accelerometer data to calibrate the offsets

		if(count < 6):
			print('Calibrating...')
			myData.accx_calib += myData.accel_x
			myData.accy_calib += myData.accel_y
			myData.accz_calib += myData.accel_z
			count += 1
			#establish spacecraft time
			oldtime = myData.timestamp

		else:
			print('processing...')
			if(count == 6):
				myData.accx_calib = myData.accx_calib/6
				myData.accy_calib = myData.accy_calib/6
				myData.accz_calib = myData.accz_calib/6
				count += 1
				myData.printCalibration()
				#print('Calibration: ' + str(ACCX_CALIB) + ', ' + str(ACCY_CALIB) + ', ' + str(ACCZ_CALIB))

			##DO STUFF WITH DATA
			#establish time elapsed
			dt = (myData.timestamp - oldtime)/1000.0  # convert ms to s
			oldtime = myData.timestamp
			print(str(dt))
			'''
			append altitude calculated from pressure
			data.append(altitudeCalc(data[1]))
			'''
			#process acceleration
			acceleration.findInertialFrameAccel(myData, dt)
			#myAcceleration = acceleration.findInertialFrameAccel(data[ACCELX], data[ACCELY], data[ACCELZ], data[GYROX], data[GYROY], data[GYROZ], dt, [ACCX_CALIB, ACCY_CALIB, ACCZ_CALIB])
			print('found acceleration')
			#integrate to find velocity and positino
			acceleration.calculateVelocityAndPosition(myData, dt)
			print('found vel and pos')
			#Process GPS coordinates
			if myData.gps_sec != oldGPSTime:
				processCoordinates(myData.timestamp, myData.gps_lon,
				                   myData.gps_lat, myData.gps_alt)
				print('processed coordinates')
			'''
			#append absolute time
			data.append(time.time())
			'''
			finalData = ""
			for i in range(len(data)-1):
				#print data[i]
				finalData = finalData + str(data[i]) + ", "
				'''
				finalData contents should be as follows, 
				as a string separated by commas:
				relative spacecraft time 
				raw accelX
				raw accelY
				raw accelZ
				gyroX
				gyroY
				gyroZ
				magX - NO
				magY - NO
				magZ - NO
				magHead - NO
				temp(C)
				altitude
				inertial accelX
				inertial accelY
				inertial accelZ
				velX
				velY
				velZ
				posX
				posY
				posZ
				absTime - NO
				'''
			print(finalData)
			myData.printData()
			print(dropped)
	except Exception as e:
		print('failed\n', e)
		print(dropped)
		continue  # maybe this should be a continue?
		######SAVE TO DATABASE

	#TODO -- might actually want to implement the data object.
	#At this point it's confusing where the processed data ends up
	'''
	try:
		new_data = Telemetry.objects.create(  #-------------- * * * -------------- SAVE TO DATABASE
			timestamp=myData.timestamp, 
			accel_x=data[6], 
			accel_y= data[7], 
			accel_z= data[8], 
			gyro_x=data[3], 
			gyro_y=data[4], 
			gyro_z= data[5],
			barometer=data[1],
			temp=data[2])
		new_data.save()

	'''
