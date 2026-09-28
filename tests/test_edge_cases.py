"""Edge-case tests for SPEC acceptance criteria AC-E1 to AC-E6."""

import logging
import math
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest

from src.analytics_engine import AnalyticsEngine
from src.data_loader import DataLoader, MissingColumnError, parse_order_date


# ---------------------------------------------------------------------------
# AC-E1: Mixed date formats and leap day
# ---------------------------------------------------------------------------

def test_parse_order_date_mixed_formats_and_leap_day() -> None:
    assert parse_order_date("01-04-2018") == pd.Timestamp(2018, 4, 1)  # DD-MM-YYYY, no swap
    assert parse_order_date("2018-05-15") == pd.Timestamp(2018, 5, 15)
    assert parse_order_date("29-02-2020") == pd.Timestamp(2020, 2, 29)
    assert parse_order_date(43191) == pd.Timestamp(2018, 4, 1)  # Excel serial


def test_load_orders_with_mixed_dates_from_excel(
    tmp_path: Path, sample_mixed_dates_records: List[Dict[str, Any]]
) -> None:
    path = tmp_path / "List of Orders.xlsx"
    pd.DataFrame(sample_mixed_dates_records).to_excel(path, index=False)

    orders = DataLoader.load_orders(path)

    assert pd.api.types.is_datetime64_any_dtype(orders["order_date"])
    assert list(orders["order_date"]) == [
        pd.Timestamp(2018, 4, 1),
        pd.Timestamp(2018, 5, 15),
        pd.Timestamp(2020, 2, 29),
        pd.Timestamp(2018, 12, 31),
    ]


# ---------------------------------------------------------------------------
# AC-E2: Negative profit (loss leaders) preserved in aggregates
# ---------------------------------------------------------------------------

def test_negative_profits_preserved_in_category_aggregate(
    sample_loss_leader_details_df: pd.DataFrame,
) -> None:
    merged = sample_loss_leader_details_df.assign(
        order_date=pd.Timestamp(2018, 4, 1), state="Goa", city="Panaji", customer_name="X"
    )

    [furniture] = AnalyticsEngine.compute_category_performance(merged)

    assert furniture.distinct_orders == 3  # no loss rows dropped
    assert furniture.total_sales == pytest.approx(10000.0)
    assert furniture.total_profit == pytest.approx(-4000.0)  # not zero-clipped
    assert furniture.profit_margin_pct == pytest.approx(-40.0)


# ---------------------------------------------------------------------------
# AC-E3: First month's MoM target change is None/NaN
# ---------------------------------------------------------------------------

def test_first_month_mom_is_none(
    sample_furniture_targets_chronological: pd.DataFrame, sample_merged_df: pd.DataFrame
) -> None:
    results = AnalyticsEngine.compute_furniture_target_mom(
        sample_furniture_targets_chronological, sample_merged_df
    )

    first = results[0]
    assert first.display_month == "Apr-18"
    assert first.mom_target_pct_change is None or math.isnan(first.mom_target_pct_change)
    assert first.is_significant_fluctuation is False
    assert results[1].mom_target_pct_change == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# AC-E4: Missing file or missing column raises a clear error
# ---------------------------------------------------------------------------

def test_missing_excel_file_raises_file_not_found(tmp_path: Path) -> None:
    missing = tmp_path / "List of Orders.xlsx"
    with pytest.raises(FileNotFoundError, match="does not exist"):
        DataLoader.load_orders(missing)


def test_missing_required_column_raises_descriptive_error(
    tmp_path: Path, sample_order_details_df: pd.DataFrame
) -> None:
    path = tmp_path / "Order Details.xlsx"
    sample_order_details_df.drop(columns=["profit"]).to_excel(path, index=False)

    with pytest.raises(MissingColumnError, match="profit") as exc_info:
        DataLoader.load_order_details(path)
    assert isinstance(exc_info.value, ValueError)


# ---------------------------------------------------------------------------
# AC-E5: Zero sales gives a safe margin
# ---------------------------------------------------------------------------

def test_zero_sales_margin_is_safe() -> None:
    merged = pd.DataFrame({
        "order_id": ["Z-1"],
        "order_date": [pd.Timestamp(2018, 4, 1)],
        "customer_name": ["Zed"],
        "state": ["Goa"],
        "city": ["Panaji"],
        "amount": [0.0],
        "profit": [0.0],
        "quantity": [1],
        "category": ["Clothing"],
        "sub_category": ["Saree"],
    })

    [clothing] = AnalyticsEngine.compute_category_performance(merged)

    margin = clothing.profit_margin_pct
    assert margin == 0.0 or math.isnan(margin)
    assert not math.isinf(margin)


# ---------------------------------------------------------------------------
# AC-E6: Unmatched order IDs excluded by inner join
# ---------------------------------------------------------------------------

def test_unmatched_order_ids_excluded_and_logged(
    sample_orders_df: pd.DataFrame,
    sample_order_details_df: pd.DataFrame,
    caplog: pytest.LogCaptureFixture,
) -> None:
    orders = pd.concat([
        sample_orders_df,
        pd.DataFrame({
            "order_id": ["ONLY-HEADER"],
            "order_date": [pd.Timestamp(2018, 9, 1)],
            "customer_name": ["Nobody"],
            "state": ["Goa"],
            "city": ["Panaji"],
        }),
    ], ignore_index=True)
    details = pd.concat([
        sample_order_details_df,
        pd.DataFrame({
            "order_id": ["ONLY-DETAIL"],
            "amount": [100.0],
            "profit": [10.0],
            "quantity": [1],
            "category": ["Clothing"],
            "sub_category": ["Saree"],
        }),
    ], ignore_index=True)

    with caplog.at_level(logging.WARNING):
        merged = AnalyticsEngine.merge_orders(orders, details)

    assert "ONLY-HEADER" not in set(merged["order_id"])
    assert "ONLY-DETAIL" not in set(merged["order_id"])
    assert len(merged) == len(sample_order_details_df)
    assert "Unmatched records" in caplog.text
