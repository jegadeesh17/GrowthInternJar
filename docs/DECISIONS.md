# Architectural Decision Records (ADRs)

This document records the key architectural, technical, and methodological choices made for the Jar Growth Intern Assignment project. Each record is written in plain, accessible language to explain the business context, alternatives weighed, and trade-offs accepted.

---

## Table of Decisions

- [ADR-001: Technology Stack Selection for Data Processing Engine](#adr-001-technology-stack-selection-for-data-processing-engine)
- [ADR-002: Client-Side Minimal-UI Pastel Web Dashboard Architecture](#adr-002-client-side-minimal-ui-pastel-web-dashboard-architecture)
- [ADR-003: Cross-Platform Executive PDF Generation Pipeline](#adr-003-cross-platform-executive-pdf-generation-pipeline)
- [ADR-004: Metric Definition for Category Average Profit per Order](#adr-004-metric-definition-for-category-average-profit-per-order)
- [ADR-005: Quantitative Threshold for Significant Furniture Target Fluctuations](#adr-005-quantitative-threshold-for-significant-furniture-target-fluctuations)
- [ADR-006: State Ranking Methodology and Regional Profitability Granularity](#adr-006-state-ranking-methodology-and-regional-profitability-granularity)
- [ADR-007: Visual Design Token System and Soft Pastel Palette](#adr-007-visual-design-token-system-and-soft-pastel-palette)
- [ADR-008: Dashboard Redesign with a Minimal UI Kit Pastel System](#adr-008-dashboard-redesign-with-a-minimal-ui-kit-pastel-system)

---

## ADR-001: Technology Stack Selection for Data Processing Engine

- **Status**: Accepted
- **Context**: The assignment requires ingesting three separate Excel workbooks (`List of Orders`, `Order Details`, and `Sales target`), validating mixed date formats, merging datasets on `Order ID`, and computing statistical aggregations across sales, margins, and monthly growth rates. We need an environment that guarantees mathematical correctness, is reproducible across different computers, and runs fast.
- **Decision**: We chose **Python 3.10+** with **Pandas** for tabular manipulation and **Pytest** for automated test verification. Typed Python dataclasses are used at the boundaries to validate data types and prevent bad data from propagating through the pipeline.
- **Alternatives Considered**:
  - *Pure Python standard library (`csv`, `sqlite3`)*: While it avoids external dependencies, doing complex joins, date parsing, and grouping with standard library data structures is verbose, harder to maintain, and prone to edge-case arithmetic bugs.
  - *R language*: Highly capable for statistics, but less aligned with the standard engineering and growth tech stack used by product teams at Jar.
  - *DuckDB / PySpark*: Excellent for massive datasets (gigabytes to terabytes), but introduces unnecessary overhead for datasets containing under 10,000 rows.
- **Consequences**:
  - Requires installing common Python packages (`pandas`, `openpyxl`, `pytest`).
  - Delivers lightning-fast execution (<1 second) with deterministic, easily auditable math.
  - Enables clean unit tests that can be run with a single command.

---

## ADR-002: Client-Side Minimal-UI Pastel Web Dashboard Architecture

- **Status**: Accepted
- **Context**: Evaluators need an engaging, interactive way to inspect findings, explore charts, and review the UX teardown and fintech growth proposals. The deliverable should be accessible directly via GitHub Pages or by double-clicking a local HTML file, without requiring the evaluator to install Node.js, run local servers, or configure build scripts.
- **Decision**: We designed `index.html` as a **self-contained static single-page application** using standard modern HTML5, CSS3, and vanilla JavaScript (ES6+), with **Chart.js** loaded via CDN. The visual styling is inspired by `minimal-ui-kit/material-kit-react`, featuring a soft pastel color palette, soft elevation cards, and fluid tab navigation.
- **Alternatives Considered**:
  - *React / Next.js single-page app*: Provides component modularity, but requires a Node.js runtime, `npm install`, a build step (`npm run build`), and creates a heavy repository with thousands of dependency files.
  - *Streamlit or Dash application*: Quick to write in Python, but requires an active Python web server to run, which cannot be hosted as a zero-cost, zero-latency static site on GitHub Pages.
  - *Static Markdown / PDF only*: Lacks interactivity, preventing evaluators from hovering over data points, toggling metrics, or filtering tables.
- **Consequences**:
  - The dashboard opens instantly in any browser with zero setup.
  - Fully hostable on GitHub Pages with continuous availability.
  - All analytical data is embedded directly into the page, allowing full offline operation.

---

## ADR-003: Cross-Platform Executive PDF Generation Pipeline

- **Status**: Accepted
- **Context**: In addition to the web dashboard, the submission requires a standalone, publication-grade executive PDF document (`Jar_Growth_Intern_Assignment_Submission.pdf`) that hiring managers can download, print, or review offline. The PDF must incorporate polished typography, clean tables, and high-resolution charts.
- **Decision**: We selected **`fpdf2`** (a lightweight, modern, pure-Python PDF library) paired with **`matplotlib`** for rendering 300 DPI pastel charts. 
- **Alternatives Considered**:
  - *WeasyPrint (HTML-to-PDF)*: Produces beautiful layouts from HTML/CSS, but depends on system-level native libraries (GTK+, Pango, Cairo). These libraries frequently fail to install or crash on Windows operating systems without complex manual configuration.
  - *Puppeteer / Headless Chrome*: Generates pixel-perfect PDFs from web pages, but requires downloading a 300MB Chromium browser binary and running Node.js.
  - *ReportLab*: Powerful, but has an arcane, proprietary layout API that is brittle and difficult to style with modern card/pastel aesthetics.
- **Consequences**:
  - Pure Python solution with zero native binary dependencies; runs reliably on Windows, macOS, and Linux.
  - Produces crisp, uncorrupted vector-text PDFs with consistent pagination, running headers, and footers.
  - Charts are pre-rendered at high resolution (300 DPI) to ensure sharp visual fidelity in both digital view and print.

---

## ADR-004: Metric Definition for Category Average Profit per Order

- **Status**: Accepted
- **Context**: Question 1 Part 1 asks for the "average profit per order" for each category. In the raw dataset, `Order Details` contains individual line items, and a single customer order may include multiple line items across different categories. There are multiple ways to interpret this calculation.
- **Decision**: We calculate the metric by first aggregating profit at the **`(Order ID, Category)`** level (summing all profits for that category within a single order), and then calculating the arithmetic average across all distinct orders that purchased items in that category:
  $$\text{Average Profit per Order}_{\text{cat}} = \frac{\sum_{\text{order} \in \text{Orders}_{\text{cat}}} \text{Profit}_{\text{order, cat}}}{|\text{Orders}_{\text{cat}}|}$$
- **Alternatives Considered**:
  - *Line-Item Average (`Total Profit / Total Rows`)*: Measures average profit per product item rather than per order, which misrepresents cart-level profitability.
  - *Dataset-Wide Divisor (`Category Profit / Total Orders in Entire Dataset`)*: Artificially depresses category profitability by dividing by orders where the category was never purchased.
- **Consequences**:
  - Accurately captures how much profit a merchant makes on average whenever an order includes that specific category.
  - Aligns with standard retail and e-commerce merchandising analytics.

---

## ADR-005: Quantitative Threshold for Significant Furniture Target Fluctuations

- **Status**: Accepted
- **Context**: Question 1 Part 2 asks to analyze month-over-month (MoM) sales target fluctuations for the Furniture category and "identify months with significant target fluctuations." The assignment prompt does not prescribe a specific numerical threshold.
- **Decision**: We established a deterministic threshold of **$|MoM \% \text{Change}| \ge 15.0\%$**. Any month where the sales target increased or decreased by 15% or more compared to the preceding month is programmatically flagged as a "Significant Fluctuation."
- **Alternatives Considered**:
  - *Subjective / Visual Inspection*: Manually picking months that look unusual on a chart. This lacks reproducibility and scientific rigor.
  - *Statistical Standard Deviation Cutoff ($2\sigma$)*: With only 12 data points (months from April 2018 to March 2019), normal distribution assumptions are statistically invalid and sensitive to single outliers.
  - *Lower Threshold (e.g., 5% or 10%)*: Flags almost every month, creating excessive noise and obscuring true strategic reallocations (such as festival spikes and post-season corrections).
- **Consequences**:
  - Provides an objective, reproducible metric that clearly isolates major seasonal planning shifts.
  - Baseline month (`Apr-18`) is explicitly marked as `N/A` (no predecessor month) to prevent artificial zero-division or misleading 0% flags.

---

## ADR-006: State Ranking Methodology and Regional Profitability Granularity

- **Status**: Accepted
- **Context**: Question 1 Part 3 requires identifying the top 5 states by order volume and evaluating their sales and average profit. We must ensure that state order volume is not inflated by multi-item orders.
- **Decision**: 
  1. We rank states strictly by the count of **distinct `Order ID`s** registered in `List of Orders`.
  2. For those top 5 states, we compute total sales, total profit, and **average profit per distinct order** ($\text{State Total Profit} / \text{Distinct Orders}$).
  3. We also provide overall profit margin percentage and line-item average profit in secondary columns to give full transparency into whether a state's profitability is driven by high ticket sizes or healthy unit margins.
- **Alternatives Considered**:
  - *Ranking by Line-Item Rows*: States where customers buy lots of cheap accessories would appear larger than states with higher transaction volume, distorting true customer reach.
  - *Ranking by Total Revenue*: Fails to answer the prompt's specific requirement to rank by "order volume."
- **Consequences**:
  - Accurately reflects true customer transaction volume per state.
  - Enables meaningful quadrant classification: High Volume / High Margin, High Volume / Low Margin, Low Volume / High Margin, and Low Volume / Low Margin.

---

## ADR-007: Visual Design Token System and Soft Pastel Palette

- **Status**: Accepted for the PDF and charts; superseded for the dashboard by ADR-008
- **Context**: Evaluators will assess both the analytical depth and the aesthetic polish of the presentation. A generic default template fails to convey high-effort product craft. We need a cohesive, modern visual language inspired by `minimal-ui-kit/material-kit-react` that works seamlessly across the web dashboard and executive PDF.
- **Decision**: We created a unified design token system based on a soft pastel palette:
  - **Soft Sage** (`#48BB78`, background tint `#E6FFFA`): Represents profitability, positive variance, and healthy metrics.
  - **Muted Gold / Amber** (`#D69E2E`, background tint `#FEFCBF`): Represents digital gold, Jar's brand identity, and savings targets.
  - **Soft Lavender** (`#805AD5`, background tint `#FAF5FF`): Represents product UX, psychological models, and strategic expansion.
  - **Warm Coral Blush** (`#E53E3E`, background tint `#FFF5F5`): Highlights friction points, losses, and negative target variances.
  - **Slate & Charcoal** (`#2D3748`, `#718096`): Used for clear, high-contrast, professional typography.
  - **Card Styling**: Generous border radius (`16px`), subtle borders (`1px solid rgba(0,0,0,0.06)`), and soft elevation shadows.
- **Alternatives Considered**:
  - *Standard Bootstrap / Default Material Blue*: Generic, unmemorable, and disconnected from Jar's fintech and gold identity.
  - *Dark Neon / Gamer Theme*: Distracting, unprofessional for executive hiring, and unreadable when printed to PDF.
- **Consequences**:
  - Both deliverables (web dashboard and PDF report) share an unmistakable, high-polish visual identity.
  - Data visualizations are easy to interpret, pleasant to read, and executive-ready.

---

## ADR-008: Dashboard Redesign with a Minimal UI Kit Pastel System

- **Status**: Accepted (post-M3)
- **Context**: The first dashboard used stacked top tabs, bordered KPI tiles and the saturated ADR-007 colours, which read as a generic template rather than the Minimal UI Kit look the user asked for.
- **Decision**: Rebuild `index.html` on Minimal UI Kit grammar: a left sidebar, sticky top bar, white 16px cards, and a pastel palette (lavender, mint, butter, peach, sky) over a grey ramp, with Barlow and DM Sans type. Q1 is split into three parts. `DESIGN.md` is the single source of truth for the tokens.
- **Scope**: Dashboard only. The PDF and Matplotlib charts keep the ADR-007 palette.
- **Consequences**:
  - The dashboard and the PDF no longer share exact colours; both stay pastel.
  - Design changes are made in `DESIGN.md` first, then in `index.html`.
