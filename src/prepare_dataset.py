from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

df=pd.read_csv("data/customer_support_tickets_200k.csv", usecols=["issue_description", "category", "resolution_notes", "status", "priority", "customer_satisfaction_score"])

sample_df=df.sample(n=10000, random_state=42)

sample_df.to_csv("data/sample_10k.csv", index=False, encoding="utf-8-sig")

total_raws=len(sample_df)
print(f'Количество строк: {total_raws}')
