"""Shared pytest fixtures and synthetic datasets for GrowthInternJar tests.

Provides deterministic test fixtures matching the schema of:
- List of Orders.xlsx
- Order Details.xlsx
- Sales target.xlsx
Including raw column naming, normalized schemas, edge cases (negative profits,
mixed date representations), and mock Excel directory generators.
"""

from datetime import datetime
import os
from pathlib import Path
import tempfile
from typing import Any, Dict, List
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Pytest Runtime Configuration & Environment Hardening
# ---------------------------------------------------------------------------

def pytest_configure(config: pytest.Config) -> None:
    """Safeguards basetemp against Windows PermissionError on locked temp dirs."""
    if config.option.basetemp is None:
        safe_temp = Path(tempfile.gettempdir()) / f"pytest_run_{os.getpid()}"
        safe_temp.mkdir(parents=True, exist_ok=True)
        config.option.basetemp = str(safe_temp)


# ---------------------------------------------------------------------------
# Raw Synthetic Record Fixtures (Excel Pre-normalization Structure)
# ---------------------------------------------------------------------------

@pytest.fixture
def raw_orders_records() -> List[Dict[str, Any]]:
    """Synthetic raw records matching raw 'List of Orders.xlsx' schema."""
    return [
        {
            "Order ID": "B-25601",
            "Order Date": "2018-04-01 00:00:00",
            "CustomerName": "Bharat",
            "State": "Gujarat",
            "City": "Ahmedabad",
        },
        {
            "Order ID": "B-25602",
            "Order Date": "2018-04-01 00:00:00",
            "CustomerName": "Pearl",
            "State": "Maharashtra",
            "City": "Pune",
        },
        {
            "Order ID": "B-25603",
            "Order Date": "2018-05-15 00:00:00",
            "CustomerName": "Jiten",
            "State": "Madhya Pradesh",
            "City": "Bhopal",
        },
        {
            "Order ID": "B-25604",
            "Order Date": "2018-06-20 00:00:00",
            "CustomerName": "Harivansh",
            "State": "Uttar Pradesh",
            "City": "Lucknow",
        },
        {
            "Order ID": "B-25605",
            "Order Date": "2018-07-10 00:00:00",
            "CustomerName": "Mudit",
            "State": "Delhi",
            "City": "Delhi",
        },
        {
            "Order ID": "B-25606",
            "Order Date": "2018-08-25 00:00:00",
            "CustomerName": "Rekha",
            "State": "Maharashtra",
            "City": "Mumbai",
        },
    ]


@pytest.fixture
def raw_order_details_records() -> List[Dict[str, Any]]:
    """Synthetic raw records matching raw 'Order Details.xlsx' schema.

    Includes multi-line orders, loss leaders (negative profit),
    and all 3 standard categories: Furniture, Clothing, Electronics.
    """
    return [
        {
            "Order ID": "B-25601",
            "Amount": 1275.0,
            "Profit": -1148.0,
            "Quantity": 7,
            "Category": "Furniture",
            "Sub-Category": "Bookcases",
        },
        {
            "Order ID": "B-25601",
            "Amount": 66.0,
            "Profit": -12.0,
            "Quantity": 5,
            "Category": "Clothing",
            "Sub-Category": "Stole",
        },
        {
            "Order ID": "B-25602",
            "Amount": 2500.0,
            "Profit": 600.0,
            "Quantity": 2,
            "Category": "Electronics",
            "Sub-Category": "Phones",
        },
        {
            "Order ID": "B-25603",
            "Amount": 800.0,
            "Profit": 160.0,
            "Quantity": 4,
            "Category": "Clothing",
            "Sub-Category": "Saree",
        },
        {
            "Order ID": "B-25604",
            "Amount": 3200.0,
            "Profit": 480.0,
            "Quantity": 3,
            "Category": "Furniture",
            "Sub-Category": "Chairs",
        },
        {
            "Order ID": "B-25605",
            "Amount": 1500.0,
            "Profit": 300.0,
            "Quantity": 1,
            "Category": "Electronics",
            "Sub-Category": "Accessories",
        },
        {
            "Order ID": "B-25606",
            "Amount": 450.0,
            "Profit": 90.0,
            "Quantity": 2,
            "Category": "Clothing",
            "Sub-Category": "T-shirt",
        },
    ]


@pytest.fixture
def raw_sales_targets_records() -> List[Dict[str, Any]]:
    """Synthetic raw records matching raw 'Sales target.xlsx' schema."""
    return [
        {"Month of Order Date": "2018-04-01", "Category": "Furniture", "Target": 10000.0},
        {"Month of Order Date": "2018-05-01", "Category": "Furniture", "Target": 12000.0},
        {"Month of Order Date": "2018-06-01", "Category": "Furniture", "Target": 9000.0},
        {"Month of Order Date": "2018-04-01", "Category": "Clothing", "Target": 15000.0},
        {"Month of Order Date": "2018-05-01", "Category": "Clothing", "Target": 16000.0},
        {"Month of Order Date": "2018-04-01", "Category": "Electronics", "Target": 18000.0},
    ]


# ---------------------------------------------------------------------------
# Raw DataFrames Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_raw_orders_df(raw_orders_records: List[Dict[str, Any]]) -> pd.DataFrame:
    """DataFrame with raw unnormalized column names for orders."""
    return pd.DataFrame(raw_orders_records)


@pytest.fixture
def sample_raw_order_details_df(raw_order_details_records: List[Dict[str, Any]]) -> pd.DataFrame:
    """DataFrame with raw unnormalized column names for order details."""
    return pd.DataFrame(raw_order_details_records)


@pytest.fixture
def sample_raw_sales_targets_df(raw_sales_targets_records: List[Dict[str, Any]]) -> pd.DataFrame:
    """DataFrame with raw unnormalized column names for sales targets."""
    return pd.DataFrame(raw_sales_targets_records)


# ---------------------------------------------------------------------------
# Normalized DataFrames Fixtures (Post-DataLoader Schema)
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_orders_df() -> pd.DataFrame:
    """Normalized orders DataFrame adhering to DataLoader output contract."""
    return pd.DataFrame({
        "order_id": ["B-25601", "B-25602", "B-25603", "B-25604", "B-25605", "B-25606"],
        "order_date": pd.to_datetime([
            "2018-04-01",
            "2018-04-01",
            "2018-05-15",
            "2018-06-20",
            "2018-07-10",
            "2018-08-25",
        ]),
        "customer_name": ["Bharat", "Pearl", "Jiten", "Harivansh", "Mudit", "Rekha"],
        "state": ["Gujarat", "Maharashtra", "Madhya Pradesh", "Uttar Pradesh", "Delhi", "Maharashtra"],
        "city": ["Ahmedabad", "Pune", "Bhopal", "Lucknow", "Delhi", "Mumbai"],
    })


@pytest.fixture
def sample_order_details_df() -> pd.DataFrame:
    """Normalized order details DataFrame adhering to DataLoader output contract."""
    return pd.DataFrame({
        "order_id": ["B-25601", "B-25601", "B-25602", "B-25603", "B-25604", "B-25605", "B-25606"],
        "amount": [1275.0, 66.0, 2500.0, 800.0, 3200.0, 1500.0, 450.0],
        "profit": [-1148.0, -12.0, 600.0, 160.0, 480.0, 300.0, 90.0],
        "quantity": [7, 5, 2, 4, 3, 1, 2],
        "category": [
            "Furniture",
            "Clothing",
            "Electronics",
            "Clothing",
            "Furniture",
            "Electronics",
            "Clothing",
        ],
        "sub_category": [
            "Bookcases",
            "Stole",
            "Phones",
            "Saree",
            "Chairs",
            "Accessories",
            "T-shirt",
        ],
    })


@pytest.fixture
def sample_sales_targets_df() -> pd.DataFrame:
    """Normalized sales targets DataFrame adhering to DataLoader output contract."""
    return pd.DataFrame({
        "month_of_order_date": pd.to_datetime([
            "2018-04-01",
            "2018-05-01",
            "2018-06-01",
            "2018-04-01",
            "2018-05-01",
            "2018-04-01",
        ]),
        "category": ["Furniture", "Furniture", "Furniture", "Clothing", "Clothing", "Electronics"],
        "target": [10000.0, 12000.0, 9000.0, 15000.0, 16000.0, 18000.0],
    })


@pytest.fixture
def sample_merged_df(sample_orders_df: pd.DataFrame, sample_order_details_df: pd.DataFrame) -> pd.DataFrame:
    """Merged transaction line items via inner join on order_id."""
    return pd.merge(sample_orders_df, sample_order_details_df, on="order_id", how="inner")


# ---------------------------------------------------------------------------
# Furniture Chronological MoM Sequence Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_furniture_targets_chronological() -> pd.DataFrame:
    """12 consecutive months of Furniture targets (Apr-18 to Mar-19).

    Contains explicit percentage swings to test MoM calculation and
    significant fluctuation flags (|MoM| >= 15.0%).
    - Apr-18: 10,000 (Baseline -> MoM is NaN/None)
    - May-18: 12,000 (+20.0% -> Flagged)
    - Jun-18: 12,500 (+4.17% -> Not Flagged)
    - Jul-18: 10,000 (-20.0% -> Flagged)
    - Aug-18: 11,500 (+15.0% -> Flagged)
    - Sep-18: 11,500 (0.0% -> Not Flagged)
    - Oct-18: 13,500 (+17.39% -> Flagged)
    - Nov-18: 13,000 (-3.70% -> Not Flagged)
    - Dec-18: 15,000 (+15.38% -> Flagged)
    - Jan-19: 15,200 (+1.33% -> Not Flagged)
    - Feb-19: 12,000 (-21.05% -> Flagged)
    - Mar-19: 14,000 (+16.67% -> Flagged)
    """
    months = [
        "2018-04-01", "2018-05-01", "2018-06-01", "2018-07-01",
        "2018-08-01", "2018-09-01", "2018-10-01", "2018-11-01",
        "2018-12-01", "2019-01-01", "2019-02-01", "2019-03-01",
    ]
    targets = [
        10000.0, 12000.0, 12500.0, 10000.0,
        11500.0, 11500.0, 13500.0, 13000.0,
        15000.0, 15200.0, 12000.0, 14000.0,
    ]
    return pd.DataFrame({
        "month_of_order_date": pd.to_datetime(months),
        "category": ["Furniture"] * 12,
        "target": targets,
    })


# ---------------------------------------------------------------------------
# Edge Case Datasets Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_mixed_dates_records() -> List[Dict[str, Any]]:
    """Records with heterogeneous date formats to test parser robustness."""
    return [
        {"Order ID": "E-001", "Order Date": "01-04-2018", "CustomerName": "Alice", "State": "Goa", "City": "Panaji"},
        {"Order ID": "E-002", "Order Date": "2018-05-15", "CustomerName": "Bob", "State": "Kerala", "City": "Kochi"},
        {"Order ID": "E-003", "Order Date": "29-02-2020", "CustomerName": "Charlie", "State": "Assam", "City": "Guwahati"},
        {"Order ID": "E-004", "Order Date": datetime(2018, 12, 31), "CustomerName": "Diana", "State": "Punjab", "City": "Amritsar"},
    ]


@pytest.fixture
def sample_loss_leader_details_df() -> pd.DataFrame:
    """Line items with deep negative profits to verify margin math preserves losses."""
    return pd.DataFrame({
        "order_id": ["L-101", "L-102", "L-103"],
        "amount": [5000.0, 2000.0, 3000.0],
        "profit": [-3000.0, -1500.0, 500.0],
        "quantity": [2, 1, 3],
        "category": ["Furniture", "Furniture", "Furniture"],
        "sub_category": ["Tables", "Chairs", "Furnishings"],
    })


# ---------------------------------------------------------------------------
# Mock Filesystem Fixture for DataLoader Ingestion Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_excel_dir(
    tmp_path: Path,
    sample_raw_orders_df: pd.DataFrame,
    sample_raw_order_details_df: pd.DataFrame,
    sample_raw_sales_targets_df: pd.DataFrame,
) -> Path:
    """Creates temporary directory containing mock Excel workbooks.

    Saves:
    - List of Orders.xlsx
    - Order Details.xlsx
    - Sales target.xlsx
    """
    orders_path = tmp_path / "List of Orders.xlsx"
    details_path = tmp_path / "Order Details.xlsx"
    targets_path = tmp_path / "Sales target.xlsx"

    sample_raw_orders_df.to_excel(orders_path, index=False)
    sample_raw_order_details_df.to_excel(details_path, index=False)
    sample_raw_sales_targets_df.to_excel(targets_path, index=False)

    return tmp_path
