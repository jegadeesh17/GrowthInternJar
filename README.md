# Jar Growth Intern Assignment

Submission for the Jar Growth Intern assignment:

- **Q1 - Sales analysis:** category and sub-category performance, the Furniture target month-over-month trend against actual sales, the top states by performance, and the cities to fix or scale. The data comes from `List of Orders.xlsx`, `Order Details.xlsx` and `Sales target.xlsx` in `data/input/`. The assignment brief is `docs/Jar - Growth Intern Assignment.pdf`.
- **Q2 - App teardown:** a UX teardown of the Jar app.
- **Q3 - Growth strategy:** a fintech growth and expansion roadmap.

## Setup

```bash
pip install -r requirements.txt
```

## Run the analytics CLI

Run this from the repository root. The three Excel files are read from `data/input/`, or from the folder given by `--data-dir`.

```bash
python -m src.main
python -m src.main --data-dir data/input --output-dir data/output --top-states 5 --quiet
```

The CLI prints the Q1, Q2 and Q3 sections and writes JSON/CSV files to `data/output/`. Environment variables can override the defaults: `DATA_DIR`, `OUTPUT_DATA_DIR`, `FURNITURE_MOM_FLUCTUATION_THRESHOLD`, `TOP_STATES_COUNT` and `LOG_LEVEL`. See `.env.example` for the full list.

## Generate the PDF report

```bash
python -m src.generate_pdf
```

This writes `data/output/Jar_Growth_Intern_Assignment_Submission.pdf`. Set `OUTPUT_PDF_PATH` to write it somewhere else, and `CANDIDATE_NAME` to set the author name on the cover. The charts are rendered to `assets/charts/` (override with `CHART_ASSETS_DIR`).

The PDF is gitignored, so generate it before opening the dashboard; its Download PDF link points to this file.

## Update and open the dashboard

After running the CLI, embed the fresh `data/output/*.json` files into the dashboard:

```bash
python -m src.build_dashboard
```

This rewrites the `<script id="dashboard-data">` block in `index.html`. `OUTPUT_DATA_DIR` and `DASHBOARD_HTML` override the input folder and target page.

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
  build_dashboard.py    Embeds data/output/*.json into index.html
tests/                  pytest suite (fixtures in conftest.py)
docs/                   Spec, architecture, decisions, tasks
data/input/             Source Excel files (tracked)
data/output/            Generated JSON/CSV files and the PDF (gitignored)
assets/charts/          Generated chart images
index.html              Interactive dashboard
DESIGN.md               Dashboard design system (colours, type, components)
PRODUCT.md              Dashboard purpose, audience and constraints
```
