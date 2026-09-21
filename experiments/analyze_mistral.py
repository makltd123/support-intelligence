import os
from mistralai.client import Mistral
from dotenv import load_dotenv
import pandas as pd

load_dotenv()


def analyze_ticket(text):
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    response = client.chat.complete(
        model="mistral-small-2506",
        messages=[
            {"role": "user", "content": f"Analyze this customer support ticket: {text}"}
        ],
    )
    
    return response.choices[0].message.content


df=pd.read_csv("data/customer_support_tickets_200k.csv", usecols=["issue_description"])
ticket_text = df["issue_description"].iloc[1] 

result = analyze_ticket(ticket_text)
print(result)
