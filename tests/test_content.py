"""Unit tests for Question 2 Jar App UX audit and Question 3 Growth Strategy content models.

Tests SPEC AC-2.1 and M2-TASK-01 requirements:
- Exactly 5 effective features / core strengths documented.
- Exactly 5 prioritized UX friction points documented.
- For each item: description, behavioral psychology / growth mechanics rationale,
  actionable solution / takeaway, and primary business impact metric.

Tests SPEC AC-3.1 and M2-TASK-02 requirements:
- Exactly 5 strategic growth verticals documented (Jar Cash, Jar Multi-Asset,
  Jar Family Vaults, Jar Earn, Jar for Work).
- Market opportunity sizing (TAM, SAM, SOM) with robust quantitative methodologies.
- Granular unit economics projections (CAC, LTV, LTV/CAC ratio, take-rates, payback).
- Integration blueprints explaining how Jar's automation and trust flywheel powers each vertical.
- Execution risk matrix with categorizations, severities, and institutional mitigation strategies.
- Immutability and input validation on dataclasses.
- JSON serialization integrity and lookup helpers.
"""

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import pytest

from src.export_service import ExportService
from src.main import main

from src.content.growth_strategy import (
    ExecutionRiskItem,
    GROWTH_STRATEGY_REPORT,
    GROWTH_VERTICALS,
    GrowthStrategyReport,
    GrowthVerticalItem,
    MarketSizing,
    PLATFORM_RISK_MATRIX,
    UnitEconomics,
    get_growth_strategy_data,
    get_growth_strategy_report,
    get_growth_verticals,
    get_market_sizing_summary,
    get_risk_matrix,
    get_unit_economics_summary,
)
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


# ===========================================================================
# 1. Primary Acceptance Criteria: SPEC AC-2.1
# ===========================================================================

def test_ux_teardown_completeness() -> None:
    """SPEC AC-2.1: Checks exactly 5 effective features and 5 prioritized UX friction points

    are documented with complete descriptions, behavioral psychology / growth mechanics
    rationale, actionable solutions, and primary impact metrics.
    """
    report = get_ux_teardown_report()
    assert isinstance(report, UXTeardownReport)

    # 1. Exactly 5 strengths
    assert len(report.strengths) == 5, f"Expected 5 strengths, found {len(report.strengths)}"
    assert len(UX_STRENGTHS) == 5

    # 2. Exactly 5 frictions
    assert len(report.frictions) == 5, f"Expected 5 frictions, found {len(report.frictions)}"
    assert len(UX_FRICTIONS) == 5

    # 3. Expected Strength Titles from SPEC
    expected_strength_titles = [
        "Frictionless UPI AutoPay Round-ups",
        "Sub-₹10 Micro-Savings Accessibility",
        "Daily Spin Habit Streaks & Variable Rewards",
        "Real-time Liquidity & Buyback Guarantee",
        "24K Vault Trust & Verification",
    ]
    actual_strength_titles = [s.title for s in report.strengths]
    assert actual_strength_titles == expected_strength_titles

    # 4. Validate completeness of every strength
    for s in report.strengths:
        assert s.id.startswith("STRENGTH-")
        assert len(s.title.strip()) > 5
        assert len(s.category.strip()) > 5
        assert len(s.description.strip()) >= 50, f"Description too brief for {s.id}"
        assert len(s.behavioral_psychology.strip()) >= 50, f"Psychology rationale too brief for {s.id}"
        assert len(s.growth_mechanism.strip()) >= 50, f"Growth mechanism too brief for {s.id}"
        assert len(s.actionable_takeaway.strip()) >= 30, f"Actionable takeaway too brief for {s.id}"
        assert len(s.primary_impact_metric.strip()) >= 20, f"Impact metric too brief for {s.id}"

        # Property aliases
        assert s.growth_mechanics == s.growth_mechanism
        assert s.behavioral_rationale == s.behavioral_psychology
        assert s.actionable_solution == s.actionable_takeaway
        assert s.impact_metric == s.primary_impact_metric

    # 5. Expected Friction Titles from SPEC
    expected_friction_titles = [
        "AutoPay Failure & Mandate Renewal Transparency",
        "Buy-Sell Spread / GST Perception Gap",
        "Notification Fatigue & Alert Granularity",
        "Asset Class Diversification Friction",
        "Family & Goal-Based Vault Separation",
    ]
    actual_friction_titles = [f.title for f in report.frictions]
    assert actual_friction_titles == expected_friction_titles

    # 6. Validate completeness of every friction point
    for f in report.frictions:
        assert f.id.startswith("FRICTION-")
        assert len(f.title.strip()) > 5
        assert f.priority in {"P0 - Critical", "P1 - High", "P2 - Medium"}
        assert len(f.description.strip()) >= 50, f"Description too brief for {f.id}"
        assert len(f.behavioral_friction.strip()) >= 50, f"Behavioral friction too brief for {f.id}"
        assert len(f.actionable_solution.strip()) >= 50, f"Actionable solution too brief for {f.id}"
        assert len(f.primary_impact_metric.strip()) >= 20, f"Impact metric too brief for {f.id}"
        assert f.implementation_effort in {"Low", "Medium", "High"}

        # Property aliases
        assert f.behavioral_psychology == f.behavioral_friction
        assert f.behavioral_rationale == f.behavioral_friction
        assert f.actionable_recommendation == f.actionable_solution
        assert f.impact_metric == f.primary_impact_metric


# ===========================================================================
# 2. Behavioral Psychology & Growth Mechanics Substantive Verification
# ===========================================================================

def test_behavioral_frameworks_depth() -> None:
    """Verifies that established behavioral psychology frameworks cited in SPEC

    are substantively embedded in the analyses.
    """
    all_text = " ".join(
        [
            s.description
            + " "
            + s.behavioral_psychology
            + " "
            + s.growth_mechanism
            + " "
            + s.actionable_takeaway
            + " "
            + s.primary_impact_metric
            for s in UX_STRENGTHS
        ]
        + [
            f.description
            + " "
            + f.behavioral_friction
            + " "
            + f.actionable_solution
            + " "
            + f.primary_impact_metric
            for f in UX_FRICTIONS
        ]
    ).lower()

    # Core cognitive frameworks required by SPEC AC-2.1
    assert "mental accounting" in all_text
    assert "variable reward" in all_text or "variable ratio" in all_text
    assert "hyperbolic discounting" in all_text
    assert "loss aversion" in all_text
    assert "cognitive overload" in all_text or "cognitive friction" in all_text

    # Specific metrics required by TASKS.json
    assert "retention" in all_text
    assert "autopay" in all_text or "auto-pay" in all_text
    assert "churn" in all_text
    assert "ltv" in all_text or "lifetime value" in all_text


# ===========================================================================
# 3. Serialization and Lookup Integrity
# ===========================================================================

def test_ux_teardown_serialization_and_json_compliance() -> None:
    """Verifies that the teardown data serializes cleanly to RFC 8259 JSON."""
    data = get_ux_teardown_data()
    assert isinstance(data, dict)
    assert "metadata" in data
    assert "strengths" in data
    assert "frictions" in data

    assert data["metadata"]["total_strengths"] == 5
    assert data["metadata"]["total_frictions"] == 5

    # Must serialize with json.dumps without error
    serialized_str = json.dumps(data, ensure_ascii=False, indent=2)
    assert len(serialized_str) > 1000

    # Round-trip verification
    deserialized = json.loads(serialized_str)
    assert len(deserialized["strengths"]) == 5
    assert len(deserialized["frictions"]) == 5


def test_ux_teardown_lookups_and_getters() -> None:
    """Tests getter functions and ID-based item lookups."""
    strengths = get_ux_strengths()
    frictions = get_ux_frictions()
    assert len(strengths) == 5
    assert len(frictions) == 5

    report = get_ux_teardown_report()

    # Successful lookups
    s1 = report.get_strength("STRENGTH-01")
    assert s1 is not None
    assert s1.title == "Frictionless UPI AutoPay Round-ups"

    f1 = report.get_friction("FRICTION-01")
    assert f1 is not None
    assert f1.title == "AutoPay Failure & Mandate Renewal Transparency"

    # Non-existent lookups
    assert report.get_strength("NON_EXISTENT") is None
    assert report.get_friction("NON_EXISTENT") is None


# ===========================================================================
# 4. Dataclass Immutability & Validation Guards
# ===========================================================================

def test_ux_strength_dataclass_validation() -> None:
    """Tests validation rules and immutability for UXStrengthItem."""
    valid_strength = UX_STRENGTHS[0]

    # Immutability check (frozen=True)
    with pytest.raises(FrozenInstanceError):
        valid_strength.title = "New Title"  # type: ignore[misc]

    # Empty field validation
    with pytest.raises(ValueError, match="id cannot be empty"):
        UXStrengthItem(
            id="",
            title="Title",
            category="Cat",
            description="Desc",
            behavioral_psychology="Psych",
            growth_mechanism="Growth",
            actionable_takeaway="Takeaway",
            primary_impact_metric="Metric",
        )

    with pytest.raises(ValueError, match="description cannot be empty"):
        UXStrengthItem(
            id="S-01",
            title="Title",
            category="Cat",
            description="   ",
            behavioral_psychology="Psych",
            growth_mechanism="Growth",
            actionable_takeaway="Takeaway",
            primary_impact_metric="Metric",
        )


def test_ux_friction_dataclass_validation() -> None:
    """Tests validation rules and immutability for UXFrictionItem."""
    valid_friction = UX_FRICTIONS[0]

    # Immutability check (frozen=True)
    with pytest.raises(FrozenInstanceError):
        valid_friction.priority = "P0"  # type: ignore[misc]

    # Invalid priority
    with pytest.raises(ValueError, match="priority must be one of"):
        UXFrictionItem(
            id="F-01",
            title="Title",
            priority="Urgent",
            description="Desc",
            behavioral_friction="Friction",
            actionable_solution="Solution",
            primary_impact_metric="Metric",
            implementation_effort="Low",
        )

    # Invalid implementation effort
    with pytest.raises(ValueError, match="implementation_effort must be"):
        UXFrictionItem(
            id="F-01",
            title="Title",
            priority="P0 - Critical",
            description="Desc",
            behavioral_friction="Friction",
            actionable_solution="Solution",
            primary_impact_metric="Metric",
            implementation_effort="Very Easy",
        )


def test_ux_teardown_report_validation() -> None:
    """Tests validation on UXTeardownReport structure."""
    valid_strengths = UX_STRENGTHS
    valid_frictions = UX_FRICTIONS

    # Must have exactly 5 strengths
    with pytest.raises(ValueError, match="must contain exactly 5 strengths"):
        UXTeardownReport(strengths=valid_strengths[:4], frictions=valid_frictions)

    # Must have exactly 5 frictions
    with pytest.raises(ValueError, match="must contain exactly 5 friction points"):
        UXTeardownReport(strengths=valid_strengths, frictions=valid_frictions[:3])

    # No duplicate IDs in strengths
    dup_strengths = [valid_strengths[0]] * 5
    with pytest.raises(ValueError, match="Duplicate strength IDs"):
        UXTeardownReport(strengths=dup_strengths, frictions=valid_frictions)

    # No duplicate IDs in frictions
    dup_frictions = [valid_frictions[0]] * 5
    with pytest.raises(ValueError, match="Duplicate friction IDs"):
        UXTeardownReport(strengths=valid_strengths, frictions=dup_frictions)


# ===========================================================================
# 5. Question 3 Primary Acceptance Criteria: SPEC AC-3.1
# ===========================================================================

def test_growth_strategy_completeness() -> None:
    """SPEC AC-3.1: Checks all 5 strategic growth verticals are documented with market opportunity

    sizing, unit economics projections, integration flywheel mechanics, and execution risks.
    """
    report = get_growth_strategy_report()
    assert isinstance(report, GrowthStrategyReport)

    # 1. Exactly 5 growth verticals
    assert len(report.verticals) == 5, f"Expected 5 verticals, found {len(report.verticals)}"
    assert len(GROWTH_VERTICALS) == 5

    # 2. Expected Vertical IDs and Names from SPEC & TASKS.json
    expected_verticals = [
        ("VERTICAL-01", "Jar Cash", "Gold-Backed Micro-Lending & Instant Credit Line"),
        ("VERTICAL-02", "Jar Multi-Asset", "Micro-SIPs in Silver ETFs & Sovereign Gold Bonds"),
        ("VERTICAL-03", "Jar Family Vaults", "Child Savings & Intergenerational Wealth Building"),
        ("VERTICAL-04", "Jar Earn", "Gold Leasing & Yield Generation (2-3% Annual Gold Yield)"),
        ("VERTICAL-05", "Jar for Work", "B2B Corporate Wellness & Gig-Worker Micro-Benefits SDK"),
    ]

    for (exp_id, exp_name, exp_tagline), actual_v in zip(expected_verticals, report.verticals):
        assert actual_v.id == exp_id
        assert actual_v.name == exp_name
        assert actual_v.tagline == exp_tagline
        assert actual_v.title == f"{exp_name}: {exp_tagline}"

    # 3. Thorough validation of every vertical's content depth
    for v in report.verticals:
        # Identification & Descriptions
        assert v.id.startswith("VERTICAL-")
        assert len(v.name.strip()) >= 5
        assert len(v.tagline.strip()) >= 15
        assert len(v.strategic_rationale.strip()) >= 100, f"Strategic rationale too brief for {v.id}"
        assert len(v.target_persona.strip()) >= 30, f"Target persona too brief for {v.id}"
        assert len(v.flywheel_integration.strip()) >= 100, f"Flywheel integration too brief for {v.id}"

        # Market Sizing Depth
        assert len(v.market_sizing.tam.strip()) > 5
        assert len(v.market_sizing.sam.strip()) > 5
        assert len(v.market_sizing.som.strip()) > 5
        assert v.market_sizing.tam_numeric_cr > 0
        assert v.market_sizing.sam_numeric_cr > 0
        assert v.market_sizing.som_numeric_cr > 0
        assert v.market_sizing.tam_numeric_cr >= v.market_sizing.sam_numeric_cr >= v.market_sizing.som_numeric_cr
        assert len(v.market_sizing.methodology.strip()) >= 50

        # Unit Economics Depth
        assert v.unit_economics.cac_inr >= 0
        assert v.unit_economics.ltv_inr > 0
        assert v.unit_economics.ltv_cac_ratio > 0
        assert len(v.unit_economics.take_rate.strip()) >= 10
        assert v.unit_economics.payback_months >= 0
        assert len(v.unit_economics.economics_narrative.strip()) >= 50

        # Execution Risks
        assert len(v.execution_risks) >= 2, f"At least 2 execution risks required for {v.id}"
        for risk in v.execution_risks:
            assert len(risk.risk_title.strip()) >= 10
            assert len(risk.risk_category.strip()) >= 4
            assert risk.severity in {"High", "Medium", "Low"}
            assert len(risk.mitigation_strategy.strip()) >= 30

        # Primary KPIs
        assert len(v.primary_kpis) >= 3, f"At least 3 KPIs required for {v.id}"
        for kpi in v.primary_kpis:
            assert len(kpi.strip()) >= 5

        # Property Aliases
        assert v.title == f"{v.name}: {v.tagline}"
        assert v.description == v.strategic_rationale
        assert v.flywheel_mechanics == v.flywheel_integration
        assert v.market_opportunity == v.market_sizing


# ===========================================================================
# 6. Market Sizing & Unit Economics Quantitative Logic
# ===========================================================================

def test_growth_strategy_market_sizing_math_and_logic() -> None:
    """Verifies that TAM >= SAM >= SOM mathematical hierarchy holds across all verticals

    and aggregate market opportunity calculations are accurate.
    """
    report = get_growth_strategy_report()

    running_tam = 0.0
    running_sam = 0.0
    running_som = 0.0

    for v in report.verticals:
        ms = v.market_sizing
        assert ms.tam_numeric_cr >= ms.sam_numeric_cr, f"TAM must be >= SAM in {v.id}"
        assert ms.sam_numeric_cr >= ms.som_numeric_cr, f"SAM must be >= SOM in {v.id}"
        running_tam += ms.tam_numeric_cr
        running_sam += ms.sam_numeric_cr
        running_som += ms.som_numeric_cr

    assert round(report.total_tam_cr, 2) == round(running_tam, 2)
    assert round(report.total_sam_cr, 2) == round(running_sam, 2)
    assert round(report.total_som_cr, 2) == round(running_som, 2)

    # Market sizing summary accessor helper
    summary = get_market_sizing_summary()
    assert summary["total_tam_inr_cr"] == report.total_tam_cr
    assert summary["total_sam_inr_cr"] == report.total_sam_cr
    assert summary["total_som_inr_cr"] == report.total_som_cr
    assert summary["total_tam_usd_b"] > 0
    assert summary["total_sam_usd_b"] > 0
    assert summary["total_som_usd_b"] > 0
    assert len(summary["vertical_breakdown"]) == 5


def test_growth_strategy_unit_economics_validation() -> None:
    """Verifies that unit economics metrics (CAC, LTV, LTV/CAC, Payback) are commercially

    viable, mathematically consistent, and backed by detailed narratives.
    """
    report = get_growth_strategy_report()

    for v in report.verticals:
        ue = v.unit_economics
        # LTV should be substantially higher than CAC for healthy fintech economics
        assert ue.ltv_inr > ue.cac_inr, f"LTV must exceed CAC for viable unit economics in {v.id}"
        assert ue.cac_inr >= 100, f"CAC should be in the hundreds of rupees in {v.id}"
        # LTV:CAC must equal LTV / CAC exactly (rounded to 1 decimal)
        assert ue.ltv_cac_ratio == round(ue.ltv_inr / ue.cac_inr, 1)
        # Realistic Indian consumer fintech ranges
        assert 2.5 <= ue.ltv_cac_ratio <= 6.0, f"LTV:CAC outside 2.5x-6x in {v.id}"
        assert 4.0 <= ue.payback_months <= 18.0, f"Payback outside 4-18 months in {v.id}"

    # Unit economics summary helper
    ue_summary = get_unit_economics_summary()
    assert ue_summary["average_cac_inr"] > 0
    assert ue_summary["average_ltv_inr"] > ue_summary["average_cac_inr"]
    assert 2.5 <= ue_summary["blended_ltv_cac_ratio"] <= 6.0
    assert 4.0 <= ue_summary["average_payback_months"] <= 18.0
    assert len(ue_summary["vertical_unit_economics"]) == 5


# ===========================================================================
# 7. Dataclass Immutability & Validation Guards
# ===========================================================================

def test_growth_strategy_dataclass_validation() -> None:
    """Tests validation rules and immutability for all growth strategy dataclasses."""
    valid_vertical = GROWTH_VERTICALS[0]
    valid_sizing = valid_vertical.market_sizing
    valid_ue = valid_vertical.unit_economics
    valid_risk = valid_vertical.execution_risks[0]

    # Immutability checks (frozen=True)
    with pytest.raises(FrozenInstanceError):
        valid_vertical.name = "New Name"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        valid_sizing.tam = "New TAM"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        valid_ue.cac_inr = 999.0  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        valid_risk.severity = "Low"  # type: ignore[misc]

    # MarketSizing validation
    with pytest.raises(ValueError, match="tam cannot be empty"):
        MarketSizing(
            tam="",
            tam_numeric_cr=100.0,
            sam="SAM",
            sam_numeric_cr=50.0,
            som="SOM",
            som_numeric_cr=10.0,
            methodology="Methodology",
        )

    with pytest.raises(ValueError, match="sam cannot be empty"):
        MarketSizing(
            tam="TAM",
            tam_numeric_cr=100.0,
            sam="",
            sam_numeric_cr=50.0,
            som="SOM",
            som_numeric_cr=10.0,
            methodology="Methodology",
        )

    with pytest.raises(ValueError, match="som cannot be empty"):
        MarketSizing(
            tam="TAM",
            tam_numeric_cr=100.0,
            sam="SAM",
            sam_numeric_cr=50.0,
            som="",
            som_numeric_cr=10.0,
            methodology="Methodology",
        )

    with pytest.raises(ValueError, match="methodology cannot be empty"):
        MarketSizing(
            tam="TAM",
            tam_numeric_cr=100.0,
            sam="SAM",
            sam_numeric_cr=50.0,
            som="SOM",
            som_numeric_cr=10.0,
            methodology="",
        )

    with pytest.raises(ValueError, match="tam_numeric_cr must be positive"):
        MarketSizing(
            tam="TAM",
            tam_numeric_cr=-1.0,
            sam="SAM",
            sam_numeric_cr=50.0,
            som="SOM",
            som_numeric_cr=10.0,
            methodology="Methodology",
        )

    with pytest.raises(ValueError, match="sam_numeric_cr must be positive"):
        MarketSizing(
            tam="TAM",
            tam_numeric_cr=100.0,
            sam="SAM",
            sam_numeric_cr=0.0,
            som="SOM",
            som_numeric_cr=10.0,
            methodology="Methodology",
        )

    with pytest.raises(ValueError, match="som_numeric_cr must be positive"):
        MarketSizing(
            tam="TAM",
            tam_numeric_cr=100.0,
            sam="SAM",
            sam_numeric_cr=50.0,
            som="SOM",
            som_numeric_cr=-5.0,
            methodology="Methodology",
        )

    with pytest.raises(ValueError, match="cannot be smaller than sam"):
        MarketSizing(
            tam="100",
            tam_numeric_cr=40.0,
            sam="200",
            sam_numeric_cr=80.0,
            som="10",
            som_numeric_cr=10.0,
            methodology="Methodology",
        )

    with pytest.raises(ValueError, match="cannot be smaller than som"):
        MarketSizing(
            tam="100",
            tam_numeric_cr=100.0,
            sam="50",
            sam_numeric_cr=50.0,
            som="80",
            som_numeric_cr=80.0,
            methodology="Methodology",
        )

    # UnitEconomics validation
    with pytest.raises(ValueError, match="cac_inr cannot be negative"):
        UnitEconomics(
            cac_inr=-10.0,
            ltv_inr=100.0,
            ltv_cac_ratio=10.0,
            take_rate="2%",
            payback_months=1.0,
            economics_narrative="Desc",
        )

    with pytest.raises(ValueError, match="ltv_inr must be positive"):
        UnitEconomics(
            cac_inr=10.0,
            ltv_inr=0.0,
            ltv_cac_ratio=10.0,
            take_rate="2%",
            payback_months=1.0,
            economics_narrative="Desc",
        )

    with pytest.raises(ValueError, match="ltv_cac_ratio must be positive"):
        UnitEconomics(
            cac_inr=10.0,
            ltv_inr=100.0,
            ltv_cac_ratio=-1.0,
            take_rate="2%",
            payback_months=1.0,
            economics_narrative="Desc",
        )

    with pytest.raises(ValueError, match="take_rate cannot be empty"):
        UnitEconomics(
            cac_inr=10.0,
            ltv_inr=100.0,
            ltv_cac_ratio=10.0,
            take_rate="",
            payback_months=1.0,
            economics_narrative="Desc",
        )

    with pytest.raises(ValueError, match="payback_months cannot be negative"):
        UnitEconomics(
            cac_inr=10.0,
            ltv_inr=100.0,
            ltv_cac_ratio=10.0,
            take_rate="2%",
            payback_months=-0.5,
            economics_narrative="Desc",
        )

    with pytest.raises(ValueError, match="economics_narrative cannot be empty"):
        UnitEconomics(
            cac_inr=10.0,
            ltv_inr=100.0,
            ltv_cac_ratio=10.0,
            take_rate="2%",
            payback_months=1.0,
            economics_narrative="  ",
        )

    # ExecutionRiskItem validation
    with pytest.raises(ValueError, match="risk_title cannot be empty"):
        ExecutionRiskItem(
            risk_title="",
            risk_category="Regulatory",
            severity="High",
            mitigation_strategy="Mitigate",
        )

    with pytest.raises(ValueError, match="risk_category cannot be empty"):
        ExecutionRiskItem(
            risk_title="Title",
            risk_category="",
            severity="High",
            mitigation_strategy="Mitigate",
        )

    with pytest.raises(ValueError, match="severity must be one of"):
        ExecutionRiskItem(
            risk_title="Title",
            risk_category="Regulatory",
            severity="Extreme",
            mitigation_strategy="Mitigate",
        )

    with pytest.raises(ValueError, match="mitigation_strategy cannot be empty"):
        ExecutionRiskItem(
            risk_title="Title",
            risk_category="Regulatory",
            severity="High",
            mitigation_strategy="",
        )

    # GrowthVerticalItem validation
    with pytest.raises(ValueError, match="id cannot be empty"):
        GrowthVerticalItem(
            id="",
            name="Name",
            tagline="Tagline",
            strategic_rationale="Rationale",
            target_persona="Persona",
            market_sizing=valid_sizing,
            unit_economics=valid_ue,
            flywheel_integration="Flywheel",
            execution_risks=[valid_risk],
            primary_kpis=["KPI 1"],
        )

    with pytest.raises(ValueError, match="name cannot be empty"):
        GrowthVerticalItem(
            id="V-99",
            name="",
            tagline="Tagline",
            strategic_rationale="Rationale",
            target_persona="Persona",
            market_sizing=valid_sizing,
            unit_economics=valid_ue,
            flywheel_integration="Flywheel",
            execution_risks=[valid_risk],
            primary_kpis=["KPI 1"],
        )

    with pytest.raises(ValueError, match="tagline cannot be empty"):
        GrowthVerticalItem(
            id="V-99",
            name="Name",
            tagline="",
            strategic_rationale="Rationale",
            target_persona="Persona",
            market_sizing=valid_sizing,
            unit_economics=valid_ue,
            flywheel_integration="Flywheel",
            execution_risks=[valid_risk],
            primary_kpis=["KPI 1"],
        )

    with pytest.raises(ValueError, match="strategic_rationale cannot be empty"):
        GrowthVerticalItem(
            id="V-99",
            name="Name",
            tagline="Tagline",
            strategic_rationale="",
            target_persona="Persona",
            market_sizing=valid_sizing,
            unit_economics=valid_ue,
            flywheel_integration="Flywheel",
            execution_risks=[valid_risk],
            primary_kpis=["KPI 1"],
        )

    with pytest.raises(ValueError, match="target_persona cannot be empty"):
        GrowthVerticalItem(
            id="V-99",
            name="Name",
            tagline="Tagline",
            strategic_rationale="Rationale",
            target_persona="",
            market_sizing=valid_sizing,
            unit_economics=valid_ue,
            flywheel_integration="Flywheel",
            execution_risks=[valid_risk],
            primary_kpis=["KPI 1"],
        )

    with pytest.raises(ValueError, match="flywheel_integration cannot be empty"):
        GrowthVerticalItem(
            id="V-99",
            name="Name",
            tagline="Tagline",
            strategic_rationale="Rationale",
            target_persona="Persona",
            market_sizing=valid_sizing,
            unit_economics=valid_ue,
            flywheel_integration="",
            execution_risks=[valid_risk],
            primary_kpis=["KPI 1"],
        )

    with pytest.raises(ValueError, match="execution_risks cannot be empty"):
        GrowthVerticalItem(
            id="V-99",
            name="Name",
            tagline="Tagline",
            strategic_rationale="Rationale",
            target_persona="Persona",
            market_sizing=valid_sizing,
            unit_economics=valid_ue,
            flywheel_integration="Flywheel",
            execution_risks=[],
            primary_kpis=["KPI 1"],
        )

    with pytest.raises(ValueError, match="primary_kpis cannot be empty"):
        GrowthVerticalItem(
            id="V-99",
            name="Name",
            tagline="Tagline",
            strategic_rationale="Rationale",
            target_persona="Persona",
            market_sizing=valid_sizing,
            unit_economics=valid_ue,
            flywheel_integration="Flywheel",
            execution_risks=[valid_risk],
            primary_kpis=[],
        )

    # GrowthStrategyReport validation
    with pytest.raises(ValueError, match="must contain exactly 5 growth verticals"):
        GrowthStrategyReport(
            verticals=GROWTH_VERTICALS[:3],
            execution_risk_matrix=PLATFORM_RISK_MATRIX,
            global_flywheel_narrative="Narrative",
        )

    dup_verticals = [GROWTH_VERTICALS[0]] * 5
    with pytest.raises(ValueError, match="Duplicate vertical IDs"):
        GrowthStrategyReport(
            verticals=dup_verticals,
            execution_risk_matrix=PLATFORM_RISK_MATRIX,
            global_flywheel_narrative="Narrative",
        )

    with pytest.raises(ValueError, match="execution_risk_matrix cannot be empty"):
        GrowthStrategyReport(
            verticals=GROWTH_VERTICALS,
            execution_risk_matrix=[],
            global_flywheel_narrative="Narrative",
        )

    with pytest.raises(ValueError, match="global_flywheel_narrative cannot be empty"):
        GrowthStrategyReport(
            verticals=GROWTH_VERTICALS,
            execution_risk_matrix=PLATFORM_RISK_MATRIX,
            global_flywheel_narrative="   ",
        )


# ===========================================================================
# 8. Serialization, Lookups, and Flywheel Matrix Depth
# ===========================================================================

def test_growth_strategy_serialization_and_json_compliance() -> None:
    """Verifies that growth strategy data serializes cleanly to RFC 8259 JSON."""
    data = get_growth_strategy_data()
    assert isinstance(data, dict)
    assert "metadata" in data
    assert "verticals" in data
    assert "execution_risk_matrix" in data
    assert "global_flywheel_narrative" in data

    assert data["metadata"]["total_verticals"] == 5
    assert data["metadata"]["total_tam_cr"] > 0
    assert data["metadata"]["total_sam_cr"] > 0
    assert data["metadata"]["total_som_cr"] > 0

    # Serialization roundtrip test
    serialized = json.dumps(data, ensure_ascii=False, indent=2)
    assert len(serialized) > 2000

    deserialized = json.loads(serialized)
    assert len(deserialized["verticals"]) == 5
    assert len(deserialized["execution_risk_matrix"]) >= 4


def test_growth_strategy_lookups_and_getters() -> None:
    """Tests getter functions and ID-based vertical lookups."""
    verticals = get_growth_verticals()
    assert len(verticals) == 5

    report = get_growth_strategy_report()

    # Successful lookups
    v1 = report.get_vertical("VERTICAL-01")
    assert v1 is not None
    assert v1.name == "Jar Cash"

    v4 = report.get_vertical("VERTICAL-04")
    assert v4 is not None
    assert v4.name == "Jar Earn"

    # Non-existent lookup
    assert report.get_vertical("UNKNOWN_ID") is None

    # Risk matrix getter
    risks = get_risk_matrix()
    assert len(risks) >= 4
    for r in risks:
        assert isinstance(r, ExecutionRiskItem)


def test_growth_flywheel_and_risk_matrix_depth() -> None:
    """Verifies substantive fintech concepts, regulatory compliance terminology,

    and flywheel mechanics embedded in the expansion strategy.
    """
    report = get_growth_strategy_report()
    flywheel_text = report.global_flywheel_narrative.lower()

    # Flywheel mechanics
    assert "flywheel" in flywheel_text
    assert "round-up" in flywheel_text or "roundup" in flywheel_text
    assert "collateral" in flywheel_text
    assert "retention" in flywheel_text

    # Cross-vertical fintech and regulatory concepts
    all_content = " ".join(
        [
            v.strategic_rationale
            + " "
            + v.flywheel_integration
            + " "
            + " ".join(r.mitigation_strategy for r in v.execution_risks)
            for v in report.verticals
        ]
        + [r.mitigation_strategy for r in report.execution_risk_matrix]
    ).lower()

    # Fintech ecosystem terms
    assert "rbi" in all_content
    assert "nbfc" in all_content
    assert "autopay" in all_content or "upi" in all_content
    assert "vault" in all_content
    assert "sebi" in all_content or "amfi" in all_content
    assert "ltv" in all_content


# ===========================================================================
# 9. Strategy Content Export & JSON Serialization Service: M2-TASK-03
# ===========================================================================

def test_content_exports(tmp_path: Path) -> None:
    """SPEC AC-2.1, AC-3.1: Validates export_ux_teardown and export_growth_strategy
    file creation, RFC 8259 JSON validity, and content schema structure.
    """
    service = ExportService(output_dir=tmp_path)

    # 1. Export UX Teardown
    ux_file = service.export_ux_teardown()
    assert ux_file == tmp_path / "ux_teardown.json"
    assert ux_file.exists()
    assert ux_file.stat().st_size > 0

    # 2. Export Growth Strategy
    strategy_file = service.export_growth_strategy()
    assert strategy_file == tmp_path / "growth_strategy.json"
    assert strategy_file.exists()
    assert strategy_file.stat().st_size > 0

    # 3. Validate UX Teardown JSON Structure
    with open(ux_file, "r", encoding="utf-8") as f:
        ux_data = json.load(f)

    assert isinstance(ux_data, dict)
    assert set(ux_data.keys()) == {"metadata", "strengths", "frictions"}

    metadata_ux = ux_data["metadata"]
    assert metadata_ux["app_name"] == "Jar: Daily Gold Savings"
    assert metadata_ux["total_strengths"] == 5
    assert metadata_ux["total_frictions"] == 5

    assert len(ux_data["strengths"]) == 5
    expected_strength_keys = {
        "id", "title", "category", "description",
        "behavioral_psychology", "growth_mechanism",
        "actionable_takeaway", "primary_impact_metric",
    }
    for item in ux_data["strengths"]:
        assert set(item.keys()) == expected_strength_keys
        assert item["id"].startswith("STRENGTH-")
        assert len(item["title"]) > 0

    assert len(ux_data["frictions"]) == 5
    expected_friction_keys = {
        "id", "title", "priority", "description",
        "behavioral_friction", "actionable_solution",
        "primary_impact_metric", "implementation_effort",
    }
    for item in ux_data["frictions"]:
        assert set(item.keys()) == expected_friction_keys
        assert item["id"].startswith("FRICTION-")
        assert item["priority"] in {"P0 - Critical", "P1 - High", "P2 - Medium"}
        assert item["implementation_effort"] in {"Low", "Medium", "High"}

    # 4. Validate Growth Strategy JSON Structure
    with open(strategy_file, "r", encoding="utf-8") as f:
        strategy_data = json.load(f)

    assert isinstance(strategy_data, dict)
    assert set(strategy_data.keys()) == {
        "metadata", "verticals", "execution_risk_matrix", "global_flywheel_narrative",
    }

    metadata_strat = strategy_data["metadata"]
    assert metadata_strat["total_verticals"] == 5
    assert metadata_strat["total_tam_cr"] == 442000.0
    assert metadata_strat["total_sam_cr"] == 60000.0
    assert metadata_strat["total_som_cr"] == 864.0

    assert len(strategy_data["verticals"]) == 5
    expected_vertical_keys = {
        "id", "name", "tagline", "title", "strategic_rationale",
        "target_persona", "market_sizing", "unit_economics",
        "flywheel_integration", "execution_risks", "primary_kpis",
    }
    for item in strategy_data["verticals"]:
        assert set(item.keys()) == expected_vertical_keys
        assert item["id"].startswith("VERTICAL-")

        # Market sizing sub-object
        ms = item["market_sizing"]
        assert {"tam", "tam_numeric_cr", "sam", "sam_numeric_cr", "som", "som_numeric_cr", "methodology"} <= set(ms.keys())
        assert ms["tam_numeric_cr"] >= ms["sam_numeric_cr"] >= ms["som_numeric_cr"]

        # Unit economics sub-object
        ue = item["unit_economics"]
        assert {"cac_inr", "ltv_inr", "ltv_cac_ratio", "take_rate", "payback_months", "economics_narrative"} <= set(ue.keys())
        assert ue["ltv_inr"] > ue["cac_inr"]

        # Execution risks
        assert len(item["execution_risks"]) >= 2
        for r in item["execution_risks"]:
            assert {"risk_title", "risk_category", "severity", "mitigation_strategy"} <= set(r.keys())

        # KPIs
        assert len(item["primary_kpis"]) >= 3

    assert len(strategy_data["execution_risk_matrix"]) >= 4
    for r in strategy_data["execution_risk_matrix"]:
        assert {"risk_title", "risk_category", "severity", "mitigation_strategy"} <= set(r.keys())

    assert len(strategy_data["global_flywheel_narrative"]) > 100


def test_export_ux_teardown_custom_report_and_dict(tmp_path: Path) -> None:
    """Tests export_ux_teardown with explicit UXTeardownReport and dict instances."""
    service = ExportService(output_dir=tmp_path)
    custom_dir = tmp_path / "custom_ux"

    # With report instance
    report = get_ux_teardown_report()
    path1 = service.export_ux_teardown(report=report, output_dir=custom_dir)
    assert path1 == custom_dir / "ux_teardown.json"
    assert path1.exists()

    with open(path1, "r", encoding="utf-8") as f:
        data1 = json.load(f)
    assert data1["metadata"]["total_strengths"] == 5

    # With dict
    dict_payload = {"metadata": {"test": True}, "strengths": [], "frictions": []}
    custom_dir_2 = tmp_path / "dict_ux"
    path2 = service.export_ux_teardown(report=dict_payload, output_dir=custom_dir_2)
    assert path2 == custom_dir_2 / "ux_teardown.json"
    assert path2.exists()

    with open(path2, "r", encoding="utf-8") as f:
        data2 = json.load(f)
    assert data2["metadata"]["test"] is True


def test_export_growth_strategy_custom_report_and_dict(tmp_path: Path) -> None:
    """Tests export_growth_strategy with explicit GrowthStrategyReport and dict instances."""
    service = ExportService(output_dir=tmp_path)
    custom_dir = tmp_path / "custom_strategy"

    # With report instance
    report = get_growth_strategy_report()
    path1 = service.export_growth_strategy(report=report, output_dir=custom_dir)
    assert path1 == custom_dir / "growth_strategy.json"
    assert path1.exists()

    with open(path1, "r", encoding="utf-8") as f:
        data1 = json.load(f)
    assert data1["metadata"]["total_verticals"] == 5

    # With dict
    dict_payload = {"metadata": {"custom_strategy": 123}, "verticals": []}
    custom_dir_2 = tmp_path / "dict_strategy"
    path2 = service.export_growth_strategy(report=dict_payload, output_dir=custom_dir_2)
    assert path2 == custom_dir_2 / "growth_strategy.json"
    assert path2.exists()

    with open(path2, "r", encoding="utf-8") as f:
        data2 = json.load(f)
    assert data2["metadata"]["custom_strategy"] == 123


def test_export_strategy_invalid_inputs(tmp_path: Path) -> None:
    """Tests boundary validation and error handling for strategy exports."""
    service = ExportService(output_dir=tmp_path)

    # Invalid types for UX teardown
    with pytest.raises(TypeError, match="report must be UXTeardownReport, dict, or None"):
        service.export_ux_teardown(report=12345)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="report must be UXTeardownReport, dict, or None"):
        service.export_ux_teardown(report=["invalid", "list"])  # type: ignore[arg-type]

    # Invalid types for Growth strategy
    with pytest.raises(TypeError, match="report must be GrowthStrategyReport, dict, or None"):
        service.export_growth_strategy(report="invalid_string")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="report must be GrowthStrategyReport, dict, or None"):
        service.export_growth_strategy(report=[1, 2, 3])  # type: ignore[arg-type]


def test_main_cli_exports_strategy_files(tmp_path: Path) -> None:
    """Tests that main() CLI invocation persists ux_teardown.json and growth_strategy.json."""
    output_dir = tmp_path / "pipeline_out"
    exit_code = main([
        "--output-dir", str(output_dir),
        "--quiet",
    ])
    assert exit_code == 0

    ux_json = output_dir / "ux_teardown.json"
    strategy_json = output_dir / "growth_strategy.json"

    assert ux_json.exists()
    assert strategy_json.exists()
    assert ux_json.stat().st_size > 500
    assert strategy_json.stat().st_size > 1000

    # Validate JSON parses without error
    with open(ux_json, "r", encoding="utf-8") as f:
        ux_data = json.load(f)
    assert len(ux_data["strengths"]) == 5
    assert len(ux_data["frictions"]) == 5

    with open(strategy_json, "r", encoding="utf-8") as f:
        strat_data = json.load(f)
    assert len(strat_data["verticals"]) == 5
    assert len(strat_data["execution_risk_matrix"]) >= 4


