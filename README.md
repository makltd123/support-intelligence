# AI Customer Support Intelligence

**English** | [Русский](README.ru.md)

[![CI](https://github.com/makltd123/support-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/makltd123/support-intelligence/actions/workflows/ci.yml)

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

- **Synthesizer** is an LLM orchestrator. In a loop it picks which agent to call and answers in JSON. The loop is bounded by a step limit; if the model answers with something other than JSON, asks for a tool that does not exist, or finishes early, the missing sections are filled by calling the agents directly. A three-section report always comes back.
- **Agents** retrieve the 20 tickets closest to the question from the Qdrant vector database. They answer only from the retrieved tickets and cite ticket numbers as sources.
- **The index** is built from a random sample of 10,000 tickets.

## Stack

Python 3.11+ · Mistral AI (`mistral-small-2506`, `mistral-embed`) · Qdrant Cloud · Gradio · reportlab · pandas

## Example report

[docs/example_report.pdf](docs/example_report.pdf) — the answer to "do a full analysis of problems in the authorization category".

To see what the PDF looks like, no keys are needed:

```bash
python examples/demo_report.py   # -> demo_report.pdf
```

## Structure

| File | What it does |
|---|---|
| `src/config.py` | Settings from environment variables, with readable errors when a key is missing |
| `src/fonts.py` | Picks a system TTF with Cyrillic coverage for the PDF |
| `src/prepare_dataset.py` | Takes a random 10,000 tickets from the full dataset |
| `src/embeddings.py` | Embeds ticket texts with `mistral-embed`; resumes after an interrupted run |
| `src/qdrant_upload.py` | Creates the Qdrant collection and uploads the vectors |
| `src/base_agent.py` | Shared helpers: embed the question, search Qdrant, build the context, retry on network failures |
| `src/agent_analyst.py` | "Problems" agent |
| `src/agent_features.py` | "Features" agent |
| `src/agent_sentiment.py` | "Sentiment" agent |
| `src/agent_synthesizer.py` | Orchestrator: calls the agents and assembles the report |
| `src/report_generator.py` | Generates the PDF |
| `src/app.py` | Gradio web UI |
| `examples/` | Synthetic dataset generator and a demo report that needs no keys |
| `tests/` | Test suite (no network required) |
| `experiments/` | Early scripts: single-ticket analysis, first RAG version, search check |

## Running it

Run every command from the project root.

**1. Dependencies**

```bash
python -m venv .venv
source .venv/bin/activate     # Linux / macOS
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

**2. Keys.** Copy `.env.example` to `.env` and fill in:
- `MISTRAL_API_KEY` — a key from [console.mistral.ai](https://console.mistral.ai);
- `QDRANT_URL` and `QDRANT_API_KEY` — the URL and key of a [Qdrant Cloud](https://cloud.qdrant.io) cluster (the free tier is enough).

The other variables are optional; `.env.example` lists them with their defaults.

**3. Data.** The dataset is not included (74 MB). Any CSV with the columns `category`, `issue_description`, `resolution_notes`, `priority`, `status`, `customer_satisfaction_score` works: put it in `data/` as `customer_support_tickets_200k.csv`, or point `DATASET_PATH` at it.

No dataset at hand — generate a synthetic one:

```bash
python examples/make_sample_dataset.py --rows 300
```

**4. Index** (once):

```bash
python src/prepare_dataset.py   # sample 10,000 tickets -> data/sample_10k.csv
python src/embeddings.py        # embeddings -> data/embeddings.npy (about 10–15 minutes)
python src/qdrant_upload.py     # upload to Qdrant
```

`src/embeddings.py` checkpoints its progress, so after an interruption you can simply run it again and it picks up where it stopped.

**5. Analysis**

```bash
python src/app.py               # web UI at http://127.0.0.1:7860
python src/agent_synthesizer.py # or straight to report.pdf for the question set in the code
```

## Tests

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

Tests make no network calls and need no keys. Building a PDF requires a system font with Cyrillic coverage (on Ubuntu: `sudo apt install fonts-dejavu-core`).

## Limitations and things to know

- **Data quality.** The public dataset everything was checked against is synthetic: texts are assembled from templates, many tickets are word-for-word identical, and the category does not always match the description. In the example report all 20 retrieved tickets have the same text. On data like this the agents' conclusions look plausible but mean little.
- **A sample, not a full analysis.** The agents only see the 20 semantically closest tickets, so "top problems" means top within that sample, not across the whole base. Real aggregation needs clustering over the full corpus.
- **No filters.** Category, time period and priority are not used in retrieval — only semantic similarity.
- **Ticket content reaches the prompt.** The agents are explicitly told to treat ticket text as data rather than instructions, but on real customer data that is not complete protection against prompt injection. Personal data in tickets should be anonymized before indexing.
- **Fonts.** The PDF needs a TTF with Cyrillic coverage. The system looks for one itself (DejaVu, Liberation, Arial, Carlito, Noto); the path can be set via `REPORT_FONT_REGULAR`.

## License

[MIT](LICENSE). The code license does not cover the dataset — check the terms of use with its source.
