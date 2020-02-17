#!/home/pi/berryconda3/bin/python3

import process_data as data
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.externals import joblib
from sklearn.metrics import confusion_matrix
import pandas as pd
import glob
import numpy as np
import os

def extract_data(folder, members, gestures=["reload", "shoot", "block"]):
	label = []
	feature = []
	for m in members:
		for g in gestures:
			for f in sorted(glob.glob(folder + "/" + m + "/" + g + "/*csv")):
				label.append(g)
				trace = pd.read_csv(f, header=0, index_col="time_ms")
				trace = trace.apply(pd.to_numeric, errors="coerce")
				temp_featrue = data.get_model_features(trace)
				feature.append(temp_featrue)

	return feature, label 

###############################################################################
###						Extract features & labels and scaling 				###
###############################################################################
feature, label = extract_data("training_data", ["test"])
print(np.shape(feature))
print(np.shape(label))
scaler = StandardScaler()

###############################################################################
###									Training 								###
###############################################################################
#split data into testing and training set for validation
x_train, x_test, y_train, y_test = train_test_split(feature, label, stratify=label, random_state=0)
scaler.fit(x_train)
x_train = scaler.transform(x_train)
x_test = scaler.transform(x_test)

model = SVC(max_iter=1000)
model.fit(x_train, y_train)

###############################################################################
###							Validation and saving model 					###
###############################################################################
predictions = model.predict(x_test)
print(confusion_matrix(y_test, predictions))
score = model.score(x_test, y_test)
df = pd.concat([pd.Series(predictions), pd.Series(y_test)], axis=1)
df.columns = ["predicted", "actual"]
print(df)
print("Score: ", score)

# Save model if desired
while True:
	key = input("(s) --> save model\n(d) --> discard model\n")
	if key is "s":
		name = input("Enter name: ")
		model_name = input("Enter model name: ")
		scaler_name = input("Enter scaler name: ")
		if not os.path.exists("models/" + name):
			os.mkdir("models/" + name)
		joblib.dump(model, 'models/' + name + "/" + model_name + ".joblib")
		joblib.dump(scaler, 'models/' + name + "/" + scaler_name + ".joblib")
		break
	elif key is "d":
		break
	else:
		print("invalid input")
