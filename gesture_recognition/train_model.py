#!/home/pi/berryconda3/bin/python3

import process_data as data
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
import pandas as pd
import glob

def extract_data(folder, members, gestures=["pass", "reload", "shoot"]):
	label = []
	feature = []
	for m in members:
		for g in gestures:
			for f in sorted(glob.glob(folder + "/" + m + "/" + g + "/*csv")):
				label.append(g)
				trace = pd.read_csv(f, header=0, index_col="time_ms")
				trace = trace.apply(pd.to_numeric, errors="coerce")
				print(trace["Accel_y"])
				temp_featrue = data.get_model_features(trace)
				feature.append(temp_featrue)

	return feature, label 


feature, label = extract_data("training_data", ["wilson"])
scaler = StandardScaler()
scaler.fit(feature)
feature = scaler.transform(feature)
print(feature)


