import os
import pickle
import warnings
import numpy as np
from sklearn.mixture import GaussianMixture as GMM
from scipy.io.wavfile import read
from extract_features import extract_features

warnings.filterwarnings("ignore")

# set filepath
model = "Models/"
train_data = "TrainingData"
file_paths = []


def get_file_paths():
    for root, dirs, files in os.walk(train_data):
        speaker_file_paths = []
        for file in files:
            speaker_file_paths.append(os.path.join(root, file))
        if speaker_file_paths != []:
            file_paths.append(speaker_file_paths)


def train_model():
    for files in file_paths:
        # Each speaker will have 1 features array
        features = np.asarray(())
        for filepath in files:
            print("Training: " + filepath)
            try:
                sr, audio = read(filepath)
                vector = extract_features(audio, sr)
            except Exception as e:
                print(e)
                continue

            if features.size == 0:
                features = vector
            else:
                try:
                    features = np.vstack((features, vector))
                except:
                    print("ValueError: Shape does not match")

        # gmm
        gmm = GMM(n_components=16, max_iter=200, covariance_type='diag', n_init=3)
        gmm.fit(features)

        # export trained model
        picklefile = model + os.path.basename(filepath).split('_')[0] + ".gmm"
        with open(picklefile, 'wb') as gmm_file:
            pickle.dump(gmm, gmm_file)

        print('successfully modeling for speaker:', picklefile, " with data point = ", features.shape)


if __name__ == '__main__':
    try:
        os.mkdir(model)
    except:
        pass

    get_file_paths()

    train_model()
