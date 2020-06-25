import os
import pickle
import warnings
import numpy as np
from scipy.io.wavfile import read
from extract_features import extract_features

warnings.filterwarnings("ignore")

# set file path
model_path = "Models/"
test_path  = "TestingData"
file_paths = []


def get_model(path):
    models = {}
    for fname in [fname for fname in os.listdir(path) if fname.endswith('.gmm')]:
        speaker = fname.split('.')[0]
        model = pickle.load(open(os.path.join(path, fname), 'rb'))
        models[speaker] = model
    return models


def get_file_path():
    for root, dirs, files in os.walk(test_path):
        for file in files:
            file_paths.append(os.path.join(root, file))


def test(models):
    error = 0
    total = 0
    print("#########################################################")
    for path in file_paths[:]:
        if os.path.basename(path).split('_')[0] in models.keys():
            sr, audio = read(path)
            vector = extract_features(audio, sr)

            if vector.shape != (0,):
                print(vector.shape)
                total += 1
                log_likelihood = {}
                m = {}
                # Scoring and find the winner with highest score
                for speaker, model in models.items():
                    gmm = model
                    scores = np.array(gmm.score(vector))
                    log_likelihood[speaker] = round(scores.sum(), 3)
                    m[speaker] = scores

                max_log_likelihood = max(log_likelihood.values())
                keys, values = list(log_likelihood.keys()), list(log_likelihood.values())
                winner = keys[values.index(max_log_likelihood)]

                checker_name = os.path.basename(path).split("_")[0]
                if winner != checker_name:
                    error += 1

            print("---------------------------------------------------------")
            print("Processed filemame : %10s" % os.path.basename(path))
            print("Expected speaker   : %10s" % os.path.basename(path).split("_")[0])
            print("Identified speaker : %10s" % winner)
            print("#########################################################")

    accuracy = ((total - error) / total) * 100
    print(" %10s : %7s " % ("ACCURACY   ", round(accuracy, 3)))
    print("#########################################################")


if __name__ == '__main__':
    models = get_model()
    get_file_path()
    test(models)
