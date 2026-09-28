"""Automated tests for ExportService and end-to-end CLI runner (M1-TASK-06).

Validates:
- SPEC AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5: End-to-end analytical pipeline execution.
- Export file integrity: JSON and CSV artifacts generated in data/output/.
- Dataclass schema compliance: deserialized JSON objects match domain models.
- Edge cases: NaN sanitization, null mapping, empty records, type errors.
- CLI execution: python -m src.main exit code 0, tabular summaries, custom arguments.
"""

from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List
import pandas as pd
import pytest

from src.analytics_engine import (
    AnalyticsEngine,
    CategoryPerformance,
    CityPerformance,
    CityPriority,
    FurnitureTargetAchievement,
    StatePerformance,
    SubCategoryPerformance,
)
from src.export_service import (
    DEFAULT_OUTPUT_DIR,
    ExportService,
    record_to_dict,
    sanitize_value_for_json,
)
from src.main import format_ascii_table, format_currency, format_pct, main


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_category_records() -> List[CategoryPerformance]:
    """Sample CategoryPerformance records matching domain model."""
    return [
        CategoryPerformance(
            category="Clothing",
            total_sales=139054.0,
            total_profit=11163.0,
            avg_profit_per_order=28.40,
            profit_margin_pct=8.03,
            distinct_orders=393,
            total_quantity=3516,
            performance_rank=1,
        ),
        CategoryPerformance(
            category="Electronics",
            total_sales=165267.0,
            total_profit=10494.0,
            avg_profit_per_order=51.44,
            profit_margin_pct=6.35,
            distinct_orders=204,
            total_quantity=1154,
            performance_rank=2,
        ),
        CategoryPerformance(
            category="Furniture",
            total_sales=127181.0,
            total_profit=2298.0,
            avg_profit_per_order=12.35,
            profit_margin_pct=1.81,
            distinct_orders=186,
            total_quantity=945,
            performance_rank=3,
        ),
    ]


@pytest.fixture
def sample_furniture_records() -> List[FurnitureTargetAchievement]:
    """Sample FurnitureTargetAchievement records with baseline and fluctuations."""
    return [
        FurnitureTargetAchievement(
            month_key="2018-04",
            display_month="Apr-18",
            target_sales=10000.0,
            actual_sales=11842.0,
            mom_target_pct_change=None,
            mom_actual_pct_change=None,
            variance=1842.0,
            achievement_pct=118.42,
            is_significant_fluctuation=False,
        ),
        FurnitureTargetAchievement(
            month_key="2018-05",
            display_month="May-18",
            target_sales=12000.0,
            actual_sales=10500.0,
            mom_target_pct_change=20.0,
            mom_actual_pct_change=-11.33,
            variance=-1500.0,
            achievement_pct=87.50,
            is_significant_fluctuation=True,
        ),
    ]


@pytest.fixture
def sample_state_records() -> List[StatePerformance]:
    """Sample StatePerformance records including loss-making state."""
    return [
        StatePerformance(
            rank=1,
            state="Madhya Pradesh",
            distinct_orders=101,
            total_sales=105140.0,
            total_profit=5551.0,
            avg_profit_per_order=54.96,
            profit_margin_pct=5.28,
            quadrant="High Volume / Low Margin",
        ),
        StatePerformance(
            rank=2,
            state="Maharashtra",
            distinct_orders=90,
            total_sales=95348.0,
            total_profit=6176.0,
            avg_profit_per_order=68.62,
            profit_margin_pct=6.48,
            quadrant="High Volume / High Margin",
        ),
        StatePerformance(
            rank=5,
            state="Punjab",
            distinct_orders=25,
            total_sales=16786.0,
            total_profit=-609.0,
            avg_profit_per_order=-24.36,
            profit_margin_pct=-3.63,
            quadrant="Low Volume / Low Margin",
        ),
    ]


@pytest.fixture
def sample_city_records() -> List[CityPerformance]:
    """Sample CityPerformance records."""
    return [
        CityPerformance(
            state="Madhya Pradesh",
            city="Indore",
            distinct_orders=50,
            total_sales=50000.0,
            total_profit=3500.0,
            avg_profit_per_order=70.0,
            profit_margin_pct=7.0,
        ),
        CityPerformance(
            state="Maharashtra",
            city="Mumbai",
            distinct_orders=45,
            total_sales=48000.0,
            total_profit=3200.0,
            avg_profit_per_order=71.11,
            profit_margin_pct=6.67,
        ),
    ]


# ---------------------------------------------------------------------------
# Unit Tests for Sanitization and Utilities
# ---------------------------------------------------------------------------

def test_sanitize_value_for_json() -> None:
    """Verifies that sanitize_value_for_json correctly handles nan, inf, and dates."""
    assert sanitize_value_for_json(float("nan")) is None
    assert sanitize_value_for_json(float("inf")) is None
    assert sanitize_value_for_json(123.45) == 123.45
    assert sanitize_value_for_json("test") == "test"
    assert sanitize_value_for_json(None) is None

    ts = pd.Timestamp("2018-04-01")
    assert sanitize_value_for_json(ts) == ts.isoformat()

    nested = {"a": float("nan"), "b": [float("inf"), 42, ts]}
    sanitized = sanitize_value_for_json(nested)
    assert sanitized["a"] is None
    assert sanitized["b"][0] is None
    assert sanitized["b"][1] == 42
    assert sanitized["b"][2] == ts.isoformat()


def test_record_to_dict_conversion(sample_category_records: List[CategoryPerformance]) -> None:
    """Verifies record_to_dict works for dataclasses and dicts."""
    c = sample_category_records[0]
    d = record_to_dict(c)
    assert isinstance(d, dict)
    assert d["category"] == "Clothing"
    assert d["total_sales"] == 139054.0

    raw_dict = {"custom": 123}
    assert record_to_dict(raw_dict) == {"custom": 123}

    with pytest.raises(TypeError, match="Expected dataclass or dict"):
        record_to_dict(42)


# ---------------------------------------------------------------------------
# Unit Tests for ExportService Methods
# ---------------------------------------------------------------------------

def test_export_category_performance_schema_and_integrity(
    tmp_path: Path,
    sample_category_records: List[CategoryPerformance],
) -> None:
    """Tests exporting CategoryPerformance to JSON and CSV, validating schema reconstitution."""
    service = ExportService(output_dir=tmp_path)
    res = service.export_category_performance(sample_category_records)

    json_path = res["json"]
    csv_path = res["csv"]

    assert json_path.exists()
    assert csv_path.exists()
    assert json_path.stat().st_size > 0
    assert csv_path.stat().st_size > 0

    # 1. Validate JSON schema compliance
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == len(sample_category_records)

    # Reconstruct dataclass instances to assert exact schema match
    for item in data:
        reconstructed = CategoryPerformance(**item)
        assert reconstructed.total_sales > 0

    # 2. Validate CSV schema compliance
    df_csv = pd.read_csv(csv_path)
    assert len(df_csv) == len(sample_category_records)
    expected_cols = [
        "category",
        "total_sales",
        "total_profit",
        "avg_profit_per_order",
        "profit_margin_pct",
        "distinct_orders",
        "total_quantity",
        "performance_rank",
    ]
    assert list(df_csv.columns) == expected_cols
    assert df_csv.loc[df_csv["category"] == "Clothing", "performance_rank"].iloc[0] == 1


def test_export_furniture_targets_schema_and_null_baseline(
    tmp_path: Path,
    sample_furniture_records: List[FurnitureTargetAchievement],
) -> None:
    """Tests exporting FurnitureTargetAchievement ensuring null baseline is preserved."""
    service = ExportService(output_dir=tmp_path)
    res = service.export_furniture_targets(sample_furniture_records)

    json_path = res["json"]
    csv_path = res["csv"]

    assert json_path.exists()
    assert csv_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 2
    # Baseline month Apr-18 must have null for mom_target_pct_change
    assert data[0]["display_month"] == "Apr-18"
    assert data[0]["mom_target_pct_change"] is None

    # Month May-18 has 20.0% MoM
    assert data[1]["display_month"] == "May-18"
    assert data[1]["mom_target_pct_change"] == 20.0
    assert data[1]["is_significant_fluctuation"] is True

    # Reconstruct dataclasses
    for item in data:
        reconstructed = FurnitureTargetAchievement(**item)
        assert reconstructed.target_sales > 0

    df_csv = pd.read_csv(csv_path)
    assert len(df_csv) == 2
    assert pd.isna(df_csv.loc[0, "mom_target_pct_change"])


def test_export_state_performance_and_negative_profits(
    tmp_path: Path,
    sample_state_records: List[StatePerformance],
) -> None:
    """Tests exporting StatePerformance preserving loss-making states (Punjab)."""
    service = ExportService(output_dir=tmp_path)
    res = service.export_state_performance(sample_state_records)

    json_path = res["json"]
    csv_path = res["csv"]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 3
    punjab_entry = next(item for item in data if item["state"] == "Punjab")
    assert punjab_entry["total_profit"] == -609.0
    assert punjab_entry["profit_margin_pct"] == -3.63

    for item in data:
        reconstructed = StatePerformance(**item)
        assert reconstructed.rank >= 1

    df_csv = pd.read_csv(csv_path)
    assert (df_csv["total_profit"] < 0).any()


def test_export_city_performance(
    tmp_path: Path,
    sample_city_records: List[CityPerformance],
) -> None:
    """Tests exporting CityPerformance records."""
    service = ExportService(output_dir=tmp_path)
    res = service.export_city_performance(sample_city_records)

    assert res["json"].exists()
    assert res["csv"].exists()

    with open(res["json"], "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 2
    for item in data:
        CityPerformance(**item)


def test_export_all_orchestration(
    tmp_path: Path,
    sample_category_records: List[CategoryPerformance],
    sample_furniture_records: List[FurnitureTargetAchievement],
    sample_state_records: List[StatePerformance],
    sample_city_records: List[CityPerformance],
) -> None:
    """Tests export_all creates all required analytical files."""
    service = ExportService(output_dir=tmp_path)
    artifacts = service.export_all(
        category_data=sample_category_records,
        furniture_data=sample_furniture_records,
        state_data=sample_state_records,
        city_data=sample_city_records,
    )

    expected_keys = {
        "category_performance",
        "furniture_targets",
        "state_performance",
        "city_performance",
    }
    assert set(artifacts.keys()) == expected_keys

    for art_key, paths in artifacts.items():
        assert "json" in paths and paths["json"].exists()
        assert "csv" in paths and paths["csv"].exists()
        assert paths["json"].stat().st_size > 0
        assert paths["csv"].stat().st_size > 0


def test_export_service_empty_sequence(tmp_path: Path) -> None:
    """Tests handling empty sequences gracefully."""
    service = ExportService(output_dir=tmp_path)
    res = service.export_category_performance([])

    with open(res["json"], "r", encoding="utf-8") as f:
        assert json.load(f) == []

    df = pd.read_csv(res["csv"])
    assert len(df) == 0
    assert "category" in df.columns


def test_export_service_input_validation(tmp_path: Path) -> None:
    """Tests invalid inputs raise appropriate TypeErrors."""
    service = ExportService(output_dir=tmp_path)

    with pytest.raises(TypeError, match="records must be a sequence"):
        service.export_records_to_json(12345, tmp_path / "bad.json")  # type: ignore

    with pytest.raises(TypeError, match="records must be a sequence"):
        service.export_records_to_csv("not-a-list", tmp_path / "bad.csv")  # type: ignore

    with pytest.raises(TypeError, match="data must be a dict"):
        service.export_dict_to_json(["not", "dict"], tmp_path / "bad.json")  # type: ignore


def test_export_service_env_var_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Tests that ExportService respects OUTPUT_DATA_DIR environment variable."""
    target_dir = tmp_path / "env_output_dir"
    monkeypatch.setenv("OUTPUT_DATA_DIR", str(target_dir))

    service = ExportService()
    assert service.output_dir == target_dir
    assert target_dir.exists()


# ---------------------------------------------------------------------------
# CLI & End-to-End Pipeline Tests
# ---------------------------------------------------------------------------

def test_main_cli_function_execution_in_process(tmp_path: Path) -> None:
    """Tests in-process invocation of main() with temporary output directory."""
    output_dir = tmp_path / "cli_output"
    exit_code = main([
        "--output-dir", str(output_dir),
        "--fluctuation-threshold", "15.0",
        "--top-states", "5",
        "--quiet",
    ])
    assert exit_code == 0

    assert (output_dir / "category_performance.json").exists()
    assert (output_dir / "category_performance.csv").exists()
    assert (output_dir / "furniture_targets.json").exists()
    assert (output_dir / "furniture_targets.csv").exists()
    assert (output_dir / "state_performance.json").exists()
    assert (output_dir / "state_performance.csv").exists()


def test_main_cli_subprocess_execution() -> None:
    """Tests executing 'python -m src.main' via subprocess end-to-end (SPEC AC-1.1 to AC-1.5)."""
    result = subprocess.run(
        [sys.executable, "-m", "src.main"],
        capture_output=True,
        text=True,
        cwd=str(Path(".").resolve()),
    )

    assert result.returncode == 0, f"Process exited with {result.returncode}. Stderr: {result.stderr}"

    stdout = result.stdout
    # Verify banner and sections are present
    assert "JAR GROWTH INTERN ASSIGNMENT - ANALYTICAL PIPELINE RUNNER" in stdout
    assert "QUESTION 1 PART 1: CATEGORY SALES & PROFITABILITY PERFORMANCE" in stdout
    assert "QUESTION 1 PART 2: FURNITURE TARGET MoM FLUCTUATION & RECONCILIATION" in stdout
    assert "QUESTION 1 PART 3: TOP 5 STATES REGIONAL PERFORMANCE" in stdout
    assert "EXPORT ARTIFACTS WRITTEN TO DISK" in stdout
    assert "PIPELINE EXECUTION COMPLETED SUCCESSFULLY" in stdout

    # Verify default output files exist
    output_dir = Path("data/output")
    assert (output_dir / "category_performance.json").exists()
    assert (output_dir / "category_performance.csv").exists()
    assert (output_dir / "furniture_targets.json").exists()
    assert (output_dir / "furniture_targets.csv").exists()
    assert (output_dir / "state_performance.json").exists()
    assert (output_dir / "state_performance.csv").exists()


def test_main_cli_custom_top_states_and_threshold(tmp_path: Path) -> None:
    """Tests CLI arguments for top_states and fluctuation threshold."""
    output_dir = tmp_path / "custom_cli"
    exit_code = main([
        "--output-dir", str(output_dir),
        "--top-states", "3",
        "--fluctuation-threshold", "20.0",
        "--quiet",
    ])
    assert exit_code == 0

    state_json = output_dir / "state_performance.json"
    with open(state_json, "r", encoding="utf-8") as f:
        states = json.load(f)
    assert len(states) == 3


def test_main_cli_invalid_data_dir() -> None:
    """Tests that pointing to a nonexistent data dir returns exit code 1."""
    exit_code = main(["--data-dir", "nonexistent_dir_random_12345", "--quiet"])
    assert exit_code == 1


# ---------------------------------------------------------------------------
# Formatting Utility Tests
# ---------------------------------------------------------------------------

def test_format_ascii_table() -> None:
    """Tests format_ascii_table renders expected borders and alignment."""
    headers = ["ColA", "ColB"]
    rows = [["1", "Apple"], ["200", "Banana"]]
    table_str = format_ascii_table(headers, rows, alignments=[">", "<"])

    assert "+------+--------+" in table_str
    assert "| ColA | ColB   |" in table_str
    assert "|    1 | Apple  |" in table_str
    assert "|  200 | Banana |" in table_str


def test_format_helpers() -> None:
    """Tests format_currency and format_pct."""
    assert format_currency(12345.67) == "Rs. 12,345.67"
    assert format_pct(None) == "N/A"
    assert format_pct(15.25) == "15.25%"
    assert format_pct(15.25, show_sign=True) == "+15.25%"
    assert format_pct(-5.5, show_sign=True) == "-5.50%"


def test_export_subcategory_priorities_and_insights(tmp_path: Path) -> None:
    """Sub-category, city-priority and Q1 insight artifacts round-trip through export_all."""
    subs = [
        SubCategoryPerformance(
            category="Furniture", sub_category="Tables", total_sales=22614.0,
            total_profit=-4011.0, profit_margin_pct=-17.74, distinct_orders=16,
            total_quantity=61, avg_order_value=1413.38, avg_profit_per_order=-250.69,
        ),
    ]
    prios = [
        CityPriority(
            action="Fix", state="Punjab", city="Chandigarh", total_sales=12279.0,
            total_profit=-1153.0, profit_margin_pct=-9.39, profit_gap=1834.67,
            in_top_states=True, reason="Loses Rs 1,153.",
        ),
    ]
    service = ExportService(output_dir=tmp_path)
    artifacts = service.export_all(
        category_data=[], furniture_data=[], state_data=[],
        subcategory_data=subs, city_priorities=prios,
        q1_insights={"part1_reasons": ["Tables loses money."]},
    )

    sub_json = tmp_path / "subcategory_performance.json"
    assert artifacts["subcategory_performance"]["json"] == sub_json
    assert (tmp_path / "subcategory_performance.csv").exists()
    data = json.loads(sub_json.read_text(encoding="utf-8"))
    assert SubCategoryPerformance(**data[0]).total_profit == -4011.0
    csv_df = pd.read_csv(tmp_path / "subcategory_performance.csv")
    assert list(csv_df.columns)[:2] == ["category", "sub_category"]

    prio_data = json.loads((tmp_path / "city_priorities.json").read_text(encoding="utf-8"))
    assert CityPriority(**prio_data[0]).city == "Chandigarh"
    insights = json.loads((tmp_path / "q1_insights.json").read_text(encoding="utf-8"))
    assert insights["part1_reasons"] == ["Tables loses money."]
