import librosa
import numpy as np
import os
import math
from sklearn.cluster import KMeans
import hmmlearn.hmm
import pickle
import time

def get_mfcc(file_path):
	try:
	    y, sr = librosa.load(file_path) # read .wav file
	    hop_length = math.floor(sr*0.010) # 10ms hop
	    win_length = math.floor(sr*0.025) # 25ms frame
	    # mfcc is 12 x T matrix
	    mfcc = librosa.feature.mfcc(
	        y, sr, n_mfcc=12, n_fft=1024,
	        hop_length=hop_length, win_length=win_length)

	    # energy is 1 x T matrix
	    rms = librosa.feature.rms(y=y, frame_length=win_length, hop_length=hop_length)
	    # substract mean from mfcc --> normalize mfcc

	    # mfcc is 13 x T matrix
	    mfcc = mfcc - np.mean(mfcc, axis=1).reshape((-1,1)) 
	    mfcc = np.concatenate([mfcc, rms], axis=0)
	        
	    # delta feature 1st order and 2nd order
	    delta1 = librosa.feature.delta(mfcc, order=1)
	    delta2 = librosa.feature.delta(mfcc, order=2)
	    # X is 39 x T
	    X = np.concatenate([mfcc, delta1, delta2], axis=0) # O^r
	    # return T x 39 (transpose of X)

	    return X.T # hmmlearn use T x N matrix
	except:
		raise ValueError("File errors, delete it: ", file_path)


def get_class_data(data_dir):
    data_dir = os.path.join('data', data_dir)
    files = os.listdir(data_dir)
    mfcc = [get_mfcc(os.path.join(data_dir,f)) for f in files if f.endswith(".wav")]
    return mfcc

def clustering(X, n_clusters=10):
    kmeans = KMeans(n_clusters=n_clusters, n_init=50, random_state=0, verbose=0)
    kmeans.fit(X)
    print("centers", kmeans.cluster_centers_.shape)
    return kmeans  

#Build state, pi, A for every word
def make_pi(n_state):
    arr = [0.0]*n_state
    #Always start at state 0
    arr[0] = 1.0
    return arr

def make_A(n_state):
    mat = [[0.0]*n_state for i in range(n_state)]
    for i in range(n_state-1):
        mat[i][i] = 0.6
        mat[i][i+1] = 0.4
    mat[n_state-1][n_state-1] = 1.0
    return mat



def main():
	n_states = {
	'khong': 11,
	'vietnam': 24,
	'nguoi': 11,
	'benhvien': 24,
	'trong': 11    
	}
	#Load dataset
	class_names = [f for f in os.listdir('data') if os.path.isdir(os.path.join('data', f))]
	dataset = {}
	for cname in class_names:
	    print(f"-->Load {cname} dataset")
	    dataset[cname] = get_class_data(cname)

	# Get all vectors in the datasets
	all_vectors = np.concatenate([np.concatenate(v, axis=0) for k, v in dataset.items()], axis=0)
	print("vectors", all_vectors.shape)
	# Run K-Means algorithm to get clusters
	kmeans = clustering(all_vectors, n_clusters=35)

	#Train model
	models = {}
	class_vectors = dataset.copy()
	for cname in class_names:
	    # convert all vectors to the cluster index
	    # dataset['one'] = [O^1, ... O^R]
	    # O^r = (c1, c2, ... ct, ... cT)
	    # O^r size T x 1
	    class_vectors[cname] = list([kmeans.predict(v).reshape(-1,1) for v in class_vectors[cname]])
	    if cname[:4] != 'test':
	        hmm = hmmlearn.hmm.MultinomialHMM(
	        n_components=n_states[cname], 
	        random_state=2020, 
	        n_iter=1000, 
	        verbose=False, 
	        init_params='e', params='te',
	        )
	        hmm.startprob_ = np.array(make_pi(n_states[cname]))
	        hmm.transmat_ = np.array(make_A(n_states[cname]))
	        X = np.concatenate(class_vectors[cname])
	        lengths = list([len(x) for x in class_vectors[cname]])
	        print("training class", cname)
	        print(X.shape, lengths, len(lengths))
	        hmm.fit(X, lengths=lengths)
	        models[cname] = hmm
	print("<--Training done-->\n")
	print("-----Testing-----")
	print("Test in Datatrain")
	for test_cname in class_names:
	    cnt = 0
	    if test_cname[:4] != "test":
	        for O in class_vectors[test_cname]:
	            score = {cname : model.score(O, [len(O)]) for cname, model in models.items() if cname[:4] != 'test' }
	            max_value = max(v for k,v in score.items())
	            #print("Max: ", max_value)
	            for k,v in score.items():
	                if v == max_value:
	                    if k== test_cname:
	                        cnt += 1
	            #print(test_cname, score)
	        print(f"{test_cname} -- Score: ", cnt/len(class_vectors[test_cname]))
	print()
	print("Test in Datatest")
	for test_cname in class_names:
	    cnt = 0
	    if test_cname[:4] == "test":
	        for O in class_vectors[test_cname]:
	            score = {cname : model.score(O, [len(O)]) for cname, model in models.items() if cname[:4] != 'test' }
	            max_value = max(v for k,v in score.items())
	            #print("Max: ", max_value)
	            for k,v in score.items():
	                if v == max_value:
	                    predict = k
	                    if predict.strip() == test_cname[5:].strip():
	                        cnt += 1
	            #print(test_cname, score)
	        print(f"{test_cname} -- Score: ", cnt/len(class_vectors[test_cname]))
			
	#Extract models parameters
	with open("Models_parameters.txt", "w") as f:
		for cname, model in models.items():
			f.write(f"Model_name : {cname}\n")
			f.write("Startprob matrix:\n")
			f.write(" ".join(map(str, model.startprob_)))
			f.write("\nTransition Matrix\n")
			f.write(" ".join(map(str, model.transmat_)))
			f.write("\nEmissionProb Matrix\n")
			f.write(" ".join(map(str, model.emissionprob_)))
			f.write("\n\n")
	print("Extracted models to Models_parameters.txt successfully")
	#Save models
	if "models" not in os.listdir():
		os.mkdir("models")
	#Kmeans
	with open(os.path.join("models","kmeans.pkl"), "wb") as f: pickle.dump(kmeans, f)
	print("Saved Kmeans model to 'models/kmeans.pkl' successfully")
	#HMM
	with open(os.path.join("models","models.pkl"), "wb") as f: pickle.dump(models, f)
	print(f"Saved HMMs model to 'models/models.pkl' successfully")

#Run
if __name__ == '__main__':
	ques = input("Do you really want to train??[Y or N]")
	if ques.lower().strip().startswith("y"):
		start_time = time.perf_counter()
		print("--HMMs training for 5 words (Benhvien, khong, nguoi, trong, vietnam)--\n")
		main()
		print(f"Run successfully in {time.perf_counter() - start_time:0.4f} seconds")
	print("Bye bye :)")