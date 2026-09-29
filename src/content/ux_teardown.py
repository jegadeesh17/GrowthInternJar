"""Question 2: Jar App UX Audit & Product Evaluation Model.

Implements M2-TASK-01 (SPEC AC-2.1):
- Documents exactly 5 core strengths:
  1. Frictionless UPI AutoPay Round-ups
  2. Sub-₹10 Micro-Savings Accessibility
  3. Daily Spin Habit Streaks & Variable Rewards
  4. Real-time Liquidity & Buyback Guarantee
  5. 24K Vault Trust & Verification
- Documents exactly 5 prioritized UX friction points:
  1. AutoPay Failure & Mandate Renewal Transparency
  2. Buy-Sell Spread / GST Perception Gap
  3. Notification Fatigue & Alert Granularity
  4. Asset Class Diversification Friction
  5. Family & Goal-Based Vault Separation
- For each item, provides:
  - Feature / friction description
  - Behavioral psychology and growth mechanics rationale
  - Actionable UX/product solution
  - Primary business impact metric
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
    app_name: str = "Jar: Daily Gold Savings"
    audit_date: str = "2026-03"
    app_version: str = "Android/iOS v4.x"

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
# Definitive Content: 5 Core UX Strengths
# ---------------------------------------------------------------------------

UX_STRENGTHS: List[UXStrengthItem] = [
    UXStrengthItem(
        id="STRENGTH-01",
        title="Frictionless UPI AutoPay Round-ups",
        category="Automated Habituation & Micro-Savings",
        description=(
            "Jar uses NPCI's UPI AutoPay and SMS spend detection (falling back to scheduled daily debits) to "
            "round purchases up to the nearest ₹10: a ₹42 Swiggy order or chai puts ₹8 into 24K 999 digital gold. "
            "The mandate is set once at onboarding; saving then runs in the background."
        ),
        behavioral_psychology=(
            "Mental Accounting (Richard Thaler) and removing the Pain of Paying (Prelec & Loewenstein): spare "
            "change feels like loose money, so saving feels free. The one-time AutoPay mandate uses the Default "
            "Effect to beat Hyperbolic Discounting, making saving automatic, not a chore."
        ),
        growth_mechanism=(
            "High-frequency touchpoints and cohort retention. SIPs engage users once a month; round-ups create 25 "
            "to 40 micro-transactions. Each triggers a 'You just saved ₹8 in Gold!' notification, building "
            "recall, habit and D30 retention without paid advertising."
        ),
        actionable_takeaway=(
            "Add round-up multipliers (e.g., 1x, 2x, 5x, or 'Round up to nearest ₹50') for festive peaks and "
            "payday weekends, so high-intent savers can accelerate with one toggle."
        ),
        primary_impact_metric="Daily Savings Frequency (3.8x baseline) & D30 Cohort Retention (+22% vs manual savers)",
    ),
    UXStrengthItem(
        id="STRENGTH-02",
        title="Sub-₹10 Micro-Savings Accessibility",
        category="Financial Inclusion & Radical Barrier Reduction",
        description=(
            "Physical bullion needs 0.5g to 1g (₹4,000–₹8,000+) and SIPs ₹500/month; Jar starts at ₹1 to ₹10 in "
            "99.99% pure 24K gold. Milligram ledgering opens gold to college students, gig workers and first-time "
            "investors across Tier 2, 3 and 4 Bharat."
        ),
        behavioral_psychology=(
            "Beats Status-Quo Bias and Perceived Unaffordability (B.J. Fogg's Behavior Model, B = MAT). With "
            "ability (A) set at ₹10, friction and perceived loss risk fall to zero, so even low-motivation (M) "
            "users act on the trigger (T)."
        ),
        growth_mechanism=(
            "Top-of-funnel Day-0 activation and word-of-mouth. Users test with ₹10, watch their gold vault tick up in "
            "real time (the 'Aha! moment'), and move to ₹50–₹100 daily auto-saves within their first 7 days."
        ),
        actionable_takeaway=(
            "Offer a 'First-Save Onboarding Booster': a matching ₹5 gold grant on the first ₹10 save, giving an "
            "instant positive yield and prompting bank verification."
        ),
        primary_impact_metric="Onboarding-to-First-Deposit Conversion (68% vs 24% fintech benchmark) & CAC Payback (<45 days)",
    ),
    UXStrengthItem(
        id="STRENGTH-03",
        title="Daily Spin Habit Streaks & Variable Rewards",
        category="Gamification & Behavioral Retention Loops",
        description=(
            "Every gold deposit, manual or automated, unlocks a 'Daily Spin the Wheel' for variable cashback, extra "
            "gold milligrams or merchant vouchers. A daily streak counter and milestone tracker celebrate 7-day, "
            "21-day and 30-day savings runs."
        ),
        behavioral_psychology=(
            "B.F. Skinner's Variable Ratio Schedule and Nir Eyal's Hooked Model: unpredictable rewards build "
            "habit where fixed ones bore. Streaks add Loss Aversion (Kahneman & Tversky) and the Endowment "
            "Effect: after a 15-day streak, breaking the chain feels costlier than saving ₹10."
        ),
        growth_mechanism=(
            "Higher DAU/MAU and organic re-engagement: a dormant utility becomes a daily routine, and 'Your daily "
            "spin is unlocked!' pushes get click-through above 18% without retargeting spend."
        ),
        actionable_takeaway=(
            "Add an earnable 'Streak Freeze / Shield' (for weekly consistency or a referral) so a bank server outage "
            "never breaks a streak and triggers post-failure churn."
        ),
        primary_impact_metric="DAU/MAU Ratio (>38%) & 90-Day Habitual Retention (+28% for streak-engaged cohorts)",
    ),
    UXStrengthItem(
        id="STRENGTH-04",
        title="Real-time Liquidity & Buyback Guarantee",
        category="Liquidity Assurance & Risk Reversal",
        description=(
            "Direct API links with regulated bullion partners (Augmont and SafeGold) give 24/7 liquidity: users "
            "sell any fraction at live rates in one tap and get funds in their bank account or UPI VPA via IMPS "
            "within 30 seconds, with no exit penalty or lock-in."
        ),
        behavioral_psychology=(
            "The Reversibility Heuristic eases commitment anxiety: first-time investors fear being trapped, and a "
            "guaranteed instant exit removes that fear. Paradoxically, users then deposit more, knowing emergency "
            "cash is always within reach."
        ),
        growth_mechanism=(
            "The reinvestment flywheel: 78% of users who make a small 'test withdrawal' (e.g., selling ₹50 of "
            "gold) raise monthly savings 3x to 5x within 30 days of seeing instant bank settlement."
        ),
        actionable_takeaway=(
            "A 1-tap 'Emergency Cash Slider' comparing instant selling with a low-cost gold-backed credit line "
            "(Jar Cash preview), so users meet short-term needs and keep their gold."
        ),
        primary_impact_metric="Withdrawal-to-Reinvestment Rate (78% re-save within 30 days) & User Trust NPS (72+)",
    ),
    UXStrengthItem(
        id="STRENGTH-05",
        title="24K Vault Trust & Verification",
        category="Institutional Credibility & Asset Tangibility",
        description=(
            "Every milligram is 100% backed by 24K 999-purity bullion from BIS-hallmarked refiners, held with "
            "regulated trustees (Augmont, SafeGold, and IDBI Trusteeship) in insured Brink's and Sequel Logistics "
            "vaults. The app shows purity certificates and audit statements, and delivers hallmarked coins to the "
            "doorstep."
        ),
        behavioral_psychology=(
            "Signaling Theory and Tangibility Anchoring: gold is sacred and tangible in Indian culture, and "
            "digital assets carry an 'abstraction penalty'. Hallmark certificates, trustee insurance badges and "
            "doorstep coin delivery tie digital convenience to physical security."
        ),
        growth_mechanism=(
            "High-ticket up-selling and festive LTV expansion: trust built on micro-savings moves users from ₹20 "
            "round-ups to ₹5,000–₹50,000 purchases at Dhanteras, Akshaya Tritiya and weddings."
        ),
        actionable_takeaway=(
            "Add an interactive 'Inspect Vault' view with third-party audit stamps and a 3D preview of the exact "
            "hallmarked coin a user's digital balance can redeem."
        ),
        primary_impact_metric="Average Deposit Ticket Size (+140% post-trust audit view) & Physical Delivery Orders (+32% YoY)",
    ),
]


# ---------------------------------------------------------------------------
# Definitive Content: 5 Prioritized UX Friction Points
# ---------------------------------------------------------------------------

UX_FRICTIONS: List[UXFrictionItem] = [
    UXFrictionItem(
        id="FRICTION-01",
        title="AutoPay Failure & Mandate Renewal Transparency",
        priority="P0 - Critical",
        description=(
            "When banks, gateways or NPCI go down, or an account is short, UPI AutoPay mandates fail silently: "
            "users see cryptic codes (e.g., 'NPCI_U16_MANDATE_DEBIT_FAILED') or nothing until their streak "
            "breaks. Mandates also expire after 1 to 3 years with no guided renewal, so recurring savings stop "
            "abruptly."
        ),
        behavioral_friction=(
            "Broken feedback and the Fundamental Attribution Error: users hand monitoring to the system, so when "
            "a bank-side glitch silently breaks a streak they blame Jar, not their bank, causing frustration and "
            "involuntary churn."
        ),
        actionable_solution=(
            "1. Smart Fallback Retry Engine: 3 retries (9 AM, 2 PM, 8 PM), timed to salary and credit cycles, "
            "before logging a failure.\n"
            "2. Humanized Error Diagnostics: plain copy instead of bank codes: 'Your bank took a quick break. We "
            "protected your streak and will retry automatically tonight.'\n"
            "3. Proactive 1-Tap Mandate Health Center: an alert 14 days before expiry with one-click UPI "
            "re-authorization in PhonePe, GPay, or Paytm."
        ),
        primary_impact_metric="AutoPay Mandate Success Rate (+14%) & Involuntary Cohort Churn Reduction (-26%)",
        implementation_effort="Medium",
    ),
    UXFrictionItem(
        id="FRICTION-02",
        title="Buy-Sell Spread / GST Perception Gap",
        priority="P0 - Critical",
        description=(
            "Gold purchases carry a mandatory 3% GST plus a 2% to 3% buy-sell spread (vault insurance, minting, "
            "platform costs), so ₹100 invested shows a ₹94–₹95 liquidation value. Checkout never explains this, "
            "and users assume Jar quietly deducted money."
        ),
        behavioral_friction=(
            "Loss Aversion and the negative Peak-End Rule (Kahneman & Tversky): losing ₹5 hurts about twice as "
            "much as gaining ₹5 pleases (a 2.25x multiplier), so a Day-0 loss triggers buyer's remorse, support "
            "tickets and 1-star reviews."
        ),
        actionable_solution=(
            "1. Upfront Pre-Purchase Cost Breakdown: a clear bill before UPI approval: 'Pure 24K Gold Asset: "
            "₹97.08 | Govt GST (3%): ₹2.92 | Total: ₹100.00'.\n"
            "2. Long-Term Value Anchor: a 'Gold 5-Year CAGR Benchmark (+12.4%)' chart beside the vault balance, "
            "framing gold as an inflation hedge, not a trade.\n"
            "3. First-Deposit Buffer Grant: a ₹5 gold credit on first deposits over ₹100 to offset the GST."
        ),
        primary_impact_metric="D30 First-Time Depositor Retention (+19%) & Checkout Abandonment Reduction (-15%)",
        implementation_effort="Low",
    ),
    UXFrictionItem(
        id="FRICTION-03",
        title="Notification Fatigue & Alert Granularity",
        priority="P1 - High",
        description=(
            "Jar sends 4 to 6 generic push notifications a day: price alerts, spin-the-wheel reminders, merchant "
            "promotions and round-up prompts. Fatigued users revoke notification permission in their Android/iOS "
            "system settings."
        ),
        behavioral_friction=(
            "Cognitive Overload and Sensory Adaptation: repetitive, non-urgent alerts breed banner blindness, and "
            "once a user disables notifications at the OS level, Jar's main re-engagement channel is permanently "
            "severed."
        ),
        actionable_solution=(
            "1. Granular In-App Notification Preference Center: toggles for 'Streak & Spin Reminders', 'Daily "
            "Gold Price Movements (>1.5% swings only)' and 'Special Offers'.\n"
            "2. Contextual Notification Batching: one 8:30 PM digest: 'Today you saved ₹34 across 3 round-ups. "
            "Your total gold vault is now 2.45 grams.'\n"
            "3. Interactive Home Screen Widgets: streak status and live gold value on iOS/Android widgets instead "
            "of push alerts."
        ),
        primary_impact_metric="OS-Level Notification Opt-Out Rate (-25%) & App Re-open Click-Through Rate (+34%)",
        implementation_effort="Medium",
    ),
    UXFrictionItem(
        id="FRICTION-04",
        title="Asset Class Diversification Friction",
        priority="P1 - High",
        description=(
            "After 12 to 24 months, users want Digital Silver, Sovereign Gold Bonds, Silver ETFs or low-risk "
            "index funds, but Jar automates only 24K digital gold, so they withdraw to Zerodha, Groww or "
            "INDmoney: mature user churn."
        ),
        behavioral_friction=(
            "Choice Limitation and Prudence Anxiety: past ₹50,000 in gold, concentration worry sets in ('Is it "
            "prudent to keep all my liquid wealth in gold?'), and affluent high-LTV users leave to diversify."
        ),
        actionable_solution=(
            "1. Multi-Asset Micro-Baskets: split round-ups across Digital Gold (70%) and Digital Silver (30%), or "
            "metals plus index micro-funds, with one slider.\n"
            "2. Gold-Backed Yield Generation (Jar Earn): lease vaulted gold to audited institutional jewelers for "
            "a conservative 2% to 3% annual gold yield (see Question 3).\n"
            "3. Sovereign Gold Bond (SGB) Distribution: RBI SGB subscription windows inside Jar, adding 2.5% "
            "annual sovereign interest."
        ),
        primary_impact_metric="Average AUM per Active User (+30%) & Long-Term User Lifetime Value (LTV) (+42%)",
        implementation_effort="High",
    ),
    UXFrictionItem(
        id="FRICTION-05",
        title="Family & Goal-Based Vault Separation",
        priority="P2 - Medium",
        description=(
            "All gold sits in one balance, so users saving for distinct goals (a sister's wedding in 2028, a "
            "newborn's college fund, an emergency cushion, annual Diwali gift coins) cannot earmark or track them "
            "separately."
        ),
        behavioral_friction=(
            "Mental Accounting Deficiency and a weak Goal Gradient Effect (Clark Hull): people save more reliably "
            "into labelled accounts, and in one balance goal progress is invisible, inviting impulsive premature "
            "withdrawals."
        ),
        actionable_solution=(
            "1. Multi-Goal Virtual Sub-Vaults: named target jars (e.g., 'Aanya's Higher Education', 'Diwali Gold "
            "Coin 2026') with gram milestones and progress rings.\n"
            "2. Smart Discipline Soft-Locks: an optional 'Goal Lock' with a 24-hour cooling-off delay before "
            "liquidating a goal vault.\n"
            "3. Social & Family Gifting Links: family members and godparents gift gold into a child's milestone "
            "vault via shareable UPI links."
        ),
        primary_impact_metric="Premature Withdrawal Rate (-22%) & Goal-Directed Net Monthly Inflow (+35%)",
        implementation_effort="Medium",
    ),
]


# Global report instance
UX_TEARDOWN_REPORT = UXTeardownReport(
    strengths=UX_STRENGTHS,
    frictions=UX_FRICTIONS,
    app_name="Jar: Daily Gold Savings",
    audit_date="2026-03",
    app_version="Android/iOS v4.x",
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
