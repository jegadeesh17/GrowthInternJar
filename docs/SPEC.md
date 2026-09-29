# Product Specification: Jar Growth Intern Assignment

## 1. Summary

- **Vision**: Deliver an executive-grade, rigorous Growth Intern assignment submission for Jar (changejar.com) that demonstrates analytical depth, commercial instincts, product teardown acumen, and clean Python software engineering. The submission delivers three integrated components:
  1. **Sales & Profitability Analytics Engine (Python)**: Robust data pipeline calculating category sales/margins, Furniture target MoM fluctuations, and regional performance across retail datasets.
  2. **Interactive Minimal-UI Web Dashboard (`index.html`)**: Production-ready static web application deployed to GitHub Pages inspired by `minimal-ui-kit/material-kit-react` with a soft pastel color scheme, interactive Chart.js visualizations, and comprehensive teardowns for Questions 1, 2, and 3.
  3. **Executive PDF Submission Document (`Jar_Growth_Intern_Assignment_Submission.pdf`)**: Publication-grade A4 executive report generated via an automated Python PDF pipeline with high-DPI visualizations, structured data tables, and strategic growth frameworks.
- **Post-spec additions**: sub-category performance, city performance with Fix/Scale city priorities, and a data-driven Q1 narrative (`q1_insights.json`) were added after M3. The dashboard was redesigned; `DESIGN.md` defines its visual system (see ADR-008).
- **Posture**: **Production**
  - All analytical calculations must be zero-defect, deterministic, typed, and backed by automated unit tests.
  - Codebase adheres to strict modular design (`src/`, `tests/`), PEP 8 standards, and industry naming conventions.
- **Target Persona**: Growth Leads, Senior Product Managers, and Hiring Evaluators at Jar.
  - Needs: Fast navigability, unmistakable analytical rigor, commercially grounded recommendations, and transparent verification of results.

---

## 2. User Journeys

### Journey 1: Growth Evaluator Runs Analytics Engine & Verifies Calculations (Question 1)
1. **Trigger**: The evaluator clones the repository and runs `python -m src.main` or `pytest`.
2. **Data Ingestion**: The system reads `List of Orders.xlsx`, `Order Details.xlsx`, and `Sales target.xlsx` from the workspace root.
3. **Validation & Cleansing**: Dates are normalized into standard ISO timestamps; currency figures, profits, and quantities are parsed into numeric types; missing and negative values are handled deterministically.
4. **Execution of Question 1 Part 1 (Sales & Profitability)**:
   - Merges `List of Orders` and `Order Details` on `Order ID`.
   - Computes total sales (`Amount`), total profit, order-level category average profit, and total profit margin percentage (`(Total Profit / Total Amount) * 100`) grouped by `Category`.
   - Ranks and outputs the top-performing and underperforming categories with business root-cause diagnoses.
5. **Execution of Question 1 Part 2 (Target Achievement Analysis)**:
   - Filters `Sales target.xlsx` for `Category == 'Furniture'`.
   - Sorts chronologically (`Apr-18` through `Mar-19`).
   - Computes month-over-month (MoM) target sales percentage change: `((Target_t - Target_{t-1}) / Target_{t-1}) * 100` (baseline month marked `N/A`).
   - Reconciles target sales against actual sales achieved for Furniture and flags months with significant fluctuations ($|MoM| \ge 15\%$).
6. **Execution of Question 1 Part 3 (Regional Performance Insights)**:
   - Identifies the Top 5 states by distinct order count from `List of Orders`.
   - Computes total sales, total profit, average profit per order, and profit margin for each of the top 5 states.
   - Highlights regional disparities (high-volume/low-margin vs. high-margin/low-volume) and pinpoints priority cities/states for operational intervention.
7. **Output**: Clean tabular summaries printed to CLI and exported to structured CSV/JSON artifacts in `data/output/`.

### Journey 2: Evaluator Explores Interactive Pastel Web Dashboard (`index.html`)
1. **Trigger**: Evaluator opens `index.html` locally or visits the deployed GitHub Pages URL.
2. **Dashboard Overview**: Evaluator lands on a clean, modern dashboard styled in `minimal-ui-kit/material-kit-react` aesthetics with the pastel palette defined in `DESIGN.md` (lavender, mint, butter, peach, sky), a left sidebar, soft-shadowed cards, and responsive KPI widgets.
3. **Q1 — Sales analytics (three parts: Sales & profitability, Target achievement, Regional insights)**:
   - Evaluator inspects interactive KPI metric cards (Total Sales, Total Profit, Overall Margin %, Top State).
   - Evaluator toggles interactive Chart.js charts:
     - Category Sales & Profitability dual-axis bar/line chart.
     - Furniture MoM Target vs. Actual Sales trajectory chart.
     - Top 5 States Regional Performance breakdown chart.
   - Evaluator reviews interactive data tables with search, sorting, and category highlight tags.
4. **Q2 — Jar App UX Teardown**:
   - Evaluator reviews 5 core UX strengths (Frictionless Round-ups, Sub-₹10 Accessibility, Daily Spin Streaks, Real-time Liquidity, 24K Vault Trust).
   - Evaluator reviews 5 prioritized friction points with root-cause mechanics and actionable solutions (AutoPay failure transparency, buy-sell spread clarity, notification fatigue controls, multi-asset diversification, family vaults).
5. **Q3 — Fintech Growth & Business Expansion Roadmap**:
   - Evaluator reads strategic growth verticals: Gold-backed Micro-Lending (Jar Cash), Micro-SIPs (Silver & SGBs), Jar Family Vaults, Gold Leasing (Jar Earn 2-3% yield), and B2B Corporate Wellness SDK.
   - Evaluator reviews market opportunity sizing, unit economics impact, and execution feasibility matrices.
6. **Action**: Evaluator clicks "Download Executive PDF Report" to retrieve the compiled offline report.

### Journey 3: Automated Compilation & Review of Executive PDF Document
1. **Trigger**: Evaluator or developer runs `python -m src.generate_pdf` or triggers the build pipeline.
2. **Pipeline Execution**: The Python PDF generation pipeline reads the analytical outputs and pre-rendered high-resolution pastel charts.
3. **Document Layout Compilation**:
   - Generates an executive cover page with metadata and table of contents.
   - Generates Section 1: Executive Summary & Question 1 Sales Analysis with styled tables, KPIs, and embedded charts.
   - Generates Section 2: Jar App UX Teardown (Question 2) with evaluation scorecards and design recommendations.
   - Generates Section 3: Fintech Product Expansion Strategy (Question 3) with growth frameworks and unit economic projections.
4. **Output**: Produces `Jar_Growth_Intern_Assignment_Submission.pdf` verified for visual fidelity, table pagination, and crisp vector typography.

### Journey 4: Continuous Quality Assurance & Test Verification
1. **Trigger**: Developer or CI workflow executes `pytest -v`.
2. **Execution**: Automated test runner discovers all test suites under `tests/`.
3. **Verification**: Tests validate data schema integrity, merge cardinality, mathematical calculations, edge-case date handling, negative profit preservation, and output file existence.
4. **Outcome**: All tests pass with zero warnings and clear assertion logs.

---

## 3. Acceptance Criteria

### Analytical Engine & Question 1 Criteria

- **AC-1.1: Dataset Ingestion and Schema Normalization**
  - **Given** raw Excel files `List of Orders.xlsx`, `Order Details.xlsx`, and `Sales target.xlsx` in the workspace,
  - **When** the ingestion module loads the datasets,
  - **Then** columns are correctly mapped, whitespace is trimmed, `Order Date` is parsed to datetime without errors, and numeric fields (`Amount`, `Profit`, `Quantity`, `Target`) are typed as `float64` or `int64`.

- **AC-1.2: Order Dataset Merging**
  - **Given** normalized `List of Orders` ($N$ orders) and `Order Details` ($M$ line items),
  - **When** an inner join is performed on `Order ID`,
  - **Then** every merged record contains valid customer geographic details (`State`, `City`) and transactional details (`Category`, `Sub-Category`, `Amount`, `Profit`), and no line items are duplicated or dropped due to key mismatches.

- **AC-1.3: Category Sales and Profitability Aggregation**
  - **Given** merged order transactions,
  - **When** aggregating by `Category`,
  - **Then** the engine outputs:
    1. Total Sales (`Sum(Amount)`) per category.
    2. Total Profit (`Sum(Profit)`) per category.
    3. Order-level Category Average Profit: grouped by `(Order ID, Category)` to find order-level category profit, averaged across distinct orders containing that category.
    4. Profit Margin %: strictly computed as `(Total Profit / Total Amount) * 100`, rounded to two decimal places.
    5. Correct identification of the highest sales category, highest margin category, and lowest/underperforming category.

- **AC-1.4: Furniture MoM Target Sales Fluctuations**
  - **Given** `Sales target.xlsx` records for `Category == 'Furniture'`,
  - **When** targets are ordered chronologically from April 2018 (`Apr-18`) through March 2019 (`Mar-19`),
  - **Then**:
    1. The baseline month (`Apr-18`) has MoM percentage change equal to `NaN` (or labeled `N/A`).
    2. For each subsequent month $t$, MoM percentage change is computed as `((Target_t - Target_{t-1}) / Target_{t-1}) * 100`.
    3. Months with absolute MoM change $|MoM| \ge 15.0\%$ are programmatically flagged as "Significant Fluctuation".
    4. Target values are compared against actual Furniture sales per month, outputting monthly variance (`Actual - Target`).

- **AC-1.5: Top 5 States Regional Performance**
  - **Given** `List of Orders` dataset,
  - **When** ranking states by distinct `Order ID` count,
  - **Then**:
    1. Exactly top 5 states are selected in descending order of order volume.
    2. For each of the top 5 states, total sales (`Sum(Amount)`), total profit (`Sum(Profit)`), average profit per order (`Total Profit / Distinct Orders`), and profit margin % are computed.
    3. States are categorized into performance quadrants (e.g., High Volume / Low Margin vs. Low Volume / High Margin).

### App UX Critique & Growth Expansion Criteria (Questions 2 & 3)

- **AC-2.1: Question 2 App Teardown Completeness**
  - **Given** the app teardown specification,
  - **When** reviewing the app evaluation section,
  - **Then** exactly 5 distinct effective features and exactly 5 prioritized UX improvement areas are documented, each accompanied by:
    1. Feature/Friction description.
    2. Behavioral psychology / growth mechanic rationale (e.g., mental accounting, loss aversion, variable rewards, cognitive load).
    3. Actionable recommendation and expected business impact metric (e.g., D30 retention, auto-pay conversion, churn reduction).

- **AC-3.1: Question 3 Strategic Growth Expansion Completeness**
  - **Given** Jar's core competencies (digital gold micro-savings, automated UPI round-ups, high user trust, 10M+ registered users),
  - **When** reviewing the new business opportunities section,
  - **Then** at least 4 (and up to 5) distinct expansion vectors are detailed, covering:
    1. Gold-Backed Credit / Micro-Overdraft (instant liquidity without liquidating savings).
    2. Micro-SIPs in Silver ETFs & Sovereign Gold Bonds (asset diversification).
    3. Jar Family Vaults & Child Savings (intergenerational habit building).
    4. Gold Leasing / Yield Generation (Jar Earn 2-3% yield).
    5. Integration blueprint explaining how Jar's automation and trust flywheel seamlessly powers each vertical.

### Deliverables & Interface Criteria

- **AC-4.1: Interactive Pastel Web Dashboard Delivery (`index.html`)**
  - **Given** the static site deliverable,
  - **When** `index.html` is rendered in a modern web browser,
  - **Then**:
    1. It loads without external framework build steps (self-contained HTML5/CSS3/JS with Chart.js CDN).
    2. The visual theme implements `minimal-ui-kit/material-kit-react` styling with the pastel palette, typography and card geometry defined in `DESIGN.md`.
    3. Includes functional sidebar navigation for: Overview & KPIs, Question 1 (Sales Analysis), Question 2 (App Teardown), Question 3 (Product Expansion), and Methodology.
    4. Renders responsive interactive Chart.js charts for Category Performance, Furniture Target vs Actual, and Top 5 States.

- **AC-4.2: Automated Executive PDF Generation (`Jar_Growth_Intern_Assignment_Submission.pdf`)**
  - **Given** the Python PDF generation script `src/generate_pdf.py`,
  - **When** executed via Python,
  - **Then**:
    1. A valid, uncorrupted PDF file `Jar_Growth_Intern_Assignment_Submission.pdf` is generated in the workspace root.
    2. The PDF contains formatted executive cover page, executive summary, analytical tables with pastel styling, embedded high-DPI charts, complete Question 2 teardown, and Question 3 expansion roadmap.
    3. Total page count is between 6 and 12 pages with proper headers, footers, and page numbers.

### Edge Cases & Data Hygiene Criteria

- **AC-E1: Date Inconsistency Handling**
  - **Given** `List of Orders` containing mixed date representations (string formats `DD-MM-YYYY`, `YYYY-MM-DD`, or Excel serial numbers),
  - **When** the date normalization parser executes,
  - **Then** all dates are coerced to uniform pandas datetime objects without raising unhandled exceptions or swapping days and months.

- **AC-E2: Negative Profit Handling**
  - **Given** order line items where `Profit < 0` (discounted sales or loss leaders),
  - **When** calculating category and state aggregates,
  - **Then** negative profits are preserved in arithmetic sums and averages, properly penalizing total margin percentage rather than being filtered out or zero-clipped.

- **AC-E3: Chronological MoM Target Baseline**
  - **Given** target sales data starting at `Apr-18`,
  - **When** calculating MoM % change for the initial month,
  - **Then** the value is strictly set to `NaN` (or `None`/`N/A`) and never causes division by zero, runtime warnings, or arbitrary default values like `0.0%`.

- **AC-E4: Missing or Corrupt Input Data Handling**
  - **Given** an execution environment where an input Excel file or mandatory column is missing,
  - **When** the data loader initializes,
  - **Then** a descriptive `FileNotFoundError` or `ValueError` is raised specifying the missing asset, preventing undefined pipeline failures.

- **AC-E5: Zero-Division Safety in Margin Calculation**
  - **Given** an edge-case subset where `Total Amount == 0`,
  - **When** computing `(Total Profit / Total Amount) * 100`,
  - **Then** the function returns `0.0` or `NaN` safely without raising `ZeroDivisionError`.

- **AC-E6: Unmatched Order IDs**
  - **Given** potential order IDs present in `Order Details` but absent in `List of Orders` (or vice-versa),
  - **When** performing the join,
  - **Then** inner join semantics retain only verified matched orders, and the count of dropped records is logged for auditability.

---

## 4. Non-Goals

1. **Complex Machine Learning & Predictive Modeling**: Complex time-series forecasting (e.g. ARIMA, Prophet, LSTM) is explicitly excluded. Focus is placed on descriptive, diagnostic, and prescriptive growth analytics.
2. **Live Backend Server & Database Infrastructure**: The submission does not require hosting persistent relational databases (e.g., PostgreSQL) or continuous server processes (e.g., Django/Node backends). A static, zero-latency GitHub Pages dashboard with offline Python execution is chosen for maximum evaluator accessibility.
3. **Real Payment Gateway & UPI Integrations**: Live NPCI UPI AutoPay sandbox integrations or real KYC verifications are out of scope.
4. **Native Mobile Application Builds**: No Android (`.apk`) or iOS (`.ipa`) compilations are generated; the product teardown relies on mobile UI/UX evaluation frameworks.

---

## 5. Open Questions & Methodological Assumptions

1. **Category Order-Level Average Profit Calculation**:
   - *Ambiguity*: In Question 1 Part 1, does "average profit per order" mean dividing category total profit by total distinct orders across the entire dataset, or dividing by distinct orders that specifically include that category?
   - *Assumption*: We group by `(Order ID, Category)` to compute total category profit per order, then take the arithmetic mean across all distinct orders that purchased items in that category. This accurately reflects the typical profitability when that category is ordered.
2. **Significant Fluctuation Threshold for Furniture Targets**:
   - *Ambiguity*: Question 1 Part 2 asks to "identify months with significant target fluctuations" without specifying a numerical cutoff.
   - *Assumption*: We set a quantitative threshold of $|MoM \% Change| \ge 15.0\%$. Any month exceeding this variance is classified as a significant fluctuation requiring structural realignment.
3. **State Average Profit Metric Granularity**:
   - *Ambiguity*: In Question 1 Part 3, does "average profit" for each of the top 5 states mean average profit per order in that state, or average profit per line-item item?
   - *Assumption*: We define it as average profit per distinct order (`State Total Profit / State Distinct Order Count`), which represents average order profitability from a growth/retention perspective. We also present average profit per line-item and overall profit margin % in the breakdown tables for full transparency.
4. **Reporting Period for Furniture Actuals vs. Targets**:
   - *Ambiguity*: The sales targets cover April 2018 to March 2019. Do the order dates map directly to this same window?
   - *Assumption*: We filter and aggregate actual orders within the identical April 2018 – March 2019 window to provide a valid, 1-to-1 variance and target achievement comparison.
