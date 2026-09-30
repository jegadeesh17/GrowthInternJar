"""CLI entry point: python -m src.generate_pdf

Builds the internal submission note (at most 2 pages) that points reviewers to
the live dashboard and the source repository. It does not repeat the analysis.

Environment variables:
    OUTPUT_PDF_PATH   PDF destination (default: <workspace>/data/output/Jegadeesh_D_Jar_Growth_Intern_Assignment.pdf).
    CANDIDATE_NAME    Name printed under the title.
    DASHBOARD_URL     Live dashboard link (default: the GitHub Pages URL).
    REPO_URL          Source repository link.

Exit codes: 0 on success, 1 on an output error.
"""

import logging
import os
import sys
from pathlib import Path

from src.pdf_generator import PdfGenerator

logger = logging.getLogger("src.generate_pdf")

EXIT_OK = 0
EXIT_FAILURE = 1


def run() -> int:
    """Builds the note and returns a process exit code."""
    workspace = Path(__file__).resolve().parent.parent
    output_path = Path(
        os.getenv(
            "OUTPUT_PDF_PATH",
            str(workspace / "data" / "output" / "Jegadeesh_D_Jar_Growth_Intern_Assignment.pdf"),
        )
    )
    gen = PdfGenerator()
    try:
        out = gen.build_submission_pdf(output_path)
    except (OSError, RuntimeError) as exc:
        print(f"ERROR: Could not generate PDF: {exc}", file=sys.stderr)
        return EXIT_FAILURE

    print(f"SUCCESS: {out} ({out.stat().st_size // 1024} KB, {gen.page_count} page(s))")
    return EXIT_OK


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    sys.exit(run())


if __name__ == "__main__":
    main()
