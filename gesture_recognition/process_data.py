import numpy as np
from sklearn.preprocessing import Normalizer

def get_header():
    header = []
    for sensor in ["Accel", "Gyro", "Mag"]:
        header.append(sensor + "_x")
        header.append(sensor + "_y")
        header.append(sensor + "_z")
    return header

def get_features(series):
    features = []
    transformer = Normalizer().fit([series])
    series = transformer.transform([series])[0]

    features.append(max(series))
    features.append(min(series))
    features.append(max(series) - min(series))
    features.append(series.mean())
    features.append(series.std())

    return features


def get_model_features(trace):
    features = []
    for sensor in ["Accel", "Gyro", "Mag"]:
        for axis in ["_x", "_y", "_z"]:
            features.extend(get_features(trace[sensor + axis]))

    return features

# def get_model_features(trace):
#     # features = []
#     # # normalize
#     # trace["Accel"] = np.linalg.norm(
#     #     (trace["Accel_x"], trace["Accel_y"], trace["Accel_z"]),
#     #     axis=0)
#     # trace["Gyro"] = np.linalg.norm(
#     #     (trace["Gyro_x"], trace["Gyro_y"], trace["Gyro_z"]),
#     #     axis=0)
#     # trace["Mag"] = np.linalg.norm(
#     #     (trace["Mag_x"], trace["Mag_y"], trace["Mag_z"]),
#     #     axis=0)

#     # for sensor in ["Accel", "Gyro", "Mag"]:
#     #     features.extend(get_features(trace[sensor]))
#     features = []
#     for sensor in ["Accel", "Gyro", "Mag"]:
#         for axis in ["_x", "_y", "_z"]:
#             features.extend(get_features(trace[sensor + axis]))

#     return features
