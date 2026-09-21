from dotenv import load_dotenv
import os
import pandas as pd
from mistralai.client import Mistral
import numpy as np
import time


load_dotenv()

print("старт")

api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-embed"

client = Mistral(api_key=api_key)

df=pd.read_csv("data/sample_10k.csv", usecols=["issue_description"])
print("CSV загружен")

def get_embeddings_by_chunks(data, chunk_size):
    chunks = [data[x : x + chunk_size] for x in range(0, len(data), chunk_size)]
    embeddings_response = []
    for c in chunks:
        result = client.embeddings.create(model=model, inputs=c)
        embeddings_response.append(result)
        time.sleep(3)
        print(f"Батч готов: {len(embeddings_response)}/{len(chunks)}")
    return [d.embedding for e in embeddings_response for d in e.data]
df['embeddings'] = get_embeddings_by_chunks(df['issue_description'].tolist(), 50)

np.save("data/embeddings.npy", df['embeddings'])

print(df.head())

print("CSV загружен, строк:", len(df))
# потом после get_embeddings_by_chunks
print("Эмбеддинги получены:", len(df['embeddings']))
# потом после np.save
print("Файл сохранён")