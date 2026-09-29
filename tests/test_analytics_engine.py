"""Unit tests for AnalyticsEngine: order merging, category performance, and target reconciliation.

Validates:
- SPEC AC-1.2: Order dataset merging (inner join semantics, cardinality, column alignment)
- SPEC AC-1.3: Category sales, profitability, order-level average profit, margin % and ranking
- SPEC AC-1.4, AC-E3: Furniture target MoM fluctuations, chronological sorting, variance & reconciliation
- SPEC AC-E2: Negative profit line-item preservation (loss leaders)
- SPEC AC-E5: Zero-division safety in profit margin % calculation
- SPEC AC-E6: Unmatched order IDs audit and handling
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd
import pytest

from src.analytics_engine import (
    AnalyticsEngine,
    CategoryPerformance,
    CityPerformance,
    FurnitureTargetAchievement,
    StatePerformance,
)
from src.data_loader import DataLoader


# ---------------------------------------------------------------------------
# Order Dataset Merging Tests (AC-1.2, AC-E6)
# ---------------------------------------------------------------------------

def test_merge_orders_real_dataset() -> None:
    """Verifies merging real List of Orders and Order Details workbooks."""
    orders_df = DataLoader.load_orders("data/input/List of Orders.xlsx")
    details_df = DataLoader.load_order_details("data/input/Order Details.xlsx")

    merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)

    # 1. Cardinality: exactly 1500 line items across 500 distinct orders
    assert len(merged_df) == 1500, f"Expected 1500 line items, got {len(merged_df)}"
    assert merged_df["order_id"].nunique() == 500, f"Expected 500 distinct orders, got {merged_df['order_id'].nunique()}"

    # 2. Output columns verification
    expected_cols = [
        "order_id",
        "order_date",
        "customer_name",
        "state",
        "city",
        "amount",
        "profit",
        "quantity",
        "category",
        "sub_category",
    ]
    assert list(merged_df.columns) == expected_cols

    # 3. Numeric & datetime type consistency
    assert pd.api.types.is_datetime64_any_dtype(merged_df["order_date"])
    assert pd.api.types.is_float_dtype(merged_df["amount"])
    assert pd.api.types.is_float_dtype(merged_df["profit"])
    assert pd.api.types.is_integer_dtype(merged_df["quantity"])

    # 4. AC-E2: Preserves negative profit values
    assert (merged_df["profit"] < 0).any(), "Merged transactions must retain negative profits"
    assert merged_df["profit"].min() == -1981.0


def test_merge_orders_inner_join_semantics_and_cardinality() -> None:
    """Tests inner join semantics when order IDs exist in only one of the datasets (AC-E6)."""
    orders_df = pd.DataFrame({
        "order_id": ["O-101", "O-102", "O-103", "O-UNMATCHED"],
        "order_date": pd.to_datetime(["2018-04-01", "2018-04-02", "2018-04-03", "2018-04-04"]),
        "customer_name": ["Alice", "Bob", "Charlie", "David"],
        "state": ["Gujarat", "Maharashtra", "Delhi", "Punjab"],
        "city": ["Surat", "Mumbai", "Delhi", "Amritsar"],
    })

    details_df = pd.DataFrame({
        "order_id": ["O-101", "O-101", "O-102", "O-ORPHAN"],
        "amount": [100.0, 200.0, 500.0, 999.0],
        "profit": [20.0, 40.0, 100.0, 200.0],
        "quantity": [1, 2, 5, 10],
        "category": ["Clothing", "Clothing", "Electronics", "Furniture"],
        "sub_category": ["Saree", "Stole", "Phones", "Chairs"],
    })

    merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)

    # Only O-101 (2 lines) and O-102 (1 line) should match -> exactly 3 lines
    assert len(merged_df) == 3
    assert set(merged_df["order_id"].unique()) == {"O-101", "O-102"}
    assert "O-UNMATCHED" not in merged_df["order_id"].values
    assert "O-ORPHAN" not in merged_df["order_id"].values

    # Check that O-101 inherited customer info on both lines
    o101_lines = merged_df[merged_df["order_id"] == "O-101"]
    assert len(o101_lines) == 2
    assert (o101_lines["customer_name"] == "Alice").all()
    assert (o101_lines["state"] == "Gujarat").all()


def test_merge_orders_empty_inputs_handling() -> None:
    """Verifies graceful handling when one or both inputs are empty."""
    empty_orders = pd.DataFrame(columns=["order_id", "order_date", "customer_name", "state", "city"])
    empty_details = pd.DataFrame(columns=["order_id", "amount", "profit", "quantity", "category", "sub_category"])

    # Both empty
    merged_empty = AnalyticsEngine.merge_orders(empty_orders, empty_details)
    assert len(merged_empty) == 0
    assert "order_id" in merged_empty.columns

    # One empty
    valid_orders = pd.DataFrame({
        "order_id": ["O-1"],
        "order_date": pd.to_datetime(["2018-04-01"]),
        "customer_name": ["Alice"],
        "state": ["Goa"],
        "city": ["Panaji"],
    })
    merged_one_empty = AnalyticsEngine.merge_orders(valid_orders, empty_details)
    assert len(merged_one_empty) == 0


def test_merge_orders_validation_errors() -> None:
    """Verifies type and schema validation in merge_orders."""
    # Non-dataframe
    with pytest.raises(TypeError, match="orders_df must be pd.DataFrame"):
        AnalyticsEngine.merge_orders("not_a_df", pd.DataFrame())  # type: ignore

    with pytest.raises(TypeError, match="details_df must be pd.DataFrame"):
        AnalyticsEngine.merge_orders(pd.DataFrame(), "not_a_df")  # type: ignore

    # Missing mandatory column in orders_df
    bad_orders = pd.DataFrame({"order_id": ["O-1"], "state": ["Goa"]})
    valid_details = pd.DataFrame({
        "order_id": ["O-1"],
        "amount": [10.0],
        "profit": [2.0],
        "quantity": [1],
        "category": ["Clothing"],
        "sub_category": ["Saree"],
    })
    with pytest.raises(ValueError, match="orders_df is missing mandatory columns"):
        AnalyticsEngine.merge_orders(bad_orders, valid_details)

    # Missing mandatory column in details_df
    valid_orders = pd.DataFrame({
        "order_id": ["O-1"],
        "order_date": pd.to_datetime(["2018-04-01"]),
        "customer_name": ["Alice"],
        "state": ["Goa"],
        "city": ["Panaji"],
    })
    bad_details = pd.DataFrame({"order_id": ["O-1"], "amount": [100.0]})
    with pytest.raises(ValueError, match="details_df is missing mandatory columns"):
        AnalyticsEngine.merge_orders(valid_orders, bad_details)


# ---------------------------------------------------------------------------
# Category Sales & Profitability Analysis Tests (AC-1.3, AC-E2, AC-E5)
# ---------------------------------------------------------------------------

def test_category_performance() -> None:
    """SPEC AC-1.2, AC-1.3, AC-E2, AC-E5, AC-E6 verification on the real assignment dataset.

    Checks:
    - Inner join cardinality: 1500 lines across 500 distinct orders.
    - Category aggregation metrics (total sales, total profit, distinct orders, total quantity).
    - Order-level average profit grouped by (order_id, category).
    - Profit margin % with zero-division safety.
    - Identification of top-performing, highest sales, and lowest/underperforming categories.
    """
    orders_df = DataLoader.load_orders("data/input/List of Orders.xlsx")
    details_df = DataLoader.load_order_details("data/input/Order Details.xlsx")

    # 1. Inner join cardinality verification
    merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)
    assert len(merged_df) == 1500
    assert merged_df["order_id"].nunique() == 500

    # 2. Compute category performance
    results = AnalyticsEngine.compute_category_performance(merged_df)

    assert len(results) == 3, f"Expected 3 categories, got {len(results)}"
    res_by_cat: Dict[str, CategoryPerformance] = {r.category: r for r in results}

    # 3. Verify Clothing category metrics
    clothing = res_by_cat["Clothing"]
    assert clothing.total_sales == 139054.00
    assert clothing.total_profit == 11163.00
    assert clothing.distinct_orders == 393
    assert clothing.total_quantity == 3516
    assert clothing.avg_profit_per_order == 28.40  # 11,163 / 393 = 28.4046
    assert clothing.profit_margin_pct == 8.03      # (11,163 / 139,054) * 100 = 8.0278%
    assert clothing.performance_rank == 1

    # 4. Verify Electronics category metrics
    electronics = res_by_cat["Electronics"]
    assert electronics.total_sales == 165267.00
    assert electronics.total_profit == 10494.00
    assert electronics.distinct_orders == 204
    assert electronics.total_quantity == 1154
    assert electronics.avg_profit_per_order == 51.44  # 10,494 / 204 = 51.4412
    assert electronics.profit_margin_pct == 6.35      # (10,494 / 165,267) * 100 = 6.3497%
    assert electronics.performance_rank == 2

    # 5. Verify Furniture category metrics (preserves negative profit loss-leaders)
    furniture = res_by_cat["Furniture"]
    assert furniture.total_sales == 127181.00
    assert furniture.total_profit == 2298.00
    assert furniture.distinct_orders == 186
    assert furniture.total_quantity == 945
    assert furniture.avg_profit_per_order == 12.35  # 2,298 / 186 = 12.3548
    assert furniture.profit_margin_pct == 1.81      # (2,298 / 127,181) * 100 = 1.8069%
    assert furniture.performance_rank == 3

    # 6. Verify rankings order in returned list: sorted by rank 1, 2, 3
    assert [r.category for r in results] == ["Clothing", "Electronics", "Furniture"]
    assert [r.performance_rank for r in results] == [1, 2, 3]

    # 7. SPEC AC-1.3 Item 5: Identify highest sales, highest margin, and lowest underperforming
    highest_sales = AnalyticsEngine.get_highest_sales_category(results)
    assert highest_sales.category == "Electronics"
    assert highest_sales.total_sales == 165267.00

    highest_margin = AnalyticsEngine.get_highest_margin_category(results)
    assert highest_margin.category == "Clothing"
    assert highest_margin.profit_margin_pct == 8.03

    lowest_margin = AnalyticsEngine.get_lowest_margin_category(results)
    assert lowest_margin.category == "Furniture"
    assert lowest_margin.profit_margin_pct == 1.81

    highest_profit = AnalyticsEngine.get_highest_profit_category(results)
    assert highest_profit.category == "Clothing"
    assert highest_profit.total_profit == 11163.00


def test_order_level_category_average_profit_math() -> None:
    """Verifies ADR-004 logic: grouping by (order_id, category) before averaging across orders."""
    # Synthetic transactions with multi-item orders
    test_df = pd.DataFrame({
        "order_id": ["O-1", "O-1", "O-2", "O-3"],
        "category": ["Clothing", "Clothing", "Clothing", "Furniture"],
        "amount": [100.0, 150.0, 200.0, 500.0],
        "profit": [40.0, 60.0, 20.0, 150.0],
        "quantity": [1, 2, 1, 3],
    })

    results = AnalyticsEngine.compute_category_performance(test_df)
    res_map = {r.category: r for r in results}

    # For Clothing:
    # - Order O-1 total clothing profit = 40 + 60 = 100.0
    # - Order O-2 total clothing profit = 20.0
    # - Order O-3 has no clothing (must NOT dilute clothing's distinct order count)
    # Distinct orders containing Clothing = 2 (O-1 and O-2)
    # Average profit per distinct order = (100.0 + 20.0) / 2 = 60.0
    clothing = res_map["Clothing"]
    assert clothing.distinct_orders == 2
    assert clothing.total_sales == 450.0  # 100 + 150 + 200
    assert clothing.total_profit == 120.0  # 40 + 60 + 20
    assert clothing.avg_profit_per_order == 60.0
    assert clothing.profit_margin_pct == round((120.0 / 450.0) * 100, 2)  # 26.67%

    # Note: Row-level average would have been 120 / 3 = 40.0; dataset-wide order average would be 120 / 3 = 40.0.
    # ADR-004 order-level average across distinct orders ordering Clothing is exactly 60.0.
    assert clothing.avg_profit_per_order != 40.0


def test_category_performance_negative_profit_preservation(
    sample_loss_leader_details_df: pd.DataFrame,
) -> None:
    """SPEC AC-E2: Loss leaders with negative profit penalize total profit and margin."""
    # Loss leader dataset from conftest:
    # Amount: 5000, 2000, 3000 -> Total Sales = 10,000.0
    # Profit: -3000, -1500, 500 -> Total Profit = -4,000.0
    # Expected margin = (-4000 / 10000) * 100 = -40.0%
    results = AnalyticsEngine.compute_category_performance(sample_loss_leader_details_df)
    assert len(results) == 1

    furniture = results[0]
    assert furniture.category == "Furniture"
    assert furniture.total_sales == 10000.0
    assert furniture.total_profit == -4000.0
    assert furniture.profit_margin_pct == -40.0
    assert furniture.distinct_orders == 3
    assert furniture.avg_profit_per_order == round(-4000.0 / 3, 2)  # -1333.33


def test_category_performance_zero_division_safety() -> None:
    """SPEC AC-E5: Total sales == 0 must safely return 0.0 margin % without ZeroDivisionError."""
    zero_sales_df = pd.DataFrame({
        "order_id": ["O-FREE-1", "O-FREE-2"],
        "category": ["Clothing", "Clothing"],
        "amount": [0.0, 0.0],
        "profit": [0.0, 0.0],
        "quantity": [1, 1],
    })

    results = AnalyticsEngine.compute_category_performance(zero_sales_df)
    assert len(results) == 1
    clothing = results[0]
    assert clothing.total_sales == 0.0
    assert clothing.total_profit == 0.0
    assert clothing.profit_margin_pct == 0.0
    assert clothing.avg_profit_per_order == 0.0


def test_category_performance_empty_and_invalid_inputs() -> None:
    """Verifies edge case handling for empty or malformed inputs."""
    # Empty DataFrame returns empty list
    empty_df = pd.DataFrame(columns=["order_id", "category", "amount", "profit", "quantity"])
    assert AnalyticsEngine.compute_category_performance(empty_df) == []

    # Non-dataframe raises TypeError
    with pytest.raises(TypeError, match="merged_df must be pd.DataFrame"):
        AnalyticsEngine.compute_category_performance("invalid_input")  # type: ignore

    # Missing mandatory column raises ValueError
    bad_df = pd.DataFrame({
        "order_id": ["O-1"],
        "category": ["Clothing"],
        # Missing 'amount', 'profit', 'quantity'
    })
    with pytest.raises(ValueError, match="merged_df is missing mandatory columns"):
        AnalyticsEngine.compute_category_performance(bad_df)


def test_category_performance_all_nan_categories() -> None:
    """Verifies that merged DataFrame with all NaN categories gracefully returns empty list."""
    nan_cat_df = pd.DataFrame({
        "order_id": ["O-1", "O-2"],
        "category": [None, np.nan],
        "amount": [100.0, 200.0],
        "profit": [20.0, 40.0],
        "quantity": [1, 2],
    })
    results = AnalyticsEngine.compute_category_performance(nan_cat_df)
    assert results == []


# ---------------------------------------------------------------------------
# CategoryPerformance Dataclass Validation Tests
# ---------------------------------------------------------------------------

def test_category_performance_dataclass_validation() -> None:
    """Verifies CategoryPerformance invariant validation in __post_init__."""
    # Valid instantiation
    rec = CategoryPerformance(
        category="Electronics",
        total_sales=1000.0,
        total_profit=100.0,
        avg_profit_per_order=50.0,
        profit_margin_pct=10.0,
        distinct_orders=2,
        total_quantity=4,
        performance_rank=1,
    )
    assert rec.category == "Electronics"
    assert rec.to_dict()["profit_margin_pct"] == 10.0

    # Margin mismatch raises ValueError
    with pytest.raises(ValueError, match="Margin mismatch"):
        CategoryPerformance(
            category="Electronics",
            total_sales=1000.0,
            total_profit=100.0,
            avg_profit_per_order=50.0,
            profit_margin_pct=99.0,  # Deliberate mismatch
            distinct_orders=2,
            total_quantity=4,
            performance_rank=1,
        )

    # Blank category
    with pytest.raises(ValueError, match="category cannot be blank"):
        CategoryPerformance(
            category="",
            total_sales=1000.0,
            total_profit=100.0,
            avg_profit_per_order=50.0,
            profit_margin_pct=10.0,
            distinct_orders=2,
            total_quantity=4,
            performance_rank=1,
        )

    # Negative distinct_orders
    with pytest.raises(ValueError, match="distinct_orders cannot be negative"):
        CategoryPerformance(
            category="Clothing",
            total_sales=1000.0,
            total_profit=100.0,
            avg_profit_per_order=50.0,
            profit_margin_pct=10.0,
            distinct_orders=-1,
            total_quantity=4,
            performance_rank=1,
        )

    # Performance rank < 1
    with pytest.raises(ValueError, match="performance_rank must be >= 1"):
        CategoryPerformance(
            category="Clothing",
            total_sales=1000.0,
            total_profit=100.0,
            avg_profit_per_order=50.0,
            profit_margin_pct=10.0,
            distinct_orders=2,
            total_quantity=4,
            performance_rank=0,
        )


# ---------------------------------------------------------------------------
# Helper Methods Tests
# ---------------------------------------------------------------------------

def test_analytics_engine_helper_inspection_methods() -> None:
    """Verifies helper methods for extracting highest sales, margin, and profit."""
    items = [
        CategoryPerformance(
            category="Electronics",
            total_sales=200000.0,
            total_profit=10000.0,
            avg_profit_per_order=50.0,
            profit_margin_pct=5.0,
            distinct_orders=200,
            total_quantity=1000,
            performance_rank=2,
        ),
        CategoryPerformance(
            category="Clothing",
            total_sales=100000.0,
            total_profit=15000.0,
            avg_profit_per_order=30.0,
            profit_margin_pct=15.0,
            distinct_orders=500,
            total_quantity=3000,
            performance_rank=1,
        ),
        CategoryPerformance(
            category="Furniture",
            total_sales=80000.0,
            total_profit=1600.0,
            avg_profit_per_order=10.0,
            profit_margin_pct=2.0,
            distinct_orders=160,
            total_quantity=800,
            performance_rank=3,
        ),
    ]

    assert AnalyticsEngine.get_highest_sales_category(items).category == "Electronics"
    assert AnalyticsEngine.get_highest_margin_category(items).category == "Clothing"
    assert AnalyticsEngine.get_lowest_margin_category(items).category == "Furniture"
    assert AnalyticsEngine.get_highest_profit_category(items).category == "Clothing"

    # Empty list raises ValueError
    with pytest.raises(ValueError, match="category_data list cannot be empty"):
        AnalyticsEngine.get_highest_sales_category([])


# ---------------------------------------------------------------------------
# Furniture Target MoM & Reconciliation Tests (AC-1.4, AC-E3)
# ---------------------------------------------------------------------------

def test_furniture_target_mom() -> None:
    """SPEC AC-1.4, AC-E3: Complete verification of Furniture Target MoM on real datasets.

    Checks:
    - Filters Category == 'Furniture'.
    - Chronological sorting from Apr-18 through Mar-19 (12 consecutive months).
    - Baseline month Apr-18 sets mom_target_pct_change to None and is_significant_fluctuation to False.
    - Subsequent months calculate MoM target % change ((Target_t - Target_{t-1}) / Target_{t-1}) * 100.
    - Monthly actual sales aggregated from merged line items, reconciling to category total (127,181.00).
    - Monthly variance (Actual - Target) and achievement % ((Actual / Target) * 100).
    - Default threshold 15.0% flags 0 months on real target data (monotonically flat targets).
    - Custom threshold 1.5% flags exactly 3 months with >1.5% growth (Jul-18, Nov-18, Mar-19).
    - Overperforming vs underperforming months correctly segregated.
    """
    orders_df = DataLoader.load_orders("data/input/List of Orders.xlsx")
    details_df = DataLoader.load_order_details("data/input/Order Details.xlsx")
    targets_df = DataLoader.load_sales_targets("data/input/Sales target.xlsx")
    merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)

    records = AnalyticsEngine.compute_furniture_target_mom(targets_df, merged_df)

    # 1. Total months: exactly 12 months (Apr-18 to Mar-19)
    assert len(records) == 12, f"Expected 12 months, got {len(records)}"

    # 2. Chronological sequence verification
    expected_display_months = [
        "Apr-18", "May-18", "Jun-18", "Jul-18",
        "Aug-18", "Sep-18", "Oct-18", "Nov-18",
        "Dec-18", "Jan-19", "Feb-19", "Mar-19",
    ]
    expected_month_keys = [
        "2018-04", "2018-05", "2018-06", "2018-07",
        "2018-08", "2018-09", "2018-10", "2018-11",
        "2018-12", "2019-01", "2019-02", "2019-03",
    ]
    assert [r.display_month for r in records] == expected_display_months
    assert [r.month_key for r in records] == expected_month_keys

    # 3. Baseline month (Apr-18) assertions
    apr18 = records[0]
    assert apr18.display_month == "Apr-18"
    assert apr18.month_key == "2018-04"
    assert apr18.target_sales == 10400.0
    assert apr18.actual_sales == 8121.0
    assert apr18.mom_target_pct_change is None
    assert apr18.mom_actual_pct_change is None
    assert apr18.is_significant_fluctuation is False
    assert apr18.variance == -2279.0  # 8121 - 10400
    assert apr18.achievement_pct == 78.09  # (8121 / 10400) * 100

    # 4. Target values across all 12 months
    expected_targets = [
        10400.0, 10500.0, 10600.0, 10800.0,
        10900.0, 11000.0, 11100.0, 11300.0,
        11400.0, 11500.0, 11600.0, 11800.0,
    ]
    assert [r.target_sales for r in records] == expected_targets

    # 5. Actual sales values and total reconciliation
    expected_actuals = [
        8121.0, 6220.0, 5532.0, 3483.0,
        9538.0, 8704.0, 6766.0, 15165.0,
        9474.0, 21257.0, 16262.0, 16659.0,
    ]
    assert [r.actual_sales for r in records] == expected_actuals
    assert sum(r.actual_sales for r in records) == 127181.0

    # 6. Subsequent MoM target % change calculations
    # May-18: (10500 - 10400) / 10400 * 100 = 0.96%
    assert records[1].mom_target_pct_change == 0.96
    # Jul-18: (10800 - 10600) / 10600 * 100 = 1.89%
    assert records[3].mom_target_pct_change == 1.89
    # Nov-18: (11300 - 11100) / 11100 * 100 = 1.80%
    assert records[7].mom_target_pct_change == 1.80
    # Mar-19: (11800 - 11600) / 11600 * 100 = 1.72%
    assert records[11].mom_target_pct_change == 1.72

    # 7. Fluctuation flags with default threshold (15.0%) -> 0 flags on real target data
    assert all(not r.is_significant_fluctuation for r in records)
    assert len(AnalyticsEngine.get_fluctuating_target_months(records)) == 0

    # 8. Fluctuation flags with custom threshold (1.5%) -> exactly 3 months flagged
    records_sensitive = AnalyticsEngine.compute_furniture_target_mom(
        targets_df, merged_df, fluctuation_threshold_pct=1.5
    )
    flagged = AnalyticsEngine.get_fluctuating_target_months(records_sensitive)
    assert [f.display_month for f in flagged] == ["Jul-18", "Nov-18", "Mar-19"]

    # 9. Overperforming vs underperforming target months
    achieved = AnalyticsEngine.get_achieved_target_months(records)
    unachieved = AnalyticsEngine.get_unachieved_target_months(records)
    assert len(achieved) == 4
    assert [a.display_month for a in achieved] == ["Nov-18", "Jan-19", "Feb-19", "Mar-19"]
    assert len(unachieved) == 8
    assert [u.display_month for u in unachieved] == [
        "Apr-18", "May-18", "Jun-18", "Jul-18", "Aug-18", "Sep-18", "Oct-18", "Dec-18"
    ]


def test_furniture_target_mom_synthetic_chronological_ordering_and_swings(
    sample_furniture_targets_chronological: pd.DataFrame,
    sample_merged_df: pd.DataFrame,
) -> None:
    """Verifies chronological sorting when targets are provided out-of-order and tests all 15% fluctuation swings."""
    # Reverse the order of targets so Mar-19 comes first and Apr-18 comes last
    reversed_targets = sample_furniture_targets_chronological.iloc[::-1].reset_index(drop=True)

    records = AnalyticsEngine.compute_furniture_target_mom(
        reversed_targets, sample_merged_df, fluctuation_threshold_pct=15.0
    )

    # 1. Output must still be sorted chronologically Apr-18 through Mar-19
    expected_display_months = [
        "Apr-18", "May-18", "Jun-18", "Jul-18",
        "Aug-18", "Sep-18", "Oct-18", "Nov-18",
        "Dec-18", "Jan-19", "Feb-19", "Mar-19",
    ]
    assert [r.display_month for r in records] == expected_display_months

    # 2. Baseline month Apr-18
    assert records[0].mom_target_pct_change is None
    assert records[0].is_significant_fluctuation is False

    # 3. Fluctuation swings test per conftest fixture specifications:
    # May-18: +20.0% -> Flagged
    assert records[1].mom_target_pct_change == 20.0
    assert records[1].is_significant_fluctuation is True

    # Jun-18: +4.17% -> Not Flagged
    assert records[2].mom_target_pct_change == 4.17
    assert records[2].is_significant_fluctuation is False

    # Jul-18: -20.0% -> Flagged
    assert records[3].mom_target_pct_change == -20.0
    assert records[3].is_significant_fluctuation is True

    # Aug-18: +15.0% -> Flagged (exact boundary check >= 15.0%)
    assert records[4].mom_target_pct_change == 15.0
    assert records[4].is_significant_fluctuation is True

    # Sep-18: 0.0% -> Not Flagged
    assert records[5].mom_target_pct_change == 0.0
    assert records[5].is_significant_fluctuation is False

    # Oct-18: +17.39% -> Flagged
    assert records[6].mom_target_pct_change == 17.39
    assert records[6].is_significant_fluctuation is True

    # Nov-18: -3.70% -> Not Flagged
    assert records[7].mom_target_pct_change == -3.70
    assert records[7].is_significant_fluctuation is False

    # Dec-18: +15.38% -> Flagged
    assert records[8].mom_target_pct_change == 15.38
    assert records[8].is_significant_fluctuation is True

    # Jan-19: +1.33% -> Not Flagged
    assert records[9].mom_target_pct_change == 1.33
    assert records[9].is_significant_fluctuation is False

    # Feb-19: -21.05% -> Flagged
    assert records[10].mom_target_pct_change == -21.05
    assert records[10].is_significant_fluctuation is True

    # Mar-19: +16.67% -> Flagged
    assert records[11].mom_target_pct_change == 16.67
    assert records[11].is_significant_fluctuation is True

    # 4. Check total flagged months count == 7
    flagged = AnalyticsEngine.get_fluctuating_target_months(records)
    assert len(flagged) == 7
    assert [f.display_month for f in flagged] == [
        "May-18", "Jul-18", "Aug-18", "Oct-18", "Dec-18", "Feb-19", "Mar-19"
    ]


def test_furniture_target_mom_variance_and_achievement_math() -> None:
    """Verifies variance and achievement mathematical precision and zero-handling."""
    targets_df = pd.DataFrame({
        "month_of_order_date": pd.to_datetime(["2018-04-01", "2018-05-01", "2018-06-01"]),
        "category": ["Furniture", "Furniture", "Furniture"],
        "target": [10000.0, 10000.0, 10000.0],
    })

    # Order details with distinct months:
    # Apr-18: 15,000 (Overachieved by 5,000 -> 150%)
    # May-18: 7,500 (Underachieved by 2,500 -> 75%)
    # Jun-18: No orders (0.0 sales -> 0%)
    orders_df = pd.DataFrame({
        "order_id": ["O-1", "O-2"],
        "order_date": pd.to_datetime(["2018-04-10", "2018-05-20"]),
        "customer_name": ["Alice", "Bob"],
        "state": ["Delhi", "Goa"],
        "city": ["Delhi", "Panaji"],
    })
    details_df = pd.DataFrame({
        "order_id": ["O-1", "O-2"],
        "amount": [15000.0, 7500.0],
        "profit": [2000.0, 1000.0],
        "quantity": [2, 1],
        "category": ["Furniture", "Furniture"],
        "sub_category": ["Chairs", "Tables"],
    })
    merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)

    records = AnalyticsEngine.compute_furniture_target_mom(targets_df, merged_df)
    assert len(records) == 3

    # Apr-18
    assert records[0].target_sales == 10000.0
    assert records[0].actual_sales == 15000.0
    assert records[0].variance == 5000.0
    assert records[0].achievement_pct == 150.0
    assert records[0].mom_actual_pct_change is None

    # May-18: actual dropped from 15,000 to 7,500 -> -50.0% MoM
    assert records[1].target_sales == 10000.0
    assert records[1].actual_sales == 7500.0
    assert records[1].variance == -2500.0
    assert records[1].achievement_pct == 75.0
    assert records[1].mom_actual_pct_change == -50.0

    # Jun-18: actual dropped to 0.0 -> -100.0% MoM
    assert records[2].target_sales == 10000.0
    assert records[2].actual_sales == 0.0
    assert records[2].variance == -10000.0
    assert records[2].achievement_pct == 0.0
    assert records[2].mom_actual_pct_change == -100.0


def test_furniture_target_mom_empty_and_invalid_inputs() -> None:
    """Verifies edge case and error handling in compute_furniture_target_mom."""
    valid_targets = pd.DataFrame({
        "month_of_order_date": ["2018-04-01"],
        "category": ["Furniture"],
        "target": [10000.0],
    })
    valid_merged = pd.DataFrame({
        "order_date": pd.to_datetime(["2018-04-01"]),
        "category": ["Furniture"],
        "amount": [8000.0],
    })

    # Type error on targets_df
    with pytest.raises(TypeError, match="targets_df must be pd.DataFrame"):
        AnalyticsEngine.compute_furniture_target_mom("not_a_df", valid_merged)  # type: ignore

    # Type error on merged_df
    with pytest.raises(TypeError, match="merged_df must be pd.DataFrame"):
        AnalyticsEngine.compute_furniture_target_mom(valid_targets, "not_a_df")  # type: ignore

    # Type error on threshold
    with pytest.raises(TypeError, match="fluctuation_threshold_pct must be numeric"):
        AnalyticsEngine.compute_furniture_target_mom(valid_targets, valid_merged, fluctuation_threshold_pct="bad")  # type: ignore

    # Negative threshold
    with pytest.raises(ValueError, match="fluctuation_threshold_pct cannot be negative"):
        AnalyticsEngine.compute_furniture_target_mom(valid_targets, valid_merged, fluctuation_threshold_pct=-5.0)

    # Missing column in targets_df
    bad_targets = pd.DataFrame({"month_of_order_date": ["2018-04-01"], "category": ["Furniture"]})
    with pytest.raises(ValueError, match="targets_df is missing mandatory columns"):
        AnalyticsEngine.compute_furniture_target_mom(bad_targets, valid_merged)

    # Missing column in merged_df
    bad_merged = pd.DataFrame({"order_date": ["2018-04-01"], "category": ["Furniture"]})
    with pytest.raises(ValueError, match="merged_df is missing mandatory columns"):
        AnalyticsEngine.compute_furniture_target_mom(valid_targets, bad_merged)

    # Empty targets_df returns empty list
    empty_targets = pd.DataFrame(columns=["month_of_order_date", "category", "target"])
    assert AnalyticsEngine.compute_furniture_target_mom(empty_targets, valid_merged) == []

    # Targets containing no Furniture rows returns empty list
    clothing_targets = pd.DataFrame({
        "month_of_order_date": ["2018-04-01"],
        "category": ["Clothing"],
        "target": [15000.0],
    })
    assert AnalyticsEngine.compute_furniture_target_mom(clothing_targets, valid_merged) == []

    # Empty merged_df still computes targets with 0 actuals
    empty_merged = pd.DataFrame(columns=["order_date", "category", "amount"])
    results_empty_merged = AnalyticsEngine.compute_furniture_target_mom(valid_targets, empty_merged)
    assert len(results_empty_merged) == 1
    assert results_empty_merged[0].actual_sales == 0.0
    assert results_empty_merged[0].variance == -10000.0
    assert results_empty_merged[0].achievement_pct == 0.0


def test_furniture_target_achievement_dataclass_validation() -> None:
    """Verifies FurnitureTargetAchievement invariant validation in __post_init__."""
    # Valid instantiation
    rec = FurnitureTargetAchievement(
        month_key="2018-04",
        display_month="Apr-18",
        target_sales=10000.0,
        actual_sales=12000.0,
        mom_target_pct_change=None,
        mom_actual_pct_change=None,
        variance=2000.0,
        achievement_pct=120.0,
        is_significant_fluctuation=False,
    )
    assert rec.month_key == "2018-04"
    assert rec.to_dict()["achievement_pct"] == 120.0

    # Blank month_key raises ValueError
    with pytest.raises(ValueError, match="month_key cannot be blank"):
        FurnitureTargetAchievement(
            month_key="",
            display_month="Apr-18",
            target_sales=10000.0,
            actual_sales=12000.0,
            mom_target_pct_change=None,
            mom_actual_pct_change=None,
            variance=2000.0,
            achievement_pct=120.0,
            is_significant_fluctuation=False,
        )

    # Blank display_month raises ValueError
    with pytest.raises(ValueError, match="display_month cannot be blank"):
        FurnitureTargetAchievement(
            month_key="2018-04",
            display_month="  ",
            target_sales=10000.0,
            actual_sales=12000.0,
            mom_target_pct_change=None,
            mom_actual_pct_change=None,
            variance=2000.0,
            achievement_pct=120.0,
            is_significant_fluctuation=False,
        )

    # Negative target_sales raises ValueError
    with pytest.raises(ValueError, match="target_sales cannot be negative"):
        FurnitureTargetAchievement(
            month_key="2018-04",
            display_month="Apr-18",
            target_sales=-100.0,
            actual_sales=12000.0,
            mom_target_pct_change=None,
            mom_actual_pct_change=None,
            variance=12100.0,
            achievement_pct=0.0,
            is_significant_fluctuation=False,
        )

    # Variance mismatch raises ValueError
    with pytest.raises(ValueError, match="Variance mismatch"):
        FurnitureTargetAchievement(
            month_key="2018-04",
            display_month="Apr-18",
            target_sales=10000.0,
            actual_sales=12000.0,
            mom_target_pct_change=None,
            mom_actual_pct_change=None,
            variance=9999.0,  # Deliberate mismatch
            achievement_pct=120.0,
            is_significant_fluctuation=False,
        )

    # Achievement % mismatch raises ValueError
    with pytest.raises(ValueError, match="Achievement % mismatch"):
        FurnitureTargetAchievement(
            month_key="2018-04",
            display_month="Apr-18",
            target_sales=10000.0,
            actual_sales=12000.0,
            mom_target_pct_change=None,
            mom_actual_pct_change=None,
            variance=2000.0,
            achievement_pct=50.0,  # Deliberate mismatch
            is_significant_fluctuation=False,
        )


def test_furniture_helper_methods() -> None:
    """Verifies target reconciliation helper methods with mixed and empty inputs."""
    r1 = FurnitureTargetAchievement(
        month_key="2018-04",
        display_month="Apr-18",
        target_sales=10000.0,
        actual_sales=12000.0,
        mom_target_pct_change=None,
        mom_actual_pct_change=None,
        variance=2000.0,
        achievement_pct=120.0,
        is_significant_fluctuation=False,
    )
    r2 = FurnitureTargetAchievement(
        month_key="2018-05",
        display_month="May-18",
        target_sales=12000.0,
        actual_sales=9000.0,
        mom_target_pct_change=20.0,
        mom_actual_pct_change=-25.0,
        variance=-3000.0,
        achievement_pct=75.0,
        is_significant_fluctuation=True,
    )
    r3 = FurnitureTargetAchievement(
        month_key="2018-06",
        display_month="Jun-18",
        target_sales=10000.0,
        actual_sales=10000.0,
        mom_target_pct_change=-16.67,
        mom_actual_pct_change=11.11,
        variance=0.0,
        achievement_pct=100.0,
        is_significant_fluctuation=True,
    )

    records = [r1, r2, r3]

    fluctuating = AnalyticsEngine.get_fluctuating_target_months(records)
    assert len(fluctuating) == 2
    assert [r.display_month for r in fluctuating] == ["May-18", "Jun-18"]

    achieved = AnalyticsEngine.get_achieved_target_months(records)
    assert len(achieved) == 2
    assert [r.display_month for r in achieved] == ["Apr-18", "Jun-18"]

    unachieved = AnalyticsEngine.get_unachieved_target_months(records)
    assert len(unachieved) == 1
    assert [r.display_month for r in unachieved] == ["May-18"]

    # Empty inputs return empty lists
    assert AnalyticsEngine.get_fluctuating_target_months([]) == []
    assert AnalyticsEngine.get_achieved_target_months([]) == []
    assert AnalyticsEngine.get_unachieved_target_months([]) == []


# ---------------------------------------------------------------------------
# Regional Performance & Quadrant Classification Tests (AC-1.5, M1-TASK-05)
# ---------------------------------------------------------------------------

def test_top_states_performance() -> None:
    """SPEC AC-1.5, AC-E2, AC-E5: Complete verification of Top States Performance on real datasets.

    Checks:
    - Ranks states strictly by distinct order_id count from List of Orders.
    - Selects exactly top 5 states: Madhya Pradesh, Maharashtra, Rajasthan, Gujarat, Punjab.
    - Computes distinct orders, total sales, total profit, average profit per order, and profit margin %.
    - AC-E2: Retains negative profit for Punjab (-609.00 profit, -3.63% margin).
    - Categorizes each state into strategic performance quadrants relative to median volume and margin.
    - Helper inspection methods: get_highest_sales_state, get_highest_profit_state,
      get_highest_margin_state, get_lowest_margin_state, get_states_by_quadrant.
    """
    orders_df = DataLoader.load_orders("data/input/List of Orders.xlsx")
    details_df = DataLoader.load_order_details("data/input/Order Details.xlsx")
    merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)

    results = AnalyticsEngine.compute_top_states_performance(orders_df, merged_df, top_n=5)

    # 1. Exactly 5 states returned, ranked 1 to 5
    assert len(results) == 5, f"Expected 5 states, got {len(results)}"
    assert [r.rank for r in results] == [1, 2, 3, 4, 5]

    res_by_state: Dict[str, StatePerformance] = {r.state: r for r in results}
    expected_order = ["Madhya Pradesh", "Maharashtra", "Rajasthan", "Gujarat", "Punjab"]
    assert [r.state for r in results] == expected_order

    # 2. Rank 1: Madhya Pradesh (High Volume / Low Margin)
    mp = res_by_state["Madhya Pradesh"]
    assert mp.rank == 1
    assert mp.distinct_orders == 101
    assert mp.total_sales == 105140.00
    assert mp.total_profit == 5551.00
    assert mp.avg_profit_per_order == 54.96  # 5,551 / 101 = 54.9604
    assert mp.profit_margin_pct == 5.28     # (5,551 / 105,140) * 100 = 5.2796%
    assert mp.quadrant == "High Volume / Low Margin"

    # 3. Rank 2: Maharashtra (High Volume / High Margin)
    mh = res_by_state["Maharashtra"]
    assert mh.rank == 2
    assert mh.distinct_orders == 90
    assert mh.total_sales == 95348.00
    assert mh.total_profit == 6176.00
    assert mh.avg_profit_per_order == 68.62  # 6,176 / 90 = 68.6222
    assert mh.profit_margin_pct == 6.48     # (6,176 / 95,348) * 100 = 6.4773%
    assert mh.quadrant == "High Volume / High Margin"

    # 4. Rank 3: Rajasthan (Low Volume / High Margin)
    rj = res_by_state["Rajasthan"]
    assert rj.rank == 3
    assert rj.distinct_orders == 32
    assert rj.total_sales == 21149.00
    assert rj.total_profit == 1257.00
    assert rj.avg_profit_per_order == 39.28  # 1,257 / 32 = 39.28125
    assert rj.profit_margin_pct == 5.94     # (1,257 / 21,149) * 100 = 5.9435%
    assert rj.quadrant == "Low Volume / High Margin"

    # 5. Rank 4: Gujarat (Low Volume / Low Margin)
    gj = res_by_state["Gujarat"]
    assert gj.rank == 4
    assert gj.distinct_orders == 27
    assert gj.total_sales == 21058.00
    assert gj.total_profit == 465.00
    assert gj.avg_profit_per_order == 17.22  # 465 / 27 = 17.2222
    assert gj.profit_margin_pct == 2.21     # (465 / 21,058) * 100 = 2.2082%
    assert gj.quadrant == "Low Volume / Low Margin"

    # 6. Rank 5: Punjab (Low Volume / Low Margin) - Loss Leader / Negative Profit (AC-E2)
    pb = res_by_state["Punjab"]
    assert pb.rank == 5
    assert pb.distinct_orders == 25
    assert pb.total_sales == 16786.00
    assert pb.total_profit == -609.00
    assert pb.avg_profit_per_order == -24.36  # -609 / 25 = -24.36
    assert pb.profit_margin_pct == -3.63     # (-609 / 16,786) * 100 = -3.6280%
    assert pb.quadrant == "Low Volume / Low Margin"

    # 7. Helper inspection methods assertions
    highest_sales = AnalyticsEngine.get_highest_sales_state(results)
    assert highest_sales.state == "Madhya Pradesh"
    assert highest_sales.total_sales == 105140.00

    highest_profit = AnalyticsEngine.get_highest_profit_state(results)
    assert highest_profit.state == "Maharashtra"
    assert highest_profit.total_profit == 6176.00

    highest_margin = AnalyticsEngine.get_highest_margin_state(results)
    assert highest_margin.state == "Maharashtra"
    assert highest_margin.profit_margin_pct == 6.48

    lowest_margin = AnalyticsEngine.get_lowest_margin_state(results)
    assert lowest_margin.state == "Punjab"
    assert lowest_margin.profit_margin_pct == -3.63

    # 8. Quadrant segregation assertions
    hi_vol_hi_mar = AnalyticsEngine.get_states_by_quadrant(results, "High Volume / High Margin")
    assert [s.state for s in hi_vol_hi_mar] == ["Maharashtra"]

    hi_vol_lo_mar = AnalyticsEngine.get_states_by_quadrant(results, "High Volume / Low Margin")
    assert [s.state for s in hi_vol_lo_mar] == ["Madhya Pradesh"]

    lo_vol_hi_mar = AnalyticsEngine.get_states_by_quadrant(results, "Low Volume / High Margin")
    assert [s.state for s in lo_vol_hi_mar] == ["Rajasthan"]

    lo_vol_lo_mar = AnalyticsEngine.get_states_by_quadrant(results, "Low Volume / Low Margin")
    assert [s.state for s in lo_vol_lo_mar] == ["Gujarat", "Punjab"]


def test_top_states_performance_distinct_orders_not_inflated_by_lines() -> None:
    """Verifies ADR-006: state order volume is based on distinct Order IDs, NOT line item row counts."""
    # State A has 2 orders with 10 total line items (bulk buyer)
    # State B has 3 orders with 1 line item each (more customer reach)
    # State B must rank ahead of State A by distinct order volume!
    orders_df = pd.DataFrame({
        "order_id": ["O-A1", "O-A2", "O-B1", "O-B2", "O-B3"],
        "order_date": pd.to_datetime(["2018-04-01"] * 5),
        "customer_name": ["Alice", "Alice", "Bob", "Charlie", "David"],
        "state": ["State A", "State A", "State B", "State B", "State B"],
        "city": ["City A", "City A", "City B", "City B", "City B"],
    })

    # Line items: State A has 5 lines for O-A1 and 5 lines for O-A2 (10 rows total)
    # State B has 1 line each (3 rows total)
    details_rows = []
    for i in range(5):
        details_rows.append({"order_id": "O-A1", "amount": 100.0, "profit": 20.0, "quantity": 1, "category": "Clothing", "sub_category": "Saree"})
        details_rows.append({"order_id": "O-A2", "amount": 100.0, "profit": 20.0, "quantity": 1, "category": "Clothing", "sub_category": "Saree"})
    for oid in ["O-B1", "O-B2", "O-B3"]:
        details_rows.append({"order_id": oid, "amount": 50.0, "profit": 10.0, "quantity": 1, "category": "Clothing", "sub_category": "Saree"})

    details_df = pd.DataFrame(details_rows)
    merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)

    results = AnalyticsEngine.compute_top_states_performance(orders_df, merged_df, top_n=2)

    # State B has 3 distinct orders, State A has 2 distinct orders -> State B is Rank 1!
    assert len(results) == 2
    assert results[0].state == "State B"
    assert results[0].distinct_orders == 3
    assert results[0].rank == 1

    assert results[1].state == "State A"
    assert results[1].distinct_orders == 2
    assert results[1].rank == 2


def test_top_states_performance_custom_benchmarks_and_top_n() -> None:
    """Verifies custom top_n, custom volume and margin benchmarks, and inclusive flag."""
    orders_df = DataLoader.load_orders("data/input/List of Orders.xlsx")
    details_df = DataLoader.load_order_details("data/input/Order Details.xlsx")
    merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)

    # top_n = 3
    top3 = AnalyticsEngine.compute_top_states_performance(orders_df, merged_df, top_n=3)
    assert len(top3) == 3
    assert [r.state for r in top3] == ["Madhya Pradesh", "Maharashtra", "Rajasthan"]

    # Custom benchmarks: volume_benchmark=50.0, margin_benchmark=6.0
    custom_results = AnalyticsEngine.compute_top_states_performance(
        orders_df,
        merged_df,
        top_n=5,
        volume_benchmark=50.0,
        margin_benchmark=6.0,
    )
    res_map = {r.state: r.quadrant for r in custom_results}
    # MP: orders 101 > 50, margin 5.28% <= 6.0% -> High Volume / Low Margin
    assert res_map["Madhya Pradesh"] == "High Volume / Low Margin"
    # MH: orders 90 > 50, margin 6.48% > 6.0% -> High Volume / High Margin
    assert res_map["Maharashtra"] == "High Volume / High Margin"
    # RJ: orders 32 <= 50, margin 5.94% <= 6.0% -> Low Volume / Low Margin
    assert res_map["Rajasthan"] == "Low Volume / Low Margin"

    # Inclusive flag test: when threshold is exact value, inclusive=True puts it in High
    exact_vol = AnalyticsEngine.compute_top_states_performance(
        orders_df,
        merged_df,
        top_n=5,
        volume_benchmark=32.0,  # Exactly Rajasthan's volume
        margin_benchmark=5.28,  # Exactly MP's margin
        inclusive=True,
    )
    inc_map = {r.state: r.quadrant for r in exact_vol}
    # Rajasthan (32 orders, 5.94% margin) with inclusive=True has volume >= 32 and margin >= 5.28 -> High Volume / High Margin
    assert inc_map["Rajasthan"] == "High Volume / High Margin"
    # Madhya Pradesh (101 orders, 5.28% margin) with inclusive=True has volume >= 32 and margin >= 5.28 -> High Volume / High Margin
    assert inc_map["Madhya Pradesh"] == "High Volume / High Margin"


def test_top_states_performance_zero_division_and_edge_cases() -> None:
    """SPEC AC-E5: Zero-division safety and graceful edge case handling."""
    # Zero sales state
    orders_df = pd.DataFrame({
        "order_id": ["O-FREE-1"],
        "state": ["Goa"],
    })
    merged_df = pd.DataFrame({
        "order_id": ["O-FREE-1"],
        "state": ["Goa"],
        "amount": [0.0],
        "profit": [0.0],
    })

    results = AnalyticsEngine.compute_top_states_performance(orders_df, merged_df, top_n=1)
    assert len(results) == 1
    goa = results[0]
    assert goa.distinct_orders == 1
    assert goa.total_sales == 0.0
    assert goa.total_profit == 0.0
    assert goa.avg_profit_per_order == 0.0
    assert goa.profit_margin_pct == 0.0

    # Empty inputs return empty list
    empty_orders = pd.DataFrame(columns=["order_id", "state"])
    empty_merged = pd.DataFrame(columns=["order_id", "state", "amount", "profit"])
    assert AnalyticsEngine.compute_top_states_performance(empty_orders, empty_merged) == []

    # Non-dataframe raises TypeError
    with pytest.raises(TypeError, match="orders_df must be pd.DataFrame"):
        AnalyticsEngine.compute_top_states_performance("not_a_df", empty_merged)  # type: ignore

    with pytest.raises(TypeError, match="merged_df must be pd.DataFrame"):
        AnalyticsEngine.compute_top_states_performance(empty_orders, "not_a_df")  # type: ignore

    # Non-integer top_n raises TypeError
    with pytest.raises(TypeError, match="top_n must be an integer"):
        AnalyticsEngine.compute_top_states_performance(orders_df, merged_df, top_n="five")  # type: ignore

    # top_n < 1 raises ValueError
    with pytest.raises(ValueError, match="top_n must be >= 1"):
        AnalyticsEngine.compute_top_states_performance(orders_df, merged_df, top_n=0)

    # Missing mandatory column raises ValueError
    bad_orders = pd.DataFrame({"order_id": ["O-1"]})  # Missing 'state'
    with pytest.raises(ValueError, match="orders_df is missing mandatory columns"):
        AnalyticsEngine.compute_top_states_performance(bad_orders, merged_df)

    bad_merged = pd.DataFrame({"order_id": ["O-1"], "state": ["Goa"]})  # Missing 'amount', 'profit'
    with pytest.raises(ValueError, match="merged_df is missing mandatory columns"):
        AnalyticsEngine.compute_top_states_performance(orders_df, bad_merged)


def test_state_performance_dataclass_validation() -> None:
    """Verifies StatePerformance invariant validation in __post_init__."""
    # Valid record
    rec = StatePerformance(
        rank=1,
        state="Maharashtra",
        distinct_orders=90,
        total_sales=95348.0,
        total_profit=6176.0,
        avg_profit_per_order=68.62,
        profit_margin_pct=6.48,
        quadrant="High Volume / High Margin",
    )
    assert rec.rank == 1
    assert rec.state == "Maharashtra"
    assert rec.to_dict()["profit_margin_pct"] == 6.48

    # rank < 1
    with pytest.raises(ValueError, match="rank must be >= 1"):
        StatePerformance(
            rank=0,
            state="Maharashtra",
            distinct_orders=90,
            total_sales=95348.0,
            total_profit=6176.0,
            avg_profit_per_order=68.62,
            profit_margin_pct=6.48,
            quadrant="High Volume / High Margin",
        )

    # Blank state
    with pytest.raises(ValueError, match="state cannot be blank"):
        StatePerformance(
            rank=1,
            state="   ",
            distinct_orders=90,
            total_sales=95348.0,
            total_profit=6176.0,
            avg_profit_per_order=68.62,
            profit_margin_pct=6.48,
            quadrant="High Volume / High Margin",
        )

    # Negative distinct_orders
    with pytest.raises(ValueError, match="distinct_orders cannot be negative"):
        StatePerformance(
            rank=1,
            state="Maharashtra",
            distinct_orders=-5,
            total_sales=95348.0,
            total_profit=6176.0,
            avg_profit_per_order=68.62,
            profit_margin_pct=6.48,
            quadrant="High Volume / High Margin",
        )

    # Average profit mismatch
    with pytest.raises(ValueError, match="Average profit mismatch"):
        StatePerformance(
            rank=1,
            state="Maharashtra",
            distinct_orders=90,
            total_sales=95348.0,
            total_profit=6176.0,
            avg_profit_per_order=999.0,  # Deliberate mismatch
            profit_margin_pct=6.48,
            quadrant="High Volume / High Margin",
        )

    # Margin mismatch
    with pytest.raises(ValueError, match="Margin mismatch"):
        StatePerformance(
            rank=1,
            state="Maharashtra",
            distinct_orders=90,
            total_sales=95348.0,
            total_profit=6176.0,
            avg_profit_per_order=68.62,
            profit_margin_pct=99.0,  # Deliberate mismatch
            quadrant="High Volume / High Margin",
        )

    # Invalid quadrant
    with pytest.raises(ValueError, match="Invalid quadrant"):
        StatePerformance(
            rank=1,
            state="Maharashtra",
            distinct_orders=90,
            total_sales=95348.0,
            total_profit=6176.0,
            avg_profit_per_order=68.62,
            profit_margin_pct=6.48,
            quadrant="Invalid Quadrant Name",
        )


# ---------------------------------------------------------------------------
# City Performance Breakdown Tests (Question 1 Part 3 Helper Deep-Dive)
# ---------------------------------------------------------------------------

def test_city_performance_real_dataset_and_helpers() -> None:
    """Verifies city-level performance breakdown, state filtering, and loss-making city identification."""
    orders_df = DataLoader.load_orders("data/input/List of Orders.xlsx")
    details_df = DataLoader.load_order_details("data/input/Order Details.xlsx")
    merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)

    # 1. State-specific city performance: Maharashtra (Mumbai vs Pune)
    mh_cities = AnalyticsEngine.compute_city_performance(merged_df, state="Maharashtra")
    assert len(mh_cities) == 2
    city_map = {c.city: c for c in mh_cities}

    mumbai = city_map["Mumbai"]
    assert mumbai.state == "Maharashtra"
    assert mumbai.distinct_orders == 68
    assert mumbai.total_sales == 61867.00
    assert mumbai.total_profit == 1637.00
    assert mumbai.avg_profit_per_order == 24.07
    assert mumbai.profit_margin_pct == 2.65

    pune = city_map["Pune"]
    assert pune.state == "Maharashtra"
    assert pune.distinct_orders == 22
    assert pune.total_sales == 33481.00
    assert pune.total_profit == 4539.00
    assert pune.avg_profit_per_order == 206.32
    assert pune.profit_margin_pct == 13.56

    # 2. State-specific city performance: Punjab (Chandigarh loss leader vs Amritsar)
    pb_cities = AnalyticsEngine.compute_city_performance(merged_df, state="Punjab")
    assert len(pb_cities) == 2
    pb_map = {c.city: c for c in pb_cities}

    chandigarh = pb_map["Chandigarh"]
    assert chandigarh.total_profit == -1153.00
    assert chandigarh.avg_profit_per_order == -72.06
    assert chandigarh.profit_margin_pct == -9.39

    amritsar = pb_map["Amritsar"]
    assert amritsar.total_profit == 544.00
    assert amritsar.avg_profit_per_order == 60.44
    assert amritsar.profit_margin_pct == 12.07

    # 3. All cities breakdown across dataset
    all_cities = AnalyticsEngine.compute_city_performance(merged_df)
    assert len(all_cities) == 26

    # 4. Helper: get_loss_making_cities across entire dataset
    loss_cities = AnalyticsEngine.get_loss_making_cities(all_cities)
    assert len(loss_cities) == 6
    # Worst loss city is Chennai (-2216.00), followed by Chandigarh (-1153.00), Ahmedabad (-880.00), Jaipur (-753.00)
    assert loss_cities[0].city == "Chennai"
    assert loss_cities[0].state == "Tamil Nadu"
    assert loss_cities[0].total_profit == -2216.00
    assert loss_cities[1].city == "Chandigarh"
    assert loss_cities[1].state == "Punjab"
    assert loss_cities[1].total_profit == -1153.00
    assert loss_cities[2].city == "Ahmedabad"
    assert loss_cities[2].state == "Gujarat"
    assert loss_cities[2].total_profit == -880.00
    assert loss_cities[3].city == "Jaipur"
    assert loss_cities[3].state == "Rajasthan"
    assert loss_cities[3].total_profit == -753.00

    # 5. Helper: get_top_performing_cities
    top_cities = AnalyticsEngine.get_top_performing_cities(all_cities, top_n=3)
    assert len(top_cities) == 3
    assert top_cities[0].profit_margin_pct >= top_cities[1].profit_margin_pct >= top_cities[2].profit_margin_pct


def test_city_performance_dataclass_validation_and_edge_cases() -> None:
    """Verifies CityPerformance validation and edge case handling."""
    # Valid instantiation
    rec = CityPerformance(
        state="Gujarat",
        city="Surat",
        distinct_orders=10,
        total_sales=6828.0,
        total_profit=1345.0,
        avg_profit_per_order=134.50,
        profit_margin_pct=19.70,
    )
    assert rec.city == "Surat"
    assert rec.to_dict()["avg_profit_per_order"] == 134.50

    # Blank city raises ValueError
    with pytest.raises(ValueError, match="city cannot be blank"):
        CityPerformance(
            state="Gujarat",
            city="",
            distinct_orders=10,
            total_sales=6828.0,
            total_profit=1345.0,
            avg_profit_per_order=134.50,
            profit_margin_pct=19.70,
        )

    # Blank state raises ValueError
    with pytest.raises(ValueError, match="state cannot be blank"):
        CityPerformance(
            state="",
            city="Surat",
            distinct_orders=10,
            total_sales=6828.0,
            total_profit=1345.0,
            avg_profit_per_order=134.50,
            profit_margin_pct=19.70,
        )

    # Empty merged_df returns empty list
    empty_df = pd.DataFrame(columns=["order_id", "state", "city", "amount", "profit"])
    assert AnalyticsEngine.compute_city_performance(empty_df) == []

    # Nonexistent state returns empty list
    orders_df = DataLoader.load_orders("data/input/List of Orders.xlsx")
    details_df = DataLoader.load_order_details("data/input/Order Details.xlsx")
    merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)
    assert AnalyticsEngine.compute_city_performance(merged_df, state="NonExistentState") == []

    # Non-dataframe raises TypeError
    with pytest.raises(TypeError, match="merged_df must be pd.DataFrame"):
        AnalyticsEngine.compute_city_performance("not_a_df")  # type: ignore

    # Missing mandatory column raises ValueError
    bad_df = pd.DataFrame({"order_id": ["O-1"], "state": ["Goa"]})
    with pytest.raises(ValueError, match="merged_df is missing mandatory columns"):
        AnalyticsEngine.compute_city_performance(bad_df)


# ---------------------------------------------------------------------------
# Q1 Deep-Dive: Sub-Categories, Target Alignment, City Priorities
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real_q1_inputs() -> Dict[str, Any]:
    """Loads and merges the real workbooks once for the deep-dive tests."""
    orders_df, details_df, targets_df = DataLoader.load_all(data_dir="data/input")
    merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)
    return {
        "targets": targets_df,
        "merged": merged_df,
        "states": AnalyticsEngine.compute_top_states_performance(orders_df, merged_df),
    }


def test_subcategory_performance_reconciles_to_category_totals(
    real_q1_inputs: Dict[str, Any],
) -> None:
    """Sub-category sales and profit sum to each category total; Tables stays loss-making."""
    merged_df = real_q1_inputs["merged"]
    subs = AnalyticsEngine.compute_subcategory_performance(merged_df)
    cats = AnalyticsEngine.compute_category_performance(merged_df)
    assert len(subs) == merged_df.groupby(["category", "sub_category"]).ngroups

    for cat in cats:
        rows = [s for s in subs if s.category == cat.category]
        assert sum(s.total_sales for s in rows) == pytest.approx(cat.total_sales, abs=0.05)
        assert sum(s.total_profit for s in rows) == pytest.approx(cat.total_profit, abs=0.05)

    tables = next(s for s in subs if s.sub_category == "Tables")
    assert tables.category == "Furniture"
    assert tables.total_profit < 0
    assert tables.profit_margin_pct == pytest.approx(-17.74, abs=0.01)


def test_subcategory_performance_keeps_negative_margin_synthetic() -> None:
    """A loss-making sub-category is kept with its negative margin; bad input is rejected."""
    df = pd.DataFrame({
        "order_id": ["A", "A", "B", "C"],
        "category": ["Furniture", "Furniture", "Furniture", "Clothing"],
        "sub_category": ["Tables", "Chairs", "Tables", "Saree"],
        "amount": [100.0, 50.0, 100.0, 40.0],
        "profit": [-30.0, 5.0, -10.0, 4.0],
        "quantity": [1, 1, 2, 1],
    })
    subs = AnalyticsEngine.compute_subcategory_performance(df)
    tables = next(s for s in subs if s.sub_category == "Tables")
    assert tables.total_sales == 200.0
    assert tables.total_profit == -40.0
    assert tables.profit_margin_pct == -20.0
    assert tables.distinct_orders == 2
    assert tables.avg_profit_per_order == -20.0
    assert AnalyticsEngine.compute_subcategory_performance(pd.DataFrame()) == []
    with pytest.raises(ValueError, match="sub-category analysis"):
        AnalyticsEngine.compute_subcategory_performance(df.drop(columns=["sub_category"]))


def test_target_alignment_half_year_split(real_q1_inputs: Dict[str, Any]) -> None:
    """Half-year actuals sum to the annual total and the second half dominates."""
    furn = AnalyticsEngine.compute_furniture_target_mom(
        real_q1_inputs["targets"], real_q1_inputs["merged"]
    )
    ta = AnalyticsEngine.compute_target_alignment(furn)
    assert ta["h1_actual"] + ta["h2_actual"] == pytest.approx(sum(f.actual_sales for f in furn))
    assert ta["h1_target"] + ta["h2_target"] == pytest.approx(sum(f.target_sales for f in furn))
    assert ta["h2_actual_share_pct"] > 60
    assert ta["rolling_mae"] < ta["flat_ramp_mae"]
    assert len(ta["quarters"]) == 4
    assert AnalyticsEngine.compute_target_alignment(furn[:2]) == {}


def test_city_priorities_name_fix_and_scale_cities(real_q1_inputs: Dict[str, Any]) -> None:
    """City prioritisation returns named Fix and Scale cities with reasons."""
    prios = AnalyticsEngine.compute_city_priorities(
        real_q1_inputs["merged"], real_q1_inputs["states"]
    )
    fix = [p for p in prios if p.action == "Fix"]
    scale = [p for p in prios if p.action == "Scale"]
    assert fix and scale
    assert all(p.city.strip() and p.reason.strip() for p in prios)
    assert ("Chandigarh", "Punjab") in {(p.city, p.state) for p in fix}
    assert any(p.city == "Mumbai" for p in fix)
    assert all(p.profit_gap > 0 for p in fix)
    assert all(p.total_profit > 0 for p in scale)
    top_states = {s.state for s in real_q1_inputs["states"]}
    assert any(p.state in top_states for p in fix)


def test_build_q1_insights_sections(real_q1_inputs: Dict[str, Any]) -> None:
    """The Q1 narrative has reasons, 2 recommendations, 3 strategies and disparities."""
    merged = real_q1_inputs["merged"]
    states = real_q1_inputs["states"]
    insights = AnalyticsEngine.build_q1_insights(
        AnalyticsEngine.compute_category_performance(merged),
        AnalyticsEngine.compute_subcategory_performance(merged),
        AnalyticsEngine.compute_furniture_target_mom(real_q1_inputs["targets"], merged),
        states,
        AnalyticsEngine.compute_city_priorities(merged, states),
    )
    assert 3 <= len(insights["part1_reasons"]) <= 4
    assert "Tables" in insights["part1_reasons"][0]
    assert len(insights["part1_recommendations"]) == 2
    assert len(insights["part2_strategies"]) == 3
    assert insights["part3_disparities"]
    assert "Chandigarh" in insights["exec_part3"]
    empty = AnalyticsEngine.build_q1_insights([], [], [], [], [])
    assert empty["part1_reasons"] == [] and empty["part2_strategies"] == []



