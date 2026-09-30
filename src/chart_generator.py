"""Publication-grade pastel chart generation module.

Implements M3-TASK-01 (SPEC AC-4.2, ADR-007):
- Headless, non-GUI Matplotlib backend ('Agg') for zero-display environments.
- High-resolution 300 DPI chart rendering with crisp typography and soft pastel aesthetics:
  1. category_profitability.png: Dual-axis bar and line chart showing sales vs. profit margin %.
  2. furniture_target_vs_actual.png / furniture_target_trajectory.png: Chronological target vs. actual
     sales trajectory highlighting months with |MoM| >= 15% fluctuation.
  3. regional_performance.png / state_regional_quadrants.png: Top 5 states order volume vs. profit
     margin analysis with 2D strategic regional quadrant classification.
- Soft pastel design token system matching minimal-ui-kit/material-kit-react specs.
- Defensive boundary validations (empty inputs, missing directories, type checks).
"""

import logging
import os
from pathlib import Path
import tempfile
from typing import Dict, List, Optional, Sequence, Tuple, Union

# Set temporary config dir for matplotlib before import to prevent lock contention / permission issues
if "MPLCONFIGDIR" not in os.environ:
    safe_mpl_dir = os.path.join(tempfile.gettempdir(), f"matplotlib_config_{os.getpid()}")
    try:
        os.makedirs(safe_mpl_dir, exist_ok=True)
        os.environ["MPLCONFIGDIR"] = safe_mpl_dir
    except Exception:
        pass

# Force headless non-GUI backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from src.analytics_engine import (
    AnalyticsEngine,
    CategoryPerformance,
    FurnitureTargetAchievement,
    StatePerformance,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Visual Design Token System (ADR-007)
# ---------------------------------------------------------------------------

PASTEL_TOKENS: Dict[str, str] = {
    # Soft Sage (Growth, Profit, Health)
    "sage": "#48BB78",
    "sage_tint": "#E6FFFA",
    "sage_light": "#9AE6B4",
    "sage_dark": "#22543D",
    "sage_border": "#38A169",

    # Muted Gold / Amber (Digital Gold, Jar Brand, Savings Targets)
    "gold": "#D69E2E",
    "gold_tint": "#FEFCBF",
    "gold_light": "#F6E05E",
    "gold_dark": "#744210",
    "gold_border": "#B7791F",

    # Soft Lavender (UX, Psychological Models, Strategy)
    "lavender": "#805AD5",
    "lavender_tint": "#FAF5FF",
    "lavender_light": "#D6BCFA",
    "lavender_dark": "#44337A",
    "lavender_border": "#6B46C1",

    # Warm Coral Blush (Losses, Friction Points, Downward Fluctuations)
    "coral": "#E53E3E",
    "coral_tint": "#FFF5F5",
    "coral_light": "#FEB2B2",
    "coral_dark": "#742A2A",
    "coral_border": "#C53030",

    # Typography & Structural Tokens
    "slate": "#2D3748",
    "slate_muted": "#718096",
    "slate_light": "#A0AEC0",
    "slate_border": "#E2E8F0",
    "canvas_bg": "#F8FAFC",
    "card_bg": "#FFFFFF",
    "grid_color": "#EDF2F7",
}

CATEGORY_COLORS: Dict[str, str] = {
    "Clothing": PASTEL_TOKENS["sage"],
    "Electronics": PASTEL_TOKENS["lavender"],
    "Furniture": PASTEL_TOKENS["gold"],
}

QUADRANT_COLORS: Dict[str, Tuple[str, str]] = {
    "High Volume / High Margin": (PASTEL_TOKENS["sage"], PASTEL_TOKENS["sage_tint"]),
    "High Volume / Low Margin": (PASTEL_TOKENS["gold"], PASTEL_TOKENS["gold_tint"]),
    "Low Volume / High Margin": (PASTEL_TOKENS["lavender"], PASTEL_TOKENS["lavender_tint"]),
    "Low Volume / Low Margin": (PASTEL_TOKENS["coral"], PASTEL_TOKENS["coral_tint"]),
}


# ---------------------------------------------------------------------------
# Formatting Helpers
# ---------------------------------------------------------------------------

def format_inr(val: float, compact: bool = False) -> str:
    """Formats numeric value into Indian Rupee representation (safe ascii/utf-8)."""
    if compact:
        if abs(val) >= 100_000:
            return f"Rs. {val / 100_000:.2f}L"
        elif abs(val) >= 1_000:
            return f"Rs. {val / 1_000:.1f}k"
        else:
            return f"Rs. {val:,.0f}"
    return f"Rs. {val:,.0f}"


# ---------------------------------------------------------------------------
# ChartGenerator Class
# ---------------------------------------------------------------------------

class ChartGenerator:
    """Generates publication-grade pastel charts at 300 DPI using Matplotlib."""

    DEFAULT_OUTPUT_DIR = Path("assets/charts")
    DPI = 300

    @classmethod
    def resolve_output_dir(cls, output_dir: Optional[Union[Path, str]] = None) -> Path:
        """Resolves target output directory from argument, environment, or default."""
        if output_dir is not None:
            resolved = Path(output_dir)
        else:
            env_dir = os.getenv("CHART_ASSETS_DIR")
            resolved = Path(env_dir) if env_dir else cls.DEFAULT_OUTPUT_DIR

        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    # -----------------------------------------------------------------------
    # Chart 1: Category Sales & Profitability
    # -----------------------------------------------------------------------

    @classmethod
    def generate_category_profitability_chart(
        cls,
        category_data: List[CategoryPerformance],
        output_path: Union[Path, str],
        dpi: int = DPI,
    ) -> Path:
        """Renders dual-axis bar and line chart showing sales vs. profit margin % per category.

        Left Y-axis (Bars): Total Sales (Rs.) with category-specific soft pastel fills.
        Right Y-axis (Line): Profit Margin % with point markers and badge annotations.

        Args:
            category_data: Ranked category performance records.
            output_path: Path to save the PNG chart.
            dpi: Output resolution (default 300 DPI).

        Returns:
            Path: Resolved path of saved PNG file.

        Raises:
            TypeError: If category_data is not a sequence.
            ValueError: If category_data is empty.
        """
        if not isinstance(category_data, Sequence):
            raise TypeError(f"category_data must be a sequence, got {type(category_data).__name__}")
        if len(category_data) == 0:
            raise ValueError("category_data sequence cannot be empty")

        target_file = Path(output_path)
        target_file.parent.mkdir(parents=True, exist_ok=True)

        categories = [c.category for c in category_data]
        sales = [c.total_sales for c in category_data]
        profits = [c.total_profit for c in category_data]
        margins = [c.profit_margin_pct for c in category_data]
        orders = [c.distinct_orders for c in category_data]

        x_indices = np.arange(len(categories))
        bar_width = 0.46

        fig, ax1 = plt.subplots(figsize=(10.5, 6.2), dpi=dpi)
        fig.patch.set_facecolor(PASTEL_TOKENS["card_bg"])
        ax1.set_facecolor(PASTEL_TOKENS["card_bg"])

        # Bar colors mapped to categories
        bar_colors = [
            CATEGORY_COLORS.get(cat, PASTEL_TOKENS["sage"])
            for cat in categories
        ]

        # Left Y-Axis: Sales Bars
        bars = ax1.bar(
            x_indices,
            sales,
            width=bar_width,
            color=bar_colors,
            edgecolor=PASTEL_TOKENS["slate_border"],
            linewidth=1.2,
            zorder=3,
            label="Total Sales (Rs.)",
        )

        # Right Y-Axis: Margin Line
        ax2 = ax1.twinx()
        ax2.set_facecolor("none")

        ax2.plot(
            x_indices,
            margins,
            color=PASTEL_TOKENS["coral"],
            linewidth=2.8,
            marker="o",
            markersize=9,
            markerfacecolor=PASTEL_TOKENS["card_bg"],
            markeredgecolor=PASTEL_TOKENS["coral"],
            markeredgewidth=2.4,
            zorder=4,
            label="Profit Margin (%)",
        )

        # Add zero-reference line on margin axis if margins span negative/positive
        if min(margins) < 0 or min(margins) < 5:
            ax2.axhline(0, color=PASTEL_TOKENS["slate_light"], linestyle=":", linewidth=1, zorder=2)

        # Bar Value Annotations (Sales & Profit)
        max_sale = max(sales) if sales else 1.0
        for i, (b, s, p, o) in enumerate(zip(bars, sales, profits, orders)):
            height = b.get_height()
            ax1.annotate(
                f"{format_inr(s, compact=True)}\n(Profit: {format_inr(p, compact=True)})",
                xy=(b.get_x() + b.get_width() / 2, height),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="semibold",
                color=PASTEL_TOKENS["slate"],
            )

        # Line Value Annotations (Margin %)
        for i, m in enumerate(margins):
            # Place annotation offset dynamically to prevent overlap
            offset_y = 12 if m >= 0 else -18
            ax2.annotate(
                f"{m:+.1f}%",
                xy=(i, m),
                xytext=(0, offset_y),
                textcoords="offset points",
                ha="center",
                va="bottom" if offset_y > 0 else "top",
                fontsize=9.5,
                fontweight="bold",
                color=PASTEL_TOKENS["coral_dark"],
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor=PASTEL_TOKENS["coral_tint"],
                    edgecolor=PASTEL_TOKENS["coral_border"],
                    linewidth=0.8,
                    alpha=0.95,
                ),
                zorder=5,
            )

        # Styling Axis 1 (Sales)
        ax1.set_xlabel("Product Category", fontsize=11, fontweight="bold", color=PASTEL_TOKENS["slate"], labelpad=10)
        ax1.set_ylabel("Total Sales Volume (Rs.)", fontsize=11, fontweight="bold", color=PASTEL_TOKENS["slate"], labelpad=10)
        ax1.set_xticks(x_indices)
        ax1.set_xticklabels([f"{c}\n({o} Orders)" for c, o in zip(categories, orders)], fontsize=10, color=PASTEL_TOKENS["slate"])
        ax1.set_ylim(0, max_sale * 1.22)
        ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: format_inr(v, compact=True)))

        # Styling Axis 2 (Margin)
        ax2.set_ylabel("Profit Margin (%)", fontsize=11, fontweight="bold", color=PASTEL_TOKENS["coral"], labelpad=10)
        margin_min = min(margins)
        margin_max = max(margins)
        lower_lim = min(0, margin_min - 4)
        upper_lim = max(margin_max * 1.4, 25.0)
        ax2.set_ylim(lower_lim, upper_lim)
        ax2.yaxis.set_major_formatter(ticker.PercentFormatter(decimals=0))

        # Grid and Spines
        ax1.grid(axis="y", linestyle="--", linewidth=0.7, color=PASTEL_TOKENS["grid_color"], zorder=0)
        ax1.spines["top"].set_visible(False)
        ax2.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)
        ax2.spines["left"].set_visible(False)
        ax1.spines["left"].set_color(PASTEL_TOKENS["slate_border"])
        ax1.spines["bottom"].set_color(PASTEL_TOKENS["slate_border"])
        ax2.spines["right"].set_color(PASTEL_TOKENS["coral_light"])
        ax2.tick_params(axis="y", colors=PASTEL_TOKENS["coral"])

        # Combined Legend
        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax1.legend(
            lines_1 + lines_2,
            labels_1 + labels_2,
            loc="upper left",
            frameon=True,
            facecolor=PASTEL_TOKENS["card_bg"],
            edgecolor=PASTEL_TOKENS["slate_border"],
            fontsize=9.5,
        )

        # Titles
        plt.title(
            "Category Sales Volume vs. Profit Margin Efficiency",
            fontsize=13,
            fontweight="bold",
            color=PASTEL_TOKENS["slate"],
            pad=18,
            loc="left",
        )
        fig.text(
            0.125,
            0.92,
            "Question 1 Part 1: Cross-category performance analysis highlighting revenue scale and margin quality",
            fontsize=8.5,
            color=PASTEL_TOKENS["slate_muted"],
        )

        plt.tight_layout(rect=[0, 0, 1, 0.94])
        fig.savefig(target_file, dpi=dpi, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.15)
        plt.close(fig)

        logger.info("Successfully generated category profitability chart at: %s", target_file)
        return target_file

    # -----------------------------------------------------------------------
    # Chart 2: Furniture Target vs. Actual Trajectory
    # -----------------------------------------------------------------------

    @classmethod
    def generate_furniture_target_chart(
        cls,
        furniture_data: List[FurnitureTargetAchievement],
        output_path: Union[Path, str],
        dpi: int = DPI,
    ) -> Path:
        """Renders monthly target vs. actual sales trajectory highlighting significant MoM fluctuations.

        Features:
        - Muted Gold line for Target Sales trajectory.
        - Soft Sage line for Actual Sales trajectory.
        - Shaded areas differentiating surplus (Actual >= Target) vs shortfall (Actual < Target).
        - Warm Coral shaded columns and badges highlighting months where |MoM| >= 15%.
        - Baseline month (Apr-18) explicitly indicated.

        Args:
            furniture_data: Chronological furniture achievement records.
            output_path: Path to save the PNG chart.
            dpi: Output resolution (default 300 DPI).

        Returns:
            Path: Resolved path of saved PNG file.

        Raises:
            TypeError: If furniture_data is not a sequence.
            ValueError: If furniture_data is empty.
        """
        if not isinstance(furniture_data, Sequence):
            raise TypeError(f"furniture_data must be a sequence, got {type(furniture_data).__name__}")
        if len(furniture_data) == 0:
            raise ValueError("furniture_data sequence cannot be empty")

        target_file = Path(output_path)
        target_file.parent.mkdir(parents=True, exist_ok=True)

        months = [r.display_month for r in furniture_data]
        targets = np.array([r.target_sales for r in furniture_data], dtype=float)
        actuals = np.array([r.actual_sales for r in furniture_data], dtype=float)
        fluctuations = [r.is_significant_fluctuation for r in furniture_data]
        mom_changes = [r.mom_target_pct_change for r in furniture_data]

        x_indices = np.arange(len(months))

        fig, ax = plt.subplots(figsize=(12, 6.2), dpi=dpi)
        fig.patch.set_facecolor(PASTEL_TOKENS["card_bg"])
        ax.set_facecolor(PASTEL_TOKENS["card_bg"])

        # Shaded Surplus & Shortfall areas
        ax.fill_between(
            x_indices,
            actuals,
            targets,
            where=(actuals >= targets),
            color=PASTEL_TOKENS["sage_tint"],
            alpha=0.85,
            interpolate=True,
            label="Achievement Surplus (Actual >= Target)",
            zorder=2,
        )
        ax.fill_between(
            x_indices,
            actuals,
            targets,
            where=(actuals < targets),
            color=PASTEL_TOKENS["coral_tint"],
            alpha=0.85,
            interpolate=True,
            label="Achievement Shortfall (Actual < Target)",
            zorder=2,
        )

        # Plot Trajectory Lines
        (target_line,) = ax.plot(
            x_indices,
            targets,
            color=PASTEL_TOKENS["gold"],
            linewidth=2.4,
            linestyle="--",
            marker="o",
            markersize=7,
            markerfacecolor=PASTEL_TOKENS["card_bg"],
            markeredgecolor=PASTEL_TOKENS["gold_border"],
            markeredgewidth=2.0,
            label="Monthly Target (Rs.)",
            zorder=4,
        )

        (actual_line,) = ax.plot(
            x_indices,
            actuals,
            color=PASTEL_TOKENS["sage_dark"],
            linewidth=2.8,
            linestyle="-",
            marker="s",
            markersize=7,
            markerfacecolor=PASTEL_TOKENS["sage"],
            markeredgecolor=PASTEL_TOKENS["sage_dark"],
            markeredgewidth=1.8,
            label="Actual Sales Achieved (Rs.)",
            zorder=5,
        )

        # Highlight Months with Significant Fluctuation (|MoM| >= 15%)
        flag_span_added = False
        for i, is_fluc in enumerate(fluctuations):
            if is_fluc:
                # Vertical highlight band
                span_label = "Significant MoM Shift (|MoM| >= 15%)" if not flag_span_added else None
                ax.axvspan(
                    i - 0.38,
                    i + 0.38,
                    facecolor=PASTEL_TOKENS["coral_light"],
                    alpha=0.22,
                    edgecolor=PASTEL_TOKENS["coral_border"],
                    linestyle=":",
                    linewidth=0.8,
                    zorder=1,
                    label=span_label,
                )
                flag_span_added = True

                # Callout badge for the MoM percentage
                mom_val = mom_changes[i]
                mom_str = f"{mom_val:+.1f}%" if mom_val is not None else ""
                ax.annotate(
                    f"MoM\n{mom_str}",
                    xy=(i, targets[i]),
                    xytext=(0, 24),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8.0,
                    fontweight="bold",
                    color=PASTEL_TOKENS["coral_dark"],
                    bbox=dict(
                        boxstyle="round,pad=0.25",
                        facecolor=PASTEL_TOKENS["coral_tint"],
                        edgecolor=PASTEL_TOKENS["coral_border"],
                        linewidth=1.0,
                        alpha=0.95,
                    ),
                    arrowprops=dict(
                        arrowstyle="->",
                        color=PASTEL_TOKENS["coral_border"],
                        lw=1.0,
                    ),
                    zorder=6,
                )

        # Baseline Callout for Apr-18
        if len(months) > 0:
            ax.annotate(
                "Baseline\n(MoM N/A)",
                xy=(0, targets[0]),
                xytext=(0, -28),
                textcoords="offset points",
                ha="center",
                va="top",
                fontsize=7.8,
                fontweight="semibold",
                color=PASTEL_TOKENS["slate_muted"],
                bbox=dict(
                    boxstyle="round,pad=0.2",
                    facecolor=PASTEL_TOKENS["grid_color"],
                    edgecolor=PASTEL_TOKENS["slate_border"],
                    linewidth=0.8,
                    alpha=0.9,
                ),
                arrowprops=dict(
                    arrowstyle="->",
                    color=PASTEL_TOKENS["slate_light"],
                    lw=0.8,
                ),
                zorder=6,
            )

        # Axes & Labels
        ax.set_xlabel("Fiscal Period (Chronological Months)", fontsize=11, fontweight="bold", color=PASTEL_TOKENS["slate"], labelpad=10)
        ax.set_ylabel("Furniture Sales Amount (Rs.)", fontsize=11, fontweight="bold", color=PASTEL_TOKENS["slate"], labelpad=10)
        ax.set_xticks(x_indices)
        ax.set_xticklabels(months, fontsize=9.5, color=PASTEL_TOKENS["slate"])

        max_val = max(np.max(targets), np.max(actuals)) if len(targets) > 0 else 1.0
        ax.set_ylim(0, max_val * 1.30)
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: format_inr(v, compact=True)))

        # Clean Spines and Grid
        ax.grid(axis="y", linestyle="--", linewidth=0.7, color=PASTEL_TOKENS["grid_color"], zorder=0)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(PASTEL_TOKENS["slate_border"])
        ax.spines["bottom"].set_color(PASTEL_TOKENS["slate_border"])

        # Legend
        ax.legend(
            loc="upper right",
            frameon=True,
            facecolor=PASTEL_TOKENS["card_bg"],
            edgecolor=PASTEL_TOKENS["slate_border"],
            fontsize=9.0,
            ncol=2,
        )

        # Titles
        plt.title(
            "Furniture Category: Sales Target vs. Actual Trajectory (FY 2018–19)",
            fontsize=13,
            fontweight="bold",
            color=PASTEL_TOKENS["slate"],
            pad=18,
            loc="left",
        )
        fig.text(
            0.125,
            0.92,
            "Question 1 Part 2: Chronological target reconciliation and structural MoM fluctuation tracking (|MoM| >= 15%)",
            fontsize=8.5,
            color=PASTEL_TOKENS["slate_muted"],
        )

        plt.tight_layout(rect=[0, 0, 1, 0.94])
        fig.savefig(target_file, dpi=dpi, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.15)
        plt.close(fig)

        logger.info("Successfully generated furniture target trajectory chart at: %s", target_file)
        return target_file

    # -----------------------------------------------------------------------
    # Chart 3: Regional Performance & Strategic Quadrants
    # -----------------------------------------------------------------------

    @classmethod
    def generate_regional_performance_chart(
        cls,
        state_data: List[StatePerformance],
        output_path: Union[Path, str],
        dpi: int = DPI,
    ) -> Path:
        """Renders comprehensive top 5 states order volume vs. profit margin analysis.

        Uses a publication-grade 2-panel figure:
        - Panel 1 (Left): Top 5 States Volume & Profitability horizontal breakdown.
        - Panel 2 (Right): 2D Regional Strategic Quadrant Matrix (Volume vs. Margin).

        Args:
            state_data: Ranked state performance records.
            output_path: Path to save the PNG chart.
            dpi: Output resolution (default 300 DPI).

        Returns:
            Path: Resolved path of saved PNG file.

        Raises:
            TypeError: If state_data is not a sequence.
            ValueError: If state_data is empty.
        """
        if not isinstance(state_data, Sequence):
            raise TypeError(f"state_data must be a sequence, got {type(state_data).__name__}")
        if len(state_data) == 0:
            raise ValueError("state_data sequence cannot be empty")

        target_file = Path(output_path)
        target_file.parent.mkdir(parents=True, exist_ok=True)

        states = [s.state for s in state_data]
        orders = [s.distinct_orders for s in state_data]
        sales = [s.total_sales for s in state_data]
        profits = [s.total_profit for s in state_data]
        margins = [s.profit_margin_pct for s in state_data]
        quadrants = [s.quadrant for s in state_data]
        ranks = [s.rank for s in state_data]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 6.2), dpi=dpi)
        fig.patch.set_facecolor(PASTEL_TOKENS["card_bg"])

        # -------------------------------------------------------------------
        # Panel 1: Horizontal Bar Chart of Top States by Order Volume
        # -------------------------------------------------------------------
        ax1.set_facecolor(PASTEL_TOKENS["card_bg"])

        # Invert order so Rank 1 appears at top
        y_pos = np.arange(len(states))[::-1]
        inv_orders = orders
        inv_margins = margins
        inv_sales = sales
        inv_profits = profits

        # Bar colors by quadrant
        bar_colors = []
        for q in quadrants:
            col_tuple = QUADRANT_COLORS.get(q, (PASTEL_TOKENS["sage"], PASTEL_TOKENS["sage_tint"]))
            bar_colors.append(col_tuple[0])

        bars = ax1.barh(
            y_pos,
            inv_orders,
            height=0.55,
            color=bar_colors,
            edgecolor=PASTEL_TOKENS["slate_border"],
            linewidth=1.2,
            zorder=3,
        )

        # Labels on bars
        max_orders = max(orders) if orders else 1
        for i, (b, o, m, s, p) in enumerate(zip(bars, inv_orders, inv_margins, inv_sales, inv_profits)):
            width = b.get_width()
            profit_prefix = "+" if p >= 0 else ""
            label_text = f" {o} orders | Margin: {m:+.1f}% | Sales: {format_inr(s, compact=True)} | Profit: {profit_prefix}{format_inr(p, compact=True)}"
            ax1.text(
                width + (max_orders * 0.02),
                b.get_y() + b.get_height() / 2,
                label_text,
                va="center",
                ha="left",
                fontsize=8.2,
                fontweight="semibold",
                color=PASTEL_TOKENS["slate"],
            )

        ax1.set_yticks(y_pos)
        ax1.set_yticklabels([f"#{r} {st}" for r, st in zip(ranks, states)], fontsize=10, fontweight="bold", color=PASTEL_TOKENS["slate"])
        ax1.set_xlabel("Distinct Order Volume", fontsize=10.5, fontweight="bold", color=PASTEL_TOKENS["slate"], labelpad=8)
        ax1.set_xlim(0, max_orders * 1.85)  # Extra room for label text
        ax1.grid(axis="x", linestyle="--", linewidth=0.7, color=PASTEL_TOKENS["grid_color"], zorder=0)
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)
        ax1.spines["left"].set_color(PASTEL_TOKENS["slate_border"])
        ax1.spines["bottom"].set_color(PASTEL_TOKENS["slate_border"])
        ax1.set_title("Top 5 States: Order Volume & Profitability", fontsize=11, fontweight="bold", color=PASTEL_TOKENS["slate"], loc="left", pad=10)

        # -------------------------------------------------------------------
        # Panel 2: 2D Strategic Regional Quadrants (Volume vs. Margin)
        # -------------------------------------------------------------------
        ax2.set_facecolor(PASTEL_TOKENS["card_bg"])

        vol_benchmark = float(np.median(orders))
        mar_benchmark = float(np.median(margins))

        min_vol = min(orders)
        max_vol = max(orders)
        min_mar = min(margins)
        max_mar = max(margins)

        x_pad = max(10, (max_vol - min_vol) * 0.25)
        y_pad = max(5.0, (max_mar - min_mar) * 0.3)

        x_min_plot = max(0, min_vol - x_pad)
        x_max_plot = max_vol + x_pad
        y_min_plot = min_mar - y_pad
        y_max_plot = max_mar + y_pad

        # Fill 4 Quadrant zones
        # 1. High Volume / High Margin (Top-Right): Soft Sage
        ax2.fill_between([vol_benchmark, x_max_plot], mar_benchmark, y_max_plot, color=PASTEL_TOKENS["sage_tint"], alpha=0.55, zorder=0)
        # 2. Low Volume / High Margin (Top-Left): Soft Lavender
        ax2.fill_between([x_min_plot, vol_benchmark], mar_benchmark, y_max_plot, color=PASTEL_TOKENS["lavender_tint"], alpha=0.55, zorder=0)
        # 3. High Volume / Low Margin (Bottom-Right): Muted Gold
        ax2.fill_between([vol_benchmark, x_max_plot], y_min_plot, mar_benchmark, color=PASTEL_TOKENS["gold_tint"], alpha=0.55, zorder=0)
        # 4. Low Volume / Low Margin (Bottom-Left): Warm Coral
        ax2.fill_between([x_min_plot, vol_benchmark], y_min_plot, mar_benchmark, color=PASTEL_TOKENS["coral_tint"], alpha=0.55, zorder=0)

        # Benchmark Crosshair Lines
        ax2.axvline(vol_benchmark, color=PASTEL_TOKENS["slate_muted"], linestyle="--", linewidth=1.2, zorder=2)
        ax2.axhline(mar_benchmark, color=PASTEL_TOKENS["slate_muted"], linestyle="--", linewidth=1.2, zorder=2)

        # Benchmark Badges
        ax2.text(
            vol_benchmark,
            y_min_plot + (y_pad * 0.2),
            f" Median Vol: {vol_benchmark:.0f}",
            fontsize=7.5,
            color=PASTEL_TOKENS["slate_muted"],
            fontweight="semibold",
            ha="left",
            va="bottom",
        )
        ax2.text(
            x_min_plot + (x_pad * 0.1),
            mar_benchmark + 0.5,
            f"Median Margin: {mar_benchmark:.1f}%",
            fontsize=7.5,
            color=PASTEL_TOKENS["slate_muted"],
            fontweight="semibold",
            ha="left",
            va="bottom",
        )

        # Quadrant Zone Labels
        ax2.text(x_max_plot - (x_pad * 0.1), y_max_plot - (y_pad * 0.2), "HIGH VOLUME\nHIGH MARGIN", ha="right", va="top", fontsize=8.0, fontweight="bold", color=PASTEL_TOKENS["sage_dark"], alpha=0.7)
        ax2.text(x_min_plot + (x_pad * 0.1), y_max_plot - (y_pad * 0.2), "LOW VOLUME\nHIGH MARGIN", ha="left", va="top", fontsize=8.0, fontweight="bold", color=PASTEL_TOKENS["lavender_dark"], alpha=0.7)
        ax2.text(x_max_plot - (x_pad * 0.1), y_min_plot + (y_pad * 0.2), "HIGH VOLUME\nLOW MARGIN", ha="right", va="bottom", fontsize=8.0, fontweight="bold", color=PASTEL_TOKENS["gold_dark"], alpha=0.7)
        ax2.text(x_min_plot + (x_pad * 0.1), y_min_plot + (y_pad * 0.2), "LOW VOLUME\nLOW MARGIN", ha="left", va="bottom", fontsize=8.0, fontweight="bold", color=PASTEL_TOKENS["coral_dark"], alpha=0.7)

        # Scatter Points for States
        for s in state_data:
            col_tuple = QUADRANT_COLORS.get(s.quadrant, (PASTEL_TOKENS["sage"], PASTEL_TOKENS["sage_tint"]))
            primary_col = col_tuple[0]
            tint_col = col_tuple[1]

            ax2.scatter(
                s.distinct_orders,
                s.profit_margin_pct,
                s=280,
                color=tint_col,
                edgecolors=primary_col,
                linewidth=2.2,
                zorder=5,
            )

            # Annotation with state name and rank
            ax2.annotate(
                f"{s.state} (#{s.rank})\n{s.profit_margin_pct:+.1f}% | {s.distinct_orders} ord",
                xy=(s.distinct_orders, s.profit_margin_pct),
                xytext=(0, 14),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8.0,
                fontweight="bold",
                color=PASTEL_TOKENS["slate"],
                bbox=dict(
                    boxstyle="round,pad=0.25",
                    facecolor=PASTEL_TOKENS["card_bg"],
                    edgecolor=primary_col,
                    linewidth=1.0,
                    alpha=0.92,
                ),
                zorder=6,
            )

        ax2.set_xlim(x_min_plot, x_max_plot)
        ax2.set_ylim(y_min_plot, y_max_plot)
        ax2.set_xlabel("Distinct Order Volume", fontsize=10.5, fontweight="bold", color=PASTEL_TOKENS["slate"], labelpad=8)
        ax2.set_ylabel("Profit Margin (%)", fontsize=10.5, fontweight="bold", color=PASTEL_TOKENS["slate"], labelpad=8)
        ax2.yaxis.set_major_formatter(ticker.PercentFormatter(decimals=1))
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        ax2.spines["left"].set_color(PASTEL_TOKENS["slate_border"])
        ax2.spines["bottom"].set_color(PASTEL_TOKENS["slate_border"])
        ax2.set_title("Strategic Regional Quadrant Matrix", fontsize=11, fontweight="bold", color=PASTEL_TOKENS["slate"], loc="left", pad=10)

        # Figure Titles
        plt.suptitle(
            "Regional Performance & Strategic Quadrant Classification",
            fontsize=13,
            fontweight="bold",
            color=PASTEL_TOKENS["slate"],
            x=0.08,
            y=0.98,
            ha="left",
        )
        fig.text(
            0.08,
            0.935,
            "Question 1 Part 3: Prioritizing state expansion vectors by transaction scale and profitability health",
            fontsize=8.5,
            color=PASTEL_TOKENS["slate_muted"],
        )

        plt.tight_layout(rect=[0, 0, 1, 0.93])
        fig.savefig(target_file, dpi=dpi, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.15)
        plt.close(fig)

        logger.info("Successfully generated regional performance chart at: %s", target_file)
        return target_file

    # -----------------------------------------------------------------------
    # Orchestration Method
    # -----------------------------------------------------------------------

    @classmethod
    def generate_all_charts(
        cls,
        category_data: List[CategoryPerformance],
        furniture_data: List[FurnitureTargetAchievement],
        state_data: List[StatePerformance],
        output_dir: Optional[Union[Path, str]] = None,
        dpi: int = DPI,
    ) -> Dict[str, Path]:
        """Renders and saves all 300 DPI publication pastel chart images.

        Renders:
        1. category_profitability.png (dual-axis bar and line chart)
        2. furniture_target_vs_actual.png & furniture_target_trajectory.png (monthly target vs actual sales trajectory)
        3. regional_performance.png & state_regional_quadrants.png (top 5 states volume vs margin analysis & quadrants)

        Args:
            category_data: Ranked category performance records.
            furniture_data: Chronological furniture achievement records.
            state_data: Ranked state performance records.
            output_dir: Target directory (defaults to CHART_ASSETS_DIR env or assets/charts/).
            dpi: Image resolution in dots-per-inch (default: 300).

        Returns:
            Dict[str, Path]: Mapping of chart identifiers to generated file paths.
        """
        resolved_dir = cls.resolve_output_dir(output_dir)

        # 1. Category Profitability Chart
        cat_file = resolved_dir / "category_profitability.png"
        cls.generate_category_profitability_chart(category_data, cat_file, dpi=dpi)

        # 2. Furniture Target Trajectory Chart
        furn_file_primary = resolved_dir / "furniture_target_vs_actual.png"
        furn_file_alias = resolved_dir / "furniture_target_trajectory.png"
        cls.generate_furniture_target_chart(furniture_data, furn_file_primary, dpi=dpi)

        # Also write alias or copy to ensure both naming schemes resolve seamlessly
        if furn_file_primary.exists():
            import shutil
            shutil.copyfile(furn_file_primary, furn_file_alias)

        # 3. Regional Performance & Quadrants Chart
        reg_file_primary = resolved_dir / "regional_performance.png"
        reg_file_alias = resolved_dir / "state_regional_quadrants.png"
        cls.generate_regional_performance_chart(state_data, reg_file_primary, dpi=dpi)

        if reg_file_primary.exists():
            import shutil
            shutil.copyfile(reg_file_primary, reg_file_alias)

        chart_manifest = {
            "category_profitability": cat_file,
            "furniture_target_vs_actual": furn_file_primary,
            "furniture_target_trajectory": furn_file_alias,
            "regional_performance": reg_file_primary,
            "state_regional_quadrants": reg_file_alias,
        }

        logger.info(
            "Successfully generated %d publication chart assets in '%s'",
            len(chart_manifest),
            resolved_dir,
        )
        return chart_manifest

    @classmethod
    def generate_from_data_dir(
        cls,
        data_dir: Optional[Union[Path, str]] = None,
        output_dir: Optional[Union[Path, str]] = None,
        fluctuation_threshold: float = 15.0,
        top_states_count: int = 5,
        dpi: int = DPI,
    ) -> Dict[str, Path]:
        """Loads data from data_dir, executes analytics engine, and renders all charts.

        Convenience orchestration pipeline linking DataLoader and AnalyticsEngine to
        ChartGenerator.

        Args:
            data_dir: Directory containing List of Orders.xlsx, Order Details.xlsx, Sales target.xlsx.
            output_dir: Target directory for chart PNGs (defaults to assets/charts/).
            fluctuation_threshold: MoM fluctuation threshold (default 15.0%).
            top_states_count: Number of top states to rank (default 5).
            dpi: Output resolution in DPI (default 300).

        Returns:
            Dict[str, Path]: Map of chart identifiers to generated file paths.
        """
        from src.data_loader import DataLoader

        resolved_data = Path(data_dir) if data_dir else Path(os.getenv("DATA_DIR", "data/input"))
        orders_path = resolved_data / "List of Orders.xlsx"
        details_path = resolved_data / "Order Details.xlsx"
        targets_path = resolved_data / "Sales target.xlsx"

        orders_df = DataLoader.load_orders(orders_path)
        details_df = DataLoader.load_order_details(details_path)
        targets_df = DataLoader.load_sales_targets(targets_path)

        merged_df = AnalyticsEngine.merge_orders(orders_df, details_df)
        cat_data = AnalyticsEngine.compute_category_performance(merged_df)
        furn_data = AnalyticsEngine.compute_furniture_target_mom(
            targets_df, merged_df, fluctuation_threshold_pct=fluctuation_threshold
        )
        state_data = AnalyticsEngine.compute_top_states_performance(
            orders_df, merged_df, top_n=top_states_count
        )

        return cls.generate_all_charts(
            category_data=cat_data,
            furniture_data=furn_data,
            state_data=state_data,
            output_dir=output_dir,
            dpi=dpi,
        )


def main() -> None:
    """CLI runner to generate publication charts."""
    import argparse

    parser = argparse.ArgumentParser(description="Render 300 DPI pastel charts for Jar assignment")
    parser.add_argument(
        "--data-dir",
        default=os.getenv("DATA_DIR", "data/input"),
        help="Path to input Excel directory (defaults to data/input)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.getenv("CHART_ASSETS_DIR", "assets/charts"),
        help="Target directory for rendered chart images (defaults to assets/charts)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Chart resolution in DPI (defaults to 300)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    manifest = ChartGenerator.generate_from_data_dir(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        dpi=args.dpi,
    )
    print(f"Generated {len(manifest)} charts in {args.output_dir}:")
    for key, path in manifest.items():
        print(f"  - {key}: {path}")


if __name__ == "__main__":
    main()

