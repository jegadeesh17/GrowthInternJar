"""Unit tests for DataLoader, schema normalization, and boundary validation.

Covers:
- SPEC AC-1.1: Dataset ingestion and schema normalization
- SPEC AC-E1: Date inconsistency handling (mixed formats, leap days, swapped mm-dd-yyyy)
- SPEC AC-E4: Missing or corrupt input data handling (FileNotFoundError, KeyError, ValueError)
"""

from datetime import datetime
from pathlib import Path
import tempfile
from typing import Any, Dict, List

import numpy as np
import openpyxl
import pandas as pd
import pytest

from src.data_loader import (
    DataLoader,
    MissingColumnError,
    RawOrderDetailRecord,
    RawOrderRecord,
    RawSalesTargetRecord,
    normalize_column_name,
    parse_order_date,
    parse_target_date,
)


# ---------------------------------------------------------------------------
# Real Files Ingestion Tests (Workspace Root Datasets)
# ---------------------------------------------------------------------------

def test_load_orders_real_dataset() -> None:
    """Verifies successful loading of real List of Orders.xlsx."""
    orders_path = Path("data/input/List of Orders.xlsx")
    assert orders_path.exists(), "List of Orders.xlsx must exist in data/input"

    df = DataLoader.load_orders(orders_path)

    # 1. Row count and columns
    assert len(df) == 500, f"Expected 500 orders, got {len(df)}"
    expected_cols = ["order_id", "order_date", "customer_name", "state", "city"]
    assert list(df.columns) == expected_cols

    # 2. Type integrity
    assert pd.api.types.is_datetime64_any_dtype(df["order_date"])
    assert pd.api.types.is_object_dtype(df["order_id"])
    assert pd.api.types.is_object_dtype(df["customer_name"])
    assert pd.api.types.is_object_dtype(df["state"])
    assert pd.api.types.is_object_dtype(df["city"])

    # 3. No null values
    assert df.isnull().sum().sum() == 0

    # 4. Chronological date range: 2018-04-01 to 2019-03-31
    assert df["order_date"].min() == pd.Timestamp("2018-04-01")
    assert df["order_date"].max() == pd.Timestamp("2019-03-31")


def test_load_order_details_real_dataset() -> None:
    """Verifies successful loading of real Order Details.xlsx."""
    details_path = Path("data/input/Order Details.xlsx")
    assert details_path.exists(), "Order Details.xlsx must exist in data/input"

    df = DataLoader.load_order_details(details_path)

    # 1. Row count and columns
    assert len(df) == 1500, f"Expected 1500 line items, got {len(df)}"
    expected_cols = [
        "order_id",
        "amount",
        "profit",
        "quantity",
        "category",
        "sub_category",
    ]
    assert list(df.columns) == expected_cols

    # 2. Numeric typing
    assert pd.api.types.is_float_dtype(df["amount"])
    assert pd.api.types.is_float_dtype(df["profit"])
    assert pd.api.types.is_integer_dtype(df["quantity"])

    # 3. Negative profit preservation (AC-E2)
    assert df["profit"].min() < 0, "Negative profits must be preserved"
    assert df["profit"].min() == -1981.0

    # 4. Valid categories
    assert set(df["category"].unique()) == {"Clothing", "Electronics", "Furniture"}
    assert df["quantity"].min() >= 1


def test_load_sales_targets_real_dataset() -> None:
    """Verifies successful loading of real Sales target.xlsx."""
    targets_path = Path("data/input/Sales target.xlsx")
    assert targets_path.exists(), "Sales target.xlsx must exist in data/input"

    df = DataLoader.load_sales_targets(targets_path)

    # 1. Row count and columns
    assert len(df) == 36, f"Expected 36 monthly targets (12 x 3), got {len(df)}"
    expected_cols = ["month_of_order_date", "category", "target"]
    assert list(df.columns) == expected_cols

    # 2. Types
    assert pd.api.types.is_datetime64_any_dtype(df["month_of_order_date"])
    assert pd.api.types.is_float_dtype(df["target"])

    # 3. Date range: exactly 12 calendar months (2018-04 to 2019-03)
    unique_months = sorted(df["month_of_order_date"].unique())
    assert len(unique_months) == 12
    assert unique_months[0] == pd.Timestamp("2018-04-01")
    assert unique_months[-1] == pd.Timestamp("2019-03-01")

    # 4. Targets strictly positive
    assert (df["target"] > 0).all()


# ---------------------------------------------------------------------------
# Synthetic & Mock Directory Ingestion Tests
# ---------------------------------------------------------------------------

def test_load_orders_from_mock_dir(mock_excel_dir: Path, sample_orders_df: pd.DataFrame) -> None:
    """Tests DataLoader.load_orders with synthetic fixture workbook."""
    orders_file = mock_excel_dir / "List of Orders.xlsx"
    loaded_df = DataLoader.load_orders(orders_file)

    assert len(loaded_df) == len(sample_orders_df)
    assert list(loaded_df.columns) == list(sample_orders_df.columns)
    assert loaded_df["order_id"].tolist() == sample_orders_df["order_id"].tolist()
    assert (loaded_df["order_date"] == sample_orders_df["order_date"]).all()


def test_load_order_details_from_mock_dir(
    mock_excel_dir: Path,
    sample_order_details_df: pd.DataFrame,
) -> None:
    """Tests DataLoader.load_order_details with synthetic fixture workbook."""
    details_file = mock_excel_dir / "Order Details.xlsx"
    loaded_df = DataLoader.load_order_details(details_file)

    assert len(loaded_df) == len(sample_order_details_df)
    assert list(loaded_df.columns) == list(sample_order_details_df.columns)
    np.testing.assert_allclose(loaded_df["amount"], sample_order_details_df["amount"])
    np.testing.assert_allclose(loaded_df["profit"], sample_order_details_df["profit"])
    assert (loaded_df["quantity"] == sample_order_details_df["quantity"]).all()


def test_load_sales_targets_from_mock_dir(
    mock_excel_dir: Path,
    sample_sales_targets_df: pd.DataFrame,
) -> None:
    """Tests DataLoader.load_sales_targets with synthetic fixture workbook."""
    targets_file = mock_excel_dir / "Sales target.xlsx"
    loaded_df = DataLoader.load_sales_targets(targets_file)

    assert len(loaded_df) == len(sample_sales_targets_df)
    assert (loaded_df["month_of_order_date"] == sample_sales_targets_df["month_of_order_date"]).all()
    np.testing.assert_allclose(loaded_df["target"], sample_sales_targets_df["target"])


# ---------------------------------------------------------------------------
# Date Normalization & Edge Cases (AC-E1)
# ---------------------------------------------------------------------------

def test_parse_order_date_heterogeneous_formats() -> None:
    """Verifies that DD-MM-YYYY, YYYY-MM-DD, leap days, and datetimes parse accurately."""
    # 1. DD-MM-YYYY format
    assert parse_order_date("01-04-2018") == pd.Timestamp("2018-04-01")
    assert parse_order_date("15-05-2018") == pd.Timestamp("2018-05-15")
    assert parse_order_date("31-12-2018") == pd.Timestamp("2018-12-31")

    # 2. YYYY-MM-DD ISO format
    assert parse_order_date("2018-04-01") == pd.Timestamp("2018-04-01")
    assert parse_order_date("2018-04-01 00:00:00") == pd.Timestamp("2018-04-01")

    # 3. Leap day (29-02-2020)
    assert parse_order_date("29-02-2020") == pd.Timestamp("2020-02-29")

    # 4. Standard Python datetime object
    dt = datetime(2018, 12, 31, 10, 30)
    assert parse_order_date(dt) == pd.Timestamp("2018-12-31 10:30:00")


def test_parse_order_date_excel_serial_number() -> None:
    """Verifies numeric Excel serial date parsing."""
    # 43104.0 is 2018-01-04 in Excel's 1900 date system
    assert parse_order_date(43104.0) == pd.Timestamp("2018-01-04")
    assert parse_order_date(43104) == pd.Timestamp("2018-01-04")


def test_parse_order_date_swapped_mm_dd_yyyy_format() -> None:
    """Verifies Excel cell with mm-dd-yyyy format recovers swapped month and day."""
    # datetime(2018, 1, 4) with mm-dd-yyyy formatting represents 01-04-2018 (April 1st)
    raw_val = datetime(2018, 1, 4)
    res = parse_order_date(raw_val, number_format="mm-dd-yyyy")
    assert res == pd.Timestamp("2018-04-01")

    # When day > 12, it is not swapped
    raw_val_unswapped = datetime(2018, 12, 25)
    res_unswapped = parse_order_date(raw_val_unswapped, number_format="mm-dd-yyyy")
    assert res_unswapped == pd.Timestamp("2018-12-25")


def test_parse_order_date_invalid_values() -> None:
    """Verifies descriptive ValueError on invalid, null, or blank order dates."""
    with pytest.raises(ValueError, match="cannot be empty or null"):
        parse_order_date(None)

    with pytest.raises(ValueError, match="cannot be empty or null"):
        parse_order_date(pd.NaT)

    with pytest.raises(ValueError, match="cannot be blank or whitespace"):
        parse_order_date("   ")

    with pytest.raises(ValueError, match="Failed to parse date string"):
        parse_order_date("invalid-non-date-string")


def test_parse_target_date_formats() -> None:
    """Verifies parsing of diverse target month representations."""
    # 1. 'Apr-18' string
    assert parse_target_date("Apr-18") == pd.Timestamp("2018-04-01")
    assert parse_target_date("Jan-19") == pd.Timestamp("2019-01-01")

    # 2. ISO date string
    assert parse_target_date("2018-04-01") == pd.Timestamp("2018-04-01")
    assert parse_target_date("2019-03-01") == pd.Timestamp("2019-03-01")

    # 3. Excel artifact datetime (e.g. 2026-04-18 for Apr-18)
    artifact_dt_18 = datetime(2026, 4, 18)
    assert parse_target_date(artifact_dt_18) == pd.Timestamp("2018-04-01")

    artifact_dt_19 = datetime(2026, 1, 19)
    assert parse_target_date(artifact_dt_19) == pd.Timestamp("2019-01-01")


def test_parse_target_date_invalid_values() -> None:
    """Verifies descriptive ValueError on invalid target dates."""
    with pytest.raises(ValueError, match="cannot be empty or null"):
        parse_target_date(None)

    with pytest.raises(ValueError, match="cannot be blank or whitespace"):
        parse_target_date("   ")

    with pytest.raises(ValueError, match="Failed to parse target date string"):
        parse_target_date("invalid-target-month")


# ---------------------------------------------------------------------------
# Column Name Normalization Tests
# ---------------------------------------------------------------------------

def test_normalize_column_name() -> None:
    """Verifies conversion of raw column headers to lowercase snake_case."""
    assert normalize_column_name("Order ID") == "order_id"
    assert normalize_column_name("Order Date") == "order_date"
    assert normalize_column_name("CustomerName") == "customer_name"
    assert normalize_column_name("Sub-Category") == "sub_category"
    assert normalize_column_name("Month of Order Date") == "month_of_order_date"
    assert normalize_column_name(" Target ") == "target"
    assert normalize_column_name("Total_Amount") == "total_amount"


# ---------------------------------------------------------------------------
# Missing & Corrupt Files / Columns Tests (AC-E4)
# ---------------------------------------------------------------------------

def test_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    """Verifies FileNotFoundError when attempting to load non-existent files."""
    missing_file = tmp_path / "NonExistentFile.xlsx"

    with pytest.raises(FileNotFoundError):
        DataLoader.load_orders(missing_file)

    with pytest.raises(FileNotFoundError):
        DataLoader.load_order_details(missing_file)

    with pytest.raises(FileNotFoundError):
        DataLoader.load_sales_targets(missing_file)


def test_empty_file_raises_value_error(tmp_path: Path) -> None:
    """Verifies ValueError when input file is 0 bytes."""
    empty_file = tmp_path / "empty.xlsx"
    empty_file.write_bytes(b"")

    with pytest.raises(ValueError, match="empty"):
        DataLoader.load_orders(empty_file)

    with pytest.raises(ValueError, match="empty"):
        DataLoader.load_order_details(empty_file)

    with pytest.raises(ValueError, match="empty"):
        DataLoader.load_sales_targets(empty_file)


def test_missing_mandatory_columns_orders(tmp_path: Path) -> None:
    """Verifies MissingColumnError when mandatory columns are absent in orders."""
    bad_orders_path = tmp_path / "BadOrders.xlsx"
    df = pd.DataFrame({
        "Order ID": ["B-101"],
        # Missing 'Order Date', 'CustomerName', 'State', 'City'
    })
    df.to_excel(bad_orders_path, index=False)

    with pytest.raises((KeyError, ValueError, MissingColumnError)):
        DataLoader.load_orders(bad_orders_path)


def test_missing_mandatory_columns_details(tmp_path: Path) -> None:
    """Verifies MissingColumnError when mandatory columns are absent in order details."""
    bad_details_path = tmp_path / "BadDetails.xlsx"
    df = pd.DataFrame({
        "Order ID": ["B-101"],
        "Amount": [100.0],
        # Missing 'Profit', 'Quantity', 'Category', 'Sub-Category'
    })
    df.to_excel(bad_details_path, index=False)

    with pytest.raises((KeyError, ValueError, MissingColumnError)):
        DataLoader.load_order_details(bad_details_path)


def test_missing_mandatory_columns_targets(tmp_path: Path) -> None:
    """Verifies MissingColumnError when mandatory columns are absent in targets."""
    bad_targets_path = tmp_path / "BadTargets.xlsx"
    df = pd.DataFrame({
        "Month of Order Date": ["2018-04-01"],
        # Missing 'Category', 'Target'
    })
    df.to_excel(bad_targets_path, index=False)

    with pytest.raises((KeyError, ValueError, MissingColumnError)):
        DataLoader.load_sales_targets(bad_targets_path)


def test_invalid_numeric_values_raise_value_error(tmp_path: Path) -> None:
    """Verifies ValueError when numeric fields contain non-numeric corrupt values."""
    corrupt_details_path = tmp_path / "CorruptDetails.xlsx"
    df = pd.DataFrame({
        "Order ID": ["B-101"],
        "Amount": ["NotANumber"],
        "Profit": [10.0],
        "Quantity": [1],
        "Category": ["Clothing"],
        "Sub-Category": ["Saree"],
    })
    df.to_excel(corrupt_details_path, index=False)

    with pytest.raises(ValueError):
        DataLoader.load_order_details(corrupt_details_path)


# ---------------------------------------------------------------------------
# Dataclass Model Validation Tests
# ---------------------------------------------------------------------------

def test_raw_order_record_validation() -> None:
    """Verifies RawOrderRecord constraints."""
    valid_dt = datetime(2018, 4, 1)

    # Valid instantiation
    rec = RawOrderRecord("B-101", valid_dt, "Alice", "Gujarat", "Surat")
    assert rec.order_id == "B-101"

    # Blank order_id
    with pytest.raises(ValueError, match="order_id cannot be blank"):
        RawOrderRecord("", valid_dt, "Alice", "Gujarat", "Surat")

    # Non-datetime order_date
    with pytest.raises(TypeError, match="order_date must be datetime"):
        RawOrderRecord("B-101", "2018-04-01", "Alice", "Gujarat", "Surat")  # type: ignore

    # Blank state
    with pytest.raises(ValueError, match="state cannot be blank"):
        RawOrderRecord("B-101", valid_dt, "Alice", "", "Surat")


def test_raw_order_detail_record_validation() -> None:
    """Verifies RawOrderDetailRecord constraints."""
    # Valid instantiation
    rec = RawOrderDetailRecord("B-101", 100.0, -20.0, 2, "Furniture", "Chairs")
    assert rec.profit == -20.0  # Preserves negative profit

    # Blank order_id
    with pytest.raises(ValueError, match="order_id cannot be blank"):
        RawOrderDetailRecord("", 100.0, 10.0, 1, "Furniture", "Chairs")

    # Negative amount
    with pytest.raises(ValueError, match="amount cannot be negative"):
        RawOrderDetailRecord("B-101", -50.0, 10.0, 1, "Furniture", "Chairs")

    # Quantity < 1
    with pytest.raises(ValueError, match="quantity must be >= 1"):
        RawOrderDetailRecord("B-101", 100.0, 10.0, 0, "Furniture", "Chairs")

    # Unrecognized category
    with pytest.raises(ValueError, match="Unrecognized category"):
        RawOrderDetailRecord("B-101", 100.0, 10.0, 1, "Automotive", "Chairs")


def test_raw_sales_target_record_validation() -> None:
    """Verifies RawSalesTargetRecord constraints."""
    # Valid instantiation
    rec = RawSalesTargetRecord("2018-04-01", "Furniture", 10000.0)
    assert rec.target == 10000.0

    # Blank month_of_order_date
    with pytest.raises(ValueError, match="month_of_order_date cannot be blank"):
        RawSalesTargetRecord("", "Furniture", 10000.0)

    # Non-positive target
    with pytest.raises(ValueError, match="target must be strictly positive"):
        RawSalesTargetRecord("2018-04-01", "Furniture", 0.0)

    with pytest.raises(ValueError, match="target must be strictly positive"):
        RawSalesTargetRecord("2018-04-01", "Furniture", -500.0)

    # Unrecognized category
    with pytest.raises(ValueError, match="Unrecognized category"):
        RawSalesTargetRecord("2018-04-01", "Books", 1000.0)


# ---------------------------------------------------------------------------
# Convenience Methods Tests (DataLoader.load_all)
# ---------------------------------------------------------------------------

def test_load_all_convenience() -> None:
    """Verifies DataLoader.load_all loads all three real workbooks in tandem."""
    orders_df, details_df, targets_df = DataLoader.load_all("data/input")

    assert len(orders_df) == 500
    assert len(details_df) == 1500
    assert len(targets_df) == 36
