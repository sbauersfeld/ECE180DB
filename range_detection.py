import numpy as np
import cv2
import imutils

def filter_color(frame):
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

	lower_red = np.array([30,150,100])
	upper_red = np.array([255,255,225])
	mask = cv2.inRange(hsv, lower_red, upper_red)

	res = cv2.bitwise_and(frame, frame, mask=mask)
	return res
 
def find_marker(image):
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (15, 15), 0)
 
	cnts = cv2.findContours(gray.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	if len(cnts) == 0:
		return [], []

	c = max(cnts, key = cv2.contourArea)
	return cv2.minAreaRect(c), c
	
# initialize the known object width
KNOWN_HEIGHT = 4.0

FPS = 30 # is this true?
INIT_TIME = 10 # seconds
INIT_COUNT = FPS * INIT_TIME

focalLength = 500 #precomputed

cap = cv2.VideoCapture(0)
idx = 0
init_pixels = np.zeros(INIT_COUNT)
while(True):
	idx += 1
	ret, frame = cap.read()

	filtered_frame = filter_color(frame)
	marker, cnt = find_marker(filtered_frame)

	if len(marker) != 0:
		box = cv2.cv.BoxPoints(marker) if imutils.is_cv2() else cv2.boxPoints(marker)
		box = np.int0(box)
		cv2.drawContours(filtered_frame, [box], -1, (0, 255, 0), 2)

		measured_height = marker[1][1]
		# print(measured_height)

		dist = (KNOWN_HEIGHT * focalLength) / measured_height
		print("distance:", dist)

	cv2.imshow('frame', filtered_frame)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		break

cap.release()
cv2.destroyAllWindows()