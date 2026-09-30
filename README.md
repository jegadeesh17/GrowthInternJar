# Jar Growth Intern Assignment

Submission for the Jar Growth Intern assignment:

- **Q1 - Sales analysis:** category and sub-category performance, the Furniture target month-over-month trend against actual sales, the top states by performance, and the cities to fix or scale. The data comes from `List of Orders.xlsx`, `Order Details.xlsx` and `Sales target.xlsx` in `data/input/`. The assignment brief is `docs/Jar - Growth Intern Assignment.pdf`.
- **Q2 - App exploration:** five things the Jar app does well and five areas to improve, each with its reasoning.
- **Q3 - Product exploration:** new business opportunities for Jar and how each uses its automation, design and credibility.

## Where to look

- **Notebook:** [Jar_Growth_Intern_Assignment.ipynb](Jar_Growth_Intern_Assignment.ipynb) answers all three questions in Python, with the code and its output side by side. Start here to see how each figure is calculated.
- **Dashboard:** https://jegadeesh17.github.io/GrowthInternJar/ shows the same results interactively.

## Setup

```bash
pip install -r requirements.txt
```

## Re-run the notebook

```bash
pip install notebook
jupyter nbconvert --to notebook --execute --inplace Jar_Growth_Intern_Assignment.ipynb
```

The notebook reads the Excel files from `data/input/`, recomputes Question 1 in plain pandas and checks the result against the pipeline in `src/`.

## Run the analytics CLI

Run this from the repository root. The three Excel files are read from `data/input/`, or from the folder given by `--data-dir`.

```bash
python -m src.main
python -m src.main --data-dir data/input --output-dir data/output --top-states 5 --quiet
```

The CLI prints the Q1, Q2 and Q3 sections and writes JSON/CSV files to `data/output/`. Environment variables can override the defaults: `DATA_DIR`, `OUTPUT_DATA_DIR`, `FURNITURE_MOM_FLUCTUATION_THRESHOLD`, `TOP_STATES_COUNT` and `LOG_LEVEL`. See `.env.example` for the full list.

## Generate the submission note

```bash
python -m src.generate_pdf
```

This writes a one-page note to `data/output/Jar_Growth_Intern_Assignment_Submission.pdf` for internal submission. It links to the live dashboard and this repository and maps each question to its dashboard section; it does not repeat the analysis. `DASHBOARD_URL`, `REPO_URL`, `CANDIDATE_NAME` and `OUTPUT_PDF_PATH` override the defaults. The PDF is gitignored and the dashboard does not link to it.

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
  chart_generator.py    Standalone Matplotlib chart export (python -m src.chart_generator)
  pdf_generator.py      Submission note builder
  generate_pdf.py       Submission note entry point
  main.py               Analytics CLI entry point
  build_dashboard.py    Embeds data/output/*.json into index.html
tests/                  pytest suite (fixtures in conftest.py)
docs/                   Assignment brief
data/input/             Source Excel files (tracked)
data/output/            Generated JSON/CSV files and the PDF (gitignored)
assets/charts/          Chart images from chart_generator (gitignored)
index.html              Interactive dashboard
Jar_Growth_Intern_Assignment.ipynb   All three answers in Python, with code and output
```
