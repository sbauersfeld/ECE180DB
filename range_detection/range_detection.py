import sys
import numpy as np
import cv2
import imutils
import time

player_default = ([160,150,150], [180,255,255], 500)
player_map = {
	"scott" : 	player_default,
	"jon" : 	([160,50,50], 	[180,255,255], 1000),
	"wilson" : 	([160,150,150], [180,255,255], 500),
	"jesse" : 	([160,150,150], [180,255,255], 500)
}

def filter_color(frame, settings):
	hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

	lower_red = np.array(settings[0])
	upper_red = np.array(settings[1])
	mask = cv2.inRange(hsv, lower_red, upper_red)

	res = cv2.bitwise_and(frame, frame, mask=mask)
	return res
 
def find_marker(image):
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (9, 9), 0)
 
	cnts = cv2.findContours(gray.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	if len(cnts) == 0:
		return [], []

	c = max(cnts, key = cv2.contourArea)
	return cv2.minAreaRect(c), c

def draw_label(img, text, pos, bg_color):
    font_face = cv2.FONT_HERSHEY_SIMPLEX
    scale = 3
    color = (255, 255, 255)
    thickness = cv2.FILLED
    margin = 2

    txt_size = cv2.getTextSize(text, font_face, scale, thickness)

    end_x = pos[0] + txt_size[0][0] + margin
    end_y = pos[1] - txt_size[0][1] - margin

    cv2.rectangle(img, pos, (end_x, end_y), bg_color, thickness)
    cv2.putText(img, text, pos, font_face, scale, color, 3, cv2.LINE_AA)
	
# initialize the known object width
KNOWN_HEIGHT = 4.0

def GetDistance(cap, settings=player_default, CAP_TIME=1, FPS=30):
	CAP_COUNT = int(FPS * CAP_TIME)
	focalLength = settings[-1]
	pixel_heights = np.zeros(CAP_COUNT)
	limit = 0
	pixel_idx = 0
	for _ in range(CAP_COUNT):
		_, frame = cap.read()

		filtered_frame = filter_color(frame, settings)
		marker, _ = find_marker(filtered_frame)

		if len(marker) != 0:
			pixel_heights[pixel_idx] = marker[1][1]
			limit += 1
			pixel_idx += 1

	if limit == 0:
		return -1
	dist = (KNOWN_HEIGHT * focalLength) / np.median(pixel_heights[:limit])
	return dist

def TestDistance(settings=player_default, display_output=False, cutoff=30, TIMEOUT=None):
	cap = cv2.VideoCapture(0)
	focalLength = settings[-1]
	idx = 0
	label_dist = -1

	if TIMEOUT:
		t_end = time.time() + TIMEOUT
	while(True):
		idx += 1
		_, frame = cap.read()

		filtered_frame = filter_color(frame, settings)
		marker, _ = find_marker(filtered_frame)

		if len(marker) != 0:
			box = cv2.cv.BoxPoints(marker) if imutils.is_cv2() else cv2.boxPoints(marker)
			box = np.int0(box)
			cv2.drawContours(filtered_frame, [box], -1, (0, 255, 0), 2)

			measured_height = marker[1][1]
			dist = (KNOWN_HEIGHT * focalLength) / measured_height
			if idx % cutoff == 0:
				label_dist = round(dist)
				if not display_output:
					print("distance:", dist)

		if display_output:
			draw_label(filtered_frame, str(label_dist), (30,100), (0,0,0))

		cv2.imshow('frame', filtered_frame)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
		if TIMEOUT and time.time() > t_end:
			break

	cap.release()
	cv2.destroyAllWindows()

if __name__ == "__main__":
	name = sys.argv[1] if len(sys.argv) == 2 else "scott"
	settings = player_map.get(name, player_default)
	TestDistance(settings)
