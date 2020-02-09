#!/home/pi/berryconda3/bin/python3

import process_data as data
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.externals import joblib
import pandas as pd
import glob

def extract_data(folder, members, gestures=["negative", "reload", "shoot", "shield"]):
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
feature, label = extract_data("training_data", ["wilson"])
scaler = StandardScaler()
scaler.fit(feature)
feature = scaler.transform(feature)

###############################################################################
###									Training 								###
###############################################################################
#split data into testing and training set for validation
x_train, x_test, y_train, y_test = train_test_split(feature, label)

model = LinearSVC(max_iter=100000, dual=False)
model.fit(x_train, y_train)

###############################################################################
###							Validation and saving model 					###
###############################################################################
predictions = model.predict(x_test)
print(confusion_matrix(y_test, predictions))

# Save model if desired
score = model.score(x_test, y_test)
print("Score: ", score)
while True:
	key = input("(s) --> save model\n(d) --> discard model\n")
	if key is "s":
		joblib.dump(model, 'models/' + "s" + score + "_q" + len(x_train) + "model.joblib")
		break
	else:
		break




