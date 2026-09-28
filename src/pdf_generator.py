"""Executive PDF submission generator for Jar Growth Intern Assignment.

Implements M3-TASK-02 (SPEC AC-4.2):
- Compiles Jar_Growth_Intern_Assignment_Submission.pdf using fpdf2.
- A4 layout with custom running header and 'Page X of Y' footer (JarPDF).
- Cover page, executive summary, Q1 data tables + embedded 300 DPI charts,
  Q2 Jar app exploration (5 strengths, 5 improvements), Q3 growth strategy
  (5 verticals with unit economics) and an execution risk matrix.
- Uses only Helvetica (built-in). All text routed through _clean() to
  strip non-latin-1 characters safely.
- Missing chart images never crash the build: a clearly labelled
  placeholder callout is rendered instead and a warning is logged.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from fpdf import FPDF
from fpdf.enums import MethodReturnValue, XPos, YPos
from fpdf.fonts import FontFace

from src.analytics_engine import (
    CategoryPerformance,
    FurnitureTargetAchievement,
    StatePerformance,
)
from src.content.ux_teardown import get_ux_strengths, get_ux_frictions
from src.content.growth_strategy import (
    get_growth_strategy_report,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pastel Design Token Constants (RGB tuples)
# ---------------------------------------------------------------------------

SAGE = (72, 187, 120)
SAGE_BG = (230, 255, 250)
GOLD = (214, 158, 46)
GOLD_BG = (254, 252, 191)
LAVENDER = (128, 90, 213)
LAVENDER_BG = (250, 245, 255)
CORAL = (229, 62, 62)
CORAL_BG = (255, 245, 245)
SLATE = (45, 55, 72)
SLATE_MUTED = (113, 128, 150)
CARD_BG = (247, 250, 252)
WHITE = (255, 255, 255)

# Page geometry constants
PAGE_W = 210
PAGE_H = 297
MARGIN = 15
INNER_W = PAGE_W - 2 * MARGIN
# Lowest y (mm) that body content may reach; the footer rule sits at PAGE_H - 10.
CONTENT_BOTTOM = PAGE_H - 16
# Minimum chart height (mm) worth scaling down to before moving to a new page.
MIN_CHART_H = 60

DEFAULT_CANDIDATE_NAME = "Growth Intern Candidate"

# Chart identifiers (ChartGenerator manifest keys) -> accepted file names.
CHART_FILES: Dict[str, Tuple[str, ...]] = {
    "category_profitability": ("category_profitability.png",),
    "furniture_target_vs_actual": (
        "furniture_target_vs_actual.png",
        "furniture_target_trajectory.png",
    ),
    "regional_performance": (
        "regional_performance.png",
        "state_regional_quadrants.png",
    ),
}

# Line-break-after-cell arguments (replacement for the deprecated ln=True).
NEXT_LINE = {"new_x": XPos.LMARGIN, "new_y": YPos.NEXT}


# ---------------------------------------------------------------------------
# JarPDF: FPDF subclass with custom header & footer
# ---------------------------------------------------------------------------

class JarPDF(FPDF):
    """FPDF subclass implementing the Jar submission header and footer."""

    def header(self) -> None:
        """Muted Gold top rule + running title line; skipped on cover page."""
        if self.page_no() <= 1:
            return  # No header on cover
        self.set_draw_color(*GOLD)
        self.set_line_width(0.4)
        self.line(MARGIN, 8, PAGE_W - MARGIN, 8)
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*SLATE)
        self.set_xy(MARGIN, 9)
        self.cell(
            INNER_W / 2,
            4,
            _clean_static("Jar Growth Intern Assignment - Confidential Submission"),
            align="L",
        )
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*SLATE_MUTED)
        self.cell(
            INNER_W / 2,
            4,
            _clean_static("Sales Analytics | App Exploration | Growth Strategy"),
            align="R",
        )
        self.set_line_width(0.2)
        self.set_xy(MARGIN, MARGIN)

    def footer(self) -> None:
        """Sage bottom rule + 'Page X of Y' centred; skipped on cover page."""
        if self.page_no() <= 1:
            return  # No footer on cover
        self.set_draw_color(*SAGE)
        self.set_line_width(0.5)
        self.line(MARGIN, PAGE_H - 10, PAGE_W - MARGIN, PAGE_H - 10)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*SLATE_MUTED)
        self.set_xy(MARGIN, PAGE_H - 9)
        self.cell(
            INNER_W,
            4,
            f"Page {self.page_no()} of {{nb}}",
            align="C",
        )


def _clean_static(text: str) -> str:
    """Module-level clean helper (used by JarPDF before self is available)."""
    if not text:
        return ""
    text = str(text).replace("₹", "Rs.")  # Rupee sign -> Rs.
    text = (
        text.replace("–", "-")
        .replace("—", "-")
        .replace("‘", "'")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("•", "-")
        .replace("→", "->")
        .replace("≤", "<=")
        .replace("≥", ">=")
        .replace("×", "x")
    )
    return text.encode("latin-1", errors="ignore").decode("latin-1")


def _shorten(text: str, limit: int) -> str:
    """Trims text to ``limit`` characters at a sentence or word boundary.

    Prefers ending on a full sentence; otherwise cuts at the last whole word
    and appends an ellipsis. Never cuts mid-word.
    """
    if not text:
        return ""
    flat = " ".join(str(text).split())
    if len(flat) <= limit:
        return flat
    window = flat[:limit]
    sentence_end = window.rfind(". ")
    if sentence_end >= int(limit * 0.5):
        # Drop a dangling list enumerator such as " 2." left by the cut.
        return re.sub(r"\s+\d+\.$", "", window[: sentence_end + 1])
    space = window.rfind(" ")
    if space > 0:
        window = window[:space]
    return window.rstrip(" ,;:-(") + "..."


def _list_headlines(text: str, limit: int) -> str:
    """Condenses a multi-line numbered list into its item headlines.

    Each line such as ``"1. Smart Retry Engine: details..."`` becomes
    ``"1. Smart Retry Engine"``; items are joined with ``"; "``. Text that is
    not a multi-line list falls back to :func:`_shorten`.
    """
    if not text:
        return ""
    lines = [ln.strip() for ln in str(text).splitlines() if ln.strip()]
    if len(lines) < 2:
        return _shorten(text, limit)
    heads = [ln.split(":", 1)[0].strip() if ":" in ln else _shorten(ln, 60) for ln in lines]
    return _shorten("; ".join(heads), limit)


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9'\"(])")


def _first_sentences(text: str, count: int, limit: int) -> str:
    """Returns up to ``count`` leading whole sentences of ``text``.

    Sentences are dropped from the end while the result exceeds ``limit``
    characters, but at least one full sentence is always kept.
    """
    if not text:
        return ""
    flat = " ".join(str(text).split())
    sentences = [part for part in _SENTENCE_SPLIT.split(flat) if part]
    chosen = sentences[: max(count, 1)]
    while len(chosen) > 1 and len(" ".join(chosen)) > limit:
        chosen.pop()
    return " ".join(chosen)


def _problem_statement(text: str) -> str:
    """Returns the opening (context) and closing (consequence) sentences.

    Friction descriptions set the scene first and state the user-facing
    problem last, so both ends are kept and the middle is dropped.
    """
    if not text:
        return ""
    flat = " ".join(str(text).split())
    sentences = [part for part in _SENTENCE_SPLIT.split(flat) if part]
    if len(sentences) <= 2:
        return " ".join(sentences)
    return f"{sentences[0]} {sentences[-1]}"


def _first_fix(solution: str) -> str:
    """Turns the first numbered solution line into ``"Headline. First sentence."``."""
    if not solution:
        return ""
    lines = [ln.strip() for ln in str(solution).splitlines() if ln.strip()]
    if not lines:
        return ""
    first = re.sub(r"^\d+\.\s*", "", lines[0])
    if ":" in first:
        head, rest = first.split(":", 1)
        rest = _first_sentences(rest, 1, 10_000)
        return f"{head.strip()}. {rest}" if rest else f"{head.strip()}."
    return _first_sentences(first, 1, 10_000)


# ---------------------------------------------------------------------------
# PdfGenerator Class
# ---------------------------------------------------------------------------

class PdfGenerator:
    """Compiles the executive PDF submission document using fpdf2.

    Usage::

        gen = PdfGenerator(chart_paths=ChartGenerator.generate_all_charts(...))
        out = gen.build_submission_pdf(
            output_path="Jar_Growth_Intern_Assignment_Submission.pdf",
            category_data=cat_data,
            furniture_data=furn_data,
            state_data=state_data,
            charts_dir=Path("assets/charts"),
        )
    """

    def __init__(self, chart_paths: Optional[Dict[str, Path]] = None) -> None:
        """Initialises the generator.

        Args:
            chart_paths: Optional chart manifest (as returned by
                ChartGenerator.generate_all_charts) mapping chart identifiers
                to PNG paths. Takes precedence over ``charts_dir`` lookups.
        """
        self.chart_paths: Dict[str, Path] = {}
        if chart_paths:
            for key, value in chart_paths.items():
                if value is not None:
                    self.chart_paths[str(key)] = Path(value)
        self.missing_charts: List[str] = []
        self.page_count: int = 0

    def _clean(self, text: str) -> str:
        """Strips non-latin-1 characters; converts the rupee symbol to 'Rs.'."""
        return _clean_static(text)

    def _set_color(
        self,
        pdf: FPDF,
        rgb: Tuple[int, int, int],
        stroke: bool = False,
    ) -> None:
        """Sets fill or stroke color from an RGB tuple."""
        if stroke:
            pdf.set_draw_color(*rgb)
        else:
            pdf.set_fill_color(*rgb)

    def _h1(self, pdf: JarPDF, text: str) -> None:
        """Renders an H1 section heading with a Sage underline rule."""
        pdf.set_x(MARGIN)
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(*SLATE)
        pdf.multi_cell(INNER_W, 8, self._clean(text), align="L", **NEXT_LINE)
        y = pdf.get_y()
        pdf.set_draw_color(*SAGE)
        pdf.set_line_width(0.6)
        pdf.line(MARGIN, y, PAGE_W - MARGIN, y)
        pdf.set_line_width(0.2)
        pdf.ln(3)

    def _h2(self, pdf: JarPDF, text: str) -> None:
        """Renders an H2 section heading with a Sage underline rule."""
        pdf.set_x(MARGIN)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*SLATE)
        pdf.multi_cell(INNER_W, 7, self._clean(text), align="L", **NEXT_LINE)
        y = pdf.get_y()
        pdf.set_draw_color(*SAGE)
        pdf.set_line_width(0.4)
        pdf.line(MARGIN, y, MARGIN + INNER_W * 0.4, y)
        pdf.set_line_width(0.2)
        pdf.ln(2)

    def _subheading(
        self,
        pdf: JarPDF,
        text: str,
        color: Tuple[int, int, int],
    ) -> None:
        """Renders a small coloured sub-heading followed by a line break."""
        pdf.set_x(MARGIN)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*color)
        pdf.cell(INNER_W, 7, self._clean(text), **NEXT_LINE)
        pdf.ln(1)

    def _paragraph(self, pdf: JarPDF, text: str, font_size: int = 9) -> None:
        """Renders a justified body paragraph across the full content width."""
        pdf.set_x(MARGIN)
        pdf.set_font("Helvetica", "", font_size)
        pdf.set_text_color(*SLATE)
        pdf.multi_cell(INNER_W, 4.8, self._clean(text), align="J", **NEXT_LINE)

    def _ensure_space(self, pdf: JarPDF, needed_h: float) -> None:
        """Starts a new page if ``needed_h`` mm do not fit above the footer."""
        if pdf.get_y() + needed_h > CONTENT_BOTTOM:
            pdf.add_page()

    # -----------------------------------------------------------------------
    # Cards / callouts
    # -----------------------------------------------------------------------

    def card_height(
        self,
        pdf: JarPDF,
        w: float,
        text: str,
        font_size: int = 9,
        title: str = "",
        min_h: float = 0.0,
    ) -> float:
        """Measures the height a card needs to hold its title and text.

        Args:
            pdf: Active JarPDF instance (used for font metrics).
            w: Card width (mm).
            text: Card body text.
            font_size: Body font size in points.
            title: Optional bold title rendered above the body.
            min_h: Minimum card height (mm).

        Returns:
            float: Required card height in mm (never below ``min_h``).
        """
        pad = 2
        line_h = font_size * 0.5
        inner_w = w - 2 * pad
        total = 2 * pad
        if title:
            pdf.set_font("Helvetica", "B", font_size + 1)
            title_lines = pdf.multi_cell(
                inner_w,
                line_h + 0.5,
                self._clean(title),
                dry_run=True,
                output=MethodReturnValue.LINES,
            )
            total += len(title_lines) * (line_h + 0.5) + 0.5
        if text:
            pdf.set_font("Helvetica", "", font_size)
            body_lines = pdf.multi_cell(
                inner_w,
                line_h,
                self._clean(text),
                dry_run=True,
                output=MethodReturnValue.LINES,
            )
            total += len(body_lines) * line_h
        return max(float(min_h), total)

    def draw_card(
        self,
        pdf: JarPDF,
        x: float,
        y: float,
        w: float,
        h: float,
        fill_rgb: Tuple[int, int, int],
        border_rgb: Tuple[int, int, int],
        text: str,
        text_color_rgb: Tuple[int, int, int],
        font_size: int = 9,
        title: str = "",
    ) -> float:
        """Draws a pastel callout card with an optional bold title and body text.

        The card grows beyond ``h`` when the text needs more room, so text never
        overflows the card border.

        Args:
            pdf: Active JarPDF instance.
            x, y: Top-left corner position (mm).
            w, h: Card width and minimum height (mm).
            fill_rgb: Background fill colour as RGB tuple.
            border_rgb: Border stroke colour as RGB tuple.
            text: Card body text.
            text_color_rgb: Text colour as RGB tuple.
            font_size: Font size in points (default 9).
            title: Optional bold title line(s) above the body.

        Returns:
            float: The actual card height drawn (mm).
        """
        if w <= 0:
            raise ValueError(f"Card width must be positive, got {w}")
        actual_h = self.card_height(pdf, w, text, font_size, title=title, min_h=h)
        pad = 2
        line_h = font_size * 0.5

        self._set_color(pdf, fill_rgb, stroke=False)
        self._set_color(pdf, border_rgb, stroke=True)
        pdf.set_line_width(0.3)
        pdf.rect(x, y, w, actual_h, style="FD")
        # Accent bar on the left edge
        self._set_color(pdf, border_rgb, stroke=False)
        pdf.rect(x, y, 1.2, actual_h, style="F")

        pdf.set_xy(x + pad, y + pad)
        pdf.set_text_color(*text_color_rgb)
        if title:
            pdf.set_font("Helvetica", "B", font_size + 1)
            pdf.multi_cell(
                w - 2 * pad, line_h + 0.5, self._clean(title), align="L",
                new_x=XPos.LEFT, new_y=YPos.NEXT,
            )
            pdf.set_y(pdf.get_y() + 0.5)
            pdf.set_x(x + pad)
        if text:
            pdf.set_font("Helvetica", "", font_size)
            pdf.multi_cell(
                w - 2 * pad, line_h, self._clean(text), align="L",
                new_x=XPos.LEFT, new_y=YPos.NEXT,
            )
        pdf.set_xy(MARGIN, y + actual_h)
        return actual_h

    def _flow_card(
        self,
        pdf: JarPDF,
        title: str,
        text: str,
        fill_rgb: Tuple[int, int, int],
        border_rgb: Tuple[int, int, int],
        font_size: int = 8,
        gap: float = 3,
    ) -> None:
        """Draws a full-width card at the cursor, breaking the page if needed."""
        needed = self.card_height(pdf, INNER_W, text, font_size, title=title)
        self._ensure_space(pdf, needed)
        self.draw_card(
            pdf,
            x=MARGIN, y=pdf.get_y(),
            w=INNER_W, h=0,
            fill_rgb=fill_rgb, border_rgb=border_rgb,
            text=text, text_color_rgb=SLATE,
            font_size=font_size, title=title,
        )
        pdf.set_y(pdf.get_y() + gap)

    # -----------------------------------------------------------------------
    # Tables
    # -----------------------------------------------------------------------

    def _render_table(
        self,
        pdf: JarPDF,
        headers: Sequence[str],
        rows: Sequence[Sequence[str]],
        col_widths: Sequence[float],
        header_rgb: Tuple[int, int, int],
        row_fills: Sequence[Tuple[int, int, int]],
        font_size: int = 8,
        text_align: str = "CENTER",
    ) -> None:
        """Renders a styled table with wrapped cells, a coloured header row and
        per-row pastel fills.

        Args:
            pdf: Active JarPDF instance.
            headers: Column header labels.
            rows: Row values (already formatted strings).
            col_widths: Relative column widths.
            header_rgb: Header row fill colour.
            row_fills: Fill colour per row (same length as ``rows``).
            font_size: Body font size in points.
            text_align: fpdf2 alignment for body cells.
        """
        pdf.set_x(MARGIN)
        pdf.set_font("Helvetica", "", font_size)
        pdf.set_text_color(*SLATE)
        pdf.set_draw_color(*SLATE_MUTED)
        pdf.set_line_width(0.1)
        heading_style = FontFace(emphasis="BOLD", color=WHITE, fill_color=header_rgb)
        with pdf.table(
            width=INNER_W,
            col_widths=tuple(col_widths),
            text_align=text_align,
            line_height=font_size * 0.55,
            headings_style=heading_style,
            padding=1,
            align="LEFT",
        ) as table:
            header_row = table.row()
            for label in headers:
                header_row.cell(self._clean(label), align="CENTER")
            for values, fill in zip(rows, row_fills):
                row = table.row()
                style = FontFace(fill_color=fill)
                for val in values:
                    row.cell(self._clean(val), style=style)
        pdf.set_line_width(0.2)
        pdf.set_x(MARGIN)

    # -----------------------------------------------------------------------
    # Charts
    # -----------------------------------------------------------------------

    def _resolve_chart(self, key: str, charts_dir: Optional[Path]) -> Optional[Path]:
        """Finds the chart PNG for ``key`` via the manifest, then ``charts_dir``."""
        manifest_path = self.chart_paths.get(key)
        if manifest_path is not None and manifest_path.is_file():
            return manifest_path
        if charts_dir is not None:
            for name in CHART_FILES.get(key, (f"{key}.png",)):
                candidate = charts_dir / name
                if candidate.is_file():
                    return candidate
        return None

    def _chart_placeholder(self, pdf: JarPDF, key: str) -> None:
        """Renders a visible callout noting that a chart image is unavailable."""
        file_name = CHART_FILES.get(key, (f"{key}.png",))[0]
        if key not in self.missing_charts:
            self.missing_charts.append(key)
        logger.warning(
            "Chart '%s' not found; rendering a placeholder in the PDF.", file_name
        )
        self._flow_card(
            pdf,
            title=f"Chart unavailable: {file_name}",
            text=(
                "The chart image could not be found in assets/charts/. Run "
                "'python -m src.generate_pdf' (which renders all charts) or "
                "'python -m src.chart_generator' to regenerate it."
            ),
            fill_rgb=GOLD_BG,
            border_rgb=GOLD,
        )

    def _embed_image(
        self,
        pdf: JarPDF,
        path: Optional[Path],
        max_w_mm: float = INNER_W,
        key: str = "",
    ) -> bool:
        """Embeds a PNG chart scaled to fit the remaining page space.

        Missing or unreadable images are replaced by a placeholder callout
        (when ``key`` is given) instead of raising.

        Args:
            pdf: Active JarPDF instance.
            path: Path to the PNG file, or None.
            max_w_mm: Maximum width in mm (default: INNER_W).
            key: Chart identifier used for the placeholder label.

        Returns:
            bool: True if the image was embedded.
        """
        if path is None or not Path(path).is_file():
            if key:
                self._chart_placeholder(pdf, key)
            else:
                logger.warning("Chart not found, skipping: %s", path)
            return False
        try:
            from PIL import Image  # Pillow is a hard dependency of fpdf2

            with Image.open(path) as img:
                px_w, px_h = img.size
            if px_w <= 0 or px_h <= 0:
                raise ValueError(f"Invalid image dimensions {px_w}x{px_h}")
            aspect = px_h / px_w
            w = max_w_mm
            h = w * aspect
            avail = CONTENT_BOTTOM - pdf.get_y()
            if h > avail:
                if avail >= MIN_CHART_H:
                    h = avail
                    w = h / aspect
                else:
                    pdf.add_page()
                    avail = CONTENT_BOTTOM - pdf.get_y()
                    if h > avail:
                        h = avail
                        w = h / aspect
            x = MARGIN + (INNER_W - w) / 2
            pdf.image(str(path), x=x, y=pdf.get_y(), w=w, h=h)
            pdf.set_xy(MARGIN, pdf.get_y() + h + 2)
            return True
        except (OSError, ValueError, RuntimeError) as exc:
            logger.warning("Could not embed image %s: %s", path, exc)
            if key:
                self._chart_placeholder(pdf, key)
            return False

    # -----------------------------------------------------------------------
    # Page builders
    # -----------------------------------------------------------------------

    def _build_cover(self, pdf: JarPDF) -> None:
        """Builds the executive cover page (page 1)."""
        pdf.add_page()

        self._set_color(pdf, SAGE_BG)
        pdf.rect(0, 0, PAGE_W, PAGE_H, style="F")

        # Decorative vertical accent lines (left & right)
        pdf.set_draw_color(*SAGE)
        pdf.set_line_width(2)
        pdf.line(8, 20, 8, PAGE_H - 20)
        pdf.line(PAGE_W - 8, 20, PAGE_W - 8, PAGE_H - 20)
        pdf.set_line_width(0.2)

        # Main title block
        pdf.set_font("Helvetica", "B", 26)
        pdf.set_text_color(*SLATE)
        pdf.set_xy(MARGIN, 60)
        pdf.multi_cell(INNER_W, 12, "Jar Growth Intern Assignment", align="C", **NEXT_LINE)
        pdf.ln(4)

        pdf.set_font("Helvetica", "I", 14)
        pdf.set_text_color(*SLATE_MUTED)
        pdf.multi_cell(
            INNER_W, 8, "Executive Submission: Sales Analytics, App Exploration & Growth Strategy",
            align="C", **NEXT_LINE,
        )
        pdf.ln(12)

        # Gold badge rect
        badge_y = pdf.get_y()
        self._set_color(pdf, GOLD_BG)
        self._set_color(pdf, GOLD, stroke=True)
        pdf.set_line_width(0.6)
        pdf.rect(MARGIN + 10, badge_y, INNER_W - 20, 18, style="FD")
        pdf.set_xy(MARGIN + 12, badge_y + 5)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*GOLD)
        pdf.multi_cell(
            INNER_W - 24,
            4,
            "Q1 Sales Analytics  |  Q2 Jar App Exploration  |  Q3 Fintech Expansion Strategy",
            align="C",
            **NEXT_LINE,
        )
        pdf.set_y(badge_y + 18 + 20)

        # Contents list
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*SLATE)
        pdf.set_x(MARGIN)
        pdf.cell(INNER_W, 6, "Contents", align="C", **NEXT_LINE)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*SLATE_MUTED)
        for entry in (
            "Executive Summary",
            "Q1 - Category Profitability, Furniture Targets, Regional Performance",
            "Q2 - Jar App Exploration: 5 Strengths & 5 Improvements",
            "Q3 - Fintech Growth Strategy: 5 Verticals with Unit Economics",
        ):
            pdf.set_x(MARGIN)
            pdf.cell(INNER_W, 5.5, entry, align="C", **NEXT_LINE)
        pdf.ln(18)

        # Candidate / date
        candidate = os.getenv("CANDIDATE_NAME", "").strip() or DEFAULT_CANDIDATE_NAME
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*SLATE)
        pdf.set_x(MARGIN)
        pdf.multi_cell(INNER_W, 6, self._clean(f"Candidate: {candidate}"), align="C", **NEXT_LINE)
        pdf.set_x(MARGIN)
        pdf.multi_cell(
            INNER_W,
            6,
            f"Prepared: {date.today().strftime('%B %Y')}",
            align="C",
            **NEXT_LINE,
        )

    def _build_executive_summary(
        self,
        pdf: JarPDF,
        category_data: List[CategoryPerformance],
        furniture_data: List[FurnitureTargetAchievement],
        state_data: List[StatePerformance],
    ) -> None:
        """Builds the executive summary page (page 2)."""
        pdf.add_page()
        self._h1(pdf, "Executive Summary")

        total_sales = sum(c.total_sales for c in category_data) if category_data else 0.0
        total_profit = sum(c.total_profit for c in category_data) if category_data else 0.0

        best_margin_cat = (
            max(category_data, key=lambda c: c.profit_margin_pct).category
            if category_data else "N/A"
        )

        furn_ach: Optional[float] = None
        if furniture_data:
            total_target = sum(f.target_sales for f in furniture_data)
            total_actual = sum(f.actual_sales for f in furniture_data)
            furn_ach = total_actual / total_target * 100 if total_target else 0.0

        top_state = (
            min(state_data, key=lambda s: s.rank).state if state_data else "N/A"
        )

        card_w = (INNER_W - 6) / 3
        card_h = 22
        kpi_y = pdf.get_y() + 2
        cards = [
            ("Total Sales", f"Rs. {total_sales:,.0f}", SAGE_BG, SAGE),
            ("Net Profit", f"Rs. {total_profit:,.0f}", GOLD_BG, GOLD),
            ("Best Margin Category", self._clean(best_margin_cat), LAVENDER_BG, LAVENDER),
            (
                "Furniture Target Achieved",
                f"{furn_ach:.1f}%" if furn_ach is not None else "N/A",
                CORAL_BG,
                CORAL,
            ),
            ("Top State by Orders", self._clean(top_state), CARD_BG, SAGE),
        ]

        # Layout: first row of 3, second row of 2
        for i, (label, value, fill, border) in enumerate(cards):
            row = i // 3
            col = i % 3
            cx = MARGIN + col * (card_w + 3)
            cy = kpi_y + row * (card_h + 4)
            self._set_color(pdf, fill)
            self._set_color(pdf, border, stroke=True)
            pdf.set_line_width(0.3)
            pdf.rect(cx, cy, card_w, card_h, style="FD")
            pdf.set_xy(cx + 2, cy + 2)
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_text_color(*SLATE_MUTED)
            pdf.cell(card_w - 4, 4, self._clean(label.upper()), align="L")
            pdf.set_xy(cx + 2, cy + 8)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*SLATE)
            pdf.multi_cell(card_w - 4, 5, self._clean(value), align="L")

        pdf.set_y(kpi_y + 2 * (card_h + 4) + 4)
        pdf.ln(2)

        narrative = (
            "This submission presents a data-driven analysis of the e-commerce "
            "sales dataset spanning April 2018 to March 2019. The Q1 analytics reveal category "
            "profitability dynamics, furniture target adherence, and regional performance "
            "quadrants. Q2 explores the Jar gold savings app, identifying 5 things that work "
            "well and 5 areas for improvement, each with reasoning and a suggested fix. Q3 proposes 5 fintech expansion verticals with "
            "TAM/SAM/SOM sizing and unit economics underpinned by Jar's core automation and "
            "trust flywheel."
        )
        self._paragraph(pdf, narrative)
        pdf.ln(4)

        # Key findings callouts
        findings: List[Tuple[str, str, Tuple[int, int, int], Tuple[int, int, int]]] = []
        if category_data:
            best_sales = max(category_data, key=lambda c: c.total_sales)
            findings.append((
                "Q1 - Category economics",
                f"{best_sales.category} leads revenue at Rs. {best_sales.total_sales:,.0f}, "
                f"while {best_margin_cat} carries the richest margin "
                f"({max(c.profit_margin_pct for c in category_data):.1f}%).",
                SAGE_BG, SAGE,
            ))
        if furniture_data:
            misses = sum(1 for f in furniture_data if f.variance < 0)
            findings.append((
                "Q1 - Furniture targets",
                f"Furniture missed target in {misses} of {len(furniture_data)} months, "
                f"averaging {furn_ach:.1f}% achievement; target setting should track "
                "realised demand rather than step changes.",
                CORAL_BG, CORAL,
            ))
        strengths = get_ux_strengths()
        frictions = get_ux_frictions()
        if strengths and frictions:
            top_frictions = [f.title for f in frictions[:2]]
            findings.append((
                "Q2 - App exploration",
                f"{len(strengths)} strengths led by '{strengths[0].title}'; "
                f"{len(frictions)} improvements, with the top priorities being "
                + " and ".join(f"'{t}'" for t in top_frictions) + ".",
                LAVENDER_BG, LAVENDER,
            ))
        verticals = get_growth_strategy_report().verticals
        if verticals:
            ratios = [v.unit_economics.ltv_cac_ratio for v in verticals]
            best = max(verticals, key=lambda v: v.unit_economics.ltv_cac_ratio)
            findings.append((
                "Q3 - Growth strategy",
                f"{len(verticals)} expansion verticals extend the savings flywheel with "
                f"LTV:CAC ratios of {min(ratios):.1f}x to {max(ratios):.1f}x; "
                f"strongest economics: {best.name}.",
                GOLD_BG, GOLD,
            ))
        for title, body, fill, border in findings:
            self._flow_card(pdf, title, body, fill, border, font_size=8, gap=2.5)

    def _build_category_page(
        self,
        pdf: JarPDF,
        category_data: List[CategoryPerformance],
        charts_dir: Optional[Path],
    ) -> None:
        """Builds Q1 Part 1 - Category Sales & Profitability (page 3)."""
        pdf.add_page()
        self._h1(pdf, "Q1 - Sales Analytics")
        self._h2(pdf, "Part 1 - Category Sales & Profitability")

        if not category_data:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(INNER_W, 6, "No category data available.", **NEXT_LINE)
        else:
            headers = [
                "Category", "Total Sales (Rs.)", "Net Profit (Rs.)",
                "Margin %", "Avg Profit/Order", "Orders",
            ]
            ranked = sorted(category_data, key=lambda c: c.performance_rank)
            rows = [
                [
                    rec.category,
                    f"Rs. {rec.total_sales:,.0f}",
                    f"Rs. {rec.total_profit:,.0f}",
                    f"{rec.profit_margin_pct:.1f}%",
                    f"Rs. {rec.avg_profit_per_order:,.0f}",
                    str(rec.distinct_orders),
                ]
                for rec in ranked
            ]
            fills = [CARD_BG if i % 2 else WHITE for i in range(len(rows))]
            self._render_table(
                pdf, headers, rows, (40, 32, 30, 22, 34, 22), SAGE, fills, font_size=8
            )

        pdf.ln(4)
        self._embed_image(
            pdf, self._resolve_chart("category_profitability", charts_dir),
            key="category_profitability",
        )
        if category_data:
            by_sales = max(category_data, key=lambda c: c.total_sales)
            by_margin = max(category_data, key=lambda c: c.profit_margin_pct)
            weakest = min(category_data, key=lambda c: c.profit_margin_pct)
            self._flow_card(
                pdf,
                "Insight",
                f"{by_sales.category} generates the highest revenue "
                f"(Rs. {by_sales.total_sales:,.0f}), but {by_margin.category} converts "
                f"sales to profit most efficiently ({by_margin.profit_margin_pct:.1f}% margin). "
                f"{weakest.category} has the thinnest margin ({weakest.profit_margin_pct:.1f}%), "
                "so pricing, discounting and fulfilment cost there deserve review first.",
                SAGE_BG,
                SAGE,
            )

    def _build_furniture_page(
        self,
        pdf: JarPDF,
        furniture_data: List[FurnitureTargetAchievement],
        charts_dir: Optional[Path],
    ) -> None:
        """Builds Q1 Part 2 - Furniture Target MoM (page 4)."""
        pdf.add_page()
        self._h2(pdf, "Part 2 - Furniture Target Month-on-Month Trajectory")

        if not furniture_data:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(INNER_W, 6, "No furniture data available.", **NEXT_LINE)
        else:
            headers = [
                "Month", "Target (Rs.)", "Actual (Rs.)",
                "Variance (Rs.)", "Achv. %", "Target MoM %",
            ]
            rows = []
            fills = []
            for rec in furniture_data:
                mom_str = (
                    f"{rec.mom_target_pct_change:+.1f}%"
                    if rec.mom_target_pct_change is not None
                    else "Baseline"
                )
                if rec.is_significant_fluctuation:
                    mom_str += " *"
                rows.append([
                    rec.display_month,
                    f"Rs. {rec.target_sales:,.0f}",
                    f"Rs. {rec.actual_sales:,.0f}",
                    f"Rs. {rec.variance:,.0f}",
                    f"{rec.achievement_pct:.1f}%",
                    mom_str,
                ])
                fills.append(CORAL_BG if rec.variance < 0 else WHITE)
            self._render_table(
                pdf, headers, rows, (24, 32, 32, 32, 26, 34), GOLD, fills, font_size=7
            )
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(*SLATE_MUTED)
            pdf.set_x(MARGIN)
            pdf.cell(
                INNER_W, 5,
                "Coral rows: actual below target.  * Significant target fluctuation (>= 15% MoM).",
                **NEXT_LINE,
            )

        pdf.ln(3)
        self._embed_image(
            pdf, self._resolve_chart("furniture_target_vs_actual", charts_dir),
            key="furniture_target_vs_actual",
        )
        if furniture_data:
            worst = min(furniture_data, key=lambda f: f.achievement_pct)
            best = max(furniture_data, key=lambda f: f.achievement_pct)
            misses = sum(1 for f in furniture_data if f.variance < 0)
            first, last = furniture_data[0], furniture_data[-1]
            target_growth = (
                (last.target_sales / first.target_sales - 1) * 100
                if first.target_sales > 0 else 0.0
            )
            self._flow_card(
                pdf,
                "Insight",
                f"Targets rose steadily ({target_growth:+.1f}% from {first.display_month} to "
                f"{last.display_month}) while actual sales were volatile: furniture missed "
                f"target in {misses} of {len(furniture_data)} months, from a low of "
                f"{worst.achievement_pct:.1f}% ({worst.display_month}) to a high of "
                f"{best.achievement_pct:.1f}% ({best.display_month}). Targets should be "
                "re-baselined on seasonal demand rather than a flat monthly increment.",
                GOLD_BG,
                GOLD,
            )

    def _build_regional_page(
        self,
        pdf: JarPDF,
        state_data: List[StatePerformance],
        charts_dir: Optional[Path],
    ) -> None:
        """Builds Q1 Part 3 - Regional Performance (page 5)."""
        pdf.add_page()
        self._h2(pdf, "Part 3 - Regional Performance (Top 5 States)")

        if not state_data:
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(INNER_W, 6, "No regional data available.", **NEXT_LINE)
        else:
            headers = [
                "#", "State", "Orders",
                "Sales (Rs.)", "Profit (Rs.)",
                "Margin %", "Quadrant",
            ]
            ranked = sorted(state_data, key=lambda s: s.rank)
            rows = [
                [
                    str(rec.rank),
                    rec.state,
                    str(rec.distinct_orders),
                    f"Rs. {rec.total_sales:,.0f}",
                    f"Rs. {rec.total_profit:,.0f}",
                    f"{rec.profit_margin_pct:.1f}%",
                    rec.quadrant,
                ]
                for rec in ranked
            ]
            fills = [LAVENDER_BG if rec.rank % 2 == 0 else WHITE for rec in ranked]
            self._render_table(
                pdf, headers, rows, (8, 32, 18, 28, 28, 20, 46), LAVENDER, fills, font_size=7
            )

        pdf.ln(4)
        self._embed_image(
            pdf, self._resolve_chart("regional_performance", charts_dir),
            key="regional_performance",
        )
        if state_data:
            leader = min(state_data, key=lambda st: st.rank)
            best_margin = max(state_data, key=lambda st: st.profit_margin_pct)
            loss_states = [st.state for st in state_data if st.total_profit < 0]
            loss_text = (
                f" {', '.join(loss_states)} {'is' if len(loss_states) == 1 else 'are'} "
                f"loss-making and {'needs' if len(loss_states) == 1 else 'need'} "
                "a margin fix before further growth spend."
                if loss_states else ""
            )
            self._flow_card(
                pdf,
                "Insight",
                f"{leader.state} leads on order volume ({leader.distinct_orders} orders, "
                f"{leader.profit_margin_pct:.1f}% margin), while {best_margin.state} earns the "
                f"best margin among the top states ({best_margin.profit_margin_pct:.1f}%)."
                + loss_text,
                LAVENDER_BG,
                LAVENDER,
            )

    def _build_ux_teardown(self, pdf: JarPDF) -> None:
        """Builds Q2 - Jar App Exploration (5 things that work, 5 improvements)."""
        pdf.add_page()
        self._h1(pdf, "Q2 - Jar App Exploration")
        self._paragraph(
            pdf,
            "Five things I found effective and user-friendly in the Jar app, and five "
            "areas for improvement with the reasoning and a suggested fix.",
        )

        strengths = get_ux_strengths()
        frictions = get_ux_frictions()

        self._subheading(pdf, "What works well", SAGE)
        for idx, s in enumerate(strengths, start=1):
            self._flow_card(
                pdf, f"S{idx}. {s.title}", _first_sentences(s.description, 2, 320),
                SAGE_BG, SAGE, font_size=8, gap=2.5,
            )

        pdf.ln(2)
        self._ensure_space(pdf, 40)
        self._subheading(pdf, "What could be improved", CORAL)
        for idx, f in enumerate(frictions, start=1):
            body = _problem_statement(f.description)
            fix = _first_fix(f.actionable_solution)
            if fix:
                body = f"{body} Suggested fix: {fix}"
            self._flow_card(
                pdf, f"F{idx}. {f.title}", body, CORAL_BG, CORAL, font_size=8, gap=2.5
            )

    def _build_growth_strategy(self, pdf: JarPDF) -> None:
        """Builds Q3 - Fintech Growth Strategy (5 verticals + risk matrix)."""
        pdf.add_page()
        self._h1(pdf, "Q3 - Fintech Growth Strategy: 5 Expansion Verticals")

        strategy_report = get_growth_strategy_report()

        narrative = (strategy_report.global_flywheel_narrative or "").strip()
        if narrative:
            intro, _, stages = narrative.partition("\n\n")
            self._paragraph(pdf, _shorten(intro, 420), font_size=8)
            if stages.strip():
                stage_heads = _list_headlines(stages, 400).replace("; ", "  ->  ")
                pdf.set_x(MARGIN)
                pdf.set_font("Helvetica", "B", 8)
                pdf.set_text_color(*LAVENDER)
                pdf.multi_cell(
                    INNER_W, 4.8, self._clean(f"Flywheel: {stage_heads}"),
                    align="L", **NEXT_LINE,
                )
            pdf.ln(3)

        # Unit economics summary table
        self._subheading(pdf, "Unit Economics at a Glance", LAVENDER)
        headers = ["Vertical", "SOM", "CAC (Rs.)", "LTV (Rs.)", "LTV:CAC", "Payback"]
        rows = []
        for v in strategy_report.verticals:
            ue = v.unit_economics
            rows.append([
                v.name,
                v.market_sizing.som,
                f"{ue.cac_inr:,.0f}",
                f"{ue.ltv_inr:,.0f}",
                f"{ue.ltv_cac_ratio:.1f}x",
                f"{ue.payback_months:.1f} mo",
            ])
        fills = [LAVENDER_BG if i % 2 else WHITE for i in range(len(rows))]
        self._render_table(
            pdf, headers, rows, (58, 42, 20, 20, 18, 22), LAVENDER, fills, font_size=7
        )
        pdf.ln(4)

        for idx, vertical in enumerate(strategy_report.verticals, start=1):
            ms = vertical.market_sizing
            ue = vertical.unit_economics
            body = (
                f"Why: {_shorten(vertical.strategic_rationale, 230)}\n"
                f"Market: TAM {ms.tam}  |  SAM {ms.sam}  |  SOM {ms.som}\n"
                f"Unit economics: CAC Rs.{ue.cac_inr:,.0f}  |  LTV Rs.{ue.ltv_inr:,.0f}"
                f"  |  LTV:CAC {ue.ltv_cac_ratio:.1f}x  |  Payback {ue.payback_months:.1f} mo\n"
                f"Take rate: {ue.take_rate}\n"
                f"Flywheel: {_shorten(vertical.flywheel_integration, 200)}"
            )
            self._flow_card(
                pdf,
                f"V{idx}. {vertical.name}: {vertical.tagline}",
                body,
                LAVENDER_BG,
                LAVENDER,
                font_size=8,
                gap=3,
            )

        # Risk matrix
        risks = strategy_report.execution_risk_matrix
        if risks:
            pdf.ln(1)
            self._ensure_space(pdf, 50)
            self._subheading(pdf, "Execution Risk Matrix", SLATE)
            severity_colors = {
                "High": CORAL_BG,
                "Medium": GOLD_BG,
                "Low": SAGE_BG,
            }
            rows = [
                [
                    _shorten(r.risk_title, 90),
                    r.risk_category,
                    r.severity,
                    _shorten(r.mitigation_strategy, 260),
                ]
                for r in risks
            ]
            fills = [severity_colors.get(r.severity, WHITE) for r in risks]
            self._render_table(
                pdf,
                ["Risk", "Category", "Severity", "Mitigation"],
                rows,
                (50, 26, 16, 88),
                SLATE,
                fills,
                font_size=7,
                text_align="LEFT",
            )

    # -----------------------------------------------------------------------
    # Main build method
    # -----------------------------------------------------------------------

    def build_submission_pdf(
        self,
        output_path: "str | Path",
        category_data: List[CategoryPerformance],
        furniture_data: List[FurnitureTargetAchievement],
        state_data: List[StatePerformance],
        charts_dir: Optional[Path] = None,
    ) -> Path:
        """Compiles the complete executive PDF submission document.

        Args:
            output_path: Destination file path for the generated PDF.
            category_data: List of CategoryPerformance records (Q1 Part 1).
            furniture_data: List of FurnitureTargetAchievement records (Q1 Part 2).
            state_data: List of StatePerformance records (Q1 Part 3).
            charts_dir: Optional directory containing pre-rendered chart PNGs,
                used for any chart not supplied via the ``chart_paths`` manifest.

        Returns:
            Path: The path to the generated PDF file.

        Raises:
            ValueError: If output_path is empty or its directory cannot be created.
            RuntimeError: If fpdf2 fails to render or write the PDF.
        """
        if output_path is None or not str(output_path).strip():
            raise ValueError("output_path must be a non-empty file path")

        if not category_data and not furniture_data and not state_data:
            logger.warning("All data inputs are empty; PDF will contain placeholder content.")

        out = Path(output_path)
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ValueError(
                f"Cannot create output directory '{out.parent}': {exc}"
            ) from exc

        if charts_dir is not None:
            charts_dir = Path(charts_dir)
            if not charts_dir.is_dir():
                logger.warning("charts_dir does not exist or is not a directory: %s", charts_dir)
                charts_dir = None

        self.missing_charts = []
        logger.info("Initialising PDF document at: %s", out)

        pdf = JarPDF(orientation="P", unit="mm", format="A4")
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=False, margin=MARGIN)
        pdf.set_margins(left=MARGIN, top=MARGIN, right=MARGIN)
        pdf.set_title("Jar Growth Intern Assignment - Executive Submission")
        pdf.set_author(os.getenv("CANDIDATE_NAME", "").strip() or DEFAULT_CANDIDATE_NAME)

        category_data = list(category_data or [])
        furniture_data = list(furniture_data or [])
        state_data = list(state_data or [])

        try:
            self._build_cover(pdf)
            self._build_executive_summary(pdf, category_data, furniture_data, state_data)
            self._build_category_page(pdf, category_data, charts_dir)
            self._build_furniture_page(pdf, furniture_data, charts_dir)
            self._build_regional_page(pdf, state_data, charts_dir)
            self._build_ux_teardown(pdf)
            self._build_growth_strategy(pdf)
            pdf.output(str(out))
        except OSError as exc:
            raise RuntimeError(f"Failed to write PDF to '{out}': {exc}") from exc
        except (ValueError, TypeError, AttributeError) as exc:
            raise RuntimeError(f"Failed to render PDF content: {exc}") from exc

        self.page_count = pdf.pages_count
        size_kb = out.stat().st_size // 1024
        logger.info(
            "PDF generated successfully: %s (%d KB, %d pages)",
            out,
            size_kb,
            self.page_count,
        )
        if self.missing_charts:
            logger.warning(
                "PDF built with placeholders for missing charts: %s",
                ", ".join(self.missing_charts),
            )

        return out
