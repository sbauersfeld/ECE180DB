import numpy as np
import cv2
import imutils

def filter_color(frame):
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

	# lower_red = np.array([30,150,50])
	# upper_red = np.array([255,255,180])
	lower_red = np.array([0,125,50])
	upper_red = np.array([10,255,200])
	mask0 = cv2.inRange(hsv, lower_red, upper_red)

	# upper mask (170-180)
	lower_red = np.array([170,125,50])
	upper_red = np.array([180,255,200])
	mask1 = cv2.inRange(hsv, lower_red, upper_red)

	# join my masks
	mask = mask0 + mask1

	res = cv2.bitwise_and(frame, frame, mask=mask)
	return res
 
def find_marker(image):
	# convert the image to grayscale, blur it, and detect edges
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (5, 5), 0)
	edged = cv2.Canny(gray, 35, 125)
 
	# find the contours in the edged image and keep the largest one;
	# we'll assume that this is our piece of paper in the image
	cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	c = max(cnts, key = cv2.contourArea)
 
	# compute the bounding box of the of the paper region and return it
	return cv2.minAreaRect(c)

# dark_red  = np.uint8([[[12,22,121]]])
# dark_red = cv2.cvtColor(dark_red,cv2.COLOR_BGR2HSV)

def distance_to_camera(knownWidth, focalLength, perWidth):
	# compute and return the distance from the maker to the camera
	return (knownWidth * focalLength) / perWidth

# initialize the known distance from the camera to the object
KNOWN_DISTANCE = 12.0
	
# initialize the known object width
KNOWN_WIDTH = 9.5

focalLength = (450 * KNOWN_DISTANCE) / KNOWN_WIDTH

cap = cv2.VideoCapture(0)
while(True):
	# Capture frame-by-frame
	ret, frame = cap.read()

	# Our operations on the frame come here
	filtered_frame = filter_color(frame)
	marker = find_marker(filtered_frame)
	box = cv2.cv.BoxPoints(marker) if imutils.is_cv2() else cv2.boxPoints(marker)
	box = np.int0(box)
	cv2.drawContours(filtered_frame, [box], -1, (0, 255, 0), 2)
	# print(marker[1][0])
	# print(distance_to_camera(KNOWN_WIDTH, focalLength, marker[1][0]))
	# exit(1)

	# Display the resulting frame
	cv2.imshow('frame', filtered_frame)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()