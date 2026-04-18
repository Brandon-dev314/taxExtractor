# Fiscal Extractor

A web app that turns messy business documents into clean, structured JSON using OpenAI's API. Built to solve a real problem: accounting teams spend hours pulling data out of informal emails, poorly filled forms, and inconsistent spreadsheets. This app does it in seconds.

## Live demo

[extractor-fiscal.streamlit.app](https://your-url.streamlit.app)

Upload a file and it returns the client name, amount, date, and request type as structured JSON, ready to drop into a database.

## Why I built this

I built this as a technical assessment for an AI developer role focused on accounting and tax automation. The challenge was straightforward on paper but interesting in practice: take unstructured text from different sources and turn it into strict JSON that a SQL database can ingest without manual cleanup.

The hard part isn't calling the API. It's making sure the output is actually usable — consistent keys, normalized formats (dates as YYYY-MM-DD, amounts as plain numbers), and a recovery strategy when the model occasionally ignores the instructions.

## How it works

1. The user uploads one or more files (txt, docx, xlsx, or pdf).
2. `unstructured` extracts the raw text regardless of format.
3. The text is sent to GPT-3.5-turbo with a strict prompt that forces JSON-only output.
4. The response is parsed and validated. If parsing fails or the data is empty, the app retries up to 3 times.
5. Results are displayed in the UI and can be downloaded as a single consolidated JSON file.

## Tech stack

- Python 3.11
- Streamlit for the UI
- OpenAI API (GPT-3.5-turbo)
- Unstructured for multi-format file parsing
- python-dotenv for local environment management

## Running locally

Clone the repo and install dependencies:

```bash
git clone https://github.com/your-username/extractor-fiscal.git
cd extractor-fiscal
pip install -r requirements.txt
```

Create a `.env` file in the root with your OpenAI key:

```
OPENAI_API_KEY=sk-your-key-here
```

Then run:

```bash
streamlit run app.py
```

## Project structure

```
extractor-fiscal/
├── app.py                  # Main application
├── requirements.txt        # Dependencies
├── .env                    # API key (not committed)
├── .streamlit/
│   └── secrets.toml        # Streamlit Cloud secrets (not committed)
└── README.md
```

## Design decisions

**Why retry logic?** LLMs occasionally add markdown fences or extra commentary even when explicitly told not to. Three attempts covers the vast majority of these cases without making the user wait too long.

**Why validate that at least one field was extracted?** Returning a JSON full of `NO_ENCONTRADO` values is technically valid but useless. The validation step distinguishes between "the model worked but the document had no relevant data" and "the model failed" — two very different problems for the end user.

**Why temperature 0?** Data extraction is not a creative task. Deterministic output matters more than variety.

## Limitations

This is a demo version with file size and quantity limits to protect against API abuse. In a production deployment for a real accounting firm, the following would need to change:

- Move from GPT-3.5 to GPT-4 for higher accuracy on edge cases
- Add a database layer to persist extractions and track history
- Build a validation UI where accountants can review and correct fields before committing
- Add batch processing for thousands of documents via a queue system

## Author

Brandon Enrique Eroza Torres
Computer Science graduate, BUAP