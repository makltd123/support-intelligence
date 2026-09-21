# AI Customer Support Intelligence

**English** | [Русский](README.ru.md)

A multi-agent RAG system that analyzes customer support tickets and builds a PDF report with three sections: top problems, customer feature requests, and customer sentiment.

The agents' prompts, the web UI and the generated reports are in Russian.

## How it works

```
Question ──► Synthesizer (Mistral) ──┬──► "Problems" agent    ─┐
                                     ├──► "Features" agent    ─┼──► Qdrant: 20 most similar tickets
                                     └──► "Sentiment" agent   ─┘    (mistral-embed embeddings)
                                                   │
                                                   ▼
                                     PDF report + Gradio web UI
```

- **Synthesizer** is an LLM orchestrator. In a loop it picks which agent to call and answers in JSON. The report is done once all three agents have run.
- **Agents** retrieve the 20 tickets closest to the question from the Qdrant vector database. They answer only from the retrieved tickets and cite ticket numbers as sources.
- **The index** is built from a random sample of 10,000 tickets.

## Stack

Python · Mistral AI (`mistral-small-2506`, `mistral-embed`) · Qdrant Cloud · Gradio · reportlab · pandas

## Example report

[docs/example_report.pdf](docs/example_report.pdf) — the answer to "do a full analysis of problems in the authorization category".

## Structure

| File | What it does |
|---|---|
| `src/prepare_dataset.py` | Takes a random 10,000 tickets from the full dataset |
| `src/embeddings.py` | Embeds ticket texts with `mistral-embed` |
| `src/qdrant_upload.py` | Creates the Qdrant collection and uploads the vectors |
| `src/base_agent.py` | Shared helpers: embed the question, search Qdrant, build the context |
| `src/agent_analyst.py` | "Problems" agent |
| `src/agent_features.py` | "Features" agent |
| `src/agent_sentiment.py` | "Sentiment" agent |
| `src/agent_synthesizer.py` | Orchestrator: calls the agents and assembles the report |
| `src/report_generator.py` | Generates the PDF |
| `src/app.py` | Gradio web UI |
| `experiments/` | Early scripts: single-ticket analysis, first RAG version, search check |

## Running it

Run every command from the project root.

**1. Dependencies**

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

**2. Keys.** Copy `.env.example` to `.env` and fill in:
- `MISTRAL_API_KEY` — a key from [console.mistral.ai](https://console.mistral.ai);
- `QDRANT_URL` and `QDRANT_API_KEY` — the URL and key of a [Qdrant Cloud](https://cloud.qdrant.io) cluster (the free tier is enough).

**3. Data.** The dataset is not included (74 MB). Any CSV with the columns `category`, `issue_description`, `resolution_notes`, `priority`, `status`, `customer_satisfaction_score` works: put it in `data/` as `customer_support_tickets_200k.csv`.

**4. Index** (once):

```bash
python src/prepare_dataset.py   # sample 10,000 tickets -> data/sample_10k.csv
python src/embeddings.py        # embeddings -> data/embeddings.npy (about 10–15 minutes)
python src/qdrant_upload.py     # upload to Qdrant
```

**5. Analysis**

```bash
python src/app.py               # web UI at http://127.0.0.1:7860
python src/agent_synthesizer.py # or straight to report.pdf for the question set in the code
```

## Limitations

- The PDF uses the Arial font from `C:/Windows/Fonts`, so reports only build on Windows. On another OS, change the font paths in `src/report_generator.py`.
- The dataset is synthetic: texts are assembled from templates, so many tickets are word-for-word identical and the category does not always match the description. In the example report all 20 retrieved tickets have the same text.
- The synthesizer parses the model's answer as JSON. If the model answers in another format, the run stops with an error.

## License

[MIT](LICENSE)
