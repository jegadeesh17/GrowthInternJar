"""Analytics engine for sales, profitability, target achievement, and regional performance.

Implements deterministic computational routines for Question 1:
- Order dataset merging with inner join semantics and cardinality audit logging (AC-1.2, AC-E6).
- Category sales, profitability, order-level average profit, and margin analysis (AC-1.3, AC-E2, AC-E5).
- Output dataclasses matching technical architecture contracts.
"""

from dataclasses import asdict, dataclass
import logging
from typing import Any, Dict, List, Optional, Set

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
