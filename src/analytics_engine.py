"""Analytics engine for sales, profitability, target achievement, and regional performance.

Implements deterministic computational routines for Question 1:
- Order dataset merging with inner join semantics and cardinality audit logging (AC-1.2, AC-E6).
- Category sales, profitability, order-level average profit, and margin analysis (AC-1.3, AC-E2, AC-E5).
- Output dataclasses matching technical architecture contracts.
"""

from dataclasses import asdict, dataclass
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from src.data_loader import parse_target_date

# Setup module logger
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mandatory Column Sets
# ---------------------------------------------------------------------------

REQUIRED_ORDERS_COLUMNS: Set[str] = {
    "order_id",
    "order_date",
    "customer_name",
    "state",
    "city",
}

REQUIRED_DETAILS_COLUMNS: Set[str] = {
    "order_id",
    "amount",
    "profit",
    "quantity",
    "category",
    "sub_category",
}

REQUIRED_MERGED_COLUMNS: Set[str] = {
    "order_id",
    "category",
    "amount",
    "profit",
    "quantity",
}

REQUIRED_TARGETS_COLUMNS: Set[str] = {
    "month_of_order_date",
    "category",
    "target",
}

REQUIRED_ACTUALS_MERGED_COLUMNS: Set[str] = {
    "order_date",
    "category",
    "amount",
}

MERGED_OUTPUT_COLUMNS: List[str] = [
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

REQUIRED_STATE_ORDERS_COLUMNS: Set[str] = {
    "order_id",
    "state",
}

REQUIRED_STATE_MERGED_COLUMNS: Set[str] = {
    "order_id",
    "state",
    "amount",
    "profit",
}

REQUIRED_SUBCATEGORY_COLUMNS: Set[str] = {
    "order_id",
    "category",
    "sub_category",
    "amount",
    "profit",
    "quantity",
}

REQUIRED_CITY_MERGED_COLUMNS: Set[str] = {
    "order_id",
    "state",
    "city",
    "amount",
    "profit",
}


# ---------------------------------------------------------------------------
# Domain Dataclasses (Output Contracts)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CategoryPerformance:
    """Aggregated sales and profitability performance metrics for a product category."""

    category: str
    total_sales: float
    total_profit: float
    avg_profit_per_order: float
    profit_margin_pct: float
    distinct_orders: int
    total_quantity: int
    performance_rank: int

    def __post_init__(self) -> None:
        if not self.category or not str(self.category).strip():
            raise ValueError("category cannot be blank or whitespace")
        if self.distinct_orders < 0:
            raise ValueError(f"distinct_orders cannot be negative: {self.distinct_orders}")
        if self.total_quantity < 0:
            raise ValueError(f"total_quantity cannot be negative: {self.total_quantity}")
        if self.performance_rank < 1:
            raise ValueError(f"performance_rank must be >= 1, got {self.performance_rank}")

        # AC-E5: Zero-division guard; ARCHITECTURE contract validation
        expected_margin = (
            round((self.total_profit / self.total_sales) * 100, 2)
            if self.total_sales > 0
            else 0.0
        )
        if round(self.profit_margin_pct, 1) != round(expected_margin, 1):
            raise ValueError(
                f"Margin mismatch for category '{self.category}': "
                f"got {self.profit_margin_pct}, expected {expected_margin}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the record to a dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class FurnitureTargetAchievement:
    """Monthly target vs. actual achievement record for Furniture category."""

    month_key: str  # ISO YYYY-MM
    display_month: str  # e.g., 'Apr-18'
    target_sales: float
    actual_sales: float
    mom_target_pct_change: Optional[float]  # None for Apr-18 baseline
    mom_actual_pct_change: Optional[float]
    variance: float  # Actual - Target
    achievement_pct: float  # (Actual / Target) * 100
    is_significant_fluctuation: bool  # True if |mom_target_pct_change| >= 15.0%

    def __post_init__(self) -> None:
        if not self.month_key or not str(self.month_key).strip():
            raise ValueError("month_key cannot be blank or whitespace")
        if not self.display_month or not str(self.display_month).strip():
            raise ValueError("display_month cannot be blank or whitespace")
        if self.target_sales < 0:
            raise ValueError(f"target_sales cannot be negative: {self.target_sales}")
        if self.actual_sales < 0:
            raise ValueError(f"actual_sales cannot be negative: {self.actual_sales}")

        expected_variance = round(self.actual_sales - self.target_sales, 2)
        if abs(self.variance - expected_variance) > 0.05:
            raise ValueError(
                f"Variance mismatch for month '{self.display_month}': "
                f"got {self.variance}, expected {expected_variance}"
            )

        expected_achievement = (
            round((self.actual_sales / self.target_sales) * 100.0, 2)
            if self.target_sales > 0
            else 0.0
        )
        if abs(self.achievement_pct - expected_achievement) > 0.1:
            raise ValueError(
                f"Achievement % mismatch for month '{self.display_month}': "
                f"got {self.achievement_pct}, expected {expected_achievement}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the record to a dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class StatePerformance:
    """Regional performance and quadrant classification for top states."""

    rank: int
    state: str
    distinct_orders: int
    total_sales: float
    total_profit: float
    avg_profit_per_order: float
    profit_margin_pct: float
    quadrant: str  # 'High Volume / High Margin', 'High Volume / Low Margin', etc.

    def __post_init__(self) -> None:
        if self.rank < 1:
            raise ValueError(f"rank must be >= 1, got {self.rank}")
        if not self.state or not str(self.state).strip():
            raise ValueError("state cannot be blank or whitespace")
        if self.distinct_orders < 0:
            raise ValueError(f"distinct_orders cannot be negative: {self.distinct_orders}")

        expected_avg = (
            round(self.total_profit / self.distinct_orders, 2)
            if self.distinct_orders > 0
            else 0.0
        )
        if abs(self.avg_profit_per_order - expected_avg) > 0.05:
            raise ValueError(
                f"Average profit mismatch for state '{self.state}': "
                f"got {self.avg_profit_per_order}, expected {expected_avg}"
            )

        expected_margin = (
            round((self.total_profit / self.total_sales) * 100, 2)
            if self.total_sales > 0
            else 0.0
        )
        if abs(self.profit_margin_pct - expected_margin) > 0.05:
            raise ValueError(
                f"Margin mismatch for state '{self.state}': "
                f"got {self.profit_margin_pct}, expected {expected_margin}"
            )

        valid_quadrants = {
            "High Volume / High Margin",
            "High Volume / Low Margin",
            "Low Volume / High Margin",
            "Low Volume / Low Margin",
        }
        if self.quadrant not in valid_quadrants:
            raise ValueError(
                f"Invalid quadrant '{self.quadrant}'. Must be one of {sorted(valid_quadrants)}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the record to a dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class CityPerformance:
    """Aggregated sales and profitability metrics for a city within a state."""

    state: str
    city: str
    distinct_orders: int
    total_sales: float
    total_profit: float
    avg_profit_per_order: float
    profit_margin_pct: float

    def __post_init__(self) -> None:
        if not self.state or not str(self.state).strip():
            raise ValueError("state cannot be blank or whitespace")
        if not self.city or not str(self.city).strip():
            raise ValueError("city cannot be blank or whitespace")
        if self.distinct_orders < 0:
            raise ValueError(f"distinct_orders cannot be negative: {self.distinct_orders}")

        expected_avg = (
            round(self.total_profit / self.distinct_orders, 2)
            if self.distinct_orders > 0
            else 0.0
        )
        if abs(self.avg_profit_per_order - expected_avg) > 0.05:
            raise ValueError(
                f"Average profit mismatch for city '{self.city}': "
                f"got {self.avg_profit_per_order}, expected {expected_avg}"
            )

        expected_margin = (
            round((self.total_profit / self.total_sales) * 100, 2)
            if self.total_sales > 0
            else 0.0
        )
        if abs(self.profit_margin_pct - expected_margin) > 0.05:
            raise ValueError(
                f"Margin mismatch for city '{self.city}': "
                f"got {self.profit_margin_pct}, expected {expected_margin}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the record to a dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class SubCategoryPerformance:
    """Sales and profitability metrics for one (Category, Sub-Category) pair."""

    category: str
    sub_category: str
    total_sales: float
    total_profit: float
    profit_margin_pct: float
    distinct_orders: int
    total_quantity: int
    avg_order_value: float  # total_sales / distinct_orders
    avg_profit_per_order: float  # total_profit / distinct_orders

    def __post_init__(self) -> None:
        if not self.category or not str(self.category).strip():
            raise ValueError("category cannot be blank or whitespace")
        if not self.sub_category or not str(self.sub_category).strip():
            raise ValueError("sub_category cannot be blank or whitespace")
        if self.distinct_orders < 0:
            raise ValueError(f"distinct_orders cannot be negative: {self.distinct_orders}")
        if self.total_quantity < 0:
            raise ValueError(f"total_quantity cannot be negative: {self.total_quantity}")
        expected_margin = (
            round((self.total_profit / self.total_sales) * 100, 2)
            if self.total_sales > 0
            else 0.0
        )
        if abs(self.profit_margin_pct - expected_margin) > 0.05:
            raise ValueError(
                f"Margin mismatch for sub-category '{self.sub_category}': "
                f"got {self.profit_margin_pct}, expected {expected_margin}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the record to a dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class CityPriority:
    """A city flagged for action: 'Fix' (loss / low margin) or 'Scale' (high margin)."""

    action: str  # 'Fix' or 'Scale'
    state: str
    city: str
    total_sales: float
    total_profit: float
    profit_margin_pct: float
    profit_gap: float  # sales x overall margin - profit (positive = below average)
    in_top_states: bool
    reason: str

    def __post_init__(self) -> None:
        if self.action not in ("Fix", "Scale"):
            raise ValueError(f"action must be 'Fix' or 'Scale', got '{self.action}'")
        if not self.city or not str(self.city).strip():
            raise ValueError("city cannot be blank or whitespace")
        if not self.state or not str(self.state).strip():
            raise ValueError("state cannot be blank or whitespace")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the record to a dictionary."""
        return asdict(self)


def _rs(value: float) -> str:
    """Formats a rupee amount as 'Rs 4,011' (sign handled by the caller)."""
    return f"Rs {abs(value):,.0f}"


def _weighted_margin(sales: float, profit: float) -> float:
    """Profit margin % with zero-division guard."""
    return (profit / sales) * 100 if sales > 0 else 0.0


# ---------------------------------------------------------------------------
# AnalyticsEngine Class
# ---------------------------------------------------------------------------

class AnalyticsEngine:
    """Performs all deterministic aggregations and metrics for Question 1."""

    @staticmethod
    def merge_orders(
        orders_df: pd.DataFrame,
        details_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Inner joins orders and details on order_id, preserving line items and logging cardinality.

        Args:
            orders_df: Normalized orders header DataFrame (from DataLoader.load_orders).
            details_df: Normalized order details DataFrame (from DataLoader.load_order_details).

        Returns:
            pd.DataFrame: Merged transaction line items containing customer geography
                          and line item details.

        Raises:
            TypeError: If either input is not a pandas DataFrame.
            ValueError: If mandatory columns are missing from either DataFrame.
        """
        if not isinstance(orders_df, pd.DataFrame):
            raise TypeError(f"orders_df must be pd.DataFrame, got {type(orders_df).__name__}")
        if not isinstance(details_df, pd.DataFrame):
            raise TypeError(f"details_df must be pd.DataFrame, got {type(details_df).__name__}")

        missing_orders_cols = REQUIRED_ORDERS_COLUMNS - set(orders_df.columns)
        if missing_orders_cols:
            raise ValueError(
                f"orders_df is missing mandatory columns: {sorted(missing_orders_cols)}"
            )

        missing_details_cols = REQUIRED_DETAILS_COLUMNS - set(details_df.columns)
        if missing_details_cols:
            raise ValueError(
                f"details_df is missing mandatory columns: {sorted(missing_details_cols)}"
            )

        orders_count = len(orders_df)
        details_count = len(details_df)
        unique_orders_header = orders_df["order_id"].nunique()
        unique_orders_details = details_df["order_id"].nunique()

        logger.info(
            "Merging orders (%d rows, %d distinct orders) with details (%d rows, %d distinct orders) on 'order_id'",
            orders_count,
            unique_orders_header,
            details_count,
            unique_orders_details,
        )

        if orders_count == 0 or details_count == 0:
            logger.warning("One or both inputs are empty; returning empty merged DataFrame")
            return pd.DataFrame(columns=MERGED_OUTPUT_COLUMNS)

        # Inner join on order_id
        merged_df = pd.merge(orders_df, details_df, on="order_id", how="inner")

        merged_count = len(merged_df)
        unique_merged_orders = merged_df["order_id"].nunique()

        # AC-E6: Audit unmatched order IDs
        dropped_orders = unique_orders_header - unique_merged_orders
        unmatched_details_lines = details_count - merged_count
        if dropped_orders > 0 or unmatched_details_lines > 0:
            logger.warning(
                "Unmatched records detected in inner join: %d order headers dropped, %d detail line items dropped",
                dropped_orders,
                unmatched_details_lines,
            )

        logger.info(
            "Successfully merged orders: %d line items retained across %d distinct orders",
            merged_count,
            unique_merged_orders,
        )

        # Guarantee column ordering: primary standard columns first, plus any extra columns
        existing_cols = [c for c in MERGED_OUTPUT_COLUMNS if c in merged_df.columns]
        extra_cols = [c for c in merged_df.columns if c not in MERGED_OUTPUT_COLUMNS]
        return merged_df[existing_cols + extra_cols].copy()

    @staticmethod
    def compute_category_performance(
        merged_df: pd.DataFrame,
    ) -> List[CategoryPerformance]:
        """Computes sales, profit, order-level average profit, and margin % per Category.

        Follows ADR-004:
        Aggregates profit at (order_id, category) level first, then averages across
        distinct orders that purchased items in that category. Preserves negative profits
        for loss-making items (AC-E2) and provides zero-division safety (AC-E5).

        Args:
            merged_df: Merged transactions DataFrame containing ['order_id', 'category', 'amount', 'profit', 'quantity'].

        Returns:
            List[CategoryPerformance]: List of category metrics ranked by performance (descending profit margin %).

        Raises:
            TypeError: If merged_df is not a pandas DataFrame.
            ValueError: If mandatory columns are missing.
        """
        if not isinstance(merged_df, pd.DataFrame):
            raise TypeError(f"merged_df must be pd.DataFrame, got {type(merged_df).__name__}")

        if merged_df.empty:
            logger.warning("Empty DataFrame passed to compute_category_performance; returning empty list")
            return []

        missing_cols = REQUIRED_MERGED_COLUMNS - set(merged_df.columns)
        if missing_cols:
            raise ValueError(
                f"merged_df is missing mandatory columns for category analysis: {sorted(missing_cols)}"
            )

        categories = sorted(merged_df["category"].dropna().unique())
        if not categories:
            logger.warning("No valid categories found in merged_df; returning empty list")
            return []

        raw_metrics: List[Dict[str, Any]] = []

        for cat in categories:
            cat_df = merged_df[merged_df["category"] == cat]

            total_sales = float(cat_df["amount"].sum())
            total_profit = float(cat_df["profit"].sum())
            total_quantity = int(cat_df["quantity"].sum())

            # ADR-004: Group by (order_id, category) to calculate order-level category profit
            order_cat_profit = cat_df.groupby("order_id")["profit"].sum()
            distinct_orders = int(len(order_cat_profit))

            # Order-level average profit across distinct orders containing this category
            avg_profit_per_order = (
                float(order_cat_profit.mean()) if distinct_orders > 0 else 0.0
            )

            # AC-E5: Zero-division safety for margin % calculation
            profit_margin_pct = (
                round((total_profit / total_sales) * 100, 2)
                if total_sales > 0
                else 0.0
            )

            raw_metrics.append({
                "category": str(cat),
                "total_sales": round(total_sales, 2),
                "total_profit": round(total_profit, 2),
                "avg_profit_per_order": round(avg_profit_per_order, 2),
                "profit_margin_pct": profit_margin_pct,
                "distinct_orders": distinct_orders,
                "total_quantity": total_quantity,
            })

        # Rank categories primarily by profit_margin_pct descending, secondary by total_profit descending
        sorted_metrics = sorted(
            raw_metrics,
            key=lambda m: (m["profit_margin_pct"], m["total_profit"]),
            reverse=True,
        )

        results: List[CategoryPerformance] = []
        for rank, m in enumerate(sorted_metrics, start=1):
            record = CategoryPerformance(
                category=m["category"],
                total_sales=m["total_sales"],
                total_profit=m["total_profit"],
                avg_profit_per_order=m["avg_profit_per_order"],
                profit_margin_pct=m["profit_margin_pct"],
                distinct_orders=m["distinct_orders"],
                total_quantity=m["total_quantity"],
                performance_rank=rank,
            )
            results.append(record)

        logger.info(
            "Computed category performance for %d categories: %s",
            len(results),
            ", ".join(f"{r.category} (Rank {r.performance_rank}, Margin {r.profit_margin_pct}%)" for r in results),
        )

        return results

    # -----------------------------------------------------------------------
    # Helper Inspection Methods (AC-1.3 Item 5)
    # -----------------------------------------------------------------------

    @staticmethod
    def get_highest_sales_category(
        category_data: List[CategoryPerformance],
    ) -> CategoryPerformance:
        """Returns the category with the highest total sales volume."""
        if not category_data:
            raise ValueError("category_data list cannot be empty")
        return max(category_data, key=lambda c: c.total_sales)

    @staticmethod
    def get_highest_margin_category(
        category_data: List[CategoryPerformance],
    ) -> CategoryPerformance:
        """Returns the category with the highest profit margin percentage."""
        if not category_data:
            raise ValueError("category_data list cannot be empty")
        return max(category_data, key=lambda c: c.profit_margin_pct)

    @staticmethod
    def get_lowest_margin_category(
        category_data: List[CategoryPerformance],
    ) -> CategoryPerformance:
        """Returns the underperforming category with the lowest profit margin percentage."""
        if not category_data:
            raise ValueError("category_data list cannot be empty")
        return min(category_data, key=lambda c: c.profit_margin_pct)

    @staticmethod
    def get_highest_profit_category(
        category_data: List[CategoryPerformance],
    ) -> CategoryPerformance:
        """Returns the category with the highest total profit."""
        if not category_data:
            raise ValueError("category_data list cannot be empty")
        return max(category_data, key=lambda c: c.total_profit)

    # -----------------------------------------------------------------------
    # Question 1 Part 2: Furniture Target MoM Fluctuation & Reconciliation (M1-TASK-04)
    # -----------------------------------------------------------------------

    @staticmethod
    def compute_furniture_target_mom(
        targets_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        fluctuation_threshold_pct: float = 15.0,
    ) -> List[FurnitureTargetAchievement]:
        """Computes chronological MoM % change in Furniture sales target and reconciles with actuals.

        Implements SPEC AC-1.4, AC-E3, and ADR-005:
        1. Filters targets_df for Category == 'Furniture'.
        2. Normalizes target dates and sorts chronologically from Apr-18 through Mar-19.
        3. Baseline month (Apr-18) sets MoM % change to None/NaN with fluctuation flag False.
        4. Subsequent months compute MoM target change: ((Target_t - Target_{t-1}) / Target_{t-1}) * 100.
        5. Flags significant fluctuations where |MoM % change| >= fluctuation_threshold_pct (default: 15.0%).
        6. Aggregates monthly actual Furniture sales from merged_df (sum of line item amount).
        7. Computes monthly variance (Actual - Target) and achievement percentage ((Actual / Target) * 100).
        8. Returns List[FurnitureTargetAchievement] in chronological order.

        Args:
            targets_df: Sales targets DataFrame (from DataLoader.load_sales_targets).
            merged_df: Merged order line items DataFrame (from AnalyticsEngine.merge_orders).
            fluctuation_threshold_pct: Threshold percentage to flag significant MoM changes (default 15.0%).

        Returns:
            List[FurnitureTargetAchievement]: Chronological list of monthly target vs actual records.

        Raises:
            TypeError: If targets_df or merged_df is not a DataFrame, or threshold is not numeric.
            ValueError: If mandatory columns are missing, or threshold is negative.
        """
        if not isinstance(targets_df, pd.DataFrame):
            raise TypeError(f"targets_df must be pd.DataFrame, got {type(targets_df).__name__}")
        if not isinstance(merged_df, pd.DataFrame):
            raise TypeError(f"merged_df must be pd.DataFrame, got {type(merged_df).__name__}")
        if not isinstance(fluctuation_threshold_pct, (int, float)):
            raise TypeError(
                f"fluctuation_threshold_pct must be numeric, got {type(fluctuation_threshold_pct).__name__}"
            )
        if fluctuation_threshold_pct < 0:
            raise ValueError(
                f"fluctuation_threshold_pct cannot be negative: {fluctuation_threshold_pct}"
            )

        missing_targets = REQUIRED_TARGETS_COLUMNS - set(targets_df.columns)
        if missing_targets:
            raise ValueError(
                f"targets_df is missing mandatory columns: {sorted(missing_targets)}"
            )

        missing_merged = REQUIRED_ACTUALS_MERGED_COLUMNS - set(merged_df.columns)
        if missing_merged:
            raise ValueError(
                f"merged_df is missing mandatory columns: {sorted(missing_merged)}"
            )

        if targets_df.empty:
            logger.warning("targets_df is empty; returning empty list")
            return []

        # Filter for Furniture category (case-insensitive, whitespace-trimmed)
        furn_targets = targets_df[
            targets_df["category"].astype(str).str.strip().str.lower() == "furniture"
        ].copy()

        if furn_targets.empty:
            logger.warning("No Furniture category records found in targets_df; returning empty list")
            return []

        # Parse month_of_order_date into normalized pd.Timestamp (1st of month)
        furn_targets["parsed_date"] = furn_targets["month_of_order_date"].apply(parse_target_date)

        # Aggregate if multiple entries for the same month exist, and sort chronologically
        monthly_targets = (
            furn_targets.groupby("parsed_date", as_index=False)["target"]
            .sum()
            .sort_values("parsed_date")
            .reset_index(drop=True)
        )

        # Aggregate actual Furniture sales per month from merged_df
        actual_by_month: Dict[str, float] = {}
        if not merged_df.empty:
            furn_merged = merged_df[
                merged_df["category"].astype(str).str.strip().str.lower() == "furniture"
            ].copy()
            if not furn_merged.empty:
                order_dates = pd.to_datetime(furn_merged["order_date"], errors="coerce")
                valid_mask = order_dates.notna()
                if valid_mask.any():
                    furn_merged = furn_merged[valid_mask].copy()
                    furn_merged["month_key"] = order_dates[valid_mask].dt.strftime("%Y-%m")
                    monthly_actuals_series = furn_merged.groupby("month_key")["amount"].sum()
                    actual_by_month = {k: float(v) for k, v in monthly_actuals_series.items()}

        results: List[FurnitureTargetAchievement] = []
        target_sales_history: List[float] = []
        actual_sales_history: List[float] = []

        for idx, row in monthly_targets.iterrows():
            dt: pd.Timestamp = row["parsed_date"]
            month_key = dt.strftime("%Y-%m")
            display_month = dt.strftime("%b-%y")
            target_sales = round(float(row["target"]), 2)
            actual_sales = round(float(actual_by_month.get(month_key, 0.0)), 2)

            # MoM target % change: baseline month is None; subsequent months ((Target_t - Target_{t-1}) / Target_{t-1}) * 100
            if idx == 0:
                mom_target_pct: Optional[float] = None
                mom_actual_pct: Optional[float] = None
                is_fluctuation = False
            else:
                prev_target = target_sales_history[-1]
                if prev_target > 0:
                    mom_target_pct = round(((target_sales - prev_target) / prev_target) * 100.0, 2)
                else:
                    mom_target_pct = 0.0

                is_fluctuation = bool(abs(mom_target_pct) >= fluctuation_threshold_pct)

                prev_actual = actual_sales_history[-1]
                if prev_actual > 0:
                    mom_actual_pct = round(((actual_sales - prev_actual) / prev_actual) * 100.0, 2)
                elif prev_actual == 0.0 and actual_sales == 0.0:
                    mom_actual_pct = 0.0
                else:
                    mom_actual_pct = None

            variance = round(actual_sales - target_sales, 2)
            achievement_pct = (
                round((actual_sales / target_sales) * 100.0, 2)
                if target_sales > 0
                else 0.0
            )

            record = FurnitureTargetAchievement(
                month_key=month_key,
                display_month=display_month,
                target_sales=target_sales,
                actual_sales=actual_sales,
                mom_target_pct_change=mom_target_pct,
                mom_actual_pct_change=mom_actual_pct,
                variance=variance,
                achievement_pct=achievement_pct,
                is_significant_fluctuation=is_fluctuation,
            )

            results.append(record)
            target_sales_history.append(target_sales)
            actual_sales_history.append(actual_sales)

        logger.info(
            "Computed furniture target MoM reconciliation for %d months (%s to %s). Fluctuation count: %d",
            len(results),
            results[0].display_month if results else "N/A",
            results[-1].display_month if results else "N/A",
            sum(1 for r in results if r.is_significant_fluctuation),
        )

        return results

    # -----------------------------------------------------------------------
    # Helper Inspection Methods for Target Reconciliation (AC-1.4)
    # -----------------------------------------------------------------------

    @staticmethod
    def get_fluctuating_target_months(
        records: List[FurnitureTargetAchievement],
    ) -> List[FurnitureTargetAchievement]:
        """Returns months flagged with significant MoM target fluctuations (|MoM| >= threshold)."""
        return [r for r in records if r.is_significant_fluctuation]

    @staticmethod
    def get_achieved_target_months(
        records: List[FurnitureTargetAchievement],
    ) -> List[FurnitureTargetAchievement]:
        """Returns months where actual Furniture sales met or exceeded the sales target (variance >= 0)."""
        return [r for r in records if r.variance >= 0]

    @staticmethod
    def get_unachieved_target_months(
        records: List[FurnitureTargetAchievement],
    ) -> List[FurnitureTargetAchievement]:
        """Returns months where actual Furniture sales fell short of the sales target (variance < 0)."""
        return [r for r in records if r.variance < 0]

    # -----------------------------------------------------------------------
    # Question 1 Part 3: Regional Performance & Quadrant Classification (M1-TASK-05)
    # -----------------------------------------------------------------------

    @staticmethod
    def classify_state_quadrant(
        distinct_orders: int,
        profit_margin_pct: float,
        volume_benchmark: float,
        margin_benchmark: float,
        inclusive: bool = False,
    ) -> str:
        """Classifies a state into one of four strategic quadrants relative to benchmarks.

        Quadrants:
        - 'High Volume / High Margin'
        - 'High Volume / Low Margin'
        - 'Low Volume / High Margin'
        - 'Low Volume / Low Margin'

        Args:
            distinct_orders: Distinct order count for the state.
            profit_margin_pct: Overall profit margin percentage for the state.
            volume_benchmark: Benchmark threshold for order volume (e.g., median volume).
            margin_benchmark: Benchmark threshold for profit margin (e.g., median margin).
            inclusive: If True, uses >= for 'High'; if False (default for top-N median splitting),
                       uses > for 'High'.

        Returns:
            str: Performance quadrant label.
        """
        is_high_volume = (
            distinct_orders >= volume_benchmark if inclusive else distinct_orders > volume_benchmark
        )
        is_high_margin = (
            profit_margin_pct >= margin_benchmark if inclusive else profit_margin_pct > margin_benchmark
        )

        if is_high_volume and is_high_margin:
            return "High Volume / High Margin"
        elif is_high_volume and not is_high_margin:
            return "High Volume / Low Margin"
        elif not is_high_volume and is_high_margin:
            return "Low Volume / High Margin"
        else:
            return "Low Volume / Low Margin"

    @staticmethod
    def compute_top_states_performance(
        orders_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        top_n: int = 5,
        volume_benchmark: Optional[float] = None,
        margin_benchmark: Optional[float] = None,
        inclusive: bool = False,
    ) -> List[StatePerformance]:
        """Ranks top states by distinct order volume and evaluates regional profitability metrics.

        Implements SPEC AC-1.5, AC-E2, AC-E5, and ADR-006:
        1. Ranks states by distinct order_id count in orders_df and selects top_n states (default: 5).
        2. Aggregates distinct orders, total sales, total profit, average profit per distinct order,
           and profit margin % for each top state.
        3. Preserves negative profits (e.g. loss-making regions like Punjab) and guards against zero-division.
        4. Calculates median volume and margin across top_n states (or uses custom benchmarks) to
           categorize states into 4 strategic performance quadrants.
        5. Returns List[StatePerformance] ordered by rank (1 to top_n).

        Args:
            orders_df: Normalized orders header DataFrame (from DataLoader.load_orders).
            merged_df: Merged order line items DataFrame (from AnalyticsEngine.merge_orders).
            top_n: Number of top states to return by distinct order volume (default: 5).
            volume_benchmark: Optional custom volume cutoff for quadrant classification.
            margin_benchmark: Optional custom margin cutoff for quadrant classification.
            inclusive: Whether benchmark threshold comparison uses >= (True) or > (False).

        Returns:
            List[StatePerformance]: Ranked list of state performance records.

        Raises:
            TypeError: If inputs are not pd.DataFrames or top_n is not an integer.
            ValueError: If mandatory columns are missing or top_n < 1.
        """
        if not isinstance(orders_df, pd.DataFrame):
            raise TypeError(f"orders_df must be pd.DataFrame, got {type(orders_df).__name__}")
        if not isinstance(merged_df, pd.DataFrame):
            raise TypeError(f"merged_df must be pd.DataFrame, got {type(merged_df).__name__}")
        if not isinstance(top_n, int):
            raise TypeError(f"top_n must be an integer, got {type(top_n).__name__}")
        if top_n < 1:
            raise ValueError(f"top_n must be >= 1, got {top_n}")

        missing_orders = REQUIRED_STATE_ORDERS_COLUMNS - set(orders_df.columns)
        if missing_orders:
            raise ValueError(
                f"orders_df is missing mandatory columns for state analysis: {sorted(missing_orders)}"
            )

        missing_merged = REQUIRED_STATE_MERGED_COLUMNS - set(merged_df.columns)
        if missing_merged:
            raise ValueError(
                f"merged_df is missing mandatory columns for state analysis: {sorted(missing_merged)}"
            )

        if orders_df.empty or merged_df.empty:
            logger.warning(
                "Empty orders_df or merged_df provided to compute_top_states_performance; returning empty list"
            )
            return []

        # Clean state names
        clean_orders = orders_df.dropna(subset=["state", "order_id"]).copy()
        clean_orders["state"] = clean_orders["state"].astype(str).str.strip()
        clean_orders = clean_orders[clean_orders["state"] != ""]

        clean_merged = merged_df.dropna(subset=["state"]).copy()
        clean_merged["state"] = clean_merged["state"].astype(str).str.strip()

        if clean_orders.empty:
            logger.warning("No valid states found in orders_df; returning empty list")
            return []

        # Count distinct order_id per state from orders_df
        # Secondary sort by total sales in merged_df descending to deterministically break any order count ties
        sales_by_state = clean_merged.groupby("state")["amount"].sum().to_dict()
        order_counts_df = (
            clean_orders.groupby("state")["order_id"]
            .nunique()
            .reset_index(name="distinct_orders")
        )
        order_counts_df["total_sales_tiebreak"] = order_counts_df["state"].map(sales_by_state).fillna(0.0)
        order_counts_df = order_counts_df.sort_values(
            by=["distinct_orders", "total_sales_tiebreak", "state"],
            ascending=[False, False, True],
        ).reset_index(drop=True)

        selected_states = order_counts_df.head(top_n)

        raw_metrics: List[Dict[str, Any]] = []
        for _, row in selected_states.iterrows():
            st_name = str(row["state"])
            dist_orders = int(row["distinct_orders"])

            st_merged = clean_merged[clean_merged["state"] == st_name]
            st_sales = round(float(st_merged["amount"].sum()), 2)
            st_profit = round(float(st_merged["profit"].sum()), 2)

            st_avg_profit = (
                round(st_profit / dist_orders, 2)
                if dist_orders > 0
                else 0.0
            )

            st_margin = (
                round((st_profit / st_sales) * 100, 2)
                if st_sales > 0
                else 0.0
            )

            raw_metrics.append({
                "state": st_name,
                "distinct_orders": dist_orders,
                "total_sales": st_sales,
                "total_profit": st_profit,
                "avg_profit_per_order": st_avg_profit,
                "profit_margin_pct": st_margin,
            })

        if not raw_metrics:
            return []

        # Determine volume and margin benchmarks for quadrant classification
        effective_vol_benchmark = (
            float(volume_benchmark)
            if volume_benchmark is not None
            else float(np.median([r["distinct_orders"] for r in raw_metrics]))
        )
        effective_mar_benchmark = (
            float(margin_benchmark)
            if margin_benchmark is not None
            else float(np.median([r["profit_margin_pct"] for r in raw_metrics]))
        )

        results: List[StatePerformance] = []
        for rank, r in enumerate(raw_metrics, start=1):
            quadrant = AnalyticsEngine.classify_state_quadrant(
                distinct_orders=r["distinct_orders"],
                profit_margin_pct=r["profit_margin_pct"],
                volume_benchmark=effective_vol_benchmark,
                margin_benchmark=effective_mar_benchmark,
                inclusive=inclusive,
            )

            record = StatePerformance(
                rank=rank,
                state=r["state"],
                distinct_orders=r["distinct_orders"],
                total_sales=r["total_sales"],
                total_profit=r["total_profit"],
                avg_profit_per_order=r["avg_profit_per_order"],
                profit_margin_pct=r["profit_margin_pct"],
                quadrant=quadrant,
            )
            results.append(record)

        logger.info(
            "Computed regional performance for top %d states (Median Volume: %.1f, Median Margin: %.2f%%): %s",
            len(results),
            effective_vol_benchmark,
            effective_mar_benchmark,
            ", ".join(
                f"{s.state} (Rank {s.rank}, {s.distinct_orders} orders, {s.profit_margin_pct}%, {s.quadrant})"
                for s in results
            ),
        )

        return results

    # -----------------------------------------------------------------------
    # Helper Inspection Methods for Regional Performance (AC-1.5)
    # -----------------------------------------------------------------------

    @staticmethod
    def get_highest_sales_state(
        state_data: List[StatePerformance],
    ) -> StatePerformance:
        """Returns the state with the highest total sales volume."""
        if not state_data:
            raise ValueError("state_data list cannot be empty")
        return max(state_data, key=lambda s: s.total_sales)

    @staticmethod
    def get_highest_profit_state(
        state_data: List[StatePerformance],
    ) -> StatePerformance:
        """Returns the state with the highest total profit."""
        if not state_data:
            raise ValueError("state_data list cannot be empty")
        return max(state_data, key=lambda s: s.total_profit)

    @staticmethod
    def get_highest_margin_state(
        state_data: List[StatePerformance],
    ) -> StatePerformance:
        """Returns the state with the highest profit margin percentage."""
        if not state_data:
            raise ValueError("state_data list cannot be empty")
        return max(state_data, key=lambda s: s.profit_margin_pct)

    @staticmethod
    def get_lowest_margin_state(
        state_data: List[StatePerformance],
    ) -> StatePerformance:
        """Returns the state with the lowest profit margin percentage."""
        if not state_data:
            raise ValueError("state_data list cannot be empty")
        return min(state_data, key=lambda s: s.profit_margin_pct)

    @staticmethod
    def get_states_by_quadrant(
        state_data: List[StatePerformance],
        quadrant: str,
    ) -> List[StatePerformance]:
        """Filters states matching a specific strategic quadrant."""
        return [s for s in state_data if s.quadrant == quadrant]

    # -----------------------------------------------------------------------
    # City Breakdown Helper Methods (Question 1 Part 3 Deep-Dive)
    # -----------------------------------------------------------------------

    @staticmethod
    def compute_city_performance(
        merged_df: pd.DataFrame,
        state: Optional[str] = None,
    ) -> List[CityPerformance]:
        """Computes city-level sales, profitability, and margin performance within states.

        Args:
            merged_df: Merged order line items DataFrame containing ['order_id', 'state', 'city', 'amount', 'profit'].
            state: Optional state name to filter city results (case-insensitive).

        Returns:
            List[CityPerformance]: List of city performance records sorted by total sales descending.

        Raises:
            TypeError: If merged_df is not a DataFrame.
            ValueError: If mandatory columns are missing.
        """
        if not isinstance(merged_df, pd.DataFrame):
            raise TypeError(f"merged_df must be pd.DataFrame, got {type(merged_df).__name__}")

        if merged_df.empty:
            logger.warning("Empty merged_df passed to compute_city_performance; returning empty list")
            return []

        missing_cols = REQUIRED_CITY_MERGED_COLUMNS - set(merged_df.columns)
        if missing_cols:
            raise ValueError(
                f"merged_df is missing mandatory columns for city analysis: {sorted(missing_cols)}"
            )

        clean_df = merged_df.dropna(subset=["state", "city"]).copy()
        clean_df["state"] = clean_df["state"].astype(str).str.strip()
        clean_df["city"] = clean_df["city"].astype(str).str.strip()
        clean_df = clean_df[(clean_df["state"] != "") & (clean_df["city"] != "")]

        if clean_df.empty:
            return []

        if state is not None:
            clean_state = str(state).strip().lower()
            clean_df = clean_df[clean_df["state"].str.lower() == clean_state]
            if clean_df.empty:
                logger.warning("No records found for state '%s'; returning empty list", state)
                return []

        grouped = clean_df.groupby(["state", "city"], as_index=False).agg(
            distinct_orders=("order_id", "nunique"),
            total_sales=("amount", "sum"),
            total_profit=("profit", "sum"),
        )

        results: List[CityPerformance] = []
        sorted_grouped = grouped.sort_values(
            by=["total_sales", "total_profit"], ascending=[False, False]
        )

        for _, row in sorted_grouped.iterrows():
            st = str(row["state"])
            ct = str(row["city"])
            orders_cnt = int(row["distinct_orders"])
            sales = round(float(row["total_sales"]), 2)
            profit = round(float(row["total_profit"]), 2)
            avg_profit = round(profit / orders_cnt, 2) if orders_cnt > 0 else 0.0
            margin = round((profit / sales) * 100, 2) if sales > 0 else 0.0

            results.append(
                CityPerformance(
                    state=st,
                    city=ct,
                    distinct_orders=orders_cnt,
                    total_sales=sales,
                    total_profit=profit,
                    avg_profit_per_order=avg_profit,
                    profit_margin_pct=margin,
                )
            )

        return results

    @staticmethod
    def get_loss_making_cities(
        city_data: List[CityPerformance],
    ) -> List[CityPerformance]:
        """Returns cities with negative total profit, sorted from largest loss to smallest."""
        loss_cities = [c for c in city_data if c.total_profit < 0]
        return sorted(loss_cities, key=lambda c: c.total_profit)

    @staticmethod
    def get_top_performing_cities(
        city_data: List[CityPerformance],
        top_n: int = 5,
    ) -> List[CityPerformance]:
        """Returns top performing cities ranked by profit margin percentage descending."""
        return sorted(city_data, key=lambda c: c.profit_margin_pct, reverse=True)[:top_n]

    # -----------------------------------------------------------------------
    # Question 1 Deep-Dive: Sub-Categories, Target Alignment, City Priorities
    # -----------------------------------------------------------------------

    @staticmethod
    def compute_subcategory_performance(
        merged_df: pd.DataFrame,
    ) -> List[SubCategoryPerformance]:
        """Aggregates sales, profit, margin % and orders per (Category, Sub-Category).

        Loss-making sub-categories are kept (negative profit and margin preserved).

        Returns:
            List[SubCategoryPerformance]: Sorted by category, then margin descending.

        Raises:
            TypeError: If merged_df is not a DataFrame.
            ValueError: If mandatory columns are missing.
        """
        if not isinstance(merged_df, pd.DataFrame):
            raise TypeError(f"merged_df must be pd.DataFrame, got {type(merged_df).__name__}")
        if merged_df.empty:
            logger.warning("Empty merged_df passed to compute_subcategory_performance; returning empty list")
            return []
        missing = REQUIRED_SUBCATEGORY_COLUMNS - set(merged_df.columns)
        if missing:
            raise ValueError(
                f"merged_df is missing mandatory columns for sub-category analysis: {sorted(missing)}"
            )

        clean = merged_df.dropna(subset=["category", "sub_category"]).copy()
        clean["category"] = clean["category"].astype(str).str.strip()
        clean["sub_category"] = clean["sub_category"].astype(str).str.strip()
        clean = clean[(clean["category"] != "") & (clean["sub_category"] != "")]
        if clean.empty:
            return []

        grouped = clean.groupby(["category", "sub_category"], as_index=False).agg(
            total_sales=("amount", "sum"),
            total_profit=("profit", "sum"),
            distinct_orders=("order_id", "nunique"),
            total_quantity=("quantity", "sum"),
        )

        results: List[SubCategoryPerformance] = []
        for _, row in grouped.iterrows():
            sales = round(float(row["total_sales"]), 2)
            profit = round(float(row["total_profit"]), 2)
            orders = int(row["distinct_orders"])
            results.append(
                SubCategoryPerformance(
                    category=str(row["category"]),
                    sub_category=str(row["sub_category"]),
                    total_sales=sales,
                    total_profit=profit,
                    profit_margin_pct=round(_weighted_margin(sales, profit), 2),
                    distinct_orders=orders,
                    total_quantity=int(row["total_quantity"]),
                    avg_order_value=round(sales / orders, 2) if orders > 0 else 0.0,
                    avg_profit_per_order=round(profit / orders, 2) if orders > 0 else 0.0,
                )
            )
        results.sort(key=lambda s: (s.category, -s.profit_margin_pct))
        logger.info("Computed sub-category performance for %d sub-categories", len(results))
        return results

    @staticmethod
    def compute_target_alignment(
        furniture_data: List[FurnitureTargetAchievement],
        window: int = 3,
    ) -> Dict[str, Any]:
        """Quantifies how far a flat target ramp is from seasonal actuals.

        Computes the half-year split (first vs second half of the months given),
        a seasonal re-phasing of the annual target, the error of a rolling
        ``window``-month baseline versus the flat ramp, and quarterly achievement.

        Returns:
            Dict[str, Any]: Supporting numbers, or {} if fewer than window + 1 months.
        """
        if not isinstance(window, int) or window < 1:
            raise ValueError(f"window must be a positive integer, got {window!r}")
        recs = list(furniture_data or [])
        if len(recs) < window + 1:
            logger.warning("Not enough months (%d) for target alignment analysis", len(recs))
            return {}

        actual = [r.actual_sales for r in recs]
        target = [r.target_sales for r in recs]
        half = len(recs) // 2
        h1, h2 = recs[:half], recs[half:]
        h1_act, h2_act = sum(actual[:half]), sum(actual[half:])
        h1_tgt, h2_tgt = sum(target[:half]), sum(target[half:])
        annual_act, annual_tgt = h1_act + h2_act, h1_tgt + h2_tgt
        h2_act_share = h2_act / annual_act * 100 if annual_act > 0 else 0.0
        h2_tgt_share = h2_tgt / annual_tgt * 100 if annual_tgt > 0 else 0.0

        flat_err = [abs(target[i] - actual[i]) for i in range(window, len(recs))]
        roll_err = [
            abs(sum(actual[i - window:i]) / window - actual[i]) for i in range(window, len(recs))
        ]
        flat_mae = sum(flat_err) / len(flat_err)
        roll_mae = sum(roll_err) / len(roll_err)

        quarters: List[Dict[str, Any]] = []
        for i in range(0, len(recs), 3):
            chunk = recs[i:i + 3]
            q_t = sum(r.target_sales for r in chunk)
            q_a = sum(r.actual_sales for r in chunk)
            quarters.append({
                "label": f"{chunk[0].display_month} to {chunk[-1].display_month}",
                "target": round(q_t, 2),
                "actual": round(q_a, 2),
                "achievement_pct": round(q_a / q_t * 100, 2) if q_t > 0 else 0.0,
            })

        moms = [r.mom_target_pct_change for r in recs if r.mom_target_pct_change is not None]
        low = min(recs, key=lambda r: r.actual_sales)
        high = max(recs, key=lambda r: r.actual_sales)
        return {
            "months": len(recs),
            "months_met": sum(1 for r in recs if r.variance >= 0),
            "first_target": target[0],
            "last_target": target[-1],
            "avg_target_mom_pct": round(sum(moms) / len(moms), 2) if moms else 0.0,
            "low_actual": low.actual_sales,
            "low_month": low.display_month,
            "high_actual": high.actual_sales,
            "high_month": high.display_month,
            "h1_label": f"{h1[0].display_month} to {h1[-1].display_month}",
            "h2_label": f"{h2[0].display_month} to {h2[-1].display_month}",
            "h1_months": len(h1),
            "h2_months": len(h2),
            "h1_actual": round(h1_act, 2),
            "h2_actual": round(h2_act, 2),
            "h1_target": round(h1_tgt, 2),
            "h2_target": round(h2_tgt, 2),
            "h1_achievement_pct": round(h1_act / h1_tgt * 100, 2) if h1_tgt > 0 else 0.0,
            "h2_achievement_pct": round(h2_act / h2_tgt * 100, 2) if h2_tgt > 0 else 0.0,
            "h2_actual_share_pct": round(h2_act_share, 2),
            "h2_target_share_pct": round(h2_tgt_share, 2),
            "annual_target": round(annual_tgt, 2),
            "annual_actual": round(annual_act, 2),
            "seasonal_h1_monthly_target": round(annual_tgt * (100 - h2_act_share) / 100 / len(h1), 2),
            "seasonal_h2_monthly_target": round(annual_tgt * h2_act_share / 100 / len(h2), 2),
            "rolling_window": window,
            "rolling_eval_label": f"{recs[window].display_month} to {recs[-1].display_month}",
            "flat_ramp_mae": round(flat_mae, 2),
            "rolling_mae": round(roll_mae, 2),
            "mae_reduction_pct": round((1 - roll_mae / flat_mae) * 100, 2) if flat_mae > 0 else 0.0,
            "latest_rolling_baseline": round(sum(actual[-window:]) / window, 2),
            "quarters": quarters,
        }

    @staticmethod
    def compute_city_priorities(
        merged_df: pd.DataFrame,
        state_data: List[StatePerformance],
        fix_n: int = 4,
        scale_n: int = 2,
    ) -> List[CityPriority]:
        """Names the cities to fix (loss / below-average margin) and to scale.

        - Fix: cities in the top states ranked by profit gap, i.e. how much profit
          they fall short of the overall margin (sales x overall margin - profit).
          The worst city outside the top states is added if its gap is larger.
        - Scale: cities with at least median city sales and above-average margin,
          ranked by total profit.

        Returns:
            List[CityPriority]: Fix cities first (largest gap first), then Scale cities.
        """
        if not isinstance(fix_n, int) or not isinstance(scale_n, int) or fix_n < 0 or scale_n < 0:
            raise ValueError("fix_n and scale_n must be non-negative integers")
        cities = AnalyticsEngine.compute_city_performance(merged_df)
        if not cities:
            return []

        total_sales = sum(c.total_sales for c in cities)
        overall = _weighted_margin(total_sales, sum(c.total_profit for c in cities))
        top_states = {s.state for s in (state_data or [])}
        median_sales = float(np.median([c.total_sales for c in cities]))
        state_sales: Dict[str, float] = {}
        for c in cities:
            state_sales[c.state] = state_sales.get(c.state, 0.0) + c.total_sales

        sub_profit: Dict[Tuple[str, str], pd.Series] = {}
        if "sub_category" in merged_df.columns:
            clean = merged_df.dropna(subset=["state", "city", "sub_category"]).copy()
            for col in ("state", "city", "sub_category"):
                clean[col] = clean[col].astype(str).str.strip()
            for (st, ct), grp in clean.groupby(["state", "city"]):
                sub_profit[(st, ct)] = grp.groupby("sub_category")["profit"].sum().sort_values()

        def gap(c: CityPerformance) -> float:
            return c.total_sales * overall / 100 - c.total_profit

        def signed(v: float) -> str:
            return f"-{_rs(v)}" if v < 0 else _rs(v)

        def fix_reason(c: CityPerformance, outside: bool) -> str:
            subs = sub_profit.get((c.state, c.city))
            drag = ""
            if subs is not None and not subs.empty:
                word = "biggest drag" if subs.iloc[0] < 0 else "weakest line"
                drag = f"; {word} is {subs.index[0]} ({signed(float(subs.iloc[0]))})"
            prefix = f"Worst city outside the top states ({c.state}): " if outside else ""
            if c.total_profit < 0:
                body = (
                    f"loses {_rs(c.total_profit)} on {_rs(c.total_sales)} of sales "
                    f"({c.profit_margin_pct:.1f}% margin)"
                )
            else:
                share = c.total_sales / state_sales[c.state] * 100 if state_sales.get(c.state) else 0.0
                body = (
                    f"{share:.0f}% of {c.state} sales but only {c.profit_margin_pct:.1f}% margin "
                    f"vs {overall:.1f}% overall"
                )
            text = prefix + body + drag + "."
            return text[0].upper() + text[1:]

        def scale_reason(c: CityPerformance) -> str:
            subs = sub_profit.get((c.state, c.city))
            lead = ""
            if subs is not None and not subs.empty:
                lead = f", led by {subs.index[-1]} ({signed(float(subs.iloc[-1]))} profit)"
            return (
                f"{c.profit_margin_pct:.1f}% margin on {_rs(c.total_sales)} of sales{lead}; "
                "add volume here."
            )

        def make(c: CityPerformance, action: str, reason: str) -> CityPriority:
            return CityPriority(
                action=action, state=c.state, city=c.city,
                total_sales=c.total_sales, total_profit=c.total_profit,
                profit_margin_pct=c.profit_margin_pct, profit_gap=round(gap(c), 2),
                in_top_states=c.state in top_states, reason=reason,
            )

        below = [c for c in cities if c.profit_margin_pct < overall and gap(c) > 0]
        fix_in = sorted([c for c in below if c.state in top_states], key=gap, reverse=True)[:fix_n]
        outside = sorted([c for c in below if c.state not in top_states], key=gap, reverse=True)
        results = [make(c, "Fix", fix_reason(c, False)) for c in fix_in]
        if outside and (not fix_in or gap(outside[0]) > gap(fix_in[0])):
            results.append(make(outside[0], "Fix", fix_reason(outside[0], True)))

        scale = sorted(
            [c for c in cities if c.total_sales >= median_sales and c.profit_margin_pct > overall],
            key=lambda c: c.total_profit, reverse=True,
        )[:scale_n]
        results.extend(make(c, "Scale", scale_reason(c)) for c in scale)
        logger.info(
            "City priorities: %s",
            ", ".join(f"{p.action} {p.city} ({p.state})" for p in results),
        )
        return results

    @staticmethod
    def build_q1_insights(
        category_data: List[CategoryPerformance],
        subcategory_data: List[SubCategoryPerformance],
        furniture_data: List[FurnitureTargetAchievement],
        state_data: List[StatePerformance],
        city_priorities: List[CityPriority],
    ) -> Dict[str, Any]:
        """Builds the data-driven Q1 narrative shared by the PDF and the dashboard.

        Every number in the text is computed from the inputs. Sections with no
        input data are returned as empty lists / strings.

        Returns:
            Dict[str, Any]: Keys part1_reasons, part1_recommendations, part2_diagnosis,
            part2_strategies, part3_disparities, exec_part1, exec_part2, exec_part3.
        """
        cats = list(category_data or [])
        subs = list(subcategory_data or [])
        states = sorted(state_data or [], key=lambda s: s.rank)
        prios = list(city_priorities or [])
        out: Dict[str, Any] = {
            "part1_reasons": [], "part1_recommendations": [],
            "part2_diagnosis": "", "part2_strategies": [],
            "part3_disparities": [],
            "exec_part1": "", "exec_part2": "", "exec_part3": "",
        }

        def signed(v: float) -> str:
            return f"-{_rs(v)}" if v < 0 else _rs(v)

        # ---------------- Part 1: why categories differ ----------------
        if cats:
            weak = min(cats, key=lambda c: c.profit_margin_pct)
            strong = max(cats, key=lambda c: c.profit_margin_pct)
            best_ppo = max(cats, key=lambda c: c.avg_profit_per_order)
            cat_margin = {c.category: c.profit_margin_pct for c in cats}
            cat_sales = {c.category: c.total_sales for c in cats}
            overall = _weighted_margin(
                sum(c.total_sales for c in cats), sum(c.total_profit for c in cats)
            )
            weak_subs = [s for s in subs if s.category == weak.category]
            worst = min(weak_subs, key=lambda s: s.total_profit) if weak_subs else None
            reasons: List[str] = []
            recs: List[str] = []
            be_margin = weak.profit_margin_pct
            if worst is not None and worst.total_profit < 0:
                be_margin = _weighted_margin(weak.total_sales, weak.total_profit - worst.total_profit)
                reasons.append(
                    f"{weak.category} has the thinnest margin ({weak.profit_margin_pct:.1f}%): "
                    f"{worst.sub_category} loses {_rs(worst.total_profit)} on {_rs(worst.total_sales)} "
                    f"of sales ({worst.profit_margin_pct:.1f}% margin). At break-even on "
                    f"{worst.sub_category}, {weak.category} would earn {be_margin:.1f}%."
                )
            elif worst is not None:
                reasons.append(
                    f"{weak.category} has the thinnest margin ({weak.profit_margin_pct:.1f}%); its "
                    f"weakest line is {worst.sub_category} ({worst.profit_margin_pct:.1f}%)."
                )
            thin = sorted(
                [s for s in subs if s is not worst and s.profit_margin_pct < overall / 2],
                key=lambda s: s.profit_margin_pct,
            )
            if thin:
                text = (
                    f"Other lines below half the {overall:.1f}% average margin: "
                    + ", ".join(
                        f"{s.sub_category} ({s.category}, {s.profit_margin_pct:.1f}%)" for s in thin
                    )
                    + "."
                )
                big = max(thin, key=lambda s: s.total_sales)
                big_cat_sales = cat_sales.get(big.category, 0.0)
                share = big.total_sales / big_cat_sales * 100 if big_cat_sales > 0 else 0.0
                if share >= 25 and big.category in cat_margin:
                    text += (
                        f" {big.sub_category} is {share:.0f}% of {big.category} sales, holding "
                        f"{big.category} to {cat_margin[big.category]:.1f}%."
                    )
                reasons.append(text)
            if len(subs) >= 2:
                median_aov = float(np.median([s.avg_order_value for s in subs]))
                high = [s for s in subs if s.avg_order_value > median_aov]
                low = [s for s in subs if s.avg_order_value <= median_aov]
                if high and low:
                    h_sales = sum(s.total_sales for s in high)
                    l_sales = sum(s.total_sales for s in low)
                    h_m = _weighted_margin(h_sales, sum(s.total_profit for s in high))
                    l_m = _weighted_margin(l_sales, sum(s.total_profit for s in low))
                    h_ex = ", ".join(
                        s.sub_category for s in sorted(high, key=lambda s: s.profit_margin_pct)[:2]
                    )
                    l_ex = ", ".join(
                        s.sub_category for s in sorted(low, key=lambda s: -s.profit_margin_pct)[:2]
                    )
                    reasons.append(
                        f"Ticket size: high-ticket lines (average order above {_rs(median_aov)}, "
                        f"e.g. {h_ex}) are {h_sales / (h_sales + l_sales) * 100:.0f}% of sales at "
                        f"{h_m:.1f}% margin; low-ticket lines (e.g. {l_ex}) earn {l_m:.1f}%."
                    )
            ppo_text = (
                f"Profit per order: {best_ppo.category} {_rs(best_ppo.avg_profit_per_order)} vs "
                f"{weak.category} {_rs(weak.avg_profit_per_order)}"
            )
            if worst is not None and worst.avg_profit_per_order < 0:
                ppo_text += (
                    f"; the average {worst.sub_category} order loses "
                    f"{_rs(worst.avg_profit_per_order)}"
                )
            reasons.append(ppo_text + ".")

            if worst is not None and worst.total_profit < 0:
                recs.append(
                    f"Reprice or cap discounts on {worst.sub_category} ({_rs(worst.avg_order_value)} "
                    f"average order, {_rs(worst.avg_profit_per_order)} lost on each). Break-even "
                    f"lifts {weak.category} margin from {weak.profit_margin_pct:.1f}% to "
                    f"{be_margin:.1f}%."
                )
            others = [s for s in subs if s is not worst]
            if others:
                second = min(others, key=lambda s: s.total_profit)
                peers = [s for s in subs if s.category == second.category and s is not second]
                top_line = max(subs, key=lambda s: s.profit_margin_pct)
                if peers:
                    partner = max(peers, key=lambda s: s.profit_margin_pct)
                    recs.append(
                        f"Bundle {second.sub_category} ({second.profit_margin_pct:.1f}%) with "
                        f"{partner.sub_category} ({partner.profit_margin_pct:.1f}% margin) and push "
                        f"high-margin add-ons like {top_line.sub_category} "
                        f"({top_line.profit_margin_pct:.1f}%) to lift basket margin, not volume."
                    )
            out["part1_reasons"] = reasons
            out["part1_recommendations"] = recs
            out["exec_part1"] = (
                f"{strong.category} converts sales to profit best ({strong.profit_margin_pct:.1f}% "
                f"margin); {weak.category} trails at {weak.profit_margin_pct:.1f}%"
                + (
                    f", mainly because {worst.sub_category} loses {_rs(worst.total_profit)}."
                    if worst is not None and worst.total_profit < 0 else "."
                )
            )

        # ---------------- Part 2: aligning targets ----------------
        ta = AnalyticsEngine.compute_target_alignment(furniture_data)
        if ta:
            h1_share = 100 - ta["h2_actual_share_pct"]
            out["part2_diagnosis"] = (
                f"Targets rise a steady {ta['avg_target_mom_pct']:.1f}% a month "
                f"({_rs(ta['first_target'])} to {_rs(ta['last_target'])}) while actual sales swing "
                f"seasonally from {_rs(ta['low_actual'])} ({ta['low_month']}) to "
                f"{_rs(ta['high_actual'])} ({ta['high_month']}). Achievement: "
                f"{ta['h1_achievement_pct']:.0f}% in {ta['h1_label']}, "
                f"{ta['h2_achievement_pct']:.0f}% in {ta['h2_label']}; target met in "
                f"{ta['months_met']} of {ta['months']} months."
            )
            qs = ta["quarters"]
            q_low = min(qs, key=lambda q: q["achievement_pct"])
            q_high = max(qs, key=lambda q: q["achievement_pct"])
            out["part2_strategies"] = [
                f"Seasonal targets: {ta['h2_label']} brought {ta['h2_actual_share_pct']:.0f}% of "
                f"actual sales ({_rs(ta['h2_actual'])} vs {_rs(ta['h1_actual'])}) but only "
                f"{ta['h2_target_share_pct']:.0f}% of the target. Splitting the annual "
                f"{_rs(ta['annual_target'])} target {h1_share:.0f}/"
                f"{ta['h2_actual_share_pct']:.0f} gives about "
                f"{_rs(ta['seasonal_h1_monthly_target'])} a month for {ta['h1_label']} and "
                f"{_rs(ta['seasonal_h2_monthly_target'])} for {ta['h2_label']}.",
                f"Rolling {ta['rolling_window']}-month baseline: setting each target at the previous "
                f"{ta['rolling_window']} months' average actual would have missed by "
                f"{_rs(ta['rolling_mae'])} a month over {ta['rolling_eval_label']}, vs "
                f"{_rs(ta['flat_ramp_mae'])} for the current ramp ({ta['mae_reduction_pct']:.0f}% "
                f"smaller). Latest baseline: {_rs(ta['latest_rolling_baseline'])} a month vs a "
                f"{_rs(ta['last_target'])} target.",
                f"Quarterly re-forecast: achievement ranged from {q_low['achievement_pct']:.0f}% "
                f"({q_low['label']}) to {q_high['achievement_pct']:.0f}% ({q_high['label']}). "
                "Resetting each next quarter's target from the seasonal split and latest run-rate "
                "stops one quarter's miss or windfall distorting the year.",
            ]
            out["exec_part2"] = (
                f"Furniture targets rise ~{ta['avg_target_mom_pct']:.1f}% a month, but "
                f"{ta['h2_label']} brings {ta['h2_actual_share_pct']:.0f}% of actual sales "
                f"({ta['h1_achievement_pct']:.0f}% vs {ta['h2_achievement_pct']:.0f}% achievement "
                "by half). Set seasonal targets on a rolling 3-month baseline and re-forecast "
                "quarterly."
            )

        # ---------------- Part 3: regional disparities ----------------
        if states:
            disp: List[str] = []
            if len(states) >= 2:
                a, b = states[0], states[1]
                lower, higher = (a, b) if a.profit_margin_pct < b.profit_margin_pct else (b, a)
                gap_pts = higher.profit_margin_pct - lower.profit_margin_pct
                disp.append(
                    f"{a.state} and {b.state} lead on volume ({a.distinct_orders} and "
                    f"{b.distinct_orders} orders; {_rs(a.total_sales)} and {_rs(b.total_sales)} "
                    f"of sales), but {lower.state} earns {lower.profit_margin_pct:.1f}% margin vs "
                    f"{higher.profit_margin_pct:.1f}%; closing the {gap_pts:.1f}-point gap is worth "
                    f"about {_rs(lower.total_sales * gap_pts / 100)} of profit."
                )
            best = max(states, key=lambda s: s.profit_margin_pct)
            worst_st = min(states, key=lambda s: s.profit_margin_pct)
            text = (
                f"Top-{len(states)} margins range from "
                f"{best.profit_margin_pct:.1f}% ({best.state}) to "
                f"{worst_st.profit_margin_pct:.1f}% ({worst_st.state})"
            )
            if worst_st.total_profit < 0:
                text += f"; {worst_st.state} loses {_rs(worst_st.total_profit)}"
                driver = next(
                    (p for p in prios if p.state == worst_st.state and p.action == "Fix"), None
                )
                if driver is not None and driver.total_profit < 0:
                    text += f", driven by {driver.city} ({signed(driver.total_profit)})"
            disp.append(text + ".")
            for sc in (p for p in prios if p.action == "Scale"):
                twin = next((p for p in prios if p.action == "Fix" and p.state == sc.state), None)
                if twin is not None:
                    disp.append(
                        f"Gaps are wider within states: in {sc.state}, {twin.city} runs at "
                        f"{twin.profit_margin_pct:.1f}% margin while {sc.city} earns "
                        f"{sc.profit_margin_pct:.1f}%, so the fix is local pricing and mix."
                    )
                    break
            out["part3_disparities"] = disp
        fix = [p for p in prios if p.action == "Fix"]
        scale = [p for p in prios if p.action == "Scale"]
        if fix or scale:
            out["exec_part3"] = (
                (f"Cities to fix first: {', '.join(p.city for p in fix)}. " if fix else "")
                + (f"Cities to scale: {', '.join(p.city for p in scale)}." if scale else "")
            ).strip()
        return out
