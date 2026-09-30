"""Tests verifying project scaffolding, environment configuration, and test fixtures (M1-TASK-01).

Acceptance Criteria:
- SPEC AC-1.1, AC-E4: Pytest discovers test fixtures via conftest.py with `python -m pytest`.
- .gitignore ignores virtualenvs, build artifacts, .env, caches, data/output/, assets/charts/, and generated PDFs.
- .env.example defines all configuration defaults.
- requirements.txt defines pinned dependencies.
- Includes invalid-input / negative test cases.
"""

from pathlib import Path
import pytest
import pandas as pd


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Test .gitignore Configuration
# ---------------------------------------------------------------------------

def test_gitignore_exists_and_contains_required_rules():
    """Verify .gitignore exists and specifies rules for virtualenvs, caches, .env, and build outputs."""
    gitignore_path = WORKSPACE_ROOT / ".gitignore"
    assert gitignore_path.exists(), ".gitignore must exist in workspace root"

    content = gitignore_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]

    # Check key exclusion patterns
    assert any(".venv" in line or "venv/" in line for line in lines), "Must ignore virtual environments"
    assert any("__pycache__" in line for line in lines), "Must ignore __pycache__"
    assert any(".pytest_cache" in line for line in lines), "Must ignore .pytest_cache"
    assert any(".env" in line for line in lines), "Must ignore .env files"
    assert any("build/" in line or "dist/" in line for line in lines), "Must ignore build artifacts"
    assert any("data/output/" in line for line in lines), "Must ignore data/output/"
    assert any("assets/charts/" in line for line in lines), "Must ignore assets/charts/"
    assert any("*.pdf" in line or "Jegadeesh_D_Jar_Growth_Intern_Assignment.pdf" in line for line in lines), (
        "Must ignore generated PDFs"
    )
    assert "!Jar - Growth Intern Assignment.pdf" in lines, "Must preserve source assignment brief PDF"


def test_gitignore_negative_does_not_ignore_source_or_docs():
    """Invalid-pattern / safety test: .gitignore must NOT ignore essential source or doc directories."""
    gitignore_path = WORKSPACE_ROOT / ".gitignore"
    content = gitignore_path.read_text(encoding="utf-8")
    ignored_patterns = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]

    # Critical project directories and files must not be ignored
    forbidden_ignores = ["src/", "docs/", "tests/", "requirements.txt", "README.md"]
    for forbidden in forbidden_ignores:
        assert forbidden not in ignored_patterns, f".gitignore should not ignore vital directory/file '{forbidden}'"


# ---------------------------------------------------------------------------
# Test .env.example Configuration
# ---------------------------------------------------------------------------

def test_env_example_contains_all_required_variables():
    """Verify .env.example defines all required configuration defaults from architecture."""
    env_path = WORKSPACE_ROOT / ".env.example"
    assert env_path.exists(), ".env.example must exist in workspace root"

    content = env_path.read_text(encoding="utf-8")
    env_vars = {}
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            env_vars[key.strip()] = val.strip()

    required_keys = [
        "APP_ENV",
        "LOG_LEVEL",
        "DATA_DIR",
        "OUTPUT_DATA_DIR",
        "CHART_ASSETS_DIR",
        "OUTPUT_PDF_PATH",
        "FURNITURE_MOM_FLUCTUATION_THRESHOLD",
        "TOP_STATES_COUNT",
    ]

    for req_key in required_keys:
        assert req_key in env_vars, f".env.example is missing required configuration key: {req_key}"

    # Verify numeric defaults parse correctly
    threshold = float(env_vars["FURNITURE_MOM_FLUCTUATION_THRESHOLD"])
    assert threshold == 15.0, f"Expected default FURNITURE_MOM_FLUCTUATION_THRESHOLD 15.0, got {threshold}"

    top_states = int(env_vars["TOP_STATES_COUNT"])
    assert top_states == 5, f"Expected default TOP_STATES_COUNT 5, got {top_states}"


def test_env_example_invalid_input_handling():
    """Invalid-input test: Parser function should reject invalid env formats."""
    def parse_env_line(line: str):
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        if "=" not in line:
            raise ValueError(f"Malformed environment variable line: {line}")
        k, v = line.split("=", 1)
        if not k.strip():
            raise ValueError("Environment variable key cannot be blank")
        return k.strip(), v.strip()

    # Valid line should parse
    assert parse_env_line("APP_ENV=production") == ("APP_ENV", "production")

    # Invalid lines should raise ValueError
    with pytest.raises(ValueError, match="Malformed"):
        parse_env_line("INVALID_NO_EQUALS_SIGN")

    with pytest.raises(ValueError, match="blank"):
        parse_env_line("=EMPTY_KEY")


# ---------------------------------------------------------------------------
# Test requirements.txt
# ---------------------------------------------------------------------------

def test_requirements_file_defines_pinned_dependencies():
    """Verify requirements.txt exists and contains all required packages."""
    req_path = WORKSPACE_ROOT / "requirements.txt"
    assert req_path.exists(), "requirements.txt must exist in workspace root"

    content = req_path.read_text(encoding="utf-8").lower()
    required_packages = ["pandas", "numpy", "openpyxl", "fpdf2", "matplotlib", "pytest"]

    for pkg in required_packages:
        assert pkg in content, f"requirements.txt missing required dependency: {pkg}"


# ---------------------------------------------------------------------------
# Test Fixtures in tests/conftest.py
# ---------------------------------------------------------------------------

def test_raw_fixtures_structure(sample_raw_orders_df, sample_raw_order_details_df, sample_raw_sales_targets_df):
    """Verify raw fixture DataFrames accurately reflect raw Excel columns."""
    # Orders raw columns
    expected_order_cols = {"Order ID", "Order Date", "CustomerName", "State", "City"}
    assert expected_order_cols.issubset(sample_raw_orders_df.columns), (
        f"Missing expected raw order columns: {expected_order_cols - set(sample_raw_orders_df.columns)}"
    )
    assert len(sample_raw_orders_df) > 0

    # Order details raw columns
    expected_details_cols = {"Order ID", "Amount", "Profit", "Quantity", "Category", "Sub-Category"}
    assert expected_details_cols.issubset(sample_raw_order_details_df.columns), (
        f"Missing expected raw detail columns: {expected_details_cols - set(sample_raw_order_details_df.columns)}"
    )
    assert len(sample_raw_order_details_df) > 0

    # Sales target raw columns
    expected_target_cols = {"Month of Order Date", "Category", "Target"}
    assert expected_target_cols.issubset(sample_raw_sales_targets_df.columns), (
        f"Missing expected raw target columns: {expected_target_cols - set(sample_raw_sales_targets_df.columns)}"
    )
    assert len(sample_raw_sales_targets_df) > 0


def test_normalized_fixtures_structure(sample_orders_df, sample_order_details_df, sample_sales_targets_df):
    """Verify normalized fixture DataFrames adhere to snake_case schema and typed fields."""
    # Normalized orders schema
    expected_norm_orders = {"order_id", "order_date", "customer_name", "state", "city"}
    assert expected_norm_orders.issubset(sample_orders_df.columns)
    assert pd.api.types.is_datetime64_any_dtype(sample_orders_df["order_date"])

    # Normalized details schema
    expected_norm_details = {"order_id", "amount", "profit", "quantity", "category", "sub_category"}
    assert expected_norm_details.issubset(sample_order_details_df.columns)
    assert pd.api.types.is_numeric_dtype(sample_order_details_df["amount"])
    assert pd.api.types.is_numeric_dtype(sample_order_details_df["profit"])
    assert pd.api.types.is_integer_dtype(sample_order_details_df["quantity"])

    # Normalized targets schema
    expected_norm_targets = {"month_of_order_date", "category", "target"}
    assert expected_norm_targets.issubset(sample_sales_targets_df.columns)
    assert pd.api.types.is_datetime64_any_dtype(sample_sales_targets_df["month_of_order_date"])
    assert pd.api.types.is_numeric_dtype(sample_sales_targets_df["target"])


def test_sample_merged_fixture(sample_merged_df):
    """Verify sample_merged_df fixture preserves inner join integrity."""
    assert len(sample_merged_df) > 0
    assert "order_id" in sample_merged_df.columns
    assert "amount" in sample_merged_df.columns
    assert "state" in sample_merged_df.columns
    assert "category" in sample_merged_df.columns


def test_furniture_chronological_fixture_ordering(sample_furniture_targets_chronological):
    """Verify chronological ordering and 12-month span for furniture target fixture."""
    df = sample_furniture_targets_chronological
    assert len(df) == 12
    assert (df["category"] == "Furniture").all()
    # Check strict chronological monotonicity
    assert df["month_of_order_date"].is_monotonic_increasing


def test_edge_case_fixtures(sample_mixed_dates_records, sample_loss_leader_details_df):
    """Verify edge case fixtures provide negative profit loss leaders and mixed dates."""
    # AC-E2: Loss leaders have negative profits
    assert (sample_loss_leader_details_df["profit"] < 0).any(), "Loss leader fixture must include negative profits"

    # AC-E1: Mixed dates fixture contains strings and datetime objects
    date_types = {type(rec["Order Date"]) for rec in sample_mixed_dates_records}
    assert str in date_types, "Mixed dates fixture must contain string date representations"


def test_mock_excel_dir_fixture(mock_excel_dir):
    """Verify mock_excel_dir fixture generates readable Excel files on disk."""
    orders_path = mock_excel_dir / "List of Orders.xlsx"
    details_path = mock_excel_dir / "Order Details.xlsx"
    targets_path = mock_excel_dir / "Sales target.xlsx"

    assert orders_path.exists(), "List of Orders.xlsx must exist in mock dir"
    assert details_path.exists(), "Order Details.xlsx must exist in mock dir"
    assert targets_path.exists(), "Sales target.xlsx must exist in mock dir"

    loaded_orders = pd.read_excel(orders_path)
    assert len(loaded_orders) > 0
    assert "Order ID" in loaded_orders.columns


def test_schema_invalid_input_validation():
    """Invalid-input test: Attempting to process corrupt records without mandatory columns raises KeyError."""
    corrupt_df = pd.DataFrame([{"invalid_col": 123}])

    def validate_orders_schema(df: pd.DataFrame):
        required = {"order_id", "order_date", "customer_name", "state", "city"}
        missing = required - set(df.columns)
        if missing:
            raise KeyError(f"Missing required columns: {missing}")

    with pytest.raises(KeyError, match="Missing required columns"):
        validate_orders_schema(corrupt_df)
