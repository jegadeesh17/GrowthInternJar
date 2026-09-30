"""Unit tests for the Question 2 app teardown and Question 3 growth strategy content models.

Question 2: exactly 5 strengths and 5 areas to improve, each with a description,
the reasoning behind it, a suggested next step and a metric to watch.

Question 3: new business opportunities, each with a rationale, who it is for,
how it earns, an illustrative scale with the reason for each assumption, how it
uses Jar's strengths, risks and KPIs, plus two prioritised first moves.
"""

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import pytest

from src.export_service import ExportService
from src.main import main

from src.content.growth_strategy import (
    ExecutionRiskItem,
    GROWTH_VERTICALS,
    GrowthStrategyReport,
    GrowthVerticalItem,
    get_growth_strategy_data,
    get_growth_strategy_report,
    get_growth_verticals,
)
from src.content.ux_teardown import (
    UXFrictionItem,
    UXStrengthItem,
    UXTeardownReport,
    UX_FRICTIONS,
    UX_STRENGTHS,
    get_ux_frictions,
    get_ux_strengths,
    get_ux_teardown_data,
    get_ux_teardown_report,
)


# ===========================================================================
# 1. Question 2: completeness
# ===========================================================================

def test_ux_teardown_completeness() -> None:
    """Checks exactly 5 strengths and 5 friction points, each fully filled in."""
    report = get_ux_teardown_report()
    assert isinstance(report, UXTeardownReport)

    assert len(report.strengths) == 5, f"Expected 5 strengths, found {len(report.strengths)}"
    assert len(UX_STRENGTHS) == 5
    assert len(report.frictions) == 5, f"Expected 5 frictions, found {len(report.frictions)}"
    assert len(UX_FRICTIONS) == 5

    expected_strength_titles = [
        "Automatic saving",
        "Start with ₹10",
        "Spins, coupons and referral bonuses",
        "Fast withdrawals",
        "Visible trust signals",
    ]
    assert [s.title for s in report.strengths] == expected_strength_titles

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

    expected_friction_titles = [
        "The day-one value drop is easy to miss",
        "Notification controls are too coarse",
        "Round-off is hard to understand",
        "Goal saving stops at festivals",
        "Nothing beyond gold for savers who want to diversify",
    ]
    assert [f.title for f in report.frictions] == expected_friction_titles

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


def test_ux_teardown_covers_core_topics() -> None:
    """Each item explains the behaviour behind it and names a metric to watch."""
    all_text = " ".join(
        [
            " ".join([s.description, s.behavioral_psychology, s.growth_mechanism,
                      s.actionable_takeaway, s.primary_impact_metric])
            for s in UX_STRENGTHS
        ]
        + [
            " ".join([f.description, f.behavioral_friction, f.actionable_solution,
                      f.primary_impact_metric])
            for f in UX_FRICTIONS
        ]
    ).lower()

    assert "spare change" in all_text
    assert "gst" in all_text
    assert "retention" in all_text
    assert "autopay" in all_text
    assert "churn" in all_text
    assert "notification" in all_text


# ===========================================================================
# 2. Question 2: serialization, lookups and validation
# ===========================================================================

def test_ux_teardown_serialization_and_json_compliance() -> None:
    """Verifies that the teardown data serializes cleanly to RFC 8259 JSON."""
    data = get_ux_teardown_data()
    assert isinstance(data, dict)
    assert set(data) == {"metadata", "strengths", "frictions"}
    assert data["metadata"]["total_strengths"] == 5
    assert data["metadata"]["total_frictions"] == 5

    serialized_str = json.dumps(data, ensure_ascii=False, indent=2)
    assert len(serialized_str) > 1000

    deserialized = json.loads(serialized_str)
    assert len(deserialized["strengths"]) == 5
    assert len(deserialized["frictions"]) == 5


def test_ux_teardown_lookups_and_getters() -> None:
    """Tests getter functions and ID-based item lookups."""
    assert len(get_ux_strengths()) == 5
    assert len(get_ux_frictions()) == 5

    report = get_ux_teardown_report()

    s1 = report.get_strength("STRENGTH-01")
    assert s1 is not None
    assert s1.title == "Automatic saving"

    f1 = report.get_friction("FRICTION-01")
    assert f1 is not None
    assert f1.title == "The day-one value drop is easy to miss"

    assert report.get_strength("NON_EXISTENT") is None
    assert report.get_friction("NON_EXISTENT") is None


def test_ux_strength_dataclass_validation() -> None:
    """Tests validation rules and immutability for UXStrengthItem."""
    valid_strength = UX_STRENGTHS[0]

    with pytest.raises(FrozenInstanceError):
        valid_strength.title = "New Title"  # type: ignore[misc]

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

    with pytest.raises(FrozenInstanceError):
        valid_friction.priority = "P0"  # type: ignore[misc]

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
    with pytest.raises(ValueError, match="must contain exactly 5 strengths"):
        UXTeardownReport(strengths=UX_STRENGTHS[:4], frictions=UX_FRICTIONS)

    with pytest.raises(ValueError, match="must contain exactly 5 friction points"):
        UXTeardownReport(strengths=UX_STRENGTHS, frictions=UX_FRICTIONS[:3])

    with pytest.raises(ValueError, match="Duplicate strength IDs"):
        UXTeardownReport(strengths=[UX_STRENGTHS[0]] * 5, frictions=UX_FRICTIONS)

    with pytest.raises(ValueError, match="Duplicate friction IDs"):
        UXTeardownReport(strengths=UX_STRENGTHS, frictions=[UX_FRICTIONS[0]] * 5)


# ===========================================================================
# 3. Question 3: completeness
# ===========================================================================

def test_growth_strategy_completeness() -> None:
    """Checks every idea has a rationale, persona, earnings model, scale, risks and KPIs."""
    report = get_growth_strategy_report()
    assert isinstance(report, GrowthStrategyReport)

    expected_verticals = [
        ("VERTICAL-01", "Jar Goals", "Named goals that family can add to"),
        ("VERTICAL-02", "Jar Funds", "Simple mutual funds alongside gold"),
        ("VERTICAL-03", "Jar Fixed", "Fixed deposits with partner banks"),
        ("VERTICAL-04", "Jar for Work", "Automatic savings for gig workers, through their platform"),
    ]
    assert [(v.id, v.name, v.tagline) for v in report.verticals] == expected_verticals
    assert len(GROWTH_VERTICALS) == len(expected_verticals)

    for v in report.verticals:
        assert v.title == f"{v.name}: {v.tagline}"
        assert len(v.strategic_rationale.strip()) >= 100, f"Strategic rationale too brief for {v.id}"
        assert len(v.target_persona.strip()) >= 30, f"Target persona too brief for {v.id}"
        assert len(v.how_it_earns.strip()) >= 30, f"Earnings model too brief for {v.id}"
        assert len(v.flywheel_integration.strip()) >= 100, f"Flywheel integration too brief for {v.id}"

        # Scale figures must be labelled as assumptions and give the reason for each
        assert "assumptions and why" in v.illustrative_scale.lower(), f"Scale assumptions not explained in {v.id}"

        # Each idea names the three strengths the brief asks about
        for strength in ("Automation:", "Design:", "Credibility:"):
            assert strength in v.flywheel_integration, f"{strength} missing in {v.id}"

        assert len(v.execution_risks) >= 2, f"At least 2 execution risks required for {v.id}"
        for risk in v.execution_risks:
            assert len(risk.risk_title.strip()) >= 10
            assert len(risk.risk_category.strip()) >= 4
            assert risk.severity in {"High", "Medium", "Low"}
            assert len(risk.mitigation_strategy.strip()) >= 30

        assert len(v.primary_kpis) >= 3, f"At least 3 KPIs required for {v.id}"
        for kpi in v.primary_kpis:
            assert len(kpi.strip()) >= 5


def test_growth_strategy_priorities_and_context() -> None:
    """Checks the first moves, the flywheel narrative and the regulatory grounding."""
    report = get_growth_strategy_report()
    flywheel_text = report.global_flywheel_narrative.lower()

    # How the ideas connect back to what Jar already has
    assert "autopay" in flywheel_text
    assert "vault" in flywheel_text
    assert "retention" in flywheel_text

    # Two prioritised first moves, each with a test and a success measure
    assert len(report.first_moves) == 2
    for move in report.first_moves:
        assert set(move) == {"name", "why", "test", "success"}
        assert all(len(v.strip()) >= 30 for k, v in move.items() if k != "name")
    assert "nek" in report.priority_note.lower()

    all_content = " ".join(
        [
            " ".join([v.strategic_rationale, v.flywheel_integration]
                     + [r.mitigation_strategy for r in v.execution_risks])
            for v in report.verticals
        ]
    ).lower()

    assert "rbi" in all_content
    assert "sebi" in all_content
    assert "amfi" in all_content
    assert "autopay" in all_content


# ===========================================================================
# 4. Question 3: serialization, lookups and validation
# ===========================================================================

def test_growth_strategy_dataclass_validation() -> None:
    """Tests validation rules and immutability for the growth strategy dataclasses."""
    valid_vertical = GROWTH_VERTICALS[0]
    valid_risk = valid_vertical.execution_risks[0]

    with pytest.raises(FrozenInstanceError):
        valid_vertical.name = "New Name"  # type: ignore[misc]

    with pytest.raises(FrozenInstanceError):
        valid_risk.severity = "Low"  # type: ignore[misc]

    # ExecutionRiskItem validation
    with pytest.raises(ValueError, match="risk_title cannot be empty"):
        ExecutionRiskItem(risk_title="", risk_category="Regulatory", severity="High", mitigation_strategy="Mitigate")

    with pytest.raises(ValueError, match="risk_category cannot be empty"):
        ExecutionRiskItem(risk_title="Title", risk_category="", severity="High", mitigation_strategy="Mitigate")

    with pytest.raises(ValueError, match="severity must be one of"):
        ExecutionRiskItem(risk_title="Title", risk_category="Regulatory", severity="Extreme", mitigation_strategy="Mitigate")

    with pytest.raises(ValueError, match="mitigation_strategy cannot be empty"):
        ExecutionRiskItem(risk_title="Title", risk_category="Regulatory", severity="High", mitigation_strategy="")

    # GrowthVerticalItem validation: every text field is required
    valid_kwargs = dict(
        id="V-99",
        name="Name",
        tagline="Tagline",
        strategic_rationale="Rationale",
        target_persona="Persona",
        how_it_earns="Earns",
        illustrative_scale="Scale",
        flywheel_integration="Flywheel",
        execution_risks=[valid_risk],
        primary_kpis=["KPI 1"],
    )
    for field_name in (
        "id", "name", "tagline", "strategic_rationale", "target_persona",
        "how_it_earns", "illustrative_scale", "flywheel_integration",
    ):
        with pytest.raises(ValueError, match=f"{field_name} cannot be empty"):
            GrowthVerticalItem(**{**valid_kwargs, field_name: ""})

    with pytest.raises(ValueError, match="execution_risks cannot be empty"):
        GrowthVerticalItem(**{**valid_kwargs, "execution_risks": []})

    with pytest.raises(ValueError, match="primary_kpis cannot be empty"):
        GrowthVerticalItem(**{**valid_kwargs, "primary_kpis": []})

    # GrowthStrategyReport validation
    with pytest.raises(ValueError, match="verticals cannot be empty"):
        GrowthStrategyReport(
            verticals=[],
            global_flywheel_narrative="Narrative",
        )

    with pytest.raises(ValueError, match="Duplicate vertical IDs"):
        GrowthStrategyReport(
            verticals=[GROWTH_VERTICALS[0]] * 2,
            global_flywheel_narrative="Narrative",
        )

    with pytest.raises(ValueError, match="global_flywheel_narrative cannot be empty"):
        GrowthStrategyReport(
            verticals=GROWTH_VERTICALS,
            global_flywheel_narrative="   ",
        )


def test_growth_strategy_serialization_and_lookups() -> None:
    """Verifies JSON round-tripping, getters and ID-based lookups."""
    data = get_growth_strategy_data()
    assert set(data) == {
        "metadata", "verticals", "global_flywheel_narrative",
        "priority_note", "first_moves",
    }
    assert data["metadata"]["total_verticals"] == len(GROWTH_VERTICALS)

    deserialized = json.loads(json.dumps(data, ensure_ascii=False, indent=2))
    assert len(deserialized["verticals"]) == len(GROWTH_VERTICALS)

    assert len(get_growth_verticals()) == len(GROWTH_VERTICALS)

    report = get_growth_strategy_report()
    v1 = report.get_vertical("VERTICAL-01")
    assert v1 is not None
    assert v1.name == "Jar Goals"
    assert report.get_vertical("UNKNOWN_ID") is None

    for v in report.verticals:
        for r in v.execution_risks:
            assert isinstance(r, ExecutionRiskItem)


# ===========================================================================
# 5. Export service and CLI
# ===========================================================================

def test_content_exports(tmp_path: Path) -> None:
    """Validates export_ux_teardown and export_growth_strategy file creation and schema."""
    service = ExportService(output_dir=tmp_path)

    ux_file = service.export_ux_teardown()
    assert ux_file == tmp_path / "ux_teardown.json"
    assert ux_file.exists()
    assert ux_file.stat().st_size > 0

    strategy_file = service.export_growth_strategy()
    assert strategy_file == tmp_path / "growth_strategy.json"
    assert strategy_file.exists()
    assert strategy_file.stat().st_size > 0

    with open(ux_file, "r", encoding="utf-8") as f:
        ux_data = json.load(f)

    assert set(ux_data.keys()) == {"metadata", "strengths", "frictions"}
    assert ux_data["metadata"]["app_name"] == "Jar:Save Money in Digital Gold"
    assert ux_data["metadata"]["total_strengths"] == 5
    assert ux_data["metadata"]["total_frictions"] == 5

    expected_strength_keys = {
        "id", "title", "category", "description",
        "behavioral_psychology", "growth_mechanism",
        "actionable_takeaway", "primary_impact_metric",
    }
    assert len(ux_data["strengths"]) == 5
    for item in ux_data["strengths"]:
        assert set(item.keys()) == expected_strength_keys
        assert item["id"].startswith("STRENGTH-")

    expected_friction_keys = {
        "id", "title", "priority", "description",
        "behavioral_friction", "actionable_solution",
        "primary_impact_metric", "implementation_effort",
    }
    assert len(ux_data["frictions"]) == 5
    for item in ux_data["frictions"]:
        assert set(item.keys()) == expected_friction_keys
        assert item["id"].startswith("FRICTION-")

    with open(strategy_file, "r", encoding="utf-8") as f:
        strategy_data = json.load(f)

    assert set(strategy_data.keys()) == {
        "metadata", "verticals", "global_flywheel_narrative",
        "priority_note", "first_moves",
    }
    assert strategy_data["metadata"]["total_verticals"] == len(GROWTH_VERTICALS)

    expected_vertical_keys = {
        "id", "name", "tagline", "title", "strategic_rationale",
        "target_persona", "how_it_earns", "illustrative_scale",
        "flywheel_integration", "execution_risks", "primary_kpis",
    }
    assert len(strategy_data["verticals"]) == len(GROWTH_VERTICALS)
    for item in strategy_data["verticals"]:
        assert set(item.keys()) == expected_vertical_keys
        assert item["id"].startswith("VERTICAL-")
        assert len(item["execution_risks"]) >= 2
        for r in item["execution_risks"]:
            assert set(r.keys()) == {"risk_title", "risk_category", "severity", "mitigation_strategy"}
        assert len(item["primary_kpis"]) >= 3

    assert len(strategy_data["global_flywheel_narrative"]) > 100


def test_export_ux_teardown_custom_report_and_dict(tmp_path: Path) -> None:
    """Tests export_ux_teardown with explicit UXTeardownReport and dict instances."""
    service = ExportService(output_dir=tmp_path)
    custom_dir = tmp_path / "custom_ux"

    path1 = service.export_ux_teardown(report=get_ux_teardown_report(), output_dir=custom_dir)
    assert path1 == custom_dir / "ux_teardown.json"
    with open(path1, "r", encoding="utf-8") as f:
        assert json.load(f)["metadata"]["total_strengths"] == 5

    dict_payload = {"metadata": {"test": True}, "strengths": [], "frictions": []}
    custom_dir_2 = tmp_path / "dict_ux"
    path2 = service.export_ux_teardown(report=dict_payload, output_dir=custom_dir_2)
    assert path2 == custom_dir_2 / "ux_teardown.json"
    with open(path2, "r", encoding="utf-8") as f:
        assert json.load(f)["metadata"]["test"] is True


def test_export_growth_strategy_custom_report_and_dict(tmp_path: Path) -> None:
    """Tests export_growth_strategy with explicit GrowthStrategyReport and dict instances."""
    service = ExportService(output_dir=tmp_path)
    custom_dir = tmp_path / "custom_strategy"

    path1 = service.export_growth_strategy(report=get_growth_strategy_report(), output_dir=custom_dir)
    assert path1 == custom_dir / "growth_strategy.json"
    with open(path1, "r", encoding="utf-8") as f:
        assert json.load(f)["metadata"]["total_verticals"] == len(GROWTH_VERTICALS)

    dict_payload = {"metadata": {"custom_strategy": 123}, "verticals": []}
    custom_dir_2 = tmp_path / "dict_strategy"
    path2 = service.export_growth_strategy(report=dict_payload, output_dir=custom_dir_2)
    assert path2 == custom_dir_2 / "growth_strategy.json"
    with open(path2, "r", encoding="utf-8") as f:
        assert json.load(f)["metadata"]["custom_strategy"] == 123


def test_export_strategy_invalid_inputs(tmp_path: Path) -> None:
    """Tests boundary validation and error handling for strategy exports."""
    service = ExportService(output_dir=tmp_path)

    with pytest.raises(TypeError, match="report must be UXTeardownReport, dict, or None"):
        service.export_ux_teardown(report=12345)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="report must be UXTeardownReport, dict, or None"):
        service.export_ux_teardown(report=["invalid", "list"])  # type: ignore[arg-type]

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

    with open(ux_json, "r", encoding="utf-8") as f:
        ux_data = json.load(f)
    assert len(ux_data["strengths"]) == 5
    assert len(ux_data["frictions"]) == 5

    with open(strategy_json, "r", encoding="utf-8") as f:
        strat_data = json.load(f)
    assert len(strat_data["verticals"]) == len(GROWTH_VERTICALS)
