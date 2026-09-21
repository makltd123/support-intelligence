from base_agent import get_embedding, text_vectors, format_context, client

chat_model = "mistral-small-2506"


def analyze(question):
    hits = text_vectors(question)
    context = format_context(hits)

    response = client.chat.complete(
        model="mistral-small-2506",
        messages=[
            {"role": "system", "content": """Ты эмпат с глубоким эмоциональным интеллектом. Анализируй тональность(эмоциональный окрас) текста клиента, используй 3 категории: позитивный, нейтральный, негативный. Не выдумывай. Отвечай на русском. ВАЖНО: Используй ТОЛЬКО данные из предоставленных тикетов.
Если цифры или факты не встречаются в тикетах — не упоминай их.
Всегда указывай номер тикета как источник: (Тикет 3), (Тикеты 1, 5, 12)."""},
            {"role": "user", "content": f"Вопрос: {question}\n\nТикеты:\n{context}"}
        ],
    )
    
    return response.choices[0].message.content

if __name__ == "__main__":
    print(analyze("В каких категориях клиенты наиболее негативны?"))