# Jar Growth Intern Assignment

Submission for the Jar Growth Intern assignment:

- **Q1 - Sales analysis:** category performance, the Furniture target month-over-month trend against actual sales, and the top states by performance. The data comes from `List of Orders.xlsx`, `Order Details.xlsx` and `Sales target.xlsx`.
- **Q2 - App teardown:** a UX teardown of the Jar app.
- **Q3 - Growth strategy:** a fintech growth and expansion roadmap.

## Setup

```bash
pip install -r requirements.txt
```

## Run the analytics CLI

Run this from the repository root. The three Excel files must be in the root, or in the folder given by `--data-dir`.

```bash
python -m src.main
python -m src.main --data-dir . --output-dir data/output --top-states 5 --quiet
```

The CLI prints the Q1, Q2 and Q3 sections and writes JSON/CSV files to `data/output/`. Environment variables can override the defaults: `DATA_DIR`, `OUTPUT_DATA_DIR`, `FURNITURE_MOM_FLUCTUATION_THRESHOLD`, `TOP_STATES_COUNT` and `LOG_LEVEL`.

## Generate the PDF report

```bash
python -m src.generate_pdf
```

This writes `Jar_Growth_Intern_Assignment_Submission.pdf` to the repository root. Set `OUTPUT_PDF_PATH` to write it somewhere else. The charts are rendered to `assets/charts/`.

## Open the dashboard

Open `index.html` in a browser. The data is embedded in the page, and Chart.js loads from a CDN, so you need an internet connection. No server is required.

## Run the tests

```bash
python -m pytest -v
```

The edge-case tests (spec criteria AC-E1 to AC-E6) are in `tests/test_edge_cases.py`.

## Project layout

```
src/
  data_loader.py        Excel ingestion, date normalization, schema checks
  analytics_engine.py   Q1 metrics: categories, Furniture targets, states, cities
  export_service.py     JSON/CSV export
  content/              Q2 UX teardown and Q3 growth strategy content
  chart_generator.py    Matplotlib charts for the PDF
  pdf_generator.py      PDF report builder
  generate_pdf.py       PDF entry point
  main.py               Analytics CLI entry point
tests/                  pytest suite (fixtures in conftest.py)
docs/                   Spec, architecture, decisions, tasks
data/output/            Generated JSON/CSV files
assets/charts/          Generated chart images
index.html              Interactive dashboard
```
