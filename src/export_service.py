"""Analytical export service for serializing calculations into JSON and CSV artifacts.

Implements M1-TASK-06 (SPEC AC-1.1 to AC-1.5) and M2-TASK-03 (SPEC AC-2.1, AC-3.1):
- Serializes CategoryPerformance, FurnitureTargetAchievement, StatePerformance,
  and CityPerformance to structured JSON and CSV files.
- Serializes Question 2 UX Teardown and Question 3 Growth Strategy reports to
  data/output/ux_teardown.json and data/output/growth_strategy.json.
- Persists outputs to data/output/ (configurable via OUTPUT_DATA_DIR env var).
- Ensures RFC 8259 JSON compliance (NaN guards, ISO timestamps, null mapping).
- Provides deterministic CSV writing with uniform column schemas.
"""

from dataclasses import asdict, is_dataclass
from datetime import datetime
import json
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import pandas as pd

from src.analytics_engine import (
    CategoryPerformance,
    CityPerformance,
    FurnitureTargetAchievement,
    StatePerformance,
)
from src.content.growth_strategy import (
    GrowthStrategyReport,
    get_growth_strategy_report,
)
from src.content.ux_teardown import (
    UXTeardownReport,
    get_ux_teardown_report,
)

logger = logging.getLogger(__name__)

# Default directory for persisted analytical artifacts
DEFAULT_OUTPUT_DIR = "data/output"


# ---------------------------------------------------------------------------
# Data Sanitization & Serialization Helpers
# ---------------------------------------------------------------------------

def sanitize_value_for_json(val: Any) -> Any:
    """Recursively coerces values into strictly JSON-compliant equivalents.

    - float('nan') and float('inf') -> None (serialized as null in JSON)
    - datetime / Timestamp -> ISO 8601 string
    - Dataclass instances -> serialized dict
    - Nested dicts and lists -> sanitized recursively
    """
    if val is None:
        return None
    if isinstance(val, (int, bool, str)):
        return val
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.isoformat()
    if is_dataclass(val):
        return sanitize_value_for_json(asdict(val))
    if isinstance(val, dict):
        return {str(k): sanitize_value_for_json(v) for k, v in val.items()}
    if isinstance(val, (list, tuple, set)):
        return [sanitize_value_for_json(x) for x in val]
    return str(val)


def record_to_dict(record: Any) -> Dict[str, Any]:
    """Converts a domain model or record into a standardized dictionary."""
    if hasattr(record, "to_dict") and callable(record.to_dict):
        return record.to_dict()
    if is_dataclass(record):
        return asdict(record)
    if isinstance(record, dict):
        return record.copy()
    raise TypeError(
        f"Expected dataclass or dict with to_dict(), got {type(record).__name__}"
    )


# ---------------------------------------------------------------------------
# ExportService Class
# ---------------------------------------------------------------------------

class ExportService:
    """Serializes analytical results into structured JSON and CSV output files."""

    def __init__(self, output_dir: Optional[Union[str, Path]] = None) -> None:
        """Initializes ExportService with target output directory.

        Args:
            output_dir: Target directory path. If None, reads from OUTPUT_DATA_DIR
                        environment variable or defaults to 'data/output'.
        """
        if output_dir is not None:
            self._output_dir = Path(output_dir)
        else:
            env_dir = os.environ.get("OUTPUT_DATA_DIR", DEFAULT_OUTPUT_DIR)
            self._output_dir = Path(env_dir)

        # Ensure target directory exists
        self._output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("Initialized ExportService with output directory: %s", self._output_dir.resolve())

    @property
    def output_dir(self) -> Path:
        """Returns the base output directory path."""
        return self._output_dir

    # -----------------------------------------------------------------------
    # Generic Serialization Primitives
    # -----------------------------------------------------------------------

    def export_records_to_json(
        self,
        records: Sequence[Any],
        file_path: Union[str, Path],
    ) -> Path:
        """Serializes a sequence of dataclass records or dicts to a JSON file.

        Args:
            records: Sequence of domain dataclass records or dictionaries.
            file_path: Destination file path.

        Returns:
            Path: Absolute or resolved path of the created JSON file.

        Raises:
            TypeError: If records is not a sequence.
            IOError: If writing to the file fails.
        """
        if not isinstance(records, (list, tuple)):
            raise TypeError(f"records must be a sequence (list or tuple), got {type(records).__name__}")

        dest = Path(file_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        dict_list = [sanitize_value_for_json(record_to_dict(r)) for r in records]

        with open(dest, "w", encoding="utf-8") as f:
            json.dump(dict_list, f, indent=2, ensure_ascii=False)

        logger.info("Exported %d records to JSON: %s (%d bytes)", len(dict_list), dest, dest.stat().st_size)
        return dest

    def export_records_to_csv(
        self,
        records: Sequence[Any],
        file_path: Union[str, Path],
        fieldnames: Optional[List[str]] = None,
    ) -> Path:
        """Serializes a sequence of dataclass records or dicts to a CSV file.

        Args:
            records: Sequence of domain dataclass records or dictionaries.
            file_path: Destination file path.
            fieldnames: Optional column order. If None, derived from records.

        Returns:
            Path: Resolved path of the created CSV file.

        Raises:
            TypeError: If records is not a sequence.
            IOError: If writing to the file fails.
        """
        if not isinstance(records, (list, tuple)):
            raise TypeError(f"records must be a sequence (list or tuple), got {type(records).__name__}")

        dest = Path(file_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if not records:
            # Write empty CSV or header-only CSV
            cols = fieldnames or []
            empty_df = pd.DataFrame(columns=cols)
            empty_df.to_csv(dest, index=False, encoding="utf-8")
            logger.info("Exported empty CSV: %s", dest)
            return dest

        dict_list = [record_to_dict(r) for r in records]
        df = pd.DataFrame(dict_list)

        if fieldnames:
            # Ensure specified columns come first, followed by any remaining
            ordered_cols = [c for c in fieldnames if c in df.columns]
            remaining_cols = [c for c in df.columns if c not in ordered_cols]
            df = df[ordered_cols + remaining_cols]

        df.to_csv(dest, index=False, encoding="utf-8")
        logger.info("Exported %d records to CSV: %s (%d bytes)", len(df), dest, dest.stat().st_size)
        return dest

    def export_dict_to_json(
        self,
        data: Dict[str, Any],
        file_path: Union[str, Path],
    ) -> Path:
        """Serializes an arbitrary dictionary (e.g. metadata or strategy teardowns) to JSON.

        Args:
            data: Dictionary of data to serialize.
            file_path: Destination file path.

        Returns:
            Path: Path of the created JSON file.
        """
        if not isinstance(data, dict):
            raise TypeError(f"data must be a dict, got {type(data).__name__}")

        dest = Path(file_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        sanitized = sanitize_value_for_json(data)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(sanitized, f, indent=2, ensure_ascii=False)

        logger.info("Exported dictionary to JSON: %s (%d bytes)", dest, dest.stat().st_size)
        return dest

    # -----------------------------------------------------------------------
    # Question 1 Specific Export Methods
    # -----------------------------------------------------------------------

    def export_category_performance(
        self,
        records: Sequence[CategoryPerformance],
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Path]:
        """Serializes CategoryPerformance records to category_performance.json and .csv.

        Args:
            records: Sequence of CategoryPerformance records.
            output_dir: Optional override directory. Defaults to self.output_dir.

        Returns:
            Dict[str, Path]: Mapping {"json": json_path, "csv": csv_path}.
        """
        base_dir = Path(output_dir) if output_dir is not None else self._output_dir
        base_dir.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "category",
            "total_sales",
            "total_profit",
            "avg_profit_per_order",
            "profit_margin_pct",
            "distinct_orders",
            "total_quantity",
            "performance_rank",
        ]

        json_path = base_dir / "category_performance.json"
        csv_path = base_dir / "category_performance.csv"

        self.export_records_to_json(records, json_path)
        self.export_records_to_csv(records, csv_path, fieldnames=fieldnames)

        return {"json": json_path, "csv": csv_path}

    def export_furniture_targets(
        self,
        records: Sequence[FurnitureTargetAchievement],
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Path]:
        """Serializes FurnitureTargetAchievement records to furniture_targets.json and .csv.

        Args:
            records: Sequence of FurnitureTargetAchievement records.
            output_dir: Optional override directory. Defaults to self.output_dir.

        Returns:
            Dict[str, Path]: Mapping {"json": json_path, "csv": csv_path}.
        """
        base_dir = Path(output_dir) if output_dir is not None else self._output_dir
        base_dir.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "month_key",
            "display_month",
            "target_sales",
            "actual_sales",
            "mom_target_pct_change",
            "mom_actual_pct_change",
            "variance",
            "achievement_pct",
            "is_significant_fluctuation",
        ]

        json_path = base_dir / "furniture_targets.json"
        csv_path = base_dir / "furniture_targets.csv"

        self.export_records_to_json(records, json_path)
        self.export_records_to_csv(records, csv_path, fieldnames=fieldnames)

        return {"json": json_path, "csv": csv_path}

    def export_state_performance(
        self,
        records: Sequence[StatePerformance],
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Path]:
        """Serializes StatePerformance records to state_performance.json and .csv.

        Args:
            records: Sequence of StatePerformance records.
            output_dir: Optional override directory. Defaults to self.output_dir.

        Returns:
            Dict[str, Path]: Mapping {"json": json_path, "csv": csv_path}.
        """
        base_dir = Path(output_dir) if output_dir is not None else self._output_dir
        base_dir.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "rank",
            "state",
            "distinct_orders",
            "total_sales",
            "total_profit",
            "avg_profit_per_order",
            "profit_margin_pct",
            "quadrant",
        ]

        json_path = base_dir / "state_performance.json"
        csv_path = base_dir / "state_performance.csv"

        self.export_records_to_json(records, json_path)
        self.export_records_to_csv(records, csv_path, fieldnames=fieldnames)

        return {"json": json_path, "csv": csv_path}

    def export_city_performance(
        self,
        records: Sequence[CityPerformance],
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Path]:
        """Serializes CityPerformance records to city_performance.json and .csv.

        Args:
            records: Sequence of CityPerformance records.
            output_dir: Optional override directory. Defaults to self.output_dir.

        Returns:
            Dict[str, Path]: Mapping {"json": json_path, "csv": csv_path}.
        """
        base_dir = Path(output_dir) if output_dir is not None else self._output_dir
        base_dir.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "state",
            "city",
            "distinct_orders",
            "total_sales",
            "total_profit",
            "avg_profit_per_order",
            "profit_margin_pct",
        ]

        json_path = base_dir / "city_performance.json"
        csv_path = base_dir / "city_performance.csv"

        self.export_records_to_json(records, json_path)
        self.export_records_to_csv(records, csv_path, fieldnames=fieldnames)

        return {"json": json_path, "csv": csv_path}

    # -----------------------------------------------------------------------
    # Question 2 & Question 3 Strategy Export Methods
    # -----------------------------------------------------------------------

    def export_ux_teardown(
        self,
        report: Optional[Union[UXTeardownReport, Dict[str, Any]]] = None,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Path:
        """Serializes Question 2 UX Teardown evaluation to ux_teardown.json.

        Args:
            report: Optional UXTeardownReport instance or dictionary.
                    If None, loads canonical report via get_ux_teardown_report().
            output_dir: Optional destination directory override. Defaults to self.output_dir.

        Returns:
            Path: Resolved path to the generated ux_teardown.json file.

        Raises:
            TypeError: If report is not a UXTeardownReport, dict, or None.
            IOError: If writing to the file fails.
        """
        if report is None:
            data = get_ux_teardown_report().to_dict()
        elif isinstance(report, UXTeardownReport):
            data = report.to_dict()
        elif hasattr(report, "to_dict") and callable(report.to_dict):
            data = report.to_dict()
        elif isinstance(report, dict):
            data = report
        else:
            raise TypeError(
                f"report must be UXTeardownReport, dict, or None, got {type(report).__name__}"
            )

        if not isinstance(data, dict):
            raise TypeError(f"Serialized report data must be a dict, got {type(data).__name__}")

        base_dir = Path(output_dir) if output_dir is not None else self._output_dir
        base_dir.mkdir(parents=True, exist_ok=True)
        dest = base_dir / "ux_teardown.json"

        return self.export_dict_to_json(data, dest)

    def export_growth_strategy(
        self,
        report: Optional[Union[GrowthStrategyReport, Dict[str, Any]]] = None,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Path:
        """Serializes Question 3 Growth Strategy framework to growth_strategy.json.

        Args:
            report: Optional GrowthStrategyReport instance or dictionary.
                    If None, loads canonical report via get_growth_strategy_report().
            output_dir: Optional destination directory override. Defaults to self.output_dir.

        Returns:
            Path: Resolved path to the generated growth_strategy.json file.

        Raises:
            TypeError: If report is not a GrowthStrategyReport, dict, or None.
            IOError: If writing to the file fails.
        """
        if report is None:
            data = get_growth_strategy_report().to_dict()
        elif isinstance(report, GrowthStrategyReport):
            data = report.to_dict()
        elif hasattr(report, "to_dict") and callable(report.to_dict):
            data = report.to_dict()
        elif isinstance(report, dict):
            data = report
        else:
            raise TypeError(
                f"report must be GrowthStrategyReport, dict, or None, got {type(report).__name__}"
            )

        if not isinstance(data, dict):
            raise TypeError(f"Serialized report data must be a dict, got {type(data).__name__}")

        base_dir = Path(output_dir) if output_dir is not None else self._output_dir
        base_dir.mkdir(parents=True, exist_ok=True)
        dest = base_dir / "growth_strategy.json"

        return self.export_dict_to_json(data, dest)

    # -----------------------------------------------------------------------
    # Comprehensive Batch Export
    # -----------------------------------------------------------------------

    def export_all(
        self,
        category_data: Sequence[CategoryPerformance],
        furniture_data: Sequence[FurnitureTargetAchievement],
        state_data: Sequence[StatePerformance],
        city_data: Optional[Sequence[CityPerformance]] = None,
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Dict[str, Path]]:
        """Executes full export of Question 1 analytical artifacts.

        Args:
            category_data: CategoryPerformance records.
            furniture_data: FurnitureTargetAchievement records.
            state_data: StatePerformance records.
            city_data: Optional CityPerformance records.
            output_dir: Optional destination directory override.

        Returns:
            Dict[str, Dict[str, Path]]: Mapping artifact names to their json and csv paths.
        """
        target_dir = Path(output_dir) if output_dir is not None else self._output_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Executing comprehensive export to: %s", target_dir.resolve())

        artifacts: Dict[str, Dict[str, Path]] = {
            "category_performance": self.export_category_performance(category_data, target_dir),
            "furniture_targets": self.export_furniture_targets(furniture_data, target_dir),
            "state_performance": self.export_state_performance(state_data, target_dir),
        }

        if city_data is not None:
            artifacts["city_performance"] = self.export_city_performance(city_data, target_dir)

        return artifacts
