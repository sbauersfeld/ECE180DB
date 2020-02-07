import sensor
import process_data
from sklearn import LinearSVC
import panda as pd
import numpy as np
import glob

def extract_data(folder, members):
    label = []
    for m in members:
        start = len(folder + "/" + m) + 1
        for f in glob.glob(folder + "/" + m + "/*.py"):
            gesture = f[start:-3]
            label.append(gesture)
            trace 

    return label

