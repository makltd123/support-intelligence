import numpy as np
embeddings = np.load("data/embeddings.npy", allow_pickle=True)
print("Размер вектора:", len(embeddings[0]))