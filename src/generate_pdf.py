"""CLI entry point: python -m src.generate_pdf

Orchestrates the complete analytics pipeline, renders the pastel 300 DPI
charts (assets/charts/*.png) via ChartGenerator, and generates the executive
PDF submission document: Jar_Growth_Intern_Assignment_Submission.pdf

Environment variables:
    DATA_DIR          Directory holding the input Excel files (default: workspace root).
    CHART_ASSETS_DIR  Chart output directory (default: <workspace>/assets/charts).
    OUTPUT_PDF_PATH   PDF destination (default: <workspace>/Jar_Growth_Intern_Assignment_Submission.pdf).
    CANDIDATE_NAME    Name printed on the cover page.

Exit codes: 0 on success, 1 on a data/rendering/output error.
"""

import logging
import os
import sys
import zipfile
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger("src.generate_pdf")

EXIT_OK = 0
EXIT_FAILURE = 1


def _configure_utf8_streams() -> None:
    """Switches stdout/stderr to UTF-8 so rupee symbols in logs never crash."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError) as exc:
            logger.debug("Could not reconfigure stream encoding: %s", exc)


def _render_charts(
    category_data: List,
    furniture_data: List,
    state_data: List,
    charts_dir: Path,
) -> Dict[str, Path]:
    """Renders all charts; on failure logs a warning and returns an empty manifest.

    The PDF build then falls back to any chart PNGs already in ``charts_dir``
    and renders a labelled placeholder for charts that are still missing.
    """
    try:
        from src.chart_generator import ChartGenerator

        return ChartGenerator.generate_all_charts(
            category_data=category_data,
            furniture_data=furniture_data,
            state_data=state_data,
            output_dir=charts_dir,
        )
    except ImportError as exc:
        logger.warning("Chart rendering unavailable (missing dependency: %s).", exc)
    except (OSError, ValueError, RuntimeError, TypeError, KeyError) as exc:
        logger.warning("Chart rendering failed: %s", exc)
    logger.warning(
        "Continuing with existing chart files in '%s' (placeholders for any missing).",
        charts_dir,
    )
    return {}


def run() -> int:
    """Runs the full pipeline and returns a process exit code."""
    workspace = Path(__file__).resolve().parent.parent

    from src.data_loader import DataLoader
    from src.analytics_engine import AnalyticsEngine
    from src.pdf_generator import PdfGenerator

    data_dir = Path(os.getenv("DATA_DIR", str(workspace)))
    charts_dir = Path(
        os.getenv("CHART_ASSETS_DIR", str(workspace / "assets" / "charts"))
    )
    output_path = Path(
        os.getenv(
            "OUTPUT_PDF_PATH",
            str(workspace / "Jar_Growth_Intern_Assignment_Submission.pdf"),
        )
    )

    try:
        logger.info("Loading datasets from: %s", data_dir)
        orders_df, details_df, targets_df = DataLoader.load_all(data_dir=data_dir)

        logger.info("Merging order transactions...")
        merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)

        logger.info("Computing analytics...")
        cat_data = AnalyticsEngine.compute_category_performance(merged_df)
        furn_data = AnalyticsEngine.compute_furniture_target_mom(targets_df, merged_df)
        state_data = AnalyticsEngine.compute_top_states_performance(orders_df, merged_df)
    except FileNotFoundError as exc:
        print(f"ERROR: Input data not found: {exc}", file=sys.stderr)
        print(
            "Set DATA_DIR to the folder containing 'List of Orders.xlsx', "
            "'Order Details.xlsx' and 'Sales target.xlsx'.",
            file=sys.stderr,
        )
        return EXIT_FAILURE
    except (zipfile.BadZipFile, OSError, EOFError) as exc:
        # Corrupt or unreadable .xlsx files (openpyxl/pandas raise these).
        print(f"ERROR: Could not read input data: {exc}", file=sys.stderr)
        return EXIT_FAILURE
    except (ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: Input data is invalid: {exc}", file=sys.stderr)
        return EXIT_FAILURE

    logger.info("Rendering charts into: %s", charts_dir)
    chart_paths = _render_charts(cat_data, furn_data, state_data, charts_dir)

    logger.info("Generating executive PDF...")
    gen = PdfGenerator(chart_paths=chart_paths)
    try:
        out = gen.build_submission_pdf(
            output_path=output_path,
            category_data=cat_data,
            furniture_data=furn_data,
            state_data=state_data,
            charts_dir=charts_dir if charts_dir.is_dir() else None,
        )
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: Could not generate PDF: {exc}", file=sys.stderr)
        return EXIT_FAILURE

    size_kb = out.stat().st_size // 1024
    if gen.missing_charts:
        print(
            "WARNING: PDF contains placeholders for missing charts: "
            + ", ".join(gen.missing_charts),
            file=sys.stderr,
        )
    print(f"SUCCESS: {out} ({size_kb} KB, {gen.page_count} pages)")
    return EXIT_OK


def main() -> None:
    """Run the full analytics pipeline and emit the executive PDF."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    _configure_utf8_streams()
    sys.exit(run())


if __name__ == "__main__":
    main()
