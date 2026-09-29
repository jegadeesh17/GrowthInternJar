"""Unit tests for src.pdf_generator.PdfGenerator (M3-TASK-02 AC-4.2).

Tests:
1.  PdfGenerator instantiates without error.
2.  build_submission_pdf returns a Path that exists.
3.  Output file is > 10 KB.
4.  Output file extension is .pdf.
5.  _clean strips Rs. symbol (rupee Unicode -> 'Rs.').
6.  _clean handles empty string without raising.
7.  build_submission_pdf with charts_dir=None still succeeds.
8.  build_submission_pdf accepts a custom output_path in a tmp dir.
9.  Output file is a valid PDF (starts with b'%PDF').
10. Page count is between 6 and 12 (exact /Type /Page count, excluding /Pages).
11. draw_card can be called without raising.
12. CLI runner 'python -m src.generate_pdf' exits 0 and writes a 6-12 page PDF
    to data/output/ (integration test).
13+ Embedded chart images, Q1/Q2/Q3 section content (decompressed streams),
    running headers/footers, missing/corrupt chart placeholders, invalid
    inputs, and CLI failure on a nonexistent DATA_DIR.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import zlib
from pathlib import Path
from typing import Dict, List

import pytest

from src.analytics_engine import (
    CategoryPerformance,
    FurnitureTargetAchievement,
    StatePerformance,
)
from src.content.growth_strategy import get_growth_strategy_report
from src.content.ux_teardown import get_ux_frictions, get_ux_strengths
from src.pdf_generator import PdfGenerator, JarPDF, MARGIN, INNER_W, SAGE_BG, SAGE, SLATE

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_PDF = PROJECT_ROOT / "data" / "output" / "Jar_Growth_Intern_Assignment_Submission.pdf"
CHART_KEYS = (
    "category_profitability",
    "furniture_target_vs_actual",
    "regional_performance",
)


# ---------------------------------------------------------------------------
# PDF inspection helpers (no third-party PDF parser required)
# ---------------------------------------------------------------------------

_PAGE_OBJ_RE = re.compile(rb"/Type\s*/Page(?![A-Za-z])")
_IMAGE_OBJ_RE = re.compile(rb"/Subtype\s*/Image(?![A-Za-z])")
_STREAM_RE = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.S)
# A '(...) Tj' show-text operand, or the ET operator that closes a text object.
_TJ_OR_ET_RE = re.compile(rb"\(((?:\\.|[^\\)])*)\)\s*Tj|\bET\b")


def _count_pages(pdf_bytes: bytes) -> int:
    """Counts page objects ('/Type /Page'), excluding the '/Type /Pages' tree node."""
    return len(_PAGE_OBJ_RE.findall(pdf_bytes))


def _count_images(pdf_bytes: bytes) -> int:
    """Counts image XObjects ('/Subtype /Image') in the PDF."""
    return len(_IMAGE_OBJ_RE.findall(pdf_bytes))


def _unescape_pdf_string(raw: bytes) -> str:
    """Decodes a PDF literal string body (handles escaped parens/backslashes)."""
    return re.sub(rb"\\([()\\])", rb"\1", raw).decode("latin-1")


def _page_texts(pdf_bytes: bytes) -> List[str]:
    """Returns the text shown by each decompressed content stream, in order.

    fpdf2 Flate-compresses content streams, so the raw bytes cannot be searched
    directly. Each text-bearing stream is decompressed; the '(...) Tj'
    fragments inside one BT/ET text object are concatenated into one line
    (fpdf2 may split a cell, e.g. 'Page 2 of ' + '9'), and lines are joined
    with newlines. Image streams are skipped.
    """
    texts: List[str] = []
    for match in _STREAM_RE.finditer(pdf_bytes):
        try:
            data = zlib.decompress(match.group(1))
        except zlib.error:
            continue
        if b"BT" not in data or b"Tj" not in data:
            continue
        lines: List[str] = []
        current: List[str] = []
        for token in _TJ_OR_ET_RE.finditer(data):
            if token.group(1) is not None:
                current.append(_unescape_pdf_string(token.group(1)))
            elif current:
                lines.append("".join(current))
                current = []
        if current:
            lines.append("".join(current))
        texts.append("\n".join(lines))
    return texts


def _all_text(pdf_path: Path) -> str:
    """Returns all shown text of a PDF as one newline-joined string."""
    return "\n".join(_page_texts(pdf_path.read_bytes()))


def _make_chart_pngs(folder: Path) -> Dict[str, Path]:
    """Writes three distinct 1500x900 RGB PNGs and returns a chart manifest."""
    from PIL import Image  # Pillow is a hard dependency of fpdf2

    folder.mkdir(parents=True, exist_ok=True)
    colours = [(72, 187, 120), (214, 158, 46), (128, 90, 213)]
    manifest: Dict[str, Path] = {}
    for key, colour in zip(CHART_KEYS, colours):
        path = folder / f"{key}.png"
        Image.new("RGB", (1500, 900), colour).save(path)
        manifest[key] = path
    return manifest


# ---------------------------------------------------------------------------
# Synthetic data helpers (avoid importing matplotlib)
# ---------------------------------------------------------------------------

def _make_category_data() -> List[CategoryPerformance]:
    """Builds minimal CategoryPerformance list for testing."""
    return [
        CategoryPerformance(
            category="Clothing",
            total_sales=10000.0,
            total_profit=2000.0,
            avg_profit_per_order=200.0,
            profit_margin_pct=20.0,
            distinct_orders=10,
            total_quantity=50,
            performance_rank=1,
        ),
        CategoryPerformance(
            category="Electronics",
            total_sales=20000.0,
            total_profit=4000.0,
            avg_profit_per_order=400.0,
            profit_margin_pct=20.0,
            distinct_orders=10,
            total_quantity=30,
            performance_rank=2,
        ),
        CategoryPerformance(
            category="Furniture",
            total_sales=5000.0,
            total_profit=500.0,
            avg_profit_per_order=166.67,
            profit_margin_pct=10.0,
            distinct_orders=3,
            total_quantity=15,
            performance_rank=3,
        ),
    ]


def _make_furniture_data() -> List[FurnitureTargetAchievement]:
    """Builds minimal FurnitureTargetAchievement list for testing."""
    rows = [
        ("2018-04", "Apr-18", 10000.0, 9500.0, None, None),
        ("2018-05", "May-18", 12000.0, 11000.0, 20.0, None),
        ("2018-06", "Jun-18", 11000.0, 12000.0, -8.33, None),
    ]
    result = []
    for month_key, display, target, actual, mom_t, mom_a in rows:
        variance = round(actual - target, 2)
        achievement_pct = round((actual / target) * 100.0, 2) if target > 0 else 0.0
        is_sig = (abs(mom_t) >= 15.0) if mom_t is not None else False
        result.append(
            FurnitureTargetAchievement(
                month_key=month_key,
                display_month=display,
                target_sales=target,
                actual_sales=actual,
                mom_target_pct_change=mom_t,
                mom_actual_pct_change=mom_a,
                variance=variance,
                achievement_pct=achievement_pct,
                is_significant_fluctuation=is_sig,
            )
        )
    return result


def _make_state_data() -> List[StatePerformance]:
    """Builds minimal StatePerformance list for testing."""
    records = [
        (1, "Maharashtra", 100, 50000.0, 10000.0, "High Volume / High Margin"),
        (2, "Uttar Pradesh", 80, 40000.0, 8000.0, "High Volume / High Margin"),
        (3, "Karnataka", 60, 30000.0, 6000.0, "High Volume / Low Margin"),
        (4, "Gujarat", 50, 25000.0, 5000.0, "Low Volume / High Margin"),
        (5, "Delhi", 40, 20000.0, 4000.0, "Low Volume / Low Margin"),
    ]
    result = []
    for rank, state, orders, sales, profit, quadrant in records:
        avg_profit = round(profit / orders, 2)
        margin = round((profit / sales) * 100, 2)
        result.append(
            StatePerformance(
                rank=rank,
                state=state,
                distinct_orders=orders,
                total_sales=sales,
                total_profit=profit,
                avg_profit_per_order=avg_profit,
                profit_margin_pct=margin,
                quadrant=quadrant,
            )
        )
    return result


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def pdf_gen() -> PdfGenerator:
    """Returns a fresh PdfGenerator instance."""
    return PdfGenerator()


@pytest.fixture
def mock_category_data() -> List[CategoryPerformance]:
    return _make_category_data()


@pytest.fixture
def mock_furniture_data() -> List[FurnitureTargetAchievement]:
    return _make_furniture_data()


@pytest.fixture
def mock_state_data() -> List[StatePerformance]:
    return _make_state_data()


@pytest.fixture
def generated_pdf(
    pdf_gen: PdfGenerator,
    mock_category_data: List[CategoryPerformance],
    mock_furniture_data: List[FurnitureTargetAchievement],
    mock_state_data: List[StatePerformance],
    tmp_path: Path,
) -> Path:
    """Generates a PDF (no charts) into the per-test tmp_path."""
    out_path = tmp_path / "test_submission.pdf"
    return pdf_gen.build_submission_pdf(
        output_path=out_path,
        category_data=mock_category_data,
        furniture_data=mock_furniture_data,
        state_data=mock_state_data,
        charts_dir=None,
    )


# ---------------------------------------------------------------------------
# Tests 1–4: Instantiation and basic output validation
# ---------------------------------------------------------------------------

def test_pdf_generator_instantiates() -> None:
    """Test 1: PdfGenerator() can be constructed without error."""
    gen = PdfGenerator()
    assert gen is not None
    assert gen.missing_charts == []
    assert gen.page_count == 0


def test_build_submission_pdf_returns_existing_path(generated_pdf: Path) -> None:
    """Test 2: build_submission_pdf returns a Path that exists on disk."""
    assert isinstance(generated_pdf, Path)
    assert generated_pdf.exists()


def test_pdf_file_size_above_10kb(generated_pdf: Path) -> None:
    """Test 3: Output file is larger than 10 KB."""
    assert generated_pdf.stat().st_size > 10_240, (
        f"PDF too small: {generated_pdf.stat().st_size} bytes"
    )


def test_pdf_file_extension(generated_pdf: Path) -> None:
    """Test 4: Output file has .pdf extension."""
    assert generated_pdf.suffix.lower() == ".pdf"


# ---------------------------------------------------------------------------
# Tests 5–6: _clean method
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("₹100", "Rs.100"),
    ("₹1,200.50", "Rs.1,200.50"),
    ("a – b → c", "a - b -> c"),
])
def test_clean_strips_rupee_symbol(
    pdf_gen: PdfGenerator,
    raw: str,
    expected: str,
) -> None:
    """Test 5: _clean converts the rupee sign / typographic chars to latin-1."""
    result = pdf_gen._clean(raw)
    assert result == expected
    result.encode("latin-1")  # must not raise


def test_clean_handles_empty_string(pdf_gen: PdfGenerator) -> None:
    """Test 6: _clean does not raise on empty string input."""
    result = pdf_gen._clean("")
    assert result == ""


# ---------------------------------------------------------------------------
# Test 7: charts_dir=None still succeeds
# ---------------------------------------------------------------------------

def test_build_without_charts_dir(
    pdf_gen: PdfGenerator,
    mock_category_data: List[CategoryPerformance],
    mock_furniture_data: List[FurnitureTargetAchievement],
    mock_state_data: List[StatePerformance],
    tmp_path: Path,
) -> None:
    """Test 7: PDF builds successfully even when charts_dir=None."""
    out_path = tmp_path / "no_charts.pdf"
    result = pdf_gen.build_submission_pdf(
        output_path=out_path,
        category_data=mock_category_data,
        furniture_data=mock_furniture_data,
        state_data=mock_state_data,
        charts_dir=None,
    )
    assert result.exists()
    assert result.stat().st_size > 0


# ---------------------------------------------------------------------------
# Test 8: Custom output_path in tmp dir
# ---------------------------------------------------------------------------

def test_build_to_custom_output_path(
    pdf_gen: PdfGenerator,
    mock_category_data: List[CategoryPerformance],
    mock_furniture_data: List[FurnitureTargetAchievement],
    mock_state_data: List[StatePerformance],
    tmp_path: Path,
) -> None:
    """Test 8: Accepts a custom output_path in a temporary directory."""
    custom_path = tmp_path / "sub" / "custom_output.pdf"
    result = pdf_gen.build_submission_pdf(
        output_path=custom_path,
        category_data=mock_category_data,
        furniture_data=mock_furniture_data,
        state_data=mock_state_data,
        charts_dir=None,
    )
    assert result == custom_path
    assert result.exists()


# ---------------------------------------------------------------------------
# Test 9: Valid PDF header
# ---------------------------------------------------------------------------

def test_pdf_has_valid_header(generated_pdf: Path) -> None:
    """Test 9: Output file starts with b'%PDF' and ends with the %%EOF trailer."""
    data = generated_pdf.read_bytes()
    assert data.startswith(b"%PDF"), f"Invalid PDF header: {data[:8]!r}"
    assert data.rstrip().endswith(b"%%EOF"), "PDF trailer missing (truncated file?)"
    assert b"xref" in data and b"trailer" in data


# ---------------------------------------------------------------------------
# Test 10: Page count between 6 and 12 (SPEC AC-4.2 #3)
# ---------------------------------------------------------------------------

def test_page_regex_excludes_pages_tree_node() -> None:
    """The page counter must not count the '/Type /Pages' tree node."""
    sample = b"<< /Type /Pages /Kids [3 0 R] >> << /Type /Page >> << /Type/Page >>"
    assert _count_pages(sample) == 2


def test_pdf_page_count_between_6_and_12(pdf_gen: PdfGenerator, generated_pdf: Path) -> None:
    """Test 10: PDF has 6-12 page objects, matching the generator's page_count."""
    data = generated_pdf.read_bytes()
    pages = _count_pages(data)
    assert 6 <= pages <= 12, f"Expected 6-12 pages, found {pages}"
    assert pdf_gen.page_count == pages, (
        f"page_count attribute ({pdf_gen.page_count}) != page objects ({pages})"
    )
    assert len(_page_texts(data)) == pages


def test_pdf_page_count_with_charts_between_6_and_12(
    mock_category_data: List[CategoryPerformance],
    mock_furniture_data: List[FurnitureTargetAchievement],
    mock_state_data: List[StatePerformance],
    tmp_path: Path,
) -> None:
    """Page count stays within 6-12 when full-size charts are embedded."""
    gen = PdfGenerator(chart_paths=_make_chart_pngs(tmp_path / "charts"))
    out = gen.build_submission_pdf(
        output_path=tmp_path / "with_charts.pdf",
        category_data=mock_category_data,
        furniture_data=mock_furniture_data,
        state_data=mock_state_data,
    )
    pages = _count_pages(out.read_bytes())
    assert 6 <= pages <= 12, f"Expected 6-12 pages, found {pages}"
    assert gen.page_count == pages


def test_page_count_cross_check_with_pypdf(pdf_gen: PdfGenerator, generated_pdf: Path) -> None:
    """Optional cross-check with pypdf (not a project dependency; skipped if absent)."""
    pypdf = pytest.importorskip("pypdf")
    reader = pypdf.PdfReader(str(generated_pdf))
    assert len(reader.pages) == _count_pages(generated_pdf.read_bytes()) == pdf_gen.page_count


# ---------------------------------------------------------------------------
# Test 11: draw_card does not raise
# ---------------------------------------------------------------------------

def test_draw_card_does_not_raise(pdf_gen: PdfGenerator) -> None:
    """Test 11: draw_card draws on a live page and returns at least the min height."""
    pdf = JarPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    height = pdf_gen.draw_card(
        pdf=pdf,
        x=MARGIN,
        y=50.0,
        w=INNER_W,
        h=20.0,
        fill_rgb=SAGE_BG,
        border_rgb=SAGE,
        text="Test card content.",
        text_color_rgb=SLATE,
        font_size=9,
    )
    assert height >= 20.0
    # Long text grows the card beyond the requested minimum height.
    grown = pdf_gen.draw_card(
        pdf=pdf, x=MARGIN, y=100.0, w=60.0, h=5.0,
        fill_rgb=SAGE_BG, border_rgb=SAGE, text="word " * 80,
        text_color_rgb=SLATE, font_size=9,
    )
    assert grown > 5.0


# ---------------------------------------------------------------------------
# Test 12: CLI integration test
# ---------------------------------------------------------------------------

def test_cli_generate_pdf_exits_zero() -> None:
    """Test 12: 'python -m src.generate_pdf' exits 0 and writes a 6-12 page PDF
    with all three charts to data/output/."""
    started = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "src.generate_pdf"],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, (
        f"CLI exited {result.returncode}.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
    assert "SUCCESS" in result.stdout, (
        f"Expected 'SUCCESS' in output.\nSTDOUT: {result.stdout}"
    )
    assert WORKSPACE_PDF.is_file(), f"Missing {WORKSPACE_PDF}"
    assert WORKSPACE_PDF.stat().st_mtime >= started - 2, "Workspace PDF was not rewritten"
    data = WORKSPACE_PDF.read_bytes()
    assert data.startswith(b"%PDF")
    assert data.rstrip().endswith(b"%%EOF"), "PDF trailer missing (truncated file?)"
    pages = _count_pages(data)
    assert 6 <= pages <= 12, f"Expected 6-12 pages, found {pages}"
    match = re.search(r"\((\d+) KB, (\d+) pages\)", result.stdout)
    assert match is not None, f"No page summary in stdout: {result.stdout}"
    assert int(match.group(2)) == pages
    # A real run renders all charts: three chart images, no placeholders.
    assert _count_images(data) >= 3, f"Found {_count_images(data)} image XObjects"
    assert "Chart unavailable" not in "\n".join(_page_texts(data))
    assert "WARNING: PDF contains placeholders" not in result.stderr


# ---------------------------------------------------------------------------
# Tests 13+: Embedded charts, section content, headers/footers
# ---------------------------------------------------------------------------

def test_pdf_embeds_three_chart_images(
    mock_category_data: List[CategoryPerformance],
    mock_furniture_data: List[FurnitureTargetAchievement],
    mock_state_data: List[StatePerformance],
    tmp_path: Path,
) -> None:
    """All 3 Q1 charts are embedded as image XObjects; no placeholders."""
    gen = PdfGenerator(chart_paths=_make_chart_pngs(tmp_path / "charts"))
    out = gen.build_submission_pdf(
        output_path=tmp_path / "charts.pdf",
        category_data=mock_category_data,
        furniture_data=mock_furniture_data,
        state_data=mock_state_data,
    )
    data = out.read_bytes()
    assert _count_images(data) >= 3, f"Found {_count_images(data)} image XObjects"
    assert gen.missing_charts == []
    assert "Chart unavailable" not in "\n".join(_page_texts(data))


def test_pdf_resolves_charts_from_charts_dir(
    mock_category_data: List[CategoryPerformance],
    mock_furniture_data: List[FurnitureTargetAchievement],
    mock_state_data: List[StatePerformance],
    tmp_path: Path,
) -> None:
    """Charts are found by file name in charts_dir when no manifest is given."""
    charts = tmp_path / "charts"
    _make_chart_pngs(charts)
    gen = PdfGenerator()
    out = gen.build_submission_pdf(
        output_path=tmp_path / "dir.pdf",
        category_data=mock_category_data,
        furniture_data=mock_furniture_data,
        state_data=mock_state_data,
        charts_dir=charts,
    )
    assert _count_images(out.read_bytes()) >= 3
    assert gen.missing_charts == []


def test_no_charts_produces_no_images_and_three_placeholders(
    pdf_gen: PdfGenerator, generated_pdf: Path
) -> None:
    """Without any charts, no images are embedded and all 3 are placeholders."""
    data = generated_pdf.read_bytes()
    assert _count_images(data) == 0
    assert sorted(pdf_gen.missing_charts) == sorted(CHART_KEYS)
    assert "\n".join(_page_texts(data)).count("Chart unavailable:") == 3


def test_missing_chart_renders_placeholder_not_crash(
    mock_category_data: List[CategoryPerformance],
    mock_furniture_data: List[FurnitureTargetAchievement],
    mock_state_data: List[StatePerformance],
    tmp_path: Path,
) -> None:
    """A single missing chart yields a labelled placeholder; others still embed."""
    manifest = _make_chart_pngs(tmp_path / "charts")
    manifest["furniture_target_vs_actual"].unlink()
    gen = PdfGenerator(chart_paths=manifest)
    out = gen.build_submission_pdf(
        output_path=tmp_path / "missing_one.pdf",
        category_data=mock_category_data,
        furniture_data=mock_furniture_data,
        state_data=mock_state_data,
        charts_dir=None,
    )
    data = out.read_bytes()
    assert data.startswith(b"%PDF")
    assert gen.missing_charts == ["furniture_target_vs_actual"]
    text = "\n".join(_page_texts(data))
    assert "Chart unavailable: furniture_target_vs_actual.png" in text
    assert text.count("Chart unavailable:") == 1
    assert _count_images(data) == 2
    assert 6 <= _count_pages(data) <= 12


def test_corrupt_chart_file_renders_placeholder_not_crash(
    mock_category_data: List[CategoryPerformance],
    mock_furniture_data: List[FurnitureTargetAchievement],
    mock_state_data: List[StatePerformance],
    tmp_path: Path,
) -> None:
    """An unreadable (non-PNG) chart file is replaced by a placeholder."""
    manifest = _make_chart_pngs(tmp_path / "charts")
    manifest["regional_performance"].write_bytes(b"this is not a png")
    gen = PdfGenerator(chart_paths=manifest)
    out = gen.build_submission_pdf(
        output_path=tmp_path / "corrupt.pdf",
        category_data=mock_category_data,
        furniture_data=mock_furniture_data,
        state_data=mock_state_data,
    )
    assert gen.missing_charts == ["regional_performance"]
    text = _all_text(out)
    assert "Chart unavailable: regional_performance.png" in text
    assert _count_images(out.read_bytes()) == 2


def test_q1_sections_and_tables_present(generated_pdf: Path) -> None:
    """Q1 heading, its 3 parts and the table rows from the inputs are rendered."""
    text = _all_text(generated_pdf)
    for heading in (
        "Executive Summary",
        "Q1 - Sales Analytics",
        "Part 1 - Category Sales & Profitability",
        "Part 2 - Furniture Target Month-on-Month Trajectory",
        "Part 3 - Regional Performance (Top 5 States)",
    ):
        assert heading in text, f"Missing section heading: {heading!r}"
    lines = set(text.splitlines())
    for cell in ("Clothing", "Electronics", "Furniture", "Rs. 20,000", "20.0%"):
        assert cell in lines, f"Missing category table cell {cell!r}"
    for cell in ("Apr-18", "May-18", "Jun-18", "Baseline", "+20.0% *", "-8.3%"):
        assert cell in lines, f"Missing furniture table cell {cell!r}"
    for cell in ("Maharashtra", "Uttar Pradesh", "Karnataka", "Gujarat", "Delhi"):
        assert cell in lines, f"Missing state table cell {cell!r}"


def test_q2_ux_teardown_has_5_strengths_and_5_frictions(generated_pdf: Path) -> None:
    """Q2 section renders exactly 5 strength cards and 5 friction cards."""
    strengths = get_ux_strengths()
    frictions = get_ux_frictions()
    assert len(strengths) == 5 and len(frictions) == 5
    text = _all_text(generated_pdf)
    lines = text.splitlines()
    assert "Q2 - Jar App Exploration" in lines
    assert "What works well" in lines
    assert "What could be improved" in lines
    assert "Psychology:" not in text and "Effort:" not in text
    s_titles = [ln for ln in lines if re.match(r"^S\d+\. ", ln)]
    f_titles = [ln for ln in lines if re.match(r"^F\d+\. ", ln)]
    assert [t.split(".")[0] for t in s_titles] == ["S1", "S2", "S3", "S4", "S5"]
    assert [t.split(".")[0] for t in f_titles] == ["F1", "F2", "F3", "F4", "F5"]
    cleaner = PdfGenerator()
    for idx, item in enumerate(strengths, start=1):
        first_word = cleaner._clean(item.title).split()[0]
        assert s_titles[idx - 1].startswith(f"S{idx}. {first_word}")
    for idx, item in enumerate(frictions, start=1):
        first_word = cleaner._clean(item.title).split()[0]
        assert f_titles[idx - 1].startswith(f"F{idx}. {first_word}")


def test_q3_growth_strategy_has_5_verticals(generated_pdf: Path) -> None:
    """Q3 section renders 5 verticals with unit economics and a risk matrix."""
    verticals = get_growth_strategy_report().verticals
    assert len(verticals) == 5
    text = _all_text(generated_pdf)
    lines = text.splitlines()
    assert "Q3 - Fintech Growth Strategy: 5 Expansion Verticals" in lines
    assert "Unit Economics (illustrative planning assumptions)" in lines
    assert "Execution Risk Matrix" in lines
    v_titles = [ln for ln in lines if re.match(r"^V\d+\. ", ln)]
    assert [t.split(".")[0] for t in v_titles] == ["V1", "V2", "V3", "V4", "V5"]
    cleaner = PdfGenerator()
    for idx, vertical in enumerate(verticals, start=1):
        first_word = cleaner._clean(vertical.name).split()[0]
        assert v_titles[idx - 1].startswith(f"V{idx}. {first_word}")
        ratio = f"{vertical.unit_economics.ltv_cac_ratio:.1f}x"
        assert ratio in lines, f"LTV:CAC {ratio} for {vertical.name} not in table"
    assert text.count("Unit economics: CAC Rs.") == 5


def test_sections_appear_in_order(generated_pdf: Path) -> None:
    """Cover -> Executive Summary -> Q1 -> Q2 -> Q3 page order."""
    pages = _page_texts(generated_pdf.read_bytes())
    assert "Jar Growth Intern Assignment" in pages[0].splitlines()

    def first_page(marker: str) -> int:
        # Skip the cover: its contents list repeats the section names.
        for i, page in enumerate(pages[1:], start=1):
            if marker in page.splitlines():
                return i
        raise AssertionError(f"{marker!r} not found on any page")

    order = [
        first_page("Executive Summary"),
        first_page("Q1 - Sales Analytics"),
        first_page("Q2 - Jar App Exploration"),
        first_page("Q3 - Fintech Growth Strategy: 5 Expansion Verticals"),
    ]
    assert order == sorted(order) and len(set(order)) == 4, order
    assert order[0] == 1


def test_headers_and_page_x_of_y_footers(generated_pdf: Path) -> None:
    """Every non-cover page has the running header and a 'Page X of Y' footer."""
    pages = _page_texts(generated_pdf.read_bytes())
    total = len(pages)
    assert "Page 1 of" not in pages[0]
    assert "Confidential Submission" not in pages[0]
    for number, page in enumerate(pages[1:], start=2):
        lines = page.splitlines()
        assert f"Page {number} of {total}" in lines, f"Footer missing on page {number}"
        assert "Jar Growth Intern Assignment - Confidential Submission" in lines
    assert "{nb}" not in "\n".join(pages), "Page total alias was not substituted"


# ---------------------------------------------------------------------------
# Invalid-input tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_path", ["", "   ", None], ids=["empty", "blank", "none"])
def test_build_rejects_empty_output_path(
    pdf_gen: PdfGenerator,
    mock_category_data: List[CategoryPerformance],
    bad_path,
) -> None:
    """An empty/None output_path raises ValueError instead of writing a file."""
    with pytest.raises(ValueError, match="output_path"):
        pdf_gen.build_submission_pdf(
            output_path=bad_path,
            category_data=mock_category_data,
            furniture_data=[],
            state_data=[],
        )


def test_draw_card_rejects_non_positive_width(pdf_gen: PdfGenerator) -> None:
    """draw_card raises ValueError for a zero width."""
    pdf = JarPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    with pytest.raises(ValueError, match="width"):
        pdf_gen.draw_card(
            pdf=pdf, x=MARGIN, y=50.0, w=0, h=10.0,
            fill_rgb=SAGE_BG, border_rgb=SAGE, text="x", text_color_rgb=SLATE,
        )


def test_build_with_empty_data_uses_placeholders(tmp_path: Path) -> None:
    """Empty analytics inputs still yield a valid PDF with 'no data' notes."""
    gen = PdfGenerator()
    out = gen.build_submission_pdf(
        output_path=tmp_path / "empty.pdf",
        category_data=[],
        furniture_data=[],
        state_data=[],
    )
    data = out.read_bytes()
    assert data.startswith(b"%PDF")
    text = _all_text(out)
    for note in (
        "No category data available.",
        "No furniture data available.",
        "No regional data available.",
    ):
        assert note in text
    assert 6 <= _count_pages(data) <= 12


def test_build_with_nonexistent_charts_dir_falls_back(
    pdf_gen: PdfGenerator,
    mock_category_data: List[CategoryPerformance],
    tmp_path: Path,
) -> None:
    """A charts_dir that does not exist is ignored (placeholders), not a crash."""
    out = pdf_gen.build_submission_pdf(
        output_path=tmp_path / "bad_dir.pdf",
        category_data=mock_category_data,
        furniture_data=[],
        state_data=[],
        charts_dir=tmp_path / "does_not_exist",
    )
    assert out.is_file()
    assert sorted(pdf_gen.missing_charts) == sorted(CHART_KEYS)


def _cli_env(tmp_path: Path, data_dir: Path) -> Dict[str, str]:
    """Environment for an isolated CLI run (outputs redirected into tmp_path)."""
    env = dict(os.environ)
    env["DATA_DIR"] = str(data_dir)
    env["CHART_ASSETS_DIR"] = str(tmp_path / "charts")
    env["OUTPUT_PDF_PATH"] = str(tmp_path / "cli_out.pdf")
    return env


@pytest.mark.parametrize("make_dir", [False, True], ids=["nonexistent", "empty"])
def test_cli_exits_1_when_data_dir_missing(tmp_path: Path, make_dir: bool) -> None:
    """CLI exits 1 with an 'ERROR:' line on stderr when input data is absent."""
    data_dir = tmp_path / "no_such_data_dir"
    if make_dir:
        data_dir.mkdir()
    result = subprocess.run(
        [sys.executable, "-m", "src.generate_pdf"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(PROJECT_ROOT),
        env=_cli_env(tmp_path, data_dir),
    )
    assert result.returncode == 1, (
        f"Expected exit 1, got {result.returncode}.\nSTDERR: {result.stderr}"
    )
    error_lines = [ln for ln in result.stderr.splitlines() if ln.startswith("ERROR:")]
    assert error_lines, f"No 'ERROR:' line on stderr:\n{result.stderr}"
    assert "Traceback" not in result.stderr
    assert "SUCCESS" not in result.stdout
    assert not (tmp_path / "cli_out.pdf").exists()
