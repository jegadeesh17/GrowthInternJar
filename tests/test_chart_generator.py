"""Automated test suite for ChartGenerator module (src/chart_generator.py).

Implements test verification for M3-TASK-01 (SPEC AC-4.2, ADR-007):
- Asserts that category_profitability.png, furniture_target_vs_actual.png, and
  regional_performance.png (and aliases) are rendered at 300 DPI in assets/charts/.
- Asserts valid 8-byte PNG file headers (b'\\x89PNG\\r\\n\\x1a\\n').
- Asserts non-zero file sizes and publication-grade pixel dimensions.
- Validates soft pastel design token constants (ADR-007).
- Tests defensive boundary handling (empty sequences, invalid types, single-item edge cases).
- Tests CLI entry point and environment variable overrides.
"""

import os
from pathlib import Path
import subprocess
import sys
from typing import Dict, List

import matplotlib
import numpy as np
from PIL import Image
import pytest

from src.analytics_engine import (
    AnalyticsEngine,
    CategoryPerformance,
    FurnitureTargetAchievement,
    StatePerformance,
)
from src.chart_generator import (
    PASTEL_TOKENS,
    ChartGenerator,
    format_inr,
)


# ---------------------------------------------------------------------------
# Synthetic Domain Dataclass Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def synthetic_category_data() -> List[CategoryPerformance]:
    """Generates synthetic category performance records."""
    return [
        CategoryPerformance(
            category="Clothing",
            total_sales=1390086.0,
            total_profit=111639.0,
            avg_profit_per_order=198.99,
            profit_margin_pct=8.03,
            distinct_orders=561,
            total_quantity=3516,
            performance_rank=1,
        ),
        CategoryPerformance(
            category="Electronics",
            total_sales=1075674.0,
            total_profit=68282.0,
            avg_profit_per_order=203.22,
            profit_margin_pct=6.35,
            distinct_orders=336,
            total_quantity=1154,
            performance_rank=2,
        ),
        CategoryPerformance(
            category="Furniture",
            total_sales=744576.0,
            total_profit=13498.0,
            avg_profit_per_order=55.55,
            profit_margin_pct=1.81,
            distinct_orders=243,
            total_quantity=944,
            performance_rank=3,
        ),
    ]


@pytest.fixture
def synthetic_furniture_data() -> List[FurnitureTargetAchievement]:
    """Generates synthetic 12-month Furniture target vs actual data with fluctuations."""
    months = [
        ("2018-04", "Apr-18", 10000.0, 9500.0, None, None, -500.0, 95.0, False),
        ("2018-05", "May-18", 12000.0, 11800.0, 20.0, 24.21, -200.0, 98.33, True),
        ("2018-06", "Jun-18", 12500.0, 13100.0, 4.17, 11.02, 600.0, 104.8, False),
        ("2018-07", "Jul-18", 10000.0, 9800.0, -20.0, -25.19, -200.0, 98.0, True),
        ("2018-08", "Aug-18", 11500.0, 12200.0, 15.0, 24.49, 700.0, 106.09, True),
        ("2018-09", "Sep-18", 11500.0, 11400.0, 0.0, -6.56, -100.0, 99.13, False),
        ("2018-10", "Oct-18", 13500.0, 14200.0, 17.39, 24.56, 700.0, 105.19, True),
        ("2018-11", "Nov-18", 13000.0, 12800.0, -3.7, -9.86, -200.0, 98.46, False),
        ("2018-12", "Dec-18", 15000.0, 16100.0, 15.38, 25.78, 1100.0, 107.33, True),
        ("2019-01", "Jan-19", 15200.0, 14900.0, 1.33, -7.45, -300.0, 98.03, False),
        ("2019-02", "Feb-19", 12000.0, 11500.0, -21.05, -22.82, -500.0, 95.83, True),
        ("2019-03", "Mar-19", 14000.0, 14800.0, 16.67, 28.7, 800.0, 105.71, True),
    ]

    records = []
    for m_key, disp, tgt, act, mom_t, mom_a, var, ach, is_fluc in months:
        rec = FurnitureTargetAchievement(
            month_key=m_key,
            display_month=disp,
            target_sales=tgt,
            actual_sales=act,
            mom_target_pct_change=mom_t,
            mom_actual_pct_change=mom_a,
            variance=var,
            achievement_pct=ach,
            is_significant_fluctuation=is_fluc,
        )
        records.append(rec)
    return records


@pytest.fixture
def synthetic_state_data() -> List[StatePerformance]:
    """Generates synthetic top 5 state performance records including loss-making state."""
    return [
        StatePerformance(
            rank=1,
            state="Madhya Pradesh",
            distinct_orders=101,
            total_sales=683100.0,
            total_profit=36080.0,
            avg_profit_per_order=357.23,
            profit_margin_pct=5.28,
            quadrant="High Volume / Low Margin",
        ),
        StatePerformance(
            rank=2,
            state="Maharashtra",
            distinct_orders=90,
            total_sales=635400.0,
            total_profit=41170.0,
            avg_profit_per_order=457.44,
            profit_margin_pct=6.48,
            quadrant="High Volume / High Margin",
        ),
        StatePerformance(
            rank=3,
            state="Rajasthan",
            distinct_orders=32,
            total_sales=218900.0,
            total_profit=13000.0,
            avg_profit_per_order=406.25,
            profit_margin_pct=5.94,
            quadrant="Low Volume / High Margin",
        ),
        StatePerformance(
            rank=4,
            state="Gujarat",
            distinct_orders=27,
            total_sales=189400.0,
            total_profit=4180.0,
            avg_profit_per_order=154.81,
            profit_margin_pct=2.21,
            quadrant="Low Volume / Low Margin",
        ),
        StatePerformance(
            rank=5,
            state="Punjab",
            distinct_orders=25,
            total_sales=165200.0,
            total_profit=-6000.0,
            avg_profit_per_order=-240.0,
            profit_margin_pct=-3.63,
            quadrant="Low Volume / Low Margin",
        ),
    ]


# ---------------------------------------------------------------------------
# Core Acceptance Criteria Tests (SPEC AC-4.2)
# ---------------------------------------------------------------------------

def test_generate_all_charts_default_paths(
    synthetic_category_data: List[CategoryPerformance],
    synthetic_furniture_data: List[FurnitureTargetAchievement],
    synthetic_state_data: List[StatePerformance],
    tmp_path: Path,
) -> None:
    """Verifies AC-4.2: ChartGenerator creates all required charts in output directory."""
    manifest = ChartGenerator.generate_all_charts(
        category_data=synthetic_category_data,
        furniture_data=synthetic_furniture_data,
        state_data=synthetic_state_data,
        output_dir=tmp_path,
    )

    expected_keys = {
        "category_profitability",
        "furniture_target_vs_actual",
        "furniture_target_trajectory",
        "regional_performance",
        "state_regional_quadrants",
    }
    assert set(manifest.keys()) == expected_keys

    # Verify each referenced file exists and has non-zero size
    for key, path in manifest.items():
        assert isinstance(path, Path)
        assert path.exists(), f"Expected chart file does not exist: {path}"
        assert path.stat().st_size > 10_000, f"Chart file too small: {path}"


def test_png_headers_and_file_integrity(
    synthetic_category_data: List[CategoryPerformance],
    synthetic_furniture_data: List[FurnitureTargetAchievement],
    synthetic_state_data: List[StatePerformance],
    tmp_path: Path,
) -> None:
    """Verifies that all generated PNG files have valid 8-byte PNG headers and non-zero sizes."""
    manifest = ChartGenerator.generate_all_charts(
        category_data=synthetic_category_data,
        furniture_data=synthetic_furniture_data,
        state_data=synthetic_state_data,
        output_dir=tmp_path,
    )

    png_header = b"\x89PNG\r\n\x1a\n"

    for key, path in manifest.items():
        with open(path, "rb") as f:
            header = f.read(8)
        assert header == png_header, f"File {path.name} does not have valid PNG header: {header}"
        assert path.stat().st_size >= 25_000, f"File {path.name} unexpectedly small ({path.stat().st_size} bytes)"


def test_image_resolution_300_dpi_and_dimensions(
    synthetic_category_data: List[CategoryPerformance],
    synthetic_furniture_data: List[FurnitureTargetAchievement],
    synthetic_state_data: List[StatePerformance],
    tmp_path: Path,
) -> None:
    """Verifies that all charts are rendered at 300 DPI with publication-ready pixel dimensions."""
    manifest = ChartGenerator.generate_all_charts(
        category_data=synthetic_category_data,
        furniture_data=synthetic_furniture_data,
        state_data=synthetic_state_data,
        output_dir=tmp_path,
        dpi=300,
    )

    for key, path in manifest.items():
        with Image.open(path) as img:
            assert img.format == "PNG", f"Expected PNG format for {path.name}, got {img.format}"

            # Verify DPI in metadata
            dpi = img.info.get("dpi")
            assert dpi is not None, f"DPI metadata missing in {path.name}"
            assert abs(dpi[0] - 300.0) < 1.0, f"Expected 300 DPI horizontal in {path.name}, got {dpi[0]}"
            assert abs(dpi[1] - 300.0) < 1.0, f"Expected 300 DPI vertical in {path.name}, got {dpi[1]}"

            # Verify high-resolution pixel dimensions
            width, height = img.size
            assert width >= 2500, f"Width {width} too small for 300 DPI chart {path.name}"
            assert height >= 1400, f"Height {height} too small for 300 DPI chart {path.name}"


# ---------------------------------------------------------------------------
# Individual Chart Generation Unit Tests
# ---------------------------------------------------------------------------

def test_generate_category_profitability_chart_isolated(
    synthetic_category_data: List[CategoryPerformance],
    tmp_path: Path,
) -> None:
    """Tests isolated generation of category profitability dual-axis chart."""
    output_path = tmp_path / "custom_category.png"
    result = ChartGenerator.generate_category_profitability_chart(
        category_data=synthetic_category_data,
        output_path=output_path,
        dpi=300,
    )

    assert result == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 20_000

    with Image.open(output_path) as img:
        dpi = img.info.get("dpi")
        assert round(dpi[0]) == 300
        assert round(dpi[1]) == 300
        assert img.size[0] >= 2800
        assert img.size[1] >= 1600


def test_generate_furniture_target_chart_with_fluctuations(
    synthetic_furniture_data: List[FurnitureTargetAchievement],
    tmp_path: Path,
) -> None:
    """Tests isolated generation of furniture trajectory chart with highlighted fluctuations."""
    output_path = tmp_path / "custom_furniture.png"
    result = ChartGenerator.generate_furniture_target_chart(
        furniture_data=synthetic_furniture_data,
        output_path=output_path,
        dpi=300,
    )

    assert result == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 20_000

    with Image.open(output_path) as img:
        dpi = img.info.get("dpi")
        assert round(dpi[0]) == 300
        assert round(dpi[1]) == 300


def test_generate_furniture_target_chart_no_fluctuations(
    tmp_path: Path,
) -> None:
    """Tests furniture trajectory chart when no months exceed fluctuation threshold."""
    calm_data = [
        FurnitureTargetAchievement(
            month_key=f"2018-{m:02d}",
            display_month=f"M{m}-18",
            target_sales=10000.0,
            actual_sales=10000.0,
            mom_target_pct_change=None if m == 4 else 2.0,
            mom_actual_pct_change=None if m == 4 else 2.0,
            variance=0.0,
            achievement_pct=100.0,
            is_significant_fluctuation=False,
        )
        for m in range(4, 10)
    ]

    output_path = tmp_path / "calm_furniture.png"
    result = ChartGenerator.generate_furniture_target_chart(
        furniture_data=calm_data,
        output_path=output_path,
        dpi=300,
    )
    assert result.exists()
    assert result.stat().st_size > 20_000


def test_generate_regional_performance_chart_isolated(
    synthetic_state_data: List[StatePerformance],
    tmp_path: Path,
) -> None:
    """Tests isolated generation of regional performance 2-panel chart."""
    output_path = tmp_path / "custom_regional.png"
    result = ChartGenerator.generate_regional_performance_chart(
        state_data=synthetic_state_data,
        output_path=output_path,
        dpi=300,
    )

    assert result == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 20_000

    with Image.open(output_path) as img:
        dpi = img.info.get("dpi")
        assert round(dpi[0]) == 300
        assert round(dpi[1]) == 300
        # 2-panel figure should be wide (>= 3500px)
        assert img.size[0] >= 3500
        assert img.size[1] >= 1600


# ---------------------------------------------------------------------------
# Directory Resolution & Environment Configuration Tests
# ---------------------------------------------------------------------------

def test_resolve_output_dir_custom_arg(tmp_path: Path) -> None:
    """Tests resolve_output_dir creates and returns explicitly passed directory."""
    custom_dir = tmp_path / "custom_sub_dir"
    resolved = ChartGenerator.resolve_output_dir(custom_dir)
    assert resolved == custom_dir
    assert custom_dir.is_dir()


def test_resolve_output_dir_env_var(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests resolve_output_dir honors CHART_ASSETS_DIR environment variable."""
    env_dir = tmp_path / "env_charts_dir"
    monkeypatch.setenv("CHART_ASSETS_DIR", str(env_dir))

    resolved = ChartGenerator.resolve_output_dir()
    assert resolved == env_dir
    assert env_dir.is_dir()


def test_format_inr_helper() -> None:
    """Tests Indian Rupee formatting utility."""
    assert format_inr(1234567.0) == "Rs. 1,234,567"
    assert format_inr(1234567.0, compact=True) == "Rs. 12.35L"
    assert format_inr(15000.0, compact=True) == "Rs. 15.0k"
    assert format_inr(500.0, compact=True) == "Rs. 500"


# ---------------------------------------------------------------------------
# Defensive Boundary Validations & Edge Cases
# ---------------------------------------------------------------------------

def test_empty_category_data_raises_value_error(tmp_path: Path) -> None:
    """Passing empty sequence to category chart raises ValueError."""
    with pytest.raises(ValueError, match="category_data sequence cannot be empty"):
        ChartGenerator.generate_category_profitability_chart([], tmp_path / "test.png")


def test_empty_furniture_data_raises_value_error(tmp_path: Path) -> None:
    """Passing empty sequence to furniture chart raises ValueError."""
    with pytest.raises(ValueError, match="furniture_data sequence cannot be empty"):
        ChartGenerator.generate_furniture_target_chart([], tmp_path / "test.png")


def test_empty_state_data_raises_value_error(tmp_path: Path) -> None:
    """Passing empty sequence to state chart raises ValueError."""
    with pytest.raises(ValueError, match="state_data sequence cannot be empty"):
        ChartGenerator.generate_regional_performance_chart([], tmp_path / "test.png")


def test_invalid_type_raises_type_error(tmp_path: Path) -> None:
    """Passing non-sequence types raises TypeError."""
    with pytest.raises(TypeError, match="category_data must be a sequence"):
        ChartGenerator.generate_category_profitability_chart(12345, tmp_path / "test.png")  # type: ignore

    with pytest.raises(TypeError, match="furniture_data must be a sequence"):
        ChartGenerator.generate_furniture_target_chart(None, tmp_path / "test.png")  # type: ignore

    with pytest.raises(TypeError, match="state_data must be a sequence"):
        ChartGenerator.generate_regional_performance_chart({"invalid": "dict"}, tmp_path / "test.png")  # type: ignore


def test_single_item_edge_case_renders_cleanly(tmp_path: Path) -> None:
    """Verifies that charts render without errors on single-item sequences."""
    single_cat = [
        CategoryPerformance(
            category="Clothing",
            total_sales=1000.0,
            total_profit=150.0,
            avg_profit_per_order=150.0,
            profit_margin_pct=15.0,
            distinct_orders=1,
            total_quantity=2,
            performance_rank=1,
        )
    ]
    single_furn = [
        FurnitureTargetAchievement(
            month_key="2018-04",
            display_month="Apr-18",
            target_sales=5000.0,
            actual_sales=5200.0,
            mom_target_pct_change=None,
            mom_actual_pct_change=None,
            variance=200.0,
            achievement_pct=104.0,
            is_significant_fluctuation=False,
        )
    ]
    single_state = [
        StatePerformance(
            rank=1,
            state="Goa",
            distinct_orders=5,
            total_sales=25000.0,
            total_profit=5000.0,
            avg_profit_per_order=1000.0,
            profit_margin_pct=20.0,
            quadrant="High Volume / High Margin",
        )
    ]

    manifest = ChartGenerator.generate_all_charts(
        category_data=single_cat,
        furniture_data=single_furn,
        state_data=single_state,
        output_dir=tmp_path / "single_item",
        dpi=150,  # Speed up test execution
    )
    for p in manifest.values():
        assert p.exists()
        assert p.stat().st_size > 5_000


def test_negative_values_and_losses_render_without_crash(tmp_path: Path) -> None:
    """Verifies that negative margins, losses, and negative variances render cleanly."""
    loss_cat = [
        CategoryPerformance(
            category="Furniture",
            total_sales=10000.0,
            total_profit=-2500.0,
            avg_profit_per_order=-500.0,
            profit_margin_pct=-25.0,
            distinct_orders=5,
            total_quantity=10,
            performance_rank=1,
        )
    ]
    output_path = tmp_path / "loss_cat.png"
    result = ChartGenerator.generate_category_profitability_chart(loss_cat, output_path, dpi=150)
    assert result.exists()
    assert result.stat().st_size > 5_000


# ---------------------------------------------------------------------------
# Design Token System Verification (ADR-007)
# ---------------------------------------------------------------------------

def test_pastel_tokens_constants() -> None:
    """Verifies that PASTEL_TOKENS defines the palette tokens mandated by ADR-007."""
    assert PASTEL_TOKENS["sage"].lower() == "#48bb78"
    assert PASTEL_TOKENS["gold"].lower() == "#d69e2e"
    assert PASTEL_TOKENS["lavender"].lower() == "#805ad5"
    assert PASTEL_TOKENS["coral"].lower() == "#e53e3e"
    assert PASTEL_TOKENS["slate"].lower() == "#2d3748"
    assert "sage_tint" in PASTEL_TOKENS
    assert "coral_tint" in PASTEL_TOKENS


# ---------------------------------------------------------------------------
# Full Pipeline Integration & CLI Runner Tests
# ---------------------------------------------------------------------------

def test_generate_from_data_dir_integration(tmp_path: Path) -> None:
    """Tests the complete end-to-end orchestration pipeline from raw data to 300 DPI charts."""
    # Run against workspace root raw datasets
    manifest = ChartGenerator.generate_from_data_dir(
        data_dir=".",
        output_dir=tmp_path / "integration_charts",
        dpi=300,
    )

    assert len(manifest) == 5
    for key, path in manifest.items():
        assert path.exists()
        with Image.open(path) as img:
            assert abs(img.info["dpi"][0] - 300.0) < 1.0


def test_chart_generator_cli_execution(tmp_path: Path) -> None:
    """Tests executing ChartGenerator CLI via python -m src.chart_generator."""
    out_dir = tmp_path / "cli_charts"
    cmd = [
        sys.executable,
        "-m",
        "src.chart_generator",
        "--data-dir",
        ".",
        "--output-dir",
        str(out_dir),
        "--dpi",
        "150",
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert proc.returncode == 0, f"CLI command failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert "Generated 5 charts in" in proc.stdout
    assert (out_dir / "category_profitability.png").exists()
    assert (out_dir / "furniture_target_vs_actual.png").exists()
    assert (out_dir / "regional_performance.png").exists()


def test_production_assets_charts_generation() -> None:
    """Verifies that 300 DPI charts are rendered in assets/charts/ without GUI display (SPEC AC-4.2)."""
    # 1. Assert headless backend (zero GUI display requirement)
    assert matplotlib.get_backend().lower() == "agg", f"Expected Agg backend, got {matplotlib.get_backend()}"

    # 2. Render charts into assets/charts
    output_dir = Path("assets/charts")
    manifest = ChartGenerator.generate_from_data_dir(
        data_dir=".",
        output_dir=output_dir,
        dpi=300,
    )

    required_charts = [
        "category_profitability.png",
        "furniture_target_vs_actual.png",
        "regional_performance.png",
    ]
    png_header = b"\x89PNG\r\n\x1a\n"

    for filename in required_charts:
        file_path = output_dir / filename
        assert file_path.exists(), f"Missing production chart: {file_path}"
        assert file_path.stat().st_size > 25_000, f"Production chart too small ({file_path.stat().st_size} bytes)"

        with open(file_path, "rb") as f:
            header = f.read(8)
        assert header == png_header, f"Invalid PNG header for {filename}"

        with Image.open(file_path) as img:
            assert img.format == "PNG"
            dpi = img.info.get("dpi")
            assert dpi is not None, f"DPI metadata missing in {filename}"
            assert abs(dpi[0] - 300.0) < 1.0, f"Expected 300 DPI in {filename}, got {dpi[0]}"
            assert abs(dpi[1] - 300.0) < 1.0, f"Expected 300 DPI in {filename}, got {dpi[1]}"
            assert img.size[0] >= 2500, f"Width too small for {filename}"
            assert img.size[1] >= 1400, f"Height too small for {filename}"

