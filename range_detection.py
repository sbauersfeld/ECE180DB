import numpy as np
import cv2
 
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

def filter_color(frame):
	lower_red = np.array([30,150,50])
	upper_red = np.array([255,255,180])

	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

	mask = cv2.inRange(hsv, lower_red, upper_red)
	res = cv2.bitwise_and(frame, frame, mask=mask)

def distance_to_camera(knownWidth, focalLength, perWidth):
	# compute and return the distance from the maker to the camera
	return (knownWidth * focalLength) / perWidth

# initialize the known distance from the camera to the object
KNOWN_DISTANCE = 12.0
	
# initialize the known object width
KNOWN_WIDTH = 9.5

focalLength = (450 * KNOWN_DISTANCE) / KNOWN_WIDTH