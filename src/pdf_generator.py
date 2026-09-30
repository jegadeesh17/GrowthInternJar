"""Submission cover note PDF (fpdf2).

The PDF is for internal submission only. It does not repeat the analysis: it
tells the reviewer where the live dashboard and source code are, and which
dashboard section answers each assignment question. It fits on one A4 page
(the hard limit is two).

Colours follow DESIGN.md (lavender primary, grey ink ramp) so the note and the
dashboard look like one submission.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

from fpdf import FPDF

DEFAULT_CANDIDATE_NAME = "Jegadeesh D"
DEFAULT_DASHBOARD_URL = "https://jegadeesh17.github.io/GrowthInternJar/"
DEFAULT_REPO_URL = "https://github.com/jegadeesh17/GrowthInternJar"
NOTEBOOK_PATH = "blob/main/Jar_Growth_Intern_Assignment.ipynb"
MAX_PAGES = 2

# DESIGN.md tokens
INK = (28, 37, 46)          # grey-800
MUTED = (99, 115, 129)      # grey-600
LINE = (223, 227, 232)      # grey-300
LAV = (91, 74, 192)         # lav-600
LAV_BG = (243, 241, 255)    # lav-50
LAV_EDGE = (213, 206, 250)  # lav-200

MARGIN = 18
PAGE_W = 210
INNER_W = PAGE_W - 2 * MARGIN

# (question, marks, dashboard section, what the section covers)
QUESTION_MAP: List[Tuple[str, str, str, str]] = [
    (
        "Q1  Sales analysis",
        "30 marks",
        "Sales analytics\nParts 1-3",
        "Category sales, average profit per order and margin; Furniture target "
        "month-over-month change and alignment strategies; top 5 states by order "
        "count, regional disparities and the cities to prioritise.",
    ),
    (
        "Q2  App exploration",
        "10 marks",
        "App teardown",
        "Five things the Jar app does well and five improvements, each with its reasoning.",
    ),
    (
        "Q3  Product exploration",
        "10 marks",
        "Expansion strategy",
        "New business opportunities for Jar, how each uses its automation, design "
        "and trust, the risks to manage, and the two I would start with.",
    ),
    (
        "Method",
        "",
        "Methodology",
        "Data preparation, formulas and in-browser checks that the numbers reconcile.",
    ),
]

REVIEW_STEPS = [
    "Open the dashboard. The Overview shows the headline numbers and key findings.",
    "Use the sidebar to go through Q1 (three parts), Q2 and Q3 in order.",
    "Open the notebook to see the Python code and output behind every figure.",
]

BUILD_NOTES = [
    "Every figure is computed in Python (pandas) from the three assignment datasets; "
    "none are typed in by hand. The notebook recomputes Question 1 step by step and "
    "checks it against the pipeline.",
    "The pipeline's outputs are embedded into the dashboard page, and an automated pytest "
    "suite checks the calculations and edge cases.",
]


class SubmissionPdf(FPDF):
    """A4 page with a thin footer; everything else is drawn by PdfGenerator."""

    def footer(self) -> None:
        self.set_y(-14)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 5, "Jar Growth Intern assignment - submission note", align="L")
        self.cell(0, 5, f"{self.page_no()}", align="R")


class PdfGenerator:
    """Builds the submission cover note."""

    def __init__(
        self,
        candidate_name: Optional[str] = None,
        dashboard_url: Optional[str] = None,
        repo_url: Optional[str] = None,
        submission_date: Optional[date] = None,
    ) -> None:
        self.candidate_name = (
            candidate_name or os.getenv("CANDIDATE_NAME", "").strip() or DEFAULT_CANDIDATE_NAME
        )
        self.dashboard_url = (
            dashboard_url or os.getenv("DASHBOARD_URL", "").strip() or DEFAULT_DASHBOARD_URL
        )
        self.repo_url = repo_url or os.getenv("REPO_URL", "").strip() or DEFAULT_REPO_URL
        self.notebook_url = f"{self.repo_url.rstrip('/')}/{NOTEBOOK_PATH}"
        self.submission_date = submission_date or date.today()
        self.page_count = 0

    def build_submission_pdf(self, output_path: "str | Path") -> Path:
        """Writes the note to output_path and returns the resolved path.

        Raises:
            RuntimeError: If the content overflows MAX_PAGES.
        """
        pdf = SubmissionPdf(format="A4")
        pdf.set_margins(MARGIN, MARGIN, MARGIN)
        pdf.set_auto_page_break(True, margin=20)
        pdf.set_title("Jar Growth Intern Assignment - Submission")
        pdf.set_author(self.candidate_name)
        pdf.add_page()

        self._header(pdf)
        self._links_card(pdf)
        self._section_title(pdf, "Where each question is answered")
        self._question_table(pdf)
        self._section_title(pdf, "Suggested review path")
        self._numbered(pdf, REVIEW_STEPS)
        self._section_title(pdf, "How the answers were produced")
        self._bullets(pdf, BUILD_NOTES)

        self.page_count = pdf.page_no()
        if self.page_count > MAX_PAGES:
            raise RuntimeError(f"Submission note is {self.page_count} pages; limit is {MAX_PAGES}")

        out = Path(output_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        pdf.output(str(out))
        return out

    # ---------- blocks ----------

    def _header(self, pdf: FPDF) -> None:
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*LAV)
        pdf.cell(0, 5, "JAR  |  GROWTH INTERN ASSIGNMENT", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(*INK)
        pdf.cell(0, 11, "Assignment submission", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10.5)
        pdf.set_text_color(*MUTED)
        when = f"{self.submission_date.day} {self.submission_date:%B %Y}"
        pdf.cell(0, 6, f"{self.candidate_name}  |  {when}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(5)
        pdf.set_font("Helvetica", "", 10.5)
        pdf.set_text_color(*INK)
        pdf.multi_cell(
            INNER_W,
            5.4,
            "All three answers are published as an interactive dashboard and as a Python "
            "notebook with the code and its output. This note only points to them.",
            align="L",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(5)

    def _links_card(self, pdf: FPDF) -> None:
        x, y, h = MARGIN, pdf.get_y(), 47
        pdf.set_fill_color(*LAV_BG)
        pdf.set_draw_color(*LAV_EDGE)
        pdf.set_line_width(0.3)
        pdf.rect(x, y, INNER_W, h, style="DF", round_corners=True, corner_radius=4)

        pad = 6
        pdf.set_xy(x + pad, y + pad)
        self._link_row(pdf, "Live dashboard (start here)", self.dashboard_url, big=True)
        pdf.set_x(x + pad)
        pdf.ln(1.5)
        pdf.set_x(x + pad)
        self._link_row(pdf, "Python notebook (code and output)", self.notebook_url, big=False)
        pdf.set_x(x + pad)
        pdf.ln(1.5)
        pdf.set_x(x + pad)
        self._link_row(pdf, "Source code and pipeline", self.repo_url, big=False)
        pdf.set_y(y + h + 6)

    def _link_row(self, pdf: FPDF, label: str, url: str, big: bool) -> None:
        left = pdf.get_x()
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(0, 5, label.upper(), new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(left)
        pdf.set_font("Helvetica", "BU" if big else "U", 13 if big else 10.5)
        pdf.set_text_color(*LAV)
        pdf.cell(0, 7 if big else 6, url, link=url, new_x="LMARGIN", new_y="NEXT")

    def _section_title(self, pdf: FPDF, text: str) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(*INK)
        pdf.cell(0, 7, text, align="L", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1.5)

    def _question_table(self, pdf: FPDF) -> None:
        col_q, col_where = 44, 46
        col_what = INNER_W - col_q - col_where
        line_h = 4.8

        pdf.set_draw_color(*LINE)
        pdf.set_line_width(0.2)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(col_q, 6, "Assignment")
        pdf.cell(col_where, 6, "Dashboard section")
        pdf.cell(col_what, 6, "What it covers", new_x="LMARGIN", new_y="NEXT")
        pdf.line(MARGIN, pdf.get_y(), MARGIN + INNER_W, pdf.get_y())

        for question, marks, where, what in QUESTION_MAP:
            top = pdf.get_y() + 2.5
            pdf.set_font("Helvetica", "", 9.5)
            rows = len(pdf.multi_cell(col_what, line_h, what, align="L", dry_run=True, output="LINES"))
            height = max(rows * line_h, 2 * line_h)

            pdf.set_xy(MARGIN, top)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*INK)
            pdf.cell(col_q, line_h, question)
            if marks:
                pdf.set_xy(MARGIN, top + line_h)
                pdf.set_font("Helvetica", "", 8.5)
                pdf.set_text_color(*MUTED)
                pdf.cell(col_q, line_h, marks)

            pdf.set_xy(MARGIN + col_q, top)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*LAV)
            pdf.multi_cell(col_where - 3, line_h, where, align="L")

            pdf.set_xy(MARGIN + col_q + col_where, top)
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(*INK)
            pdf.multi_cell(col_what, line_h, what, align="L")

            bottom = top + height + 2.5
            pdf.line(MARGIN, bottom, MARGIN + INNER_W, bottom)
            pdf.set_y(bottom)
        pdf.ln(5)

    def _numbered(self, pdf: FPDF, items: List[str]) -> None:
        for i, text in enumerate(items, start=1):
            y = pdf.get_y()
            pdf.set_fill_color(*LAV_BG)
            pdf.ellipse(MARGIN, y + 0.2, 5, 5, style="F")
            pdf.set_xy(MARGIN, y + 0.2)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_text_color(*LAV)
            pdf.cell(5, 5, str(i), align="C")
            pdf.set_xy(MARGIN + 8, y)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*INK)
            pdf.multi_cell(INNER_W - 8, 5.4, text, align="L", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1.5)
        pdf.ln(3)

    def _bullets(self, pdf: FPDF, items: List[str]) -> None:
        for text in items:
            y = pdf.get_y()
            pdf.set_fill_color(*LAV)
            pdf.ellipse(MARGIN + 1.5, y + 2, 1.6, 1.6, style="F")
            pdf.set_xy(MARGIN + 8, y)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(*INK)
            pdf.multi_cell(INNER_W - 8, 5.4, text, align="L", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1.5)
