# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Jar's growth team, reviewing a Growth Intern assignment submission. They skim the headline KPIs first, then drill into Q1 (sales analytics), Q2 (Jar app UX teardown) and Q3 (fintech expansion strategy).

## Product Purpose
A single-file interactive dashboard (`index.html`) that presents the assignment's answers from the Python pipeline's outputs. Success: a reviewer understands the findings quickly and trusts the numbers.

## Operating Context
Opened locally in a desktop browser, with no server. Data is embedded as JSON by `python -m src.build_dashboard`, and Chart.js loads from a CDN. A companion PDF (`Jar_Growth_Intern_Assignment_Submission.pdf`) is downloadable from the page.

## Capabilities and Constraints
- Every figure is computed by the pipeline; the page must not hand-edit values. The `<script id="dashboard-data">` block must stay intact for `build_dashboard.py`.
- Sections: Overview, Q1, Q2, Q3, Methodology (including in-browser consistency checks).
- Scope is deliberately lean (intern assignment): no frameworks or build step.

## Brand Commitments
- Visual reference pinned by the user: Minimal UI Kit (minimal-ui-kit/material-kit-react) layout language, with pastel or soft colours instead of its saturated palette.

## Evidence on Hand
Pipeline outputs in `data/output/*.json`; source Excel files in the repo root. There are no testimonials or external claims, and none should be invented.
