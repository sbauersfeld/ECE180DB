import numpy as np
import cv2
import imutils

def filter_color(frame):
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

	# lower_red = np.array([30,150,50])
	# upper_red = np.array([255,255,180])
	lower_red = np.array([0,150,100])
	upper_red = np.array([10,255,200])
	mask0 = cv2.inRange(hsv, lower_red, upper_red)

	# upper mask (170-180)
	lower_red = np.array([170,150,100])
	upper_red = np.array([180,255,200])
	mask1 = cv2.inRange(hsv, lower_red, upper_red)

	# join my masks
	mask = mask0 + mask1

	res = cv2.bitwise_and(frame, frame, mask=mask)
	return res
 
def find_marker(image):
	# convert the image to grayscale, blur it, and detect edges
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (3, 3), 0)
	edged = imutils.auto_canny(gray)
 
	# find the contours in the edged image and keep the largest one;
	# we'll assume that this is our piece of paper in the image
	cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	c = max(cnts, key = cv2.contourArea)
 
	# compute the bounding box of the of the paper region and return it
	return cv2.minAreaRect(c), c

# dark_red  = np.uint8([[[12,22,121]]])
# dark_red = cv2.cvtColor(dark_red,cv2.COLOR_BGR2HSV)

def distance_to_camera(knownWidth, focalLength, perWidth):
	# compute and return the distance from the maker to the camera
	return (knownWidth * focalLength) / perWidth

# initialize the known distance from the camera to the object # neopixel from adafruit
KNOWN_DISTANCE = 12.0
	
# initialize the known object width
KNOWN_HEIGHT = 3.0

FPS = 30 # is this true?
INIT_TIME = 2 # seconds
INIT_COUNT = FPS * INIT_TIME

# focalLength = (450 * KNOWN_DISTANCE) / KNOWN_HEIGHT

cap = cv2.VideoCapture(0)
idx = 0
init_pixels = np.zeros(INIT_COUNT)
while(True):
	# Capture frame-by-frame
	ret, frame = cap.read()

	# Our operations on the frame come here
	filtered_frame = filter_color(frame)
	marker, cnt = find_marker(filtered_frame)
	# cv2.drawContours(frame, [cnt], -1, (0, 255, 0), 2)

	box = cv2.cv.BoxPoints(marker) if imutils.is_cv2() else cv2.boxPoints(marker)
	box = np.int0(box)
	cv2.drawContours(frame, [box], -1, (0, 255, 0), 2)

	# min_y, min_x = np.Infinity, np.Infinity
	# max_y, max_x = 0, 0
	# print(box)
	# for point in box:
	# 	min_y = min(min_y, point[1])
	# 	max_y = max(max_y, point[1])
	# 	min_x = min(min_x, point[0])
	# 	max_x = max(max_x, point[0])
	# print(max_y - min_y)

	measured_height = marker[1][1]
	# print(measured_height)

	if idx < INIT_COUNT:
		init_pixels[idx] = measured_height
	elif idx == INIT_COUNT:
		focalLength = np.mean(init_pixels) * KNOWN_DISTANCE / KNOWN_HEIGHT ## TODO: remove calibration stage
		print("focal length:", focalLength)
	else:
		dist = distance_to_camera(KNOWN_HEIGHT, focalLength, measured_height)
		if idx % int(FPS*0.5) == 0:
			print("distance:", dist)

	# Display the resulting frame
	cv2.imshow('frame', frame)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

	idx += 1

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()