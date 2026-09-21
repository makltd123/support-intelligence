import os
from mistralai.client import Mistral
from dotenv import load_dotenv
import pandas as pd
import json

load_dotenv()


def analyze_ticket(text, category, priority, cussatscore):
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    response = client.chat.complete(
        model="mistral-small-2506",
        messages=[
            {"role": "system", "content": """You are a customer support analyst with 10 years of experience in digital product support. You analyze support tickets to identify key system issues. If you dont know something, say so directly and never make things up. Respond only in JSON with this exact structure:
{
  "problem_summary": "...",
  "sentiment": "positive/negative/neutral",
  "priority_assessment": "correct/underestimated/overestimated",
  "recommended_action": "..."
}
Return raw JSON only, no markdown, no code blocks, no backticks. Always respond in Russian."""},
            {"role": "user", "content": f"Analyze this customer support ticket: {text}. Category: {category}. Priority: {priority}. Customer Satisfaction Score: {cussatscore}"}
        ],
    )
    
    raw = response.choices[0].message.content
    clean = raw.replace("```json", "").replace("```", "").strip()
    data=json.loads(clean)
    return data


df=pd.read_csv("data/customer_support_tickets_200k.csv", usecols=["issue_description", "category", "priority", "customer_satisfaction_score"])
ticket_text = df["issue_description"].iloc[1] 
ticket_category = df["category"].iloc[1]
ticket_priority = df["priority"].iloc[1]
ticket_cussatscore = df["customer_satisfaction_score"].iloc[1]

result = analyze_ticket(ticket_text, ticket_category, ticket_priority, ticket_cussatscore)
print(result)

