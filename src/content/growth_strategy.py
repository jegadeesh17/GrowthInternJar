"""Question 3: new business opportunities for Jar.

Four ideas that build on Jar's automatic saving habit, UPI AutoPay set-up and
the trust it has built, each with how it would earn, an illustrative scale,
KPIs and risks, plus the two I would start with and how to test them.
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
    execution_risk_matrix: List[ExecutionRiskItem]
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
        if not self.execution_risk_matrix:
            raise ValueError("execution_risk_matrix cannot be empty")
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
            "execution_risk_matrix": [r.to_dict() for r in self.execution_risk_matrix],
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
            "Jar already has a festival saving option. The bigger things families save gold for, such as a wedding "
            "or a child's education, work the same way: a name, a target and a date. Jar could let a user create a "
            "named goal and share a link, so grandparents and relatives add gold to it on birthdays or Diwali "
            "instead of giving cash shagun. I found no way to create a named goal other than the festival one "
            "(September 2026)."
        ),
        target_persona=(
            "Parents (roughly 24-40) saving for their children, and relatives who give cash gifts at festivals and "
            "family events."
        ),
        how_it_earns=(
            "The same margin Jar earns on gold today, on money that would otherwise be given as cash."
        ),
        illustrative_scale=(
            "Jar's website says 5 crore+ Indians use it. If 1 in 250 of them (200,000) created a goal that "
            "collected ₹7,500, which is ₹25 a day for 300 days, that would be ₹150 Cr of gold saved. The 1 in 250 "
            "and the ₹25 a day are my own assumptions."
        ),
        flywheel_integration=(
            "Automation: the owner's daily save can point at the goal, using the AutoPay set-up they already have. "
            "Design: it is the festival saving flow users already know, with a name and a progress bar. "
            "Credibility: each relative who contributes meets Jar through someone they trust, and can start "
            "saving themselves."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Goals for minors",
                risk_category="Regulatory",
                severity="Medium",
                mitigation_strategy=(
                    "Keep the goal under the parent's account and KYC, and give a yearly statement of contributions "
                    "received for tax records."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Fake contribution links",
                risk_category="Fraud",
                severity="Medium",
                mitigation_strategy=(
                    "Show the verified goal owner's name on every link and make links expire, so fakes are easy "
                    "to spot."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Early withdrawals",
                risk_category="Operational",
                severity="Low",
                mitigation_strategy=(
                    "Don't lock the money. Add a short wait and a reminder of the goal before a withdrawal, so it "
                    "stays available in an emergency."
                ),
            ),
        ],
        primary_kpis=[
            "Share of goals that receive a contribution from someone else",
            "Share of contributors who start saving within 30 days",
            "Average time money stays in a goal",
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
            "Savers who have built a gold balance eventually want to spread it, and I found no way to save in "
            "silver or mutual funds in the app (September 2026). Jar could offer a short list of simple mutual funds, for "
            "example an index fund, a liquid fund, and gold and silver funds, with the same set-once, "
            "save-automatically flow and no demat account. Mutual funds are SEBI-regulated, which matters because "
            "digital gold is not: SEBI said so in a caution to investors in November 2025. Silver would come "
            "through a silver fund, not unregulated digital silver."
        ),
        target_persona=(
            "Users who have saved in Jar for 6+ months and have a sizeable balance (say ₹15,000 or more)."
        ),
        how_it_earns=(
            "Distribution commission from fund houses, a small yearly percentage of the balance held, so it grows "
            "with balances, not transactions."
        ),
        illustrative_scale=(
            "If 150,000 savers each put ₹500 a month into funds for a year, that would be ₹90 Cr of balances. "
            "Distributor commission on index and liquid funds is low, so at an assumed 0.2% a year that is about "
            "₹18 lakh: this is a retention product first and a revenue line later. The saver count, amount and "
            "rate are my own assumptions."
        ),
        flywheel_integration=(
            "Automation: the routine users already know, choose an amount once, approve a UPI AutoPay mandate, "
            "and saving happens on its own. Funds would need their own mandate, because fund money has to go "
            "from the investor's bank to the fund house and not through Jar. Design: a short list in plain words "
            "instead of thousands of schemes. Credibility: a SEBI-regulated product inside an app users already "
            "trust with their savings."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Licensing and KYC",
                risk_category="Regulatory",
                severity="High",
                mitigation_strategy=(
                    "Register as a mutual fund distributor with AMFI. Funds need full KYC with PAN, more than Jar's "
                    "sign-up asks for, so ask for it only when a user first chooses a fund."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Fund minimums above ₹10",
                risk_category="Operational",
                severity="Medium",
                mitigation_strategy=(
                    "Fund SIP minimums are usually higher than Jar's ₹10 daily save, so start with weekly or "
                    "monthly fund SIPs for users who already save larger amounts."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Funds can lose value",
                risk_category="Market",
                severity="Medium",
                mitigation_strategy=(
                    "Keep the list short, label each fund's risk in plain words, and explain up front that silver "
                    "and equity move more than gold, so a drop isn't a surprise."
                ),
            ),
        ],
        primary_kpis=[
            "Share of long-term savers who add a fund",
            "Balance per user holding both gold and funds",
            "Churn of long-term savers",
            "Share of fund users who keep their gold save running",
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
            "Some savers want a fixed return and no price swings, which gold can't give them. Jar could offer "
            "fixed deposits from partner banks inside the app, as apps such as Stable Money do. The deposit is "
            "held by an RBI-regulated bank, not by Jar, and is covered by deposit insurance (DICGC) up to the "
            "statutory limit. It gives users a safe place for money they would otherwise withdraw from Jar."
        ),
        target_persona=(
            "Cautious savers, and users about to withdraw a lump sum who have no immediate use for it."
        ),
        how_it_earns="A sourcing fee from the partner bank for each deposit booked through Jar.",
        illustrative_scale=(
            "If 100,000 savers each placed ₹10,000, that would be ₹100 Cr of deposits sourced for partner banks; "
            "at an assumed 0.5% sourcing fee that is about ₹50 lakh. The saver count, deposit size and fee are my "
            "own assumptions."
        ),
        flywheel_integration=(
            "Automation: a withdrawal can be redirected into a deposit in a couple of taps, and the deposit can "
            "renew on its own at maturity. Design: booking takes the same few steps as a gold save. Credibility: "
            "the money sits with an RBI-regulated bank, offered by an app the user already trusts with small saves."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Handling deposit money",
                risk_category="Regulatory",
                severity="High",
                mitigation_strategy=(
                    "Jar acts only as the bank's sourcing partner: money moves directly between the user's bank "
                    "account and the partner bank, and the bank does the KYC."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Partner bank trouble",
                risk_category="Counterparty",
                severity="Medium",
                mitigation_strategy=(
                    "Choose partner banks carefully, show the deposit insurance limit clearly, and warn users "
                    "before they go over it with one bank."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Money moving out of gold",
                risk_category="Market",
                severity="Medium",
                mitigation_strategy=(
                    "Offer deposits at withdrawal, not in place of the daily gold save, and track whether gold "
                    "saving drops among users who book one."
                ),
            ),
        ],
        primary_kpis=[
            "Deposits booked (₹ Cr)",
            "Share of withdrawals redirected into a deposit",
            "Share of deposits renewed at maturity",
            "Gold saving of deposit users vs before",
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
            "NITI Aayog estimated about 7.7 million gig workers in India in 2020-21, rising to 23.5 million by "
            "2029-30, and gig work usually comes without an employer provident fund. Jar could partner with "
            "delivery and ride platforms so a small share of each payout (1-2%) is saved in gold automatically, "
            "with the platform optionally adding a match. For the platform, it is a cheap benefit that can help "
            "keep workers."
        ),
        target_persona=(
            "Delivery and ride-hailing workers, and the operations or HR teams at those platforms who want to "
            "reduce worker churn."
        ),
        how_it_earns=(
            "A monthly fee per active worker paid by the platform, plus Jar's usual margin on the gold bought."
        ),
        illustrative_scale=(
            "A worker paid about ₹20,000 a month who saves 2% puts away ₹400. If 100,000 workers did that, it "
            "would be ₹48 Cr of new saving a year. The pay level, share and worker count are my own assumptions."
        ),
        flywheel_integration=(
            "Automation: saving happens when the payout arrives, so it doesn't depend on a bank balance being "
            "there for an AutoPay debit. Design: workers get the same app, gold balance and withdrawals as any "
            "other Jar user. Credibility: an established savings app is easier for a platform to offer its "
            "workers than an unknown one."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Long B2B sales cycles",
                risk_category="Operational",
                severity="Medium",
                mitigation_strategy=(
                    "Start with one platform and a free 90-day pilot, judged on worker retention."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Irregular income",
                risk_category="Financial",
                severity="Medium",
                mitigation_strategy=(
                    "Save a percentage of each payout rather than a fixed amount, skip zero-earning days, and allow "
                    "a one-tap 'skip today'."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Rules on pay deductions",
                risk_category="Regulatory",
                severity="Medium",
                mitigation_strategy=(
                    "Make it strictly opt-in, with the money withdrawable at any time and no employer lock-in."
                ),
            ),
        ],
        primary_kpis=[
            "Partner platforms signed",
            "Workers enrolled and still saving after 90 days",
            "Average monthly saving per worker",
            "Retention of enrolled vs non-enrolled workers",
        ],
    ),
]


# ---------------------------------------------------------------------------
# Content: risks across all four ideas
# ---------------------------------------------------------------------------

PLATFORM_RISK_MATRIX: List[ExecutionRiskItem] = [
    ExecutionRiskItem(
        risk_title="Digital gold is unregulated",
        risk_category="Regulatory",
        severity="High",
        mitigation_strategy=(
            "Build new products with regulated partners (SEBI-registered fund houses, RBI-regulated banks) and "
            "label clearly in the app which products are regulated and by whom."
        ),
    ),
    ExecutionRiskItem(
        risk_title="Handling customer money",
        risk_category="Regulatory",
        severity="High",
        mitigation_strategy=(
            "For funds and deposits, money goes directly from the user's bank to the fund house or partner bank, "
            "never through Jar's own accounts."
        ),
    ),
    ExecutionRiskItem(
        risk_title="KYC drop-off",
        risk_category="Operational",
        severity="Medium",
        mitigation_strategy=(
            "Funds and deposits need fuller KYC than gold saving, so ask for it only when a user first chooses one."
        ),
    ),
    ExecutionRiskItem(
        risk_title="New products pulling money out of gold",
        risk_category="Market",
        severity="Medium",
        mitigation_strategy=(
            "Aim funds and deposits at money that would otherwise leave Jar, and track gold saving per user "
            "before and after."
        ),
    ),
    ExecutionRiskItem(
        risk_title="Fake contribution links",
        risk_category="Fraud",
        severity="Medium",
        mitigation_strategy="Show the verified goal owner's name on every link and make links expire.",
    ),
    ExecutionRiskItem(
        risk_title="Slow B2B sales",
        risk_category="Operational",
        severity="Low",
        mitigation_strategy="Start with one platform and a free pilot judged on worker retention.",
    ),
]


GLOBAL_FLYWHEEL_NARRATIVE: str = (
    "All four ideas reuse what Jar already has: users with an automatic saving habit, a UPI AutoPay set-up they "
    "understand, a simple design and the trust built through vault-backed gold.\n\n"
    "1. New savers: contributions to family goals (Jar Goals) and payout saving (Jar for Work) introduce Jar to "
    "people through someone they already trust.\n"
    "2. Bigger balances: named goals give users more reasons to save.\n"
    "3. Longer retention: funds and fixed deposits give long-term savers a reason to stay instead of moving to "
    "another app when they want to diversify or withdraw.\n"
    "4. New revenue: fund commissions, bank sourcing fees and platform fees add income that doesn't depend on the "
    "gold margin."
)


PRIORITY_NOTE: str = (
    "Jar already has gold saving with a festival option and a jewellery brand, Nek, and its Play Store listing "
    "advertises personal loans through lending partners (I did not see a loans section in my own app), so I "
    "left those out. I also dropped one idea I first considered, "
    "loans against the gold users hold in Jar: RBI's gold-collateral rules, in force since 1 April 2026, don't "
    "allow lending against primary gold or assets backed by it, which rules out digital gold as collateral. Of the "
    "four ideas below, I would start with the two that are cheapest to test. The other two need bank partners or "
    "long B2B sales, so they come later."
)

FIRST_MOVES: List[Dict[str, str]] = [
    {
        "name": "Family goals (Jar Goals)",
        "why": (
            "It extends the festival saving Jar already has, uses the existing gold product, and every "
            "contribution introduces Jar to someone new. Diwali and the wedding season are a natural launch window."
        ),
        "test": (
            "Before Diwali, let 5% of users create a named goal with a share link and compare them with a control "
            "group that doesn't have it."
        ),
        "success": (
            "Share of goals that receive a contribution from someone else, and how many contributors start saving "
            "on their own within 30 days."
        ),
    },
    {
        "name": "Mutual funds alongside gold (Jar Funds)",
        "why": (
            "Long-term savers have nowhere to diversify inside Jar today, and funds are a regulated product that "
            "fits the same saving habit."
        ),
        "test": (
            "Show a 'Save in funds too' card to users who have saved for 6+ months and count taps and waitlist "
            "sign-ups before building anything. Then pilot with two or three funds."
        ),
        "success": (
            "Waitlist sign-up rate among long-term savers and, in the pilot, the share of fund users who keep "
            "their gold save running."
        ),
    },
]


# Global strategy report instance
GROWTH_STRATEGY_REPORT = GrowthStrategyReport(
    verticals=GROWTH_VERTICALS,
    execution_risk_matrix=PLATFORM_RISK_MATRIX,
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


def get_risk_matrix() -> List[ExecutionRiskItem]:
    """Returns the platform-wide execution risk matrix items."""
    return list(PLATFORM_RISK_MATRIX)
