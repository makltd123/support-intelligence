import numpy as np
from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient
import pandas as pd
from qdrant_client.models import PointStruct, VectorParams, Distance
import time

load_dotenv()

api_key = os.environ["QDRANT_API_KEY"]
url = os.environ["QDRANT_URL"]

qdrant_client = QdrantClient(api_key=api_key, url=url, timeout=60)

df=pd.read_csv("data/sample_10k.csv", usecols=["issue_description", "category", "resolution_notes", "status", "priority", "customer_satisfaction_score"])
embeddings=np.load('data/embeddings.npy', allow_pickle=True)

if not qdrant_client.collection_exists("support_tickets"):
    qdrant_client.create_collection(
        collection_name="support_tickets",
        vectors_config=VectorParams(size=len(embeddings[0]), distance=Distance.COSINE),
    )

batch_size = 50
start_from = 0  # если загрузка прервалась, поставь номер, с которого продолжить
for i in range(start_from, len(embeddings), batch_size):
    batch = [
        PointStruct(
            id=idx,
            vector=embeddings[idx],
            payload={
                "text": df["issue_description"].iloc[idx],
                "category": df["category"].iloc[idx],
                "resolution_notes": df["resolution_notes"].iloc[idx],
                "status": df["status"].iloc[idx],
                "priority": df["priority"].iloc[idx],
                "customer_satisfaction_score": df["customer_satisfaction_score"].iloc[idx].item(),
            }
        )
        for idx in range(i, min(i + batch_size, len(embeddings)))
    ]
    qdrant_client.upsert(collection_name="support_tickets", points=batch)
    time.sleep(1)
    print(f"Загружено: {min(i + batch_size, len(embeddings))}/{len(embeddings)}")

print("Загружено векторов:", len(embeddings))