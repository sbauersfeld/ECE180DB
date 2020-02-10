import numpy as np

def get_header():
    header = []
    for sensor in ["Accel", "Gyro", "Mag"]:
        header.append(sensor + "_x")
        header.append(sensor + "_y")
        header.append(sensor + "_z")
    return header

def get_features(series):
    features = []
    features.append(max(series))
    features.append(min(series))
    features.append(max(series) - min(series))
    features.append(series.mean())
    features.append(series.std())
    return features


def get_model_features(trace):
    features = []
    # normalize
    trace["Accel"] = np.linalg.norm(
        (trace["Accel_x"], trace["Accel_y"], trace["Accel_z"]),
        axis=0)
    trace["Gyro"] = np.linalg.norm(
        (trace["Gyro_x"], trace["Gyro_y"], trace["Gyro_z"]),
        axis=0)
    trace["Mag"] = np.linalg.norm(
        (trace["Mag_x"], trace["Mag_y"], trace["Mag_z"]),
        axis=0)

    for sensor in ["Accel", "Gyro", "Mag"]:
        features.extend(get_features(trace[sensor]))

    return features

# def get_model_features(trace, generate_feature_names=False):
#     features = []
#     trace["accel"] = np.linalg.norm(
#         (trace["accel_ms2_x"], trace["accel_ms2_y"], trace["accel_ms2_z"]),
#         axis=0)
#     trace["gyro"] = np.linalg.norm(
#         (trace['gyro_degs_x'], trace['gyro_degs_y'], trace['gyro_degs_z']),
#         axis=0)

#     for sensor in ['accel', 'gyro']:
#         features_temp = get_features(trace[sensor], generate_feature_names)
#         if generate_feature_names:
#             features.extend([x + '_' + sensor for x in features_temp])
#         else:
#             features.extend(features_temp)

#     if generate_feature_names:
#         features.append('accel_z_peaks')
#     else:
#         normalized = min_max_scaler.fit_transform(
#             trace['accel_ms2_z'].values.reshape(-1, 1))[:, 0]  # normalize
#         normalized = normalized[0:len(normalized):5]  # subsample
#         normalized = np.diff(
#             (normalized > 0.77).astype(int))  # convert to binary classifier
#         normalized = normalized[normalized > 0]
#         features.append(sum(normalized))

#     return features
