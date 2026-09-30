"""Question 3: new business opportunities for Jar.

Four ideas that build on Jar's automatic saving habit, UPI AutoPay set-up and
the trust it has built. Each has how it would earn, an illustrative scale with
the reason for every assumption, KPIs and risks, plus the two I would start
with and how to test them.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data Models for Growth Strategy
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExecutionRiskItem:
    """Represents an execution risk, severity, and mitigation strategy."""

    risk_title: str
    risk_category: str
    severity: str
    mitigation_strategy: str

    def __post_init__(self) -> None:
        if not self.risk_title or not self.risk_title.strip():
            raise ValueError("risk_title cannot be empty")
        if not self.risk_category or not self.risk_category.strip():
            raise ValueError("risk_category cannot be empty")
        valid_severities = {"High", "Medium", "Low"}
        if self.severity not in valid_severities:
            raise ValueError(f"severity must be one of {valid_severities}, got {self.severity}")
        if not self.mitigation_strategy or not self.mitigation_strategy.strip():
            raise ValueError("mitigation_strategy cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Converts risk item to a serializable dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class GrowthVerticalItem:
    """Represents a new business opportunity proposed for Jar."""

    id: str
    name: str
    tagline: str
    strategic_rationale: str
    target_persona: str
    how_it_earns: str
    illustrative_scale: str
    flywheel_integration: str
    execution_risks: List[ExecutionRiskItem]
    primary_kpis: List[str]

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("id cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("name cannot be empty")
        if not self.tagline or not self.tagline.strip():
            raise ValueError("tagline cannot be empty")
        if not self.strategic_rationale or not self.strategic_rationale.strip():
            raise ValueError("strategic_rationale cannot be empty")
        if not self.target_persona or not self.target_persona.strip():
            raise ValueError("target_persona cannot be empty")
        if not self.how_it_earns or not self.how_it_earns.strip():
            raise ValueError("how_it_earns cannot be empty")
        if not self.illustrative_scale or not self.illustrative_scale.strip():
            raise ValueError("illustrative_scale cannot be empty")
        if not self.flywheel_integration or not self.flywheel_integration.strip():
            raise ValueError("flywheel_integration cannot be empty")
        if not self.execution_risks or len(self.execution_risks) == 0:
            raise ValueError("execution_risks cannot be empty")
        if not self.primary_kpis or len(self.primary_kpis) == 0:
            raise ValueError("primary_kpis cannot be empty")

    @property
    def title(self) -> str:
        """Composite title combining product name and descriptive tagline."""
        return f"{self.name}: {self.tagline}"

    def to_dict(self) -> Dict[str, Any]:
        """Converts growth vertical to a serializable dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "tagline": self.tagline,
            "title": self.title,
            "strategic_rationale": self.strategic_rationale,
            "target_persona": self.target_persona,
            "how_it_earns": self.how_it_earns,
            "illustrative_scale": self.illustrative_scale,
            "flywheel_integration": self.flywheel_integration,
            "execution_risks": [r.to_dict() for r in self.execution_risks],
            "primary_kpis": list(self.primary_kpis),
        }


@dataclass(frozen=True)
class GrowthStrategyReport:
    """Container report housing the complete Question 3 answer."""

    verticals: List[GrowthVerticalItem]
    global_flywheel_narrative: str
    strategy_version: str = "September 2026"
    author: str = "Jegadeesh D"
    priority_note: str = ""
    first_moves: List[Dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.verticals:
            raise ValueError("verticals cannot be empty")
        vertical_ids = [v.id for v in self.verticals]
        if len(set(vertical_ids)) != len(vertical_ids):
            raise ValueError("Duplicate vertical IDs detected in GrowthStrategyReport")
        if not self.global_flywheel_narrative or not self.global_flywheel_narrative.strip():
            raise ValueError("global_flywheel_narrative cannot be empty")

    def get_vertical(self, vertical_id: str) -> Optional[GrowthVerticalItem]:
        """Looks up a vertical item by its ID."""
        for v in self.verticals:
            if v.id == vertical_id:
                return v
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the complete Growth Strategy report to a structured dictionary."""
        return {
            "metadata": {
                "strategy_version": self.strategy_version,
                "author": self.author,
                "total_verticals": len(self.verticals),
            },
            "verticals": [v.to_dict() for v in self.verticals],
            "global_flywheel_narrative": self.global_flywheel_narrative,
            "priority_note": self.priority_note,
            "first_moves": [dict(m) for m in self.first_moves],
        }


# ---------------------------------------------------------------------------
# Content: 4 new business opportunities
# ---------------------------------------------------------------------------

GROWTH_VERTICALS: List[GrowthVerticalItem] = [
    # -----------------------------------------------------------------------
    # Vertical 1: Jar Goals
    # -----------------------------------------------------------------------
    GrowthVerticalItem(
        id="VERTICAL-01",
        name="Jar Goals",
        tagline="Named goals that family can add to",
        strategic_rationale=(
            "Jar has festival saving, but I found no way to create any other named goal (September 2026). Let "
            "users name a goal such as a wedding or a child's education and share a link, so relatives add gold "
            "on birthdays or Diwali instead of giving cash."
        ),
        target_persona="Parents saving for their children, and relatives who give cash gifts.",
        how_it_earns="Jar's existing margin on gold, on money that would otherwise be given as cash.",
        illustrative_scale=(
            "200,000 goals x ₹7,500 = ₹150 Cr of gold saved. Assumptions and why: 200,000 is 1 in 250 of the "
            "5 crore+ users on Jar's website, kept small because most users won't set up a goal. ₹7,500 is ₹25 a "
            "day for 300 days, a little above the ₹10 minimum because a goal also collects gifts."
        ),
        flywheel_integration=(
            "Automation: the daily AutoPay save can point at the goal. Design: the festival saving flow users "
            "already know. Credibility: relatives meet Jar through someone they trust."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Fake contribution links",
                risk_category="Fraud",
                severity="Medium",
                mitigation_strategy="Show the verified goal owner's name on every link and make links expire.",
            ),
            ExecutionRiskItem(
                risk_title="Goals for minors",
                risk_category="Regulatory",
                severity="Medium",
                mitigation_strategy="Keep the goal under the parent's account and KYC.",
            ),
        ],
        primary_kpis=[
            "Goals that receive a contribution from someone else",
            "Contributors who start saving within 30 days",
            "Monthly saving of users with a goal vs without",
        ],
    ),
    # -----------------------------------------------------------------------
    # Vertical 2: Jar Funds
    # -----------------------------------------------------------------------
    GrowthVerticalItem(
        id="VERTICAL-02",
        name="Jar Funds",
        tagline="Simple mutual funds alongside gold",
        strategic_rationale=(
            "Long-term savers want to diversify, and I found no way to save in silver or mutual funds in the app "
            "(September 2026). Offer a short list of simple funds (index, liquid, gold and silver) with the same "
            "set-once flow. Funds are SEBI-regulated; digital gold is not, as SEBI cautioned in November 2025."
        ),
        target_persona="Users who have saved for 6+ months and built a balance.",
        how_it_earns="Yearly distribution commission from fund houses on the balance held.",
        illustrative_scale=(
            "150,000 savers x ₹500 a month x 12 = ₹90 Cr of balances; at 0.2% a year that is about ₹18 lakh, so "
            "this is a retention product first. Assumptions and why: 150,000 is about 1 in 330 of Jar's 5 crore+ "
            "users, fewer than for goals because funds need full KYC. ₹500 a month is a common minimum SIP. 0.2% "
            "sits in the 0.05-0.25% range distributors typically earn on index and liquid funds."
        ),
        flywheel_integration=(
            "Automation: the same set-once AutoPay routine, on a separate mandate because fund money must go from "
            "the investor's bank to the fund house, not through Jar. Design: a short list in plain words. "
            "Credibility: a regulated product inside an app users already trust."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Licensing and KYC",
                risk_category="Regulatory",
                severity="High",
                mitigation_strategy=(
                    "Register as a distributor with AMFI, and ask for full KYC (PAN) only when a user first "
                    "picks a fund."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Fund minimums above ₹10",
                risk_category="Operational",
                severity="Medium",
                mitigation_strategy="Daily fund SIPs usually start near ₹100, so begin with weekly or monthly SIPs.",
            ),
        ],
        primary_kpis=[
            "Long-term savers who add a fund",
            "Churn of long-term savers",
            "Fund users who keep their gold save running",
        ],
    ),
    # -----------------------------------------------------------------------
    # Vertical 3: Jar Fixed
    # -----------------------------------------------------------------------
    GrowthVerticalItem(
        id="VERTICAL-03",
        name="Jar Fixed",
        tagline="Fixed deposits with partner banks",
        strategic_rationale=(
            "Some savers want a fixed return without price swings, which gold can't give, and I found no deposit "
            "option in the app (September 2026). Offer fixed deposits from partner banks, as apps such as Stable "
            "Money do. The deposit sits with an RBI-regulated bank, not Jar, and carries deposit insurance (DICGC)."
        ),
        target_persona="Cautious savers, and users about to withdraw a lump sum.",
        how_it_earns="A sourcing fee from the partner bank on each deposit.",
        illustrative_scale=(
            "100,000 savers x ₹10,000 = ₹100 Cr of deposits; at a 0.5% fee that is about ₹50 lakh. Assumptions "
            "and why: 100,000 is 1 in 500 of Jar's 5 crore+ users, the smallest share because a deposit needs a "
            "lump sum. ₹10,000 is a modest first deposit for a small saver. 0.5% is mid-range of the 0.10-1.25% "
            "Stable Money pays its own referral partners."
        ),
        flywheel_integration=(
            "Automation: a withdrawal can be redirected into a deposit, which renews on its own at maturity. "
            "Design: the same few taps as a gold save. Credibility: an RBI-regulated bank behind an app the user "
            "already trusts."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Handling deposit money",
                risk_category="Regulatory",
                severity="High",
                mitigation_strategy=(
                    "Money moves directly between the user's bank and the partner bank, which also does the KYC."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Money moving out of gold",
                risk_category="Market",
                severity="Medium",
                mitigation_strategy="Offer deposits at withdrawal, not in place of the daily gold save.",
            ),
        ],
        primary_kpis=[
            "Deposits booked",
            "Withdrawals redirected into a deposit",
            "Deposits renewed at maturity",
        ],
    ),
    # -----------------------------------------------------------------------
    # Vertical 4: Jar for Work
    # -----------------------------------------------------------------------
    GrowthVerticalItem(
        id="VERTICAL-04",
        name="Jar for Work",
        tagline="Automatic savings for gig workers, through their platform",
        strategic_rationale=(
            "NITI Aayog counted 7.7 million gig workers in 2020-21 and projects 23.5 million by 2029-30, usually "
            "without an employer provident fund. Partner with delivery and ride platforms so 1-2% of each payout "
            "is saved in gold automatically, with an optional match from the platform."
        ),
        target_persona="Delivery and ride-hailing workers, and the platforms that want to retain them.",
        how_it_earns="A monthly fee per active worker from the platform, plus Jar's margin on gold.",
        illustrative_scale=(
            "100,000 workers x ₹400 a month x 12 = ₹48 Cr a year. Assumptions and why: ₹400 is 2% of about "
            "₹20,000, near the ₹22,500 average monthly gig earnings in a Primus Partners survey. 100,000 workers "
            "is just over 1% of the 7.7 million NITI Aayog counted, kept small because it depends on signing platforms."
        ),
        flywheel_integration=(
            "Automation: saving happens at payout, with no AutoPay debit that can fail. Design: the same app and "
            "withdrawals as any Jar user. Credibility: a known savings app is easier for a platform to offer than "
            "an unknown one."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Long B2B sales cycles",
                risk_category="Operational",
                severity="Medium",
                mitigation_strategy="Start with one platform and a free 90-day pilot.",
            ),
            ExecutionRiskItem(
                risk_title="Rules on pay deductions",
                risk_category="Regulatory",
                severity="Medium",
                mitigation_strategy="Keep it opt-in and withdrawable at any time.",
            ),
        ],
        primary_kpis=[
            "Partner platforms signed",
            "Workers still saving after 90 days",
            "Retention of enrolled vs other workers",
        ],
    ),
]


GLOBAL_FLYWHEEL_NARRATIVE: str = (
    "All four reuse what Jar already has: a saving habit, a UPI AutoPay set-up users understand, and trust built "
    "on vault-backed gold. Goals and Jar for Work bring in new savers. Funds and deposits improve retention by "
    "giving long-term savers a reason to stay. Commissions and fees add income beyond the gold margin."
)


PRIORITY_NOTE: str = (
    "Jar already has gold saving with a festival option, a jewellery brand (Nek) and personal loans (listed on "
    "the Play Store; not visible in my app), so I left those out. I also dropped loans against Jar gold: RBI's "
    "gold-collateral rules, in force since 1 April 2026, rule out digital gold as collateral. I would start with "
    "the two ideas that are cheapest to test."
)

FIRST_MOVES: List[Dict[str, str]] = [
    {
        "name": "Family goals (Jar Goals)",
        "why": "It extends the festival saving Jar already has, and every contribution introduces Jar to someone new.",
        "test": "Before Diwali, give 5% of users named goals with a share link and compare with a control group.",
        "success": (
            "Share of goals that get a contribution from someone else; contributors who start saving within 30 days."
        ),
    },
    {
        "name": "Mutual funds alongside gold (Jar Funds)",
        "why": "Long-term savers can't diversify inside Jar today, and funds are a regulated product.",
        "test": (
            "Show a 'Save in funds too' card to users who have saved 6+ months and count waitlist sign-ups before "
            "building anything."
        ),
        "success": "Waitlist sign-up rate; in a pilot, the share of fund users who keep their gold save running.",
    },
]


# Global strategy report instance
GROWTH_STRATEGY_REPORT = GrowthStrategyReport(
    verticals=GROWTH_VERTICALS,
    global_flywheel_narrative=GLOBAL_FLYWHEEL_NARRATIVE,
    strategy_version="September 2026",
    author="Jegadeesh D",
    priority_note=PRIORITY_NOTE,
    first_moves=FIRST_MOVES,
)


# ---------------------------------------------------------------------------
# Accessor Functions
# ---------------------------------------------------------------------------

def get_growth_verticals() -> List[GrowthVerticalItem]:
    """Returns the list of documented growth verticals."""
    return list(GROWTH_VERTICALS)


def get_growth_strategy_report() -> GrowthStrategyReport:
    """Returns the complete GrowthStrategyReport domain model instance."""
    return GROWTH_STRATEGY_REPORT


def get_growth_strategy_data() -> Dict[str, Any]:
    """Returns the full Growth Strategy roadmap serialized as a JSON-compliant dict."""
    return GROWTH_STRATEGY_REPORT.to_dict()
