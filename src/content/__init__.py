"""Content package for Jar Growth Intern strategic analysis and product teardowns.

Contains domain models, evaluation frameworks, and structured content for:
- Question 2: Jar App UX Teardown (strengths & prioritized frictions)
- Question 3: Fintech Business & Vertical Expansion Strategy
"""

from src.content.ux_teardown import (
    UXFrictionItem,
    UXStrengthItem,
    UXTeardownReport,
    UX_FRICTIONS,
    UX_STRENGTHS,
    UX_TEARDOWN_REPORT,
    get_ux_frictions,
    get_ux_strengths,
    get_ux_teardown_data,
    get_ux_teardown_report,
)

__all__ = [
    "UXStrengthItem",
    "UXFrictionItem",
    "UXTeardownReport",
    "UX_STRENGTHS",
    "UX_FRICTIONS",
    "UX_TEARDOWN_REPORT",
    "get_ux_strengths",
    "get_ux_frictions",
    "get_ux_teardown_report",
    "get_ux_teardown_data",
]
