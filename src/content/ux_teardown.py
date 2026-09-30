"""Question 2: Jar app exploration.

Five things the Jar app does well and five areas to improve. Each item has a
short description, why it matters, a suggested next step and the metric to
watch.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data Models for UX Teardown
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class UXStrengthItem:
    """Represents an effective product feature and UX strength in Jar."""

    id: str
    title: str
    category: str
    description: str
    behavioral_psychology: str
    growth_mechanism: str
    actionable_takeaway: str
    primary_impact_metric: str

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("id cannot be empty")
        if not self.title or not self.title.strip():
            raise ValueError("title cannot be empty")
        if not self.category or not self.category.strip():
            raise ValueError("category cannot be empty")
        if not self.description or not self.description.strip():
            raise ValueError("description cannot be empty")
        if not self.behavioral_psychology or not self.behavioral_psychology.strip():
            raise ValueError("behavioral_psychology cannot be empty")
        if not self.growth_mechanism or not self.growth_mechanism.strip():
            raise ValueError("growth_mechanism cannot be empty")
        if not self.actionable_takeaway or not self.actionable_takeaway.strip():
            raise ValueError("actionable_takeaway cannot be empty")
        if not self.primary_impact_metric or not self.primary_impact_metric.strip():
            raise ValueError("primary_impact_metric cannot be empty")

    @property
    def growth_mechanics(self) -> str:
        """Alias for growth_mechanism to ensure flexible downstream consumption."""
        return self.growth_mechanism

    @property
    def behavioral_rationale(self) -> str:
        """Alias for behavioral_psychology."""
        return self.behavioral_psychology

    @property
    def actionable_solution(self) -> str:
        """Alias for actionable_takeaway."""
        return self.actionable_takeaway

    @property
    def impact_metric(self) -> str:
        """Alias for primary_impact_metric."""
        return self.primary_impact_metric

    def to_dict(self) -> Dict[str, Any]:
        """Converts strength item to a clean serializable dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class UXFrictionItem:
    """Represents a prioritized UX friction point and recommended solution."""

    id: str
    title: str
    priority: str
    description: str
    behavioral_friction: str
    actionable_solution: str
    primary_impact_metric: str
    implementation_effort: str

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("id cannot be empty")
        if not self.title or not self.title.strip():
            raise ValueError("title cannot be empty")
        if not self.priority or not self.priority.strip():
            raise ValueError("priority cannot be empty")
        if not self.description or not self.description.strip():
            raise ValueError("description cannot be empty")
        if not self.behavioral_friction or not self.behavioral_friction.strip():
            raise ValueError("behavioral_friction cannot be empty")
        if not self.actionable_solution or not self.actionable_solution.strip():
            raise ValueError("actionable_solution cannot be empty")
        if not self.primary_impact_metric or not self.primary_impact_metric.strip():
            raise ValueError("primary_impact_metric cannot be empty")
        if self.implementation_effort not in {"Low", "Medium", "High"}:
            raise ValueError(
                f"implementation_effort must be 'Low', 'Medium', or 'High', got {self.implementation_effort}"
            )
        valid_priorities = {"P0 - Critical", "P1 - High", "P2 - Medium"}
        if self.priority not in valid_priorities:
            raise ValueError(f"priority must be one of {valid_priorities}, got {self.priority}")

    @property
    def behavioral_psychology(self) -> str:
        """Alias for behavioral_friction for unified interface access."""
        return self.behavioral_friction

    @property
    def behavioral_rationale(self) -> str:
        """Alias for behavioral_friction."""
        return self.behavioral_friction

    @property
    def actionable_recommendation(self) -> str:
        """Alias for actionable_solution."""
        return self.actionable_solution

    @property
    def impact_metric(self) -> str:
        """Alias for primary_impact_metric."""
        return self.primary_impact_metric

    def to_dict(self) -> Dict[str, Any]:
        """Converts friction item to a clean serializable dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class UXTeardownReport:
    """Container report housing the complete Question 2 evaluation model."""

    strengths: List[UXStrengthItem]
    frictions: List[UXFrictionItem]
    app_name: str = "Jar:Save Money in Digital Gold"
    audit_date: str = "September 2026"
    app_version: str = "Android app"

    def __post_init__(self) -> None:
        if len(self.strengths) != 5:
            raise ValueError(f"Report must contain exactly 5 strengths, got {len(self.strengths)}")
        if len(self.frictions) != 5:
            raise ValueError(f"Report must contain exactly 5 friction points, got {len(self.frictions)}")

        strength_ids = [s.id for s in self.strengths]
        if len(set(strength_ids)) != 5:
            raise ValueError("Duplicate strength IDs detected")

        friction_ids = [f.id for f in self.frictions]
        if len(set(friction_ids)) != 5:
            raise ValueError("Duplicate friction IDs detected")

    def get_strength(self, item_id: str) -> Optional[UXStrengthItem]:
        """Looks up a strength item by its ID."""
        for s in self.strengths:
            if s.id == item_id:
                return s
        return None

    def get_friction(self, item_id: str) -> Optional[UXFrictionItem]:
        """Looks up a friction item by its ID."""
        for f in self.frictions:
            if f.id == item_id:
                return f
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the complete UX Teardown report to a structured dictionary."""
        return {
            "metadata": {
                "app_name": self.app_name,
                "audit_date": self.audit_date,
                "app_version": self.app_version,
                "total_strengths": len(self.strengths),
                "total_frictions": len(self.frictions),
            },
            "strengths": [s.to_dict() for s in self.strengths],
            "frictions": [f.to_dict() for f in self.frictions],
        }


# ---------------------------------------------------------------------------
# Content: 5 things Jar does well
# ---------------------------------------------------------------------------

UX_STRENGTHS: List[UXStrengthItem] = [
    UXStrengthItem(
        id="STRENGTH-01",
        title="Automatic saving",
        category="Set once, save daily",
        description=(
            "You pick an amount once, set up UPI AutoPay, and Jar buys gold for you every day (or week, or month) "
            "without you doing anything. A round-off option adds spare change on top: in Jar's own example, a ₹27 "
            "spend is rounded up to ₹30 and the ₹3 is saved."
        ),
        behavioral_psychology=(
            "Saving is on by default, so it doesn't depend on willpower. Small daily amounts and spare change "
            "don't feel like real money, so saving them barely hurts."
        ),
        growth_mechanism=(
            "Daily saves create around 30 small deposits a month instead of one monthly SIP, so users have far "
            "more reasons to open Jar, which helps retention without ad spend."
        ),
        actionable_takeaway=(
            "Suggest raising the daily amount at the right moments (payday, or after 30 days of successful saves), "
            "so keen savers can speed up with one tap."
        ),
        primary_impact_metric="Share of users still auto-saving after 30 and 90 days; average daily saving amount",
    ),
    UXStrengthItem(
        id="STRENGTH-02",
        title="Start with ₹10",
        category="Low barrier to start",
        description=(
            "You can start saving in 24K gold with ₹10, compared with thousands of rupees for a physical coin. "
            "That opens gold up to students, gig workers and first-time savers who would never walk into a "
            "jeweller to invest."
        ),
        behavioral_psychology=(
            "A tiny first amount removes the fear of losing money, so people try it now instead of putting it off."
        ),
        growth_mechanism=(
            "A ₹10 first save is an easy activation step. Once users see their gold balance grow, moving up to a "
            "daily auto-save is a much smaller ask."
        ),
        actionable_takeaway=(
            "Prompt a daily auto-save straight after the first manual save, while the user is most engaged."
        ),
        primary_impact_metric="Install-to-first-save conversion; share of new savers who set up a daily save within 7 days",
    ),
    UXStrengthItem(
        id="STRENGTH-03",
        title="Spins, coupons and referral bonuses",
        category="Rewards",
        description=(
            "The app has spins, coupons and a referral bonus, so using it comes with small wins and there is a "
            "reason to bring a friend in."
        ),
        behavioral_psychology=(
            "Unpredictable rewards such as a spin keep people coming back more than a fixed reward of the same "
            "value would."
        ),
        growth_mechanism=(
            "Rewards turn a set-and-forget product into one people have a reason to open, and a referral bonus "
            "brings in new savers through someone they already trust."
        ),
        actionable_takeaway=(
            "I couldn't find a streak in the app. An extra spin for seven saves in a row would reward consistency, "
            "not just single saves."
        ),
        primary_impact_metric="Share of spins and coupons redeemed; referred users who make a first save",
    ),
    UXStrengthItem(
        id="STRENGTH-04",
        title="Fast withdrawals",
        category="Easy exit",
        description=(
            "When I sold a small test amount of gold, the money reached my bank account in about 3 seconds. "
            "First-time investors worry about getting stuck, and a withdrawal that fast removes that worry."
        ),
        behavioral_psychology="Knowing you can get out easily makes it easier to put money in.",
        growth_mechanism=(
            "A fast exit lowers the risk of the first deposit, and a user whose first withdrawal goes smoothly "
            "is more likely to keep saving."
        ),
        actionable_takeaway=(
            "I only tested a small amount. If larger withdrawals are as fast, that speed is worth stating up front "
            "when a new saver makes a first deposit."
        ),
        primary_impact_metric="Share of users who save again within 30 days of a withdrawal",
    ),
    UXStrengthItem(
        id="STRENGTH-05",
        title="Visible trust signals",
        category="Trust and proof",
        description=(
            "Jar says the gold is 24K, stored in Brink's vaults and insured by ICICI Lombard, with independent "
            "oversight by Vistra, and the app offers delivery of gold coins. For a first-time investor, being "
            "able to hold the coin makes digital gold feel real."
        ),
        behavioral_psychology=(
            "Gold is already trusted in Indian households; vault details and coin delivery carry that trust over "
            "to the app."
        ),
        growth_mechanism=(
            "Trust built on small saves is what lets users make bigger purchases later, for example at Dhanteras "
            "or Akshaya Tritiya."
        ),
        actionable_takeaway=(
            "Keep the vault, insurer and oversight details one tap from the balance screen, since that is where "
            "a nervous saver looks."
        ),
        primary_impact_metric="Average purchase size around festivals; coin delivery orders",
    ),
]


# ---------------------------------------------------------------------------
# Content: 5 areas to improve
# ---------------------------------------------------------------------------

UX_FRICTIONS: List[UXFrictionItem] = [
    UXFrictionItem(
        id="FRICTION-01",
        title="The day-one value drop is easy to miss",
        priority="P0 - Critical",
        description=(
            "Buying gold includes 3% GST, and the buy and sell prices differ, so ₹100 of gold is worth less than "
            "₹100 if sold straight away. Jar does show the GST breakdown, but inside a dropdown at checkout that "
            "is easy to skip, so a new user can still be surprised when their balance is lower than what they paid."
        ),
        behavioral_friction=(
            "A loss on day one feels bigger than the same gain later, and it's the kind of surprise that leads to "
            "complaints and bad reviews."
        ),
        actionable_solution=(
            "1. Open the GST breakdown by default on a user's first purchase instead of hiding it in a dropdown.\n"
            "2. On the same screen, show in one line what the gold would fetch if sold today, so the gap is seen "
            "before paying, not after."
        ),
        primary_impact_metric="First-week withdrawals by new users; reviews and tickets mentioning 'loss' or 'deduction'",
        implementation_effort="Low",
    ),
    UXFrictionItem(
        id="FRICTION-02",
        title="Notification controls are too coarse",
        priority="P1 - High",
        description=(
            "I have Jar's notifications turned off, and the settings give me no way to turn on only the ones I "
            "would want. Inside the app the only choice is a gold price alert. In Android's settings Jar has just "
            "two notification categories, an announcements one and 'Miscellaneous', so an alert about my money "
            "and a promotion can't be told apart."
        ),
        behavioral_friction=(
            "When the choice is all or nothing, cautious users choose nothing, and Jar loses its main way to "
            "reach them about a failed payment or a goal that is nearly met."
        ),
        actionable_solution=(
            "1. Split notifications into clear types (payments and account, gold price, rewards, offers) in the "
            "app and as separate Android categories.\n"
            "2. When asking for permission, say that offers can be switched off on their own."
        ),
        primary_impact_metric="Share of users with notifications on; app opens from notifications",
        implementation_effort="Medium",
    ),
    UXFrictionItem(
        id="FRICTION-03",
        title="Round-off is hard to understand",
        priority="P1 - High",
        description=(
            "I could see the round-off feature but couldn't tell from the screen how it works: which spends it "
            "counts, how Jar sees them, or how much it would take in a month."
        ),
        behavioral_friction=(
            "People don't switch on something that moves their money automatically unless they can predict what "
            "it will do."
        ),
        actionable_solution=(
            "1. Show one worked example on the round-off screen (a ₹27 spend becomes ₹30, and ₹3 is saved).\n"
            "2. Say plainly how Jar detects spends and what it needs access to.\n"
            "3. Let users set a monthly cap before switching it on."
        ),
        primary_impact_metric="Share of savers who switch on round-off; round-off savings per user per month",
        implementation_effort="Low",
    ),
    UXFrictionItem(
        id="FRICTION-04",
        title="Goal saving stops at festivals",
        priority="P1 - High",
        description=(
            "Jar already lets you save towards festivals, which shows goal-based saving works. But the bigger "
            "things people save for (a wedding, a child's education, an emergency fund) can't be set up the same "
            "way, so that money sits in one balance with no visible progress."
        ),
        behavioral_friction=(
            "People save more steadily towards a named goal, and seeing progress makes them less likely to "
            "withdraw early."
        ),
        actionable_solution=(
            "1. Extend festival saving to any named goal, with a target amount, a date and a progress bar.\n"
            "2. Add an optional 24-hour wait before withdrawing from a goal.\n"
            "3. Let family members add gold to a goal through a shareable link (see Q3)."
        ),
        primary_impact_metric="Early withdrawal rate; monthly saving of users with goals vs without",
        implementation_effort="Medium",
    ),
    UXFrictionItem(
        id="FRICTION-05",
        title="Nothing beyond gold for savers who want to diversify",
        priority="P2 - Medium",
        description=(
            "The app sells silver jewellery, but I found no way to save in silver or in mutual funds "
            "(September 2026). Someone who has saved for a year "
            "and wants to spread their money has to open another app such as Groww or Zerodha to do it."
        ),
        behavioral_friction=(
            "Once savings get large, keeping everything in one asset starts to feel risky, and the app a user "
            "opens to diversify can become the one they save in."
        ),
        actionable_solution=(
            "1. Offer a short list of simple mutual funds, including gold and silver funds, alongside gold "
            "(see Q3).\n"
            "2. Keep the same set-once, save-automatically flow so it doesn't feel like a different product."
        ),
        primary_impact_metric="Balance per user after 12 months; churn of users with large balances",
        implementation_effort="High",
    ),
]


# Global report instance
UX_TEARDOWN_REPORT = UXTeardownReport(
    strengths=UX_STRENGTHS,
    frictions=UX_FRICTIONS,
    app_name="Jar:Save Money in Digital Gold",
    audit_date="September 2026",
    app_version="Android app",
)


# ---------------------------------------------------------------------------
# Accessor Functions
# ---------------------------------------------------------------------------

def get_ux_strengths() -> List[UXStrengthItem]:
    """Returns the list of 5 documented core strengths."""
    return list(UX_STRENGTHS)


def get_ux_frictions() -> List[UXFrictionItem]:
    """Returns the list of 5 documented prioritized friction points."""
    return list(UX_FRICTIONS)


def get_ux_teardown_report() -> UXTeardownReport:
    """Returns the complete UXTeardownReport domain model instance."""
    return UX_TEARDOWN_REPORT


def get_ux_teardown_data() -> Dict[str, Any]:
    """Returns the full UX Teardown evaluation serialized as a JSON-compliant dict."""
    return UX_TEARDOWN_REPORT.to_dict()
