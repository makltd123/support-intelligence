from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
api_key=os.getenv("MISTRAL_API_KEY")

df=pd.read_csv("data/customer_support_tickets_200k.csv", usecols=["issue_description", "category", "resolution_notes", "status", "priority", "customer_satisfaction_score"])

total_raws=len(df)
print(f'Количество строк: {total_raws}')

df.head(10)
print(df.head(10))