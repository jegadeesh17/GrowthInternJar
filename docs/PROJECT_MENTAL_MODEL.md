# Project Mental Model: Jar Growth Intern Assignment

## Vision
Deliver an executive-grade, rigorous Growth Intern assignment submission for Jar that demonstrates strong analytical acumen, business instincts, product thinking, and Python programming proficiency across three core areas:
1. **Sales & Profitability Analytics (Python)**: Data-backed diagnosis of sales, profitability margins, month-over-month target achievement fluctuations, and regional sales disparities across e-commerce retail data.
2. **App UX & Teardown Evaluation**: High-signal product critique of the Jar app, identifying 5 key strengths and 5 prioritized UX/conversion friction points with actionable improvements.
3. **Fintech Business & Product Expansion**: Commercially grounded growth strategies detailing new business verticals (e.g., micro-investing, credit/gold leasing, habit loops) leveraging Jar's core strengths in automation, digital gold savings, and user trust.

## Posture
- **Posture**: **Production**
- **Rationale**: This is a competitive hiring assignment. It requires clean, typed, modular, and tested Python code, zero-defect statistical metrics, defensible commercial assumptions, and well-structured deliverables.

## Target Persona
- **Evaluators**: Growth Lead, Product Managers, and Hiring Team at Jar (changejar.com).
- **Expectation**: Strong analytical depth (beyond superficial summaries), sharp commercial reasoning, actionable growth hypotheses, and clean code hygiene.

## Milestones
- **M1: MVP Vertical Slice — Python Analytics Pipeline (Question 1)**:
  - Part 1: Sales and Profitability Analysis (category aggregation, average profit per order, profit margin %, top/underperforming identification & root-cause analysis).
  - Part 2: Target Achievement Analysis (Furniture target MoM % change, trend & fluctuation analysis, target-setting alignment strategies).
  - Part 3: Regional Performance Insights (Top 5 states by order volume, sales & average profit, regional disparities, prioritized regions/cities for intervention).
  - Automated tests verifying all mathematical aggregations and data joins.
- **M2: Core Flows — App UX Critique & Growth Opportunities (Questions 2 & 3)**:
  - Question 2: In-depth teardown of 5 effective features and 5 targeted improvement areas with behavioural psychology / growth mechanics rationale.
  - Question 3: Strategic expansion roadmap exploring new business models, product integrations, and monetization avenues leveraging Jar's existing distribution and automated savings flywheel.
- **M3: Polish, Visualization & Interactive GitHub Pages Site**:
  - Publication-ready visualizations, data exports, responsive GitHub Pages static web report (`index.html`) ready for instant deployment, edge-case validation, and final handover.

## Part 1: Requirements and UX

### 1. Primary User Journey & Deliverables
- **Reviewer Persona**: Growth Leads / Senior PMs reviewing intern applicant submissions.
- **Deliverables**:
  - **Executable Python Module & Unit Tests** (`src/`, `tests/`): Python data processing engine executing all joins, calculations, and aggregations required by Question 1, with pytest verification.
  - **Interactive GitHub Pages Web Application** (`index.html`): High-aesthetic, responsive dashboard inspired by `minimal-ui-kit/material-kit-react`. Built with a soft pastel color scheme (soft sage, muted amber/gold, soft lavender, slate blue, warm blush), sleek rounded cards, modern typography, and interactive Chart.js visualizations covering Question 1, 2, and 3.
  - **Executive PDF Submission Document** (`Jar_Growth_Intern_Assignment_Submission.pdf`): A comprehensive, publication-grade executive PDF document containing executive summaries, professional tables, high-resolution pastel charts, the complete Jar UX audit (Question 2), and growth expansion strategy (Question 3). Generated via an automated Python PDF compilation pipeline.

### 2. Analytical Calculations & Methodological Decisions
- **Sales & Profitability (Q1 Part 1)**:
  - Join: Inner join on `Order ID` between `List of Orders` and `Order Details`.
  - Level of Granularity for "Average Profit per Order": Group by `(Order ID, Category)` to calculate order-level category profit before taking the mean per category.
  - Margin: `(Total Profit / Total Amount) * 100` per category.
- **Target Achievement (Q1 Part 2)**:
  - Standardize `Month of Order Date` from Excel format (`Apr-18` through `Mar-19`).
  - Calculate MoM Target % Change: `((Target_t - Target_{t-1}) / Target_{t-1}) * 100`.
  - Reconcile with actual sales achieved per month for Furniture to identify gaps.
- **Regional Performance (Q1 Part 3)**:
  - Order Count: Distinct `Order ID` count per state from `List of Orders`.
  - Top 5 States: Ranked by order volume; calculate total sales and average profit across merged line items.
  - Regional Disparities: Diagnose high-volume/low-margin states versus high-margin/low-volume states.

### 3. Edge Cases & Data Hygiene
- **Date Format Inconsistency**: Handle mixed date formats in `List of Orders` (string `DD-MM-YYYY` vs datetime timestamps).
- **Negative Profit**: Properly handle negative profit line items (loss-making orders/discounts) without dropping them.
- **Missing Baseline**: First month of MoM change is strictly baseline (NaN / labeled N/A).

### 4. Non-Goals
- Complex Machine Learning / Predictive Forecasting (e.g. ARIMA, Prophet, LSTM) is explicitly out of scope.
- Full-stack web applications requiring complex backend servers or database management are out of scope (a clean, responsive client-side static site for GitHub Pages with interactive Chart.js/visualizations and offline markdown reports will be used instead).


## Scope update (2026-09-29, user direction during M3)

- **Dashboard (`index.html`):** informative and visually clean. Q1 insights and recommendations, all Q2 items, all Q3 opportunities. Restrained pastel accents, no clutter.
- **PDF, Question 2:** keep simple: 5 strengths and 5 improvements, with reasoning.
- **PDF, Question 3:** keep unchanged, with full detail (user decision).
- **General:** avoid over-engineering. Build to the acceptance criteria and skip extra polish.
- **Post-M3 additions:** Q1 gained sub-category and city drill-downs (cities to fix or scale) and a shared data-driven narrative. The dashboard was redesigned to the Minimal UI Kit pastel system in `DESIGN.md` (ADR-008). The PDF keeps the ADR-007 palette.
- **Submission PDF (post-M3, user direction):** replaced the 9-page report with a one-page internal note that links to the hosted dashboard and repo; no analysis in the PDF (ADR-009). The dashboard no longer offers a PDF download.
