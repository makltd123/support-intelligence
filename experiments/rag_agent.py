import numpy as np
from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient
from mistralai.client import Mistral
import json

load_dotenv()

api_key = os.environ["QDRANT_API_KEY"]
url = os.environ["QDRANT_URL"]
api_key2 = os.environ["MISTRAL_API_KEY"]
embed_model = "mistral-embed"
chat_model = "mistral-small-2506"

client = Mistral(api_key=api_key2)

qdrant_client = QdrantClient(api_key=api_key, url=url)

def get_embedding(text):
    result = client.embeddings.create(model=embed_model, inputs=[text])
    return result.data[0].embedding

def text_vectors(text):
    query_vector = get_embedding(text)
    hits = qdrant_client.query_points(
    collection_name="support_tickets",
    query=query_vector,
    limit=20
    )
    return hits

def format_context(hits):
    context = ""
    for i, hit in enumerate(hits.points):
        payload = hit.payload
        context += f"""
Тикет {i+1}:
Проблема: {payload['text']}
Категория: {payload['category']}
Приоритет: {payload['priority']}
Оценка: {payload['customer_satisfaction_score']}
Решение: {payload['resolution_notes']}
Статус: {payload['status']}
---
"""
    return context

def analyze(question):
    hits = text_vectors(question)
    context = format_context(hits)

    response = client.chat.complete(
        model="mistral-small-2506",
        messages=[
            {"role": "system", "content": """Ты аналитик поддержки. Отвечай только на основе предоставленных тикетов, не выдумывай. Отвечай на русском."""},
            {"role": "user", "content": f"Вопрос: {question}\n\nТикеты:\n{context}"}
        ],
    )
    
    return response.choices[0].message.content
print(analyze("какие топ проблемы в категории Billing?"))