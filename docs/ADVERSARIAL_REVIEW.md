# Adversarial Review Log

## Milestone M1 Review
Verdict: APPROVED
Test command: `python -m pytest -v` -> exit code 0 (76 passed in 8.90s)

### Critical defects (must fix; any defect means REJECTED)
None.

### Recommendations (non-blocking)
- `pyproject.toml` / `pytest.ini`: Configure `asyncio_default_fixture_loop_scope = "function"` to preemptively suppress the deprecation warning emitted by `pytest-asyncio` plugin when running pytest.
- `src/main.py`: Consider adding an optional `--export-excel` flag if downstream business stakeholders or evaluators request consolidated `.xlsx` reports in addition to JSON and CSV artifacts.

---

### Detailed Adversarial Audit Findings

#### 1. Contract Drift & Interface Fidelity (SPEC AC-1.1 to AC-1.5)
- **AC-1.1 (Dataset Ingestion & Schema Normalization)**:
  - `DataLoader.load_orders`, `load_order_details`, and `load_sales_targets` strictly map columns to lowercase `snake_case`, trim surrounding whitespace, and enforce dataclass contracts (`RawOrderRecord`, `RawOrderDetailRecord`, `RawSalesTargetRecord`).
  - Dates are parsed to uniform `pd.Timestamp` across heterogeneous representations.
  - Numeric columns are cast to `float64` (`amount`, `profit`, `target`) and `int64` (`quantity`) with `errors="raise"`.
- **AC-1.2 (Order Dataset Merging)**:
  - `AnalyticsEngine.merge_orders()` performs an inner join on `order_id`, preserving 1,500 order line items across 500 distinct orders from the raw workbook.
  - Column alignment exactly matches `MERGED_OUTPUT_COLUMNS` specification (`order_id`, `order_date`, `customer_name`, `state`, `city`, `amount`, `profit`, `quantity`, `category`, `sub_category`).
  - Cardinality and unmatched order audit logging implemented per AC-E6.
- **AC-1.3 (Category Sales & Profitability Aggregation)**:
  - Distinct order counts and average profit per order are grouped at `(order_id, category)` per ADR-004 to prevent dilution from unrelated orders.
  - Profit margin % is computed as `(total_profit / total_sales) * 100` rounded to 2 decimal places.
  - Primary ranking is by margin % descending, secondary by total profit descending.
  - Helper inspection methods (`get_highest_sales_category`, `get_highest_margin_category`, `get_lowest_margin_category`, `get_highest_profit_category`) match interface requirements.
- **AC-1.4 (Furniture Target MoM Fluctuation & Reconciliation)**:
  - Chronological sorting strictly verified from `Apr-18` to `Mar-19` (12 months), handling out-of-order target records.
  - Baseline month `Apr-18` strictly assigns `None` (`null` in JSON, `NaN` in pandas/CSV) with `is_significant_fluctuation = False`.
  - MoM % change formula `((Target_t - Target_{t-1}) / Target_{t-1}) * 100` verified across all subsequent months.
  - Monthly actual sales aggregated from line items reconcile to the Furniture category total (₹127,181.00).
- **AC-1.5 (Top 5 States Regional Performance)**:
  - States are ranked strictly by distinct `order_id` volume from `List of Orders` (preventing line-item inflation per ADR-006).
  - Selected top 5 states: Madhya Pradesh (101 orders), Maharashtra (90 orders), Rajasthan (32 orders), Gujarat (27 orders), and Punjab (25 orders).
  - Strategic quadrant classification correctly segments states based on median volume (32.0 orders) and median margin (5.28%).

#### 2. Mathematical Accuracy of Analytics Engine
- **Category Sales & Margins (Question 1 Part 1)**:
  - `Clothing`: Total Sales = ₹139,054.00, Total Profit = ₹11,163.00, Distinct Orders = 393, Total Quantity = 3,516, Avg Profit/Order = ₹28.40, Margin = 8.03% (Rank 1).
  - `Electronics`: Total Sales = ₹165,267.00, Total Profit = ₹10,494.00, Distinct Orders = 204, Total Quantity = 1,154, Avg Profit/Order = ₹51.44, Margin = 6.35% (Rank 2).
  - `Furniture`: Total Sales = ₹127,181.00, Total Profit = ₹2,298.00, Distinct Orders = 186, Total Quantity = 945, Avg Profit/Order = ₹12.35, Margin = 1.81% (Rank 3).
  - Net reconciliation: ₹139,054 + ₹165,267 + ₹127,181 = ₹431,502.00 total sales; ₹11,163 + ₹10,494 + ₹2,298 = ₹23,955.00 total profit. Math is verified to the exact cent.
- **Furniture Target Reconciliation (Question 1 Part 2)**:
  - Full-year Target = ₹132,900.00; Full-year Actual Sales = ₹127,181.00; Net Variance = -₹5,719.00 (95.70% overall achievement).
  - Baseline month `Apr-18`: Target ₹10,400.00, Actual ₹8,121.00, MoM = `null`, Variance = -₹2,279.00 (78.09% achievement).
  - 4 months achieved target (Nov-18: 134.20%, Jan-19: 184.84%, Feb-19: 140.19%, Mar-19: 141.18%).
  - At default $|MoM| \ge 15.0\%$ cutoff, 0 months flagged on monotonic raw target curve; tested and verified with synthetic 12-month test fixture where all 7 significant swings ($|MoM| \ge 15\%$) are correctly identified.
- **State Metrics & Quadrants (Question 1 Part 3)**:
  - `Madhya Pradesh`: Orders = 101, Sales = ₹105,140.00, Profit = ₹5,551.00, Avg Profit = ₹54.96, Margin = 5.28% -> `High Volume / Low Margin`.
  - `Maharashtra`: Orders = 90, Sales = ₹95,348.00, Profit = ₹6,176.00, Avg Profit = ₹68.62, Margin = 6.48% -> `High Volume / High Margin`.
  - `Rajasthan`: Orders = 32, Sales = ₹21,149.00, Profit = ₹1,257.00, Avg Profit = ₹39.28, Margin = 5.94% -> `Low Volume / High Margin`.
  - `Gujarat`: Orders = 27, Sales = ₹21,058.00, Profit = ₹465.00, Avg Profit = ₹17.22, Margin = 2.21% -> `Low Volume / Low Margin`.
  - `Punjab`: Orders = 25, Sales = ₹16,786.00, Profit = -₹609.00, Avg Profit = -₹24.36, Margin = -3.63% -> `Low Volume / Low Margin`.

#### 3. Edge Cases & Resilience (AC-E1 to AC-E6)
- **AC-E1 (Date parsing)**: Tested and verified across `DD-MM-YYYY`, `YYYY-MM-DD`, leap day (`29-02-2020`), Excel float serials (`43104.0`), and inverted `mm-dd-yyyy` cell number formats.
- **AC-E2 (Negative profits)**: Preserved through arithmetic sums and averages, properly penalizing margins for loss leaders (e.g., Punjab -₹609.00, -3.63% margin; Chennai -₹2,216.00).
- **AC-E3 (Chronological baseline)**: Baseline month strictly set to `None`/`null` without division-by-zero or default 0.0% false flags.
- **AC-E4 (Missing/corrupt files)**: Validated with `FileNotFoundError`, `ValueError` for 0-byte files, and `MissingColumnError` (subclassing both `KeyError` and `ValueError`) for missing schema headers.
- **AC-E5 (Zero-division safety)**: When `total_sales == 0.0`, margin returns `0.0` safely across all analytics methods and dataclass validators.
- **AC-E6 (Unmatched order IDs)**: Inner join drops unmatched rows and logs cardinality differences.

#### 4. Code Quality, CLI Runner, & Security Audit
- **CLI Runner (`src/main.py`)**:
  - Successfully executed `python -m src.main` (exit code 0 in 0.50s).
  - Renders clean ASCII formatted tables with currency formatting (`Rs. X,XXX.XX`) and percentage alignment.
  - Persists validated artifacts in `data/output/` (`category_performance.json/csv`, `furniture_targets.json/csv`, `state_performance.json/csv`, `city_performance.json/csv`).
- **Security**:
  - Zero hardcoded credentials or API keys.
  - Subprocess calls in tests use argument arrays with no shell execution (`shell=False`).
  - No SQL injection or arbitrary file path traversal vulnerabilities.
  - `sanitize_value_for_json` guarantees RFC 8259 JSON compliance (converts `NaN` and `inf` to `null`).
- **Verification Proof**:
  - Complete test suite `python -m pytest -v` executed: **76 tests passed in 8.90s with 0 failures**. Every test makes substantive assertions against real and synthetic data.


---

## Milestone M2 Review
Verdict: APPROVED
Test command: `python -m pytest -v` -> exit code 0 (95 passed in 10.08s)

### Critical defects (must fix; any defect means REJECTED)
None.

### Recommendations (non-blocking)
- `src/export_service.py`: Consider adding an optional `include_strategy: bool = False` flag to `ExportService.export_all()` to allow single-call batch exports of all analytical and strategic content artifacts across Questions 1, 2, and 3. Currently `main.py` invokes `export_all()` followed by `export_ux_teardown()` and `export_growth_strategy()`, which works reliably but could be unified.
- `src/content/growth_strategy.py:861-863`: The USD conversion rate in `get_market_sizing_summary()` uses a benchmark conversion rate of 83.33 INR/USD. Externalizing this conversion factor or documenting the baseline currency exchange date would further enhance financial modeling clarity for evaluators.

### Detailed Audit Summary
- **Question 2 (Jar App UX Teardown)**: Exactly 5 effective strengths (`STRENGTH-01` to `05`) and 5 prioritized friction points (`FRICTION-01` to `05`) comprehensively articulated with behavioral psychology frameworks (Mental Accounting, Variable Reward Schedule, Default Effect, Loss Aversion, Goal Gradient Effect), actionable solutions, and impact metrics.
- **Question 3 (Fintech Product Expansion)**: 5 strategic growth verticals (`VERTICAL-01` to `05`: Jar Cash, Jar Multi-Asset, Jar Family Vaults, Jar Earn, Jar for Work) fully modeled with mathematical market opportunity sizing ($TAM \ge SAM \ge SOM$), unit economics (LTV:CAC 18.7x to 83.9x, payback <3 months), flywheel integration blueprints, and execution risk matrices.
- **Serialization & CLI Orchestration**: `data/output/ux_teardown.json` (18.4KB) and `growth_strategy.json` (29.7KB) exported with strict RFC 8259 JSON compliance. CLI runner `python -m src.main` successfully renders complete Question 1, 2, and 3 executive tables and exits 0.

## Milestone M3 Review

**Verdict: APPROVED** (light review limited to critical defects, per the user's request to finish fast)

The reviewer checked every figure in the 9-page PDF against `data/output/*.json`. They also checked that the dashboard's Q2, Q3 and Methodology tabs render and that its 10 built-in consistency checks pass. `index.html` has no injection path, since it uses `textContent` only. `generate_pdf.py` exits cleanly with an error message on missing or corrupt input. Scope matches the user's decisions: PDF Q2 is simple, PDF Q3 is unchanged.

### Critical defects
- None.

### Non-blocking recommendations (applied before commit)
1. `src/chart_generator.py:778`: the quadrant chart's y-axis tick labels rounded 2.5% steps to whole numbers, which was misleading.
2. `src/pdf_generator.py:740`: the PDF's furniture achievement (average of monthly %, 94.4%) disagreed with the dashboard (total actual / total target, 95.70%). Aligned to the total ratio.
3. `src/pdf_generator.py:1024`: singular/plural grammar ("need" → "needs").
