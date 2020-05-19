from sklearn.cluster import KMeans
import hmmlearn.hmm


def load_model(path):
    try:
        model_pkl = open(path, "rb")
        models = pickle.load(model_pkl)
    except:
        raise FileNotFoundError("You don't have any models at this path: ", path)
    return models

kmeans = load_model(os.path.join("models", "kmeans.pkl"))
hmms = load_model(os.path.join("models", "models.pkl"))

