"""Data ingestion, schema normalization, and validation module.

Ingests List of Orders.xlsx, Order Details.xlsx, and Sales target.xlsx,
normalizes column names to lowercase snake_case, coerces heterogeneous
date formats (DD-MM-YYYY, YYYY-MM-DD, Excel serials, openpyxl datetimes)
into uniform pandas datetime objects, enforces numeric type casting,
and validates records using typed dataclasses.
"""

from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import openpyxl
import pandas as pd


# ---------------------------------------------------------------------------
# Domain Exceptions & Error Classes
# ---------------------------------------------------------------------------

class MissingColumnError(KeyError, ValueError):
    """Raised when one or more mandatory columns are missing from an input dataset.

    Inherits from both KeyError and ValueError to satisfy both the ARCHITECTURE
    spec (KeyError) and the TASKS / error-handling specs (ValueError).
    """
    pass


# ---------------------------------------------------------------------------
# Mandatory Column Schemas
# ---------------------------------------------------------------------------

REQUIRED_ORDERS_COLUMNS: Set[str] = {
    "order_id",
    "order_date",
    "customer_name",
    "state",
    "city",
}

REQUIRED_ORDER_DETAILS_COLUMNS: Set[str] = {
    "order_id",
    "amount",
    "profit",
    "quantity",
    "category",
    "sub_category",
}

REQUIRED_SALES_TARGET_COLUMNS: Set[str] = {
    "month_of_order_date",
    "category",
    "target",
}

VALID_CATEGORIES: Set[str] = {"Clothing", "Electronics", "Furniture"}


# ---------------------------------------------------------------------------
# Ingestion Dataclasses (Boundary Validation Models)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RawOrderRecord:
    """Ingestion model representing a single order header record."""

    order_id: str
    order_date: datetime
    customer_name: str
    state: str
    city: str

    def __post_init__(self) -> None:
        if not self.order_id or not self.order_id.strip():
            raise ValueError("order_id cannot be blank or whitespace")
        if not isinstance(self.order_date, datetime):
            raise TypeError(f"order_date must be datetime, got {type(self.order_date)}")
        if not self.state or not self.state.strip():
            raise ValueError("state cannot be blank")


@dataclass(frozen=True)
class RawOrderDetailRecord:
    """Ingestion model representing a single order transaction line item."""

    order_id: str
    amount: float
    profit: float
    quantity: int
    category: str
    sub_category: str

    def __post_init__(self) -> None:
        if not self.order_id or not self.order_id.strip():
            raise ValueError("order_id cannot be blank")
        if self.amount < 0:
            raise ValueError(f"amount cannot be negative: {self.amount}")
        if self.quantity < 1:
            raise ValueError(f"quantity must be >= 1: {self.quantity}")
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"Unrecognized category: {self.category}")


@dataclass(frozen=True)
class RawSalesTargetRecord:
    """Ingestion model representing a monthly sales target expectation."""

    month_of_order_date: str
    category: str
    target: float

    def __post_init__(self) -> None:
        if isinstance(self.month_of_order_date, (datetime, pd.Timestamp)):
            object.__setattr__(
                self,
                "month_of_order_date",
                self.month_of_order_date.strftime("%Y-%m-%d"),
            )
        elif not isinstance(self.month_of_order_date, str):
            raise TypeError(
                f"month_of_order_date must be str or datetime, got {type(self.month_of_order_date)}"
            )
        if not self.month_of_order_date or not self.month_of_order_date.strip():
            raise ValueError("month_of_order_date cannot be blank")
        if self.target <= 0:
            raise ValueError(f"target must be strictly positive: {self.target}")
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"Unrecognized category: {self.category}")


# ---------------------------------------------------------------------------
# Column & Date Normalization Utilities
# ---------------------------------------------------------------------------

def normalize_column_name(col: str) -> str:
    """Converts a raw column name to normalized lowercase snake_case.

    Examples:
        'Order ID'            -> 'order_id'
        'Order Date'          -> 'order_date'
        'CustomerName'        -> 'customer_name'
        'Sub-Category'        -> 'sub_category'
        'Month of Order Date' -> 'month_of_order_date'
    """
    s = str(col).strip()
    # Replace non-alphanumeric characters (hyphens, spaces) with underscores
    s = re.sub(r"[-\s]+", "_", s)
    # Split camelCase or PascalCase: e.g., CustomerName -> Customer_Name
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    # Condense multiple underscores and lowercase
    s = re.sub(r"_+", "_", s).lower()
    return s.strip("_")


def parse_order_date(
    value: Any,
    number_format: Optional[str] = None,
) -> pd.Timestamp:
    """Parses heterogeneous date representations into pd.Timestamp.

    Handles:
    - String representations: DD-MM-YYYY, YYYY-MM-DD, leap days (29-02-2020)
    - Python datetime / pd.Timestamp objects
    - Inverted mm-dd-yyyy formatting from raw Excel workbooks where day <= 12
    - Excel integer/float serial numbers (origin 1899-12-30)

    Args:
        value: Date representation (string, datetime, Timestamp, float/int).
        number_format: Optional Excel cell number_format code.

    Returns:
        pd.Timestamp: Standardized timestamp.

    Raises:
        ValueError: If value is null, blank, or cannot be parsed into a date.
    """
    if value is None or pd.isna(value):
        raise ValueError("Order date value cannot be empty or null")

    # Numeric Excel serial number (e.g., 43104.0)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return pd.Timestamp(pd.to_datetime(value, unit="D", origin="1899-12-30"))
        except Exception as err:
            raise ValueError(
                f"Could not parse numeric Excel serial date '{value}': {err}"
            ) from err

    # String format
    if isinstance(value, str):
        s = value.strip()
        if not s:
            raise ValueError("Order date string cannot be blank or whitespace")
        # Try explicit common formats to prevent day/month ambiguity
        for fmt in (
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                return pd.Timestamp(datetime.strptime(s, fmt))
            except ValueError:
                continue
        # Fallback to pd.to_datetime with dayfirst=True
        try:
            dt = pd.to_datetime(s, dayfirst=True)
            if pd.isna(dt):
                raise ValueError(f"Could not parse date string: '{value}'")
            return pd.Timestamp(dt)
        except Exception as err:
            raise ValueError(f"Failed to parse date string '{value}': {err}") from err

    # Python datetime or Timestamp
    if isinstance(value, (datetime, pd.Timestamp)):
        # Excel bug recovery: in raw 'List of Orders.xlsx', the worksheet was
        # formatted with 'mm-dd-yyyy'/'m-d-yyyy', causing Excel to swap day and month
        # for days 1 to 12.
        if (
            number_format
            and str(number_format).lower() in ("mm-dd-yyyy", "m-d-yyyy")
            and value.day <= 12
        ):
            try:
                return pd.Timestamp(
                    year=value.year,
                    month=value.day,
                    day=value.month,
                )
            except ValueError:
                return pd.Timestamp(value)
        return pd.Timestamp(value)

    raise ValueError(f"Unsupported order date type: {type(value)} for value '{value}'")


def parse_target_date(value: Any) -> pd.Timestamp:
    """Parses monthly sales target dates into first-of-month pd.Timestamp.

    Handles:
    - Raw Excel cells saved as 'Apr-18' with mmm-d formatting (which Excel
      interpreted as 18th of month in 2024-2026).
    - String representations: 'Apr-18', '2018-04-01', 'April 2018'.
    - Existing datetime / Timestamp objects.

    Returns:
        pd.Timestamp normalized to the first day of the target month (day=1).
    """
    if value is None or pd.isna(value):
        raise ValueError("Sales target date value cannot be empty or null")

    # Excel serial number
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            dt = pd.to_datetime(value, unit="D", origin="1899-12-30")
            return pd.Timestamp(year=dt.year, month=dt.month, day=1)
        except Exception as err:
            raise ValueError(
                f"Could not parse numeric Excel serial target date '{value}': {err}"
            ) from err

    # Datetime / Timestamp
    if isinstance(value, (datetime, pd.Timestamp)):
        # Recover 'Apr-18' to 'Dec-18' and 'Jan-19' to 'Mar-19' typed in Excel
        if value.year >= 2024 and value.day in (18, 19):
            target_year = 2018 if value.day == 18 else 2019
            return pd.Timestamp(year=target_year, month=value.month, day=1)
        return pd.Timestamp(year=value.year, month=value.month, day=1)

    # String format
    if isinstance(value, str):
        s = value.strip()
        if not s:
            raise ValueError("Sales target date string cannot be blank or whitespace")
        for fmt in (
            "%b-%y",
            "%B-%y",
            "%b-%Y",
            "%B-%Y",
            "%Y-%m-%d",
            "%Y-%m",
            "%d-%m-%Y",
            "%m/%d/%Y",
        ):
            try:
                dt = datetime.strptime(s, fmt)
                return pd.Timestamp(year=dt.year, month=dt.month, day=1)
            except ValueError:
                pass
        try:
            dt = pd.to_datetime(s, dayfirst=True)
            if pd.isna(dt):
                raise ValueError(f"Could not parse target date string: '{value}'")
            return pd.Timestamp(year=dt.year, month=dt.month, day=1)
        except Exception as err:
            raise ValueError(
                f"Failed to parse target date string '{value}': {err}"
            ) from err

    raise ValueError(
        f"Unsupported target date type: {type(value)} for value '{value}'"
    )


# ---------------------------------------------------------------------------
# DataLoader Class
# ---------------------------------------------------------------------------

class DataLoader:
    """Handles loading, schema normalization, and validation of raw Excel files."""

    # Expose normalization utilities as static methods
    normalize_column_name = staticmethod(normalize_column_name)
    parse_order_date = staticmethod(parse_order_date)
    parse_target_date = staticmethod(parse_target_date)

    @classmethod
    def _validate_file_path(cls, file_path: Union[str, Path]) -> Path:
        """Validates that file_path exists, is a file, and is not 0 bytes."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Input file does not exist: {path.resolve()}")
        if not path.is_file():
            raise FileNotFoundError(f"Path is not a regular file: {path.resolve()}")
        if path.stat().st_size == 0:
            raise ValueError(f"Input file is completely empty (0 bytes): {path.resolve()}")
        return path

    @staticmethod
    def load_orders(file_path: Union[str, Path]) -> pd.DataFrame:
        """Loads and normalizes List of Orders.xlsx.

        Args:
            file_path: Path to List of Orders.xlsx

        Returns:
            pd.DataFrame with columns:
                ['order_id', 'order_date', 'customer_name', 'state', 'city']
            where 'order_date' is pd.Timestamp (datetime64[ns]).

        Raises:
            FileNotFoundError: If file is missing.
            MissingColumnError (KeyError & ValueError): If required columns are missing.
            ValueError: If parsing date format fails completely or file has no data rows.
        """
        path = DataLoader._validate_file_path(file_path)

        rows_data: List[Dict[str, Any]] = []

        if path.suffix.lower() in (".xlsx", ".xlsm", ".xltx", ".xltm"):
            wb = openpyxl.load_workbook(path, data_only=True)
            try:
                ws = wb.active
                if ws is None:
                    raise ValueError(f"Workbook {path} has no active worksheet")
                rows_iter = ws.iter_rows(values_only=False)
                header_cells = next(rows_iter, None)
                if header_cells is None:
                    raise ValueError(f"Workbook {path} contains no header row")

                raw_headers = [c.value for c in header_cells]
                norm_headers = [
                    normalize_column_name(h) if h is not None else ""
                    for h in raw_headers
                ]

                missing = REQUIRED_ORDERS_COLUMNS - set(norm_headers)
                if missing:
                    raise MissingColumnError(
                        f"Missing mandatory columns in orders file {path.name}: {sorted(missing)}"
                    )

                col_idx = {
                    h: i for i, h in enumerate(norm_headers) if h in REQUIRED_ORDERS_COLUMNS
                }

                for row_idx, row_cells in enumerate(rows_iter, start=2):
                    # Check if entire row is empty
                    if all(row_cells[col_idx[c]].value is None for c in REQUIRED_ORDERS_COLUMNS):
                        continue

                    order_id_raw = row_cells[col_idx["order_id"]].value
                    order_date_cell = row_cells[col_idx["order_date"]]
                    cust_raw = row_cells[col_idx["customer_name"]].value
                    state_raw = row_cells[col_idx["state"]].value
                    city_raw = row_cells[col_idx["city"]].value

                    order_id = str(order_id_raw or "").strip()
                    parsed_dt = parse_order_date(
                        order_date_cell.value,
                        number_format=order_date_cell.number_format,
                    )
                    customer_name = str(cust_raw or "").strip()
                    state = str(state_raw or "").strip()
                    city = str(city_raw or "").strip()

                    # Validate with dataclass
                    RawOrderRecord(
                        order_id=order_id,
                        order_date=parsed_dt.to_pydatetime(),
                        customer_name=customer_name,
                        state=state,
                        city=city,
                    )

                    rows_data.append({
                        "order_id": order_id,
                        "order_date": parsed_dt,
                        "customer_name": customer_name,
                        "state": state,
                        "city": city,
                    })
            finally:
                wb.close()
        else:
            # Fallback for CSV or other tabular formats
            raw_df = pd.read_csv(path)
            norm_map = {c: normalize_column_name(c) for c in raw_df.columns}
            df_norm = raw_df.rename(columns=norm_map)

            missing = REQUIRED_ORDERS_COLUMNS - set(df_norm.columns)
            if missing:
                raise MissingColumnError(
                    f"Missing mandatory columns in orders file {path.name}: {sorted(missing)}"
                )

            for _, row in df_norm.iterrows():
                order_id = str(row["order_id"] or "").strip()
                parsed_dt = parse_order_date(row["order_date"], number_format=None)
                customer_name = str(row["customer_name"] or "").strip()
                state = str(row["state"] or "").strip()
                city = str(row["city"] or "").strip()

                RawOrderRecord(
                    order_id=order_id,
                    order_date=parsed_dt.to_pydatetime(),
                    customer_name=customer_name,
                    state=state,
                    city=city,
                )

                rows_data.append({
                    "order_id": order_id,
                    "order_date": parsed_dt,
                    "customer_name": customer_name,
                    "state": state,
                    "city": city,
                })

        if not rows_data:
            raise ValueError(f"Orders dataset in {path.name} contains no valid records")

        out_df = pd.DataFrame(rows_data)
        out_df["order_id"] = out_df["order_id"].astype(str)
        out_df["order_date"] = pd.to_datetime(out_df["order_date"])
        out_df["customer_name"] = out_df["customer_name"].astype(str)
        out_df["state"] = out_df["state"].astype(str)
        out_df["city"] = out_df["city"].astype(str)

        return out_df[["order_id", "order_date", "customer_name", "state", "city"]]

    @staticmethod
    def load_order_details(file_path: Union[str, Path]) -> pd.DataFrame:
        """Loads and normalizes Order Details.xlsx.

        Args:
            file_path: Path to Order Details.xlsx

        Returns:
            pd.DataFrame with columns:
                ['order_id', 'amount', 'profit', 'quantity', 'category', 'sub_category']
            with numeric typing: amount (float64), profit (float64), quantity (int64).

        Raises:
            FileNotFoundError: If file is missing.
            MissingColumnError (KeyError & ValueError): If required columns are missing.
            ValueError: If numeric columns cannot be cast or validation fails.
        """
        path = DataLoader._validate_file_path(file_path)

        if path.suffix.lower() in (".xlsx", ".xlsm", ".xltx", ".xltm"):
            raw_df = pd.read_excel(path)
        else:
            raw_df = pd.read_csv(path)

        norm_map = {c: normalize_column_name(c) for c in raw_df.columns}
        df_norm = raw_df.rename(columns=norm_map)

        missing = REQUIRED_ORDER_DETAILS_COLUMNS - set(df_norm.columns)
        if missing:
            raise MissingColumnError(
                f"Missing mandatory columns in order details file {path.name}: {sorted(missing)}"
            )

        if df_norm.empty:
            raise ValueError(f"Order details dataset in {path.name} contains no records")

        # Cast numerics with strict error-raising
        try:
            df_norm["amount"] = pd.to_numeric(df_norm["amount"], errors="raise").astype("float64")
        except Exception as err:
            raise ValueError(f"Could not cast 'amount' to float64 in {path.name}: {err}") from err

        try:
            df_norm["profit"] = pd.to_numeric(df_norm["profit"], errors="raise").astype("float64")
        except Exception as err:
            raise ValueError(f"Could not cast 'profit' to float64 in {path.name}: {err}") from err

        try:
            df_norm["quantity"] = pd.to_numeric(df_norm["quantity"], errors="raise").astype("int64")
        except Exception as err:
            raise ValueError(f"Could not cast 'quantity' to int64 in {path.name}: {err}") from err

        # Strip whitespace on strings
        df_norm["order_id"] = df_norm["order_id"].astype(str).str.strip()
        df_norm["category"] = df_norm["category"].astype(str).str.strip()
        df_norm["sub_category"] = df_norm["sub_category"].astype(str).str.strip()

        # Validate each record using dataclass
        for idx, row in df_norm.iterrows():
            RawOrderDetailRecord(
                order_id=row["order_id"],
                amount=row["amount"],
                profit=row["profit"],
                quantity=row["quantity"],
                category=row["category"],
                sub_category=row["sub_category"],
            )

        return df_norm[
            ["order_id", "amount", "profit", "quantity", "category", "sub_category"]
        ].copy()

    @staticmethod
    def load_sales_targets(file_path: Union[str, Path]) -> pd.DataFrame:
        """Loads and normalizes Sales target.xlsx.

        Args:
            file_path: Path to Sales target.xlsx

        Returns:
            pd.DataFrame with columns:
                ['month_of_order_date', 'category', 'target']
            where 'month_of_order_date' is pd.Timestamp (datetime64[ns])
            and 'target' is float64.

        Raises:
            FileNotFoundError: If file is missing.
            MissingColumnError (KeyError & ValueError): If required columns are missing.
            ValueError: If target values cannot be parsed or validation fails.
        """
        path = DataLoader._validate_file_path(file_path)

        if path.suffix.lower() in (".xlsx", ".xlsm", ".xltx", ".xltm"):
            raw_df = pd.read_excel(path)
        else:
            raw_df = pd.read_csv(path)

        norm_map = {c: normalize_column_name(c) for c in raw_df.columns}
        df_norm = raw_df.rename(columns=norm_map)

        missing = REQUIRED_SALES_TARGET_COLUMNS - set(df_norm.columns)
        if missing:
            raise MissingColumnError(
                f"Missing mandatory columns in sales target file {path.name}: {sorted(missing)}"
            )

        if df_norm.empty:
            raise ValueError(f"Sales target dataset in {path.name} contains no records")

        # Parse target dates
        parsed_dates = df_norm["month_of_order_date"].apply(parse_target_date)
        df_norm["month_of_order_date"] = pd.to_datetime(parsed_dates)

        # Cast target numeric
        try:
            df_norm["target"] = pd.to_numeric(df_norm["target"], errors="raise").astype("float64")
        except Exception as err:
            raise ValueError(f"Could not cast 'target' to float64 in {path.name}: {err}") from err

        df_norm["category"] = df_norm["category"].astype(str).str.strip()

        # Validate with dataclass
        for idx, row in df_norm.iterrows():
            RawSalesTargetRecord(
                month_of_order_date=str(row["month_of_order_date"].strftime("%Y-%m-%d")),
                category=row["category"],
                target=row["target"],
            )

        return df_norm[["month_of_order_date", "category", "target"]].copy()

    @classmethod
    def load_all(
        cls,
        data_dir: Union[str, Path] = ".",
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Loads all three normalized datasets from the specified directory.

        Args:
            data_dir: Directory containing List of Orders.xlsx, Order Details.xlsx,
                      and Sales target.xlsx. Defaults to current working directory.

        Returns:
            Tuple of (orders_df, order_details_df, sales_targets_df)
        """
        base = Path(data_dir)
        orders_path = base / "List of Orders.xlsx"
        details_path = base / "Order Details.xlsx"
        targets_path = base / "Sales target.xlsx"

        orders_df = cls.load_orders(orders_path)
        details_df = cls.load_order_details(details_path)
        targets_df = cls.load_sales_targets(targets_path)

        return orders_df, details_df, targets_df
