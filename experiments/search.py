import numpy as np
from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient
from mistralai.client import Mistral

load_dotenv()

api_key = os.environ["QDRANT_API_KEY"]
url = os.environ["QDRANT_URL"]
api_key2 = os.environ["MISTRAL_API_KEY"]
model = "mistral-embed"

client = Mistral(api_key=api_key2)

qdrant_client = QdrantClient(api_key=api_key, url=url)

def get_embedding(text):
    result = client.embeddings.create(model=model, inputs=[text])
    return result.data[0].embedding


query_vector = get_embedding("app crashes when uploading file")
hits = qdrant_client.query_points(
    collection_name="support_tickets",
    query=query_vector,
    limit=5
)
print(hits)