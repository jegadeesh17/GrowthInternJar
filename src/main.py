"""Command-line entry point and orchestration runner for the GrowthInternJar analytics pipeline.

Implements M1-TASK-06 (SPEC AC-1.1 to AC-1.5) and M2-TASK-03 (SPEC AC-2.1, AC-3.1):
- Orchestrates DataLoader, AnalyticsEngine, ExportService, and Strategy Content Models.
- Prints clean, publication-grade ASCII tabular summaries of Question 1, Question 2,
  and Question 3 results to stdout.
- Persists structured JSON and CSV artifacts to data/output/ (including ux_teardown.json
  and growth_strategy.json).
- Configurable via environment variables (DATA_DIR, OUTPUT_DATA_DIR,
  FURNITURE_MOM_FLUCTUATION_THRESHOLD, TOP_STATES_COUNT, LOG_LEVEL) or CLI arguments.
"""

import argparse
from datetime import datetime
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.analytics_engine import (
    AnalyticsEngine,
    CategoryPerformance,
    CityPerformance,
    CityPriority,
    FurnitureTargetAchievement,
    StatePerformance,
    SubCategoryPerformance,
)
from src.content.growth_strategy import (
    GrowthStrategyReport,
    get_growth_strategy_report,
)
from src.content.ux_teardown import (
    UXTeardownReport,
    get_ux_teardown_report,
)
from src.data_loader import DataLoader
from src.export_service import ExportService

logger = logging.getLogger("growth_intern_jar")


# ---------------------------------------------------------------------------
# ASCII Table Formatting Utility
# ---------------------------------------------------------------------------

def safe_terminal_text(text: Any) -> str:
    """Sanitizes text for safe terminal display across all platforms and Windows code pages."""
    return str(text).replace("\u20b9", "Rs. ")


def format_ascii_table(
    headers: List[str],
    rows: List[List[str]],
    alignments: Optional[List[str]] = None,
) -> str:
    """Renders a clean, formatted ASCII table with border dividers.

    Args:
        headers: Column header strings.
        rows: 2D list of row string values.
        alignments: List of alignment codes: '<' (left), '>' (right), '^' (center).
                    Defaults to left alignment for text, right for numeric headers.

    Returns:
        str: Formatted multi-line ASCII table string.
    """
    clean_headers = [safe_terminal_text(h) for h in headers]
    clean_rows = [[safe_terminal_text(cell) for cell in row] for row in rows]

    col_count = len(clean_headers)
    if alignments is None:
        alignments = ["<"] * col_count

    # Calculate max width per column
    col_widths = [len(h) for h in clean_headers]
    for row in clean_rows:
        for i, val in enumerate(row):
            if i < col_count:
                col_widths[i] = max(col_widths[i], len(str(val)))

    # Formatting templates
    def render_row(cells: Sequence[str]) -> str:
        formatted = []
        for i, cell in enumerate(cells):
            align = alignments[i] if i < len(alignments) else "<"
            width = col_widths[i]
            if align == ">":
                formatted.append(f" {cell:>{width}} ")
            elif align == "^":
                formatted.append(f" {cell:^{width}} ")
            else:
                formatted.append(f" {cell:<{width}} ")
        return "|" + "|".join(formatted) + "|"

    border_parts = ["-" * (w + 2) for w in col_widths]
    border = "+" + "+".join(border_parts) + "+"

    lines = [
        border,
        render_row(clean_headers),
        border,
    ]
    for row in clean_rows:
        lines.append(render_row(row))
    lines.append(border)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Presentation Formatting Helpers
# ---------------------------------------------------------------------------

def format_currency(val: float) -> str:
    """Formats float value as standard Indian Rupee notation or formatted currency."""
    return f"Rs. {val:,.2f}"


def format_pct(val: Optional[float], show_sign: bool = False) -> str:
    """Formats float value as percentage string."""
    if val is None:
        return "N/A"
    sign = "+" if show_sign and val > 0 else ""
    return f"{sign}{val:.2f}%"


# ---------------------------------------------------------------------------
# Section Summarizers & CLI Renderers
# ---------------------------------------------------------------------------

def render_category_section(categories: List[CategoryPerformance]) -> None:
    """Prints Question 1 Part 1 Category Sales & Profitability analysis table."""
    print("\n" + "=" * 92)
    print("  QUESTION 1 PART 1: CATEGORY SALES & PROFITABILITY PERFORMANCE")
    print("=" * 92)

    headers = [
        "Rank",
        "Category",
        "Total Sales",
        "Total Profit",
        "Avg Profit/Order",
        "Margin %",
        "Orders",
        "Quantity",
    ]
    alignments = [">", "<", ">", ">", ">", ">", ">", ">"]

    rows = []
    for c in categories:
        rows.append([
            str(c.performance_rank),
            c.category,
            format_currency(c.total_sales),
            format_currency(c.total_profit),
            format_currency(c.avg_profit_per_order),
            format_pct(c.profit_margin_pct),
            f"{c.distinct_orders:,}",
            f"{c.total_quantity:,}",
        ])

    print(format_ascii_table(headers, rows, alignments))

    # Analytical highlights
    if categories:
        highest_sales = AnalyticsEngine.get_highest_sales_category(categories)
        highest_margin = AnalyticsEngine.get_highest_margin_category(categories)
        lowest_margin = AnalyticsEngine.get_lowest_margin_category(categories)

        print("\n  Strategic Insights:")
        print(f"  * Highest Sales Volume:      {highest_sales.category} ({format_currency(highest_sales.total_sales)})")
        print(f"  * Highest Profit Margin:     {highest_margin.category} ({format_pct(highest_margin.profit_margin_pct)})")
        print(f"  * Underperforming Category:  {lowest_margin.category} ({format_pct(lowest_margin.profit_margin_pct)} margin - severe margin compression)")


def render_furniture_target_section(
    targets: List[FurnitureTargetAchievement],
    fluctuation_threshold: float,
) -> None:
    """Prints Question 1 Part 2 Furniture MoM Target Fluctuation & Achievement table."""
    print("\n" + "=" * 98)
    print(f"  QUESTION 1 PART 2: FURNITURE TARGET MoM FLUCTUATION & RECONCILIATION (|MoM| >= {fluctuation_threshold}%)")
    print("=" * 98)

    headers = [
        "Month",
        "Target Sales",
        "MoM Target %",
        "Actual Sales",
        "Variance",
        "Achievement %",
        "Status",
    ]
    alignments = ["^", ">", ">", ">", ">", ">", "<"]

    rows = []
    total_target = sum(t.target_sales for t in targets)
    total_actual = sum(t.actual_sales for t in targets)

    for t in targets:
        flag = "[*] FLAGGED" if t.is_significant_fluctuation else "Normal"
        rows.append([
            t.display_month,
            format_currency(t.target_sales),
            format_pct(t.mom_target_pct_change, show_sign=True),
            format_currency(t.actual_sales),
            format_currency(t.variance),
            format_pct(t.achievement_pct),
            flag,
        ])

    print(format_ascii_table(headers, rows, alignments))

    fluctuating = AnalyticsEngine.get_fluctuating_target_months(targets)
    achieved = AnalyticsEngine.get_achieved_target_months(targets)
    overall_variance = total_actual - total_target
    overall_achievement = (total_actual / total_target * 100) if total_target > 0 else 0.0

    print("\n  Target Reconciliation Highlights:")
    print(f"  * Full Year Target:          {format_currency(total_target)}")
    print(f"  * Full Year Actual Sales:    {format_currency(total_actual)}")
    print(f"  * Overall Variance:          {format_currency(overall_variance)} ({format_pct(overall_achievement)} achieved)")
    print(f"  * Fluctuation Outliers:      {len(fluctuating)} of {len(targets)} months exceeded |MoM| >= {fluctuation_threshold}%")
    if fluctuating:
        outlier_list = ", ".join(f"{f.display_month} ({format_pct(f.mom_target_pct_change, show_sign=True)})" for f in fluctuating)
        print(f"    Months: {outlier_list}")
    print(f"  * Months Meeting Target:     {len(achieved)} of {len(targets)} months ({', '.join(a.display_month for a in achieved) or 'None'})")


def render_state_performance_section(
    states: List[StatePerformance],
    top_n: int,
) -> None:
    """Prints Question 1 Part 3 Regional Performance & Quadrant Classification table."""
    print("\n" + "=" * 106)
    print(f"  QUESTION 1 PART 3: TOP {top_n} STATES REGIONAL PERFORMANCE & STRATEGIC QUADRANTS")
    print("=" * 106)

    headers = [
        "Rank",
        "State",
        "Distinct Orders",
        "Total Sales",
        "Total Profit",
        "Avg Profit/Order",
        "Margin %",
        "Strategic Quadrant",
    ]
    alignments = [">", "<", ">", ">", ">", ">", ">", "<"]

    rows = []
    for s in states:
        rows.append([
            str(s.rank),
            s.state,
            f"{s.distinct_orders:,}",
            format_currency(s.total_sales),
            format_currency(s.total_profit),
            format_currency(s.avg_profit_per_order),
            format_pct(s.profit_margin_pct),
            s.quadrant,
        ])

    print(format_ascii_table(headers, rows, alignments))

    if states:
        highest_sales = AnalyticsEngine.get_highest_sales_state(states)
        highest_margin = AnalyticsEngine.get_highest_margin_state(states)
        lowest_margin = AnalyticsEngine.get_lowest_margin_state(states)

        print("\n  Regional Insights:")
        print(f"  * Top Volume Driver:         {states[0].state} ({states[0].distinct_orders} orders, {format_currency(states[0].total_sales)} sales)")
        print(f"  * Star Margin State:         {highest_margin.state} ({format_pct(highest_margin.profit_margin_pct)} margin, {format_currency(highest_margin.total_profit)} profit)")
        if lowest_margin.total_profit < 0:
            print(f"  * Loss-Leader Risk State:    {lowest_margin.state} ({format_currency(lowest_margin.total_profit)} net loss, {format_pct(lowest_margin.profit_margin_pct)} margin)")


def render_q1_deep_dive_section(
    subcategories: List[SubCategoryPerformance],
    priorities: List[CityPriority],
    insights: Dict[str, Any],
) -> None:
    """Prints the sub-category breakdown, cities to prioritise and Q1 insight bullets."""
    print("\n" + "=" * 92)
    print("  QUESTION 1 DEEP-DIVE: SUB-CATEGORIES, TARGET ALIGNMENT & CITIES TO PRIORITISE")
    print("=" * 92)
    rows = [
        [
            s.category,
            s.sub_category,
            format_currency(s.total_sales),
            format_currency(s.total_profit),
            format_pct(s.profit_margin_pct),
            f"{s.distinct_orders:,}",
        ]
        for s in subcategories
    ]
    print(format_ascii_table(
        ["Category", "Sub-Category", "Sales", "Profit", "Margin %", "Orders"],
        rows,
        ["<", "<", ">", ">", ">", ">"],
    ))
    if priorities:
        print(format_ascii_table(
            ["Action", "City", "State", "Sales", "Margin %"],
            [
                [p.action, p.city, p.state, format_currency(p.total_sales), format_pct(p.profit_margin_pct)]
                for p in priorities
            ],
            ["<", "<", "<", ">", ">"],
        ))
    sections = (
        ("Part 1 - Why categories differ", insights.get("part1_reasons", [])),
        ("Part 1 - Recommendations", insights.get("part1_recommendations", [])),
        ("Part 2 - Aligning targets", insights.get("part2_strategies", [])),
        ("Part 3 - Regional disparities", insights.get("part3_disparities", [])),
    )
    for title, bullets in sections:
        if bullets:
            print(f"\n  {title}:")
            for b in bullets:
                print(f"  * {safe_terminal_text(b)}")


def render_ux_teardown_section(report: UXTeardownReport) -> None:
    """Prints Question 2 Jar App UX Audit & Evaluation summary scorecard."""
    print("\n" + "=" * 108)
    print("  QUESTION 2: JAR APP UX AUDIT & PRODUCT EVALUATION SCORECARD")
    print(f"  Audit Target: {report.app_name} ({report.app_version}) | Period: {report.audit_date}")
    print("=" * 108)

    print("\n  [PART 1: 5 CORE PRODUCT & UX STRENGTHS]")
    headers_s = ["ID", "Feature / Strength Title", "Behavioral Category", "Primary Impact Metric"]
    alignments_s = ["^", "<", "<", "<"]
    rows_s = []
    for s in report.strengths:
        rows_s.append([
            s.id,
            s.title,
            s.category,
            s.primary_impact_metric,
        ])
    print(format_ascii_table(headers_s, rows_s, alignments_s))

    print("\n  [PART 2: 5 PRIORITIZED UX FRICTION POINTS & SOLUTIONS]")
    headers_f = ["ID", "Priority", "Friction Point Title", "Effort", "Primary Impact Metric"]
    alignments_f = ["^", "^", "<", "^", "<"]
    rows_f = []
    for f in report.frictions:
        rows_f.append([
            f.id,
            f.priority,
            f.title,
            f.implementation_effort,
            f.primary_impact_metric,
        ])
    print(format_ascii_table(headers_f, rows_f, alignments_f))

    p0_count = sum(1 for f in report.frictions if f.priority.startswith("P0"))
    p1_count = sum(1 for f in report.frictions if f.priority.startswith("P1"))
    p2_count = sum(1 for f in report.frictions if f.priority.startswith("P2"))

    print("\n  UX Audit Key Takeaways:")
    print(f"  * Core Strengths Identified:   {len(report.strengths)} foundational growth & retention loops")
    print(f"  * Prioritized Friction Areas: {len(report.frictions)} bottlenecks ({p0_count} Critical P0, {p1_count} High P1, {p2_count} Medium P2)")
    print("  * Top Operational Priorities: Transparent GST pre-purchase breakdown + AutoPay smart retry engine")


def render_growth_strategy_section(report: GrowthStrategyReport) -> None:
    """Prints Question 3 Fintech Business & Vertical Expansion Strategy summary."""
    print("\n" + "=" * 114)
    print("  QUESTION 3: FINTECH BUSINESS & VERTICAL EXPANSION STRATEGY")
    print(f"  Version: {report.strategy_version} | Strategic Scope: 5 High-Impact Business Expansion Verticals")
    print("=" * 114)

    print("\n  [STRATEGIC GROWTH VERTICALS & UNIT ECONOMICS]")
    headers_v = [
        "ID",
        "Vertical Name",
        "TAM (INR Cr)",
        "SAM (INR Cr)",
        "SOM (INR Cr)",
        "CAC",
        "LTV",
        "LTV/CAC",
        "Payback",
    ]
    alignments_v = ["^", "<", ">", ">", ">", ">", ">", ">", ">"]
    rows_v = []
    for v in report.verticals:
        rows_v.append([
            v.id,
            v.name,
            f"Rs. {v.market_sizing.tam_numeric_cr:,.0f} Cr",
            f"Rs. {v.market_sizing.sam_numeric_cr:,.0f} Cr",
            f"Rs. {v.market_sizing.som_numeric_cr:,.0f} Cr",
            f"Rs. {v.unit_economics.cac_inr:.0f}",
            f"Rs. {v.unit_economics.ltv_inr:,.0f}",
            f"{v.unit_economics.ltv_cac_ratio:.1f}x",
            f"{v.unit_economics.payback_months:.1f} mo",
        ])
    print(format_ascii_table(headers_v, rows_v, alignments_v))

    print("\n  Market Opportunity & Economics Highlights:")
    print(f"  * Combined Addressable TAM:    Rs. {report.total_tam_cr:,.1f} Cr (~${report.total_tam_cr / 83.33 / 100:.2f}B USD)")
    print(f"  * Serviceable SAM:             Rs. {report.total_sam_cr:,.1f} Cr (~${report.total_sam_cr / 83.33 / 100:.2f}B USD)")
    print(f"  * 36-Month Target SOM:         Rs. {report.total_som_cr:,.1f} Cr (~${report.total_som_cr / 83.33 / 100:.2f}B USD)")

    avg_cac = sum(v.unit_economics.cac_inr for v in report.verticals) / len(report.verticals)
    avg_ltv = sum(v.unit_economics.ltv_inr for v in report.verticals) / len(report.verticals)
    blended_ratio = avg_ltv / avg_cac if avg_cac > 0 else 0
    print(f"  * Blended Unit Economics:      {blended_ratio:.1f}x LTV/CAC (Avg CAC: Rs. {avg_cac:.1f}, Avg LTV: Rs. {avg_ltv:,.1f})")

    high_risks = sum(1 for r in report.execution_risk_matrix if r.severity == "High")
    med_risks = sum(1 for r in report.execution_risk_matrix if r.severity == "Medium")
    low_risks = sum(1 for r in report.execution_risk_matrix if r.severity == "Low")
    print(f"  * Platform Risk Matrix:        {len(report.execution_risk_matrix)} risks identified ({high_risks} High, {med_risks} Medium, {low_risks} Low severity with mitigations)")


def render_export_summary(
    artifacts: Dict[str, Dict[str, Path]],
    strategy_artifacts: Optional[Dict[str, Path]] = None,
) -> None:
    """Prints a summary of all exported data artifacts."""
    print("\n" + "=" * 80)
    print("  EXPORT ARTIFACTS WRITTEN TO DISK")
    print("=" * 80)

    for artifact_name, paths in artifacts.items():
        print(f"\n  [{artifact_name}]")
        for fmt, path in paths.items():
            if path.exists():
                size = path.stat().st_size
                print(f"    - {fmt.upper()}: {path} ({size:,} bytes)")
            else:
                print(f"    - {fmt.upper()}: {path} (pending)")

    if strategy_artifacts:
        for name, path in strategy_artifacts.items():
            print(f"\n  [{name}]")
            if path.exists():
                size = path.stat().st_size
                print(f"    - JSON: {path} ({size:,} bytes)")
            else:
                print(f"    - JSON: {path} (pending)")


# ---------------------------------------------------------------------------
# CLI Argument Parser
# ---------------------------------------------------------------------------

def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parses CLI arguments with environment variable fallbacks."""
    parser = argparse.ArgumentParser(
        description="Jar Growth Intern Assignment - Retail Analytics Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default=os.environ.get("DATA_DIR", "."),
        help="Input directory containing raw Excel workbooks (List of Orders.xlsx, etc.)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=os.environ.get("OUTPUT_DATA_DIR", "data/output"),
        help="Target output directory for JSON and CSV analytical artifacts",
    )
    parser.add_argument(
        "--fluctuation-threshold",
        type=float,
        default=float(os.environ.get("FURNITURE_MOM_FLUCTUATION_THRESHOLD", "15.0")),
        help="MoM percentage change threshold to flag significant furniture target fluctuations",
    )
    parser.add_argument(
        "--top-states",
        type=int,
        default=int(os.environ.get("TOP_STATES_COUNT", "5")),
        help="Number of top states to rank and evaluate for regional performance",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed tabular output and only print execution summary",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.environ.get("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level for pipeline diagnostics",
    )

    return parser.parse_args(args)


# ---------------------------------------------------------------------------
# Main Pipeline Orchestration
# ---------------------------------------------------------------------------

def main(cli_args: Optional[Sequence[str]] = None) -> int:
    """Executes the complete retail analytics ingestion, computation, and export pipeline.

    Args:
        cli_args: Optional command line argument list. If None, reads from sys.argv.

    Returns:
        int: Exit status code (0 for success, 1 for fatal error).
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    start_time = time.time()
    args = parse_args(cli_args)

    # Configure logging
    log_numeric_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if not args.quiet:
        print("\n" + "#" * 80)
        print("  JAR GROWTH INTERN ASSIGNMENT - ANALYTICAL PIPELINE RUNNER")
        print(f"  Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("#" * 80)

    try:
        # Step 1: Data Ingestion
        data_dir = Path(args.data_dir)
        if not args.quiet:
            print(f"\n[1/5] Ingesting datasets from: {data_dir.resolve()} ...")

        orders_df, details_df, targets_df = DataLoader.load_all(data_dir=data_dir)

        if not args.quiet:
            print(f"      - List of Orders:     {len(orders_df):,} orders loaded")
            print(f"      - Order Details:      {len(details_df):,} line items loaded")
            print(f"      - Sales Targets:      {len(targets_df):,} monthly targets loaded")

        # Step 2: Merging Datasets
        if not args.quiet:
            print("\n[2/5] Merging order transactions on 'order_id' ...")

        merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)

        if not args.quiet:
            print(f"      - Merged Transactions: {len(merged_df):,} records ({merged_df['order_id'].nunique():,} unique orders)")

        # Step 3: Analytical Computations
        if not args.quiet:
            print("\n[3/5] Computing analytical models for Question 1 ...")

        # Part 1: Category Sales & Profitability
        category_data = AnalyticsEngine.compute_category_performance(merged_df)

        # Part 2: Furniture Target MoM Fluctuation
        furniture_data = AnalyticsEngine.compute_furniture_target_mom(
            targets_df=targets_df,
            merged_df=merged_df,
            fluctuation_threshold_pct=args.fluctuation_threshold,
        )

        # Part 3: Regional Performance & Quadrants
        state_data = AnalyticsEngine.compute_top_states_performance(
            orders_df=orders_df,
            merged_df=merged_df,
            top_n=args.top_states,
        )
        city_data = AnalyticsEngine.compute_city_performance(merged_df)

        # Deep-dive: sub-categories, cities to prioritise, narrative insights
        subcategory_data = AnalyticsEngine.compute_subcategory_performance(merged_df)
        city_priorities = AnalyticsEngine.compute_city_priorities(merged_df, state_data)
        q1_insights = AnalyticsEngine.build_q1_insights(
            category_data, subcategory_data, furniture_data, state_data, city_priorities
        )

        # Step 4: Loading Strategy & Product Teardown Models
        if not args.quiet:
            print("\n[4/5] Loading Question 2 (UX Teardown) & Question 3 (Growth Strategy) models ...")

        ux_report = get_ux_teardown_report()
        strategy_report = get_growth_strategy_report()

        if not args.quiet:
            print(f"      - Q2 UX Teardown:       {len(ux_report.strengths)} strengths & {len(ux_report.frictions)} friction points loaded")
            print(f"      - Q3 Growth Strategy:   {len(strategy_report.verticals)} growth verticals loaded (TAM: Rs. {strategy_report.total_tam_cr:,.0f} Cr)")

            # Render Terminal Tables if not in quiet mode
            render_category_section(category_data)
            render_furniture_target_section(furniture_data, args.fluctuation_threshold)
            render_state_performance_section(state_data, args.top_states)
            render_q1_deep_dive_section(subcategory_data, city_priorities, q1_insights)
            render_ux_teardown_section(ux_report)
            render_growth_strategy_section(strategy_report)

        # Step 5: Export to Disk
        output_dir = Path(args.output_dir)
        if not args.quiet:
            print(f"\n[5/5] Persisting analytical and strategic outputs to: {output_dir.resolve()} ...")

        exporter = ExportService(output_dir=output_dir)
        artifacts = exporter.export_all(
            category_data=category_data,
            furniture_data=furniture_data,
            state_data=state_data,
            city_data=city_data,
            subcategory_data=subcategory_data,
            city_priorities=city_priorities,
            q1_insights=q1_insights,
        )

        ux_json_path = exporter.export_ux_teardown(report=ux_report, output_dir=output_dir)
        strategy_json_path = exporter.export_growth_strategy(report=strategy_report, output_dir=output_dir)

        strategy_artifacts = {
            "ux_teardown": ux_json_path,
            "growth_strategy": strategy_json_path,
        }

        if not args.quiet:
            render_export_summary(artifacts, strategy_artifacts=strategy_artifacts)

        elapsed = time.time() - start_time
        print("\n" + "=" * 80)
        print(f"  PIPELINE EXECUTION COMPLETED SUCCESSFULLY in {elapsed:.2f} seconds.")
        print("=" * 80 + "\n")
        return 0

    except Exception as exc:
        logger.exception("Pipeline execution failed with fatal error: %s", exc)
        print(f"\n[ERROR] Pipeline failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
