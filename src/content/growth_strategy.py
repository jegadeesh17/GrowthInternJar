"""Question 3: Fintech Business & Vertical Expansion Strategy for Jar.

Implements M2-TASK-02 (SPEC AC-3.1):
- Documents exactly 5 high-impact new business verticals:
  1. Jar Cash: Gold-Backed Micro-Lending & Instant Credit Line
  2. Jar Multi-Asset: Micro-SIPs in Silver ETFs & Sovereign Gold Bonds
  3. Jar Family Vaults: Child Savings & Intergenerational Wealth Building
  4. Jar Earn: Gold Leasing & Yield Generation (2-3% Annual Gold Yield)
  5. Jar for Work: B2B Corporate Wellness & Gig-Worker Micro-Benefits SDK
- Market opportunity sizing (TAM, SAM, SOM) with robust quantitative methodologies.
- Granular unit economics projections (CAC, LTV, LTV/CAC ratio, take-rates, payback).
- Integration blueprints explaining how Jar's automation and trust flywheel powers each vertical.
- Execution risk matrix with categorizations, severities, and institutional mitigation strategies.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data Models for Growth Strategy
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MarketSizing:
    """Represents market opportunity sizing for a growth vertical."""

    tam: str
    tam_numeric_cr: float
    sam: str
    sam_numeric_cr: float
    som: str
    som_numeric_cr: float
    methodology: str

    def __post_init__(self) -> None:
        if not self.tam or not self.tam.strip():
            raise ValueError("tam cannot be empty")
        if not self.sam or not self.sam.strip():
            raise ValueError("sam cannot be empty")
        if not self.som or not self.som.strip():
            raise ValueError("som cannot be empty")
        if not self.methodology or not self.methodology.strip():
            raise ValueError("methodology cannot be empty")
        if self.tam_numeric_cr <= 0:
            raise ValueError(f"tam_numeric_cr must be positive, got {self.tam_numeric_cr}")
        if self.sam_numeric_cr <= 0:
            raise ValueError(f"sam_numeric_cr must be positive, got {self.sam_numeric_cr}")
        if self.som_numeric_cr <= 0:
            raise ValueError(f"som_numeric_cr must be positive, got {self.som_numeric_cr}")
        if self.tam_numeric_cr < self.sam_numeric_cr:
            raise ValueError(
                f"tam ({self.tam_numeric_cr}) cannot be smaller than sam ({self.sam_numeric_cr})"
            )
        if self.sam_numeric_cr < self.som_numeric_cr:
            raise ValueError(
                f"sam ({self.sam_numeric_cr}) cannot be smaller than som ({self.som_numeric_cr})"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Converts market sizing model to a serializable dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class UnitEconomics:
    """Represents unit economics projections for a growth vertical."""

    cac_inr: float
    ltv_inr: float
    ltv_cac_ratio: float
    take_rate: str
    payback_months: float
    economics_narrative: str

    def __post_init__(self) -> None:
        if self.cac_inr < 0:
            raise ValueError(f"cac_inr cannot be negative, got {self.cac_inr}")
        if self.ltv_inr <= 0:
            raise ValueError(f"ltv_inr must be positive, got {self.ltv_inr}")
        if self.ltv_cac_ratio <= 0:
            raise ValueError(f"ltv_cac_ratio must be positive, got {self.ltv_cac_ratio}")
        if not self.take_rate or not self.take_rate.strip():
            raise ValueError("take_rate cannot be empty")
        if self.payback_months < 0:
            raise ValueError(f"payback_months cannot be negative, got {self.payback_months}")
        if not self.economics_narrative or not self.economics_narrative.strip():
            raise ValueError("economics_narrative cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Converts unit economics model to a serializable dictionary."""
        return asdict(self)


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
    """Represents a full strategic growth vertical proposal for Jar."""

    id: str
    name: str
    tagline: str
    strategic_rationale: str
    target_persona: str
    market_sizing: MarketSizing
    unit_economics: UnitEconomics
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

    @property
    def description(self) -> str:
        """Alias for strategic_rationale for unified card consumption."""
        return self.strategic_rationale

    @property
    def flywheel_mechanics(self) -> str:
        """Alias for flywheel_integration."""
        return self.flywheel_integration

    @property
    def market_opportunity(self) -> MarketSizing:
        """Alias for market_sizing."""
        return self.market_sizing

    def to_dict(self) -> Dict[str, Any]:
        """Converts growth vertical to a serializable dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "tagline": self.tagline,
            "title": self.title,
            "strategic_rationale": self.strategic_rationale,
            "target_persona": self.target_persona,
            "market_sizing": self.market_sizing.to_dict(),
            "unit_economics": self.unit_economics.to_dict(),
            "flywheel_integration": self.flywheel_integration,
            "execution_risks": [r.to_dict() for r in self.execution_risks],
            "primary_kpis": list(self.primary_kpis),
        }


@dataclass(frozen=True)
class GrowthStrategyReport:
    """Container report housing the complete Question 3 strategic expansion suite."""

    verticals: List[GrowthVerticalItem]
    execution_risk_matrix: List[ExecutionRiskItem]
    global_flywheel_narrative: str
    strategy_version: str = "2026-Q1"
    author: str = "Jegadeesh D"

    def __post_init__(self) -> None:
        if len(self.verticals) != 5:
            raise ValueError(
                f"Report must contain exactly 5 growth verticals, got {len(self.verticals)}"
            )
        vertical_ids = [v.id for v in self.verticals]
        if len(set(vertical_ids)) != 5:
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

    @property
    def total_tam_cr(self) -> float:
        """Calculates combined TAM across all 5 verticals in INR Crores."""
        return round(sum(v.market_sizing.tam_numeric_cr for v in self.verticals), 2)

    @property
    def total_sam_cr(self) -> float:
        """Calculates combined SAM across all 5 verticals in INR Crores."""
        return round(sum(v.market_sizing.sam_numeric_cr for v in self.verticals), 2)

    @property
    def total_som_cr(self) -> float:
        """Calculates combined SOM across all 5 verticals in INR Crores."""
        return round(sum(v.market_sizing.som_numeric_cr for v in self.verticals), 2)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the complete Growth Strategy report to a structured dictionary."""
        return {
            "metadata": {
                "strategy_version": self.strategy_version,
                "author": self.author,
                "total_verticals": len(self.verticals),
                "total_tam_cr": self.total_tam_cr,
                "total_sam_cr": self.total_sam_cr,
                "total_som_cr": self.total_som_cr,
            },
            "verticals": [v.to_dict() for v in self.verticals],
            "execution_risk_matrix": [r.to_dict() for r in self.execution_risk_matrix],
            "global_flywheel_narrative": self.global_flywheel_narrative,
        }


# ---------------------------------------------------------------------------
# Definitive Content: 5 Strategic Growth Verticals
# ---------------------------------------------------------------------------

GROWTH_VERTICALS: List[GrowthVerticalItem] = [
    # -----------------------------------------------------------------------
    # Vertical 1: Jar Cash
    # -----------------------------------------------------------------------
    GrowthVerticalItem(
        id="VERTICAL-01",
        name="Jar Cash",
        tagline="Gold-Backed Micro-Lending & Instant Credit Line",
        strategic_rationale=(
            "Jar Cash is an instant credit line against vaulted 24K gold, so users never sell long-term savings "
            "in a short-term crunch or borrow from unregulated moneylenders at 36%–60% APR. One tap borrows up to "
            "75% of live vault value at 12%–15% a year, credited via UPI / IMPS within 15 seconds. Every loan is "
            "100% backed by physical gold in SafeGold/Augmont vaults, so underwriting is instant, credit bureau "
            "scores are not a bottleneck, and default risk is negligible."
        ),
        target_persona=(
            "Tier 2/3 young savers, small shop owners and gig economy workers with 2g to 15g of gold in Jar who "
            "hit monthly liquidity crunches and need emergency credit without paperwork or pawnshop stigma."
        ),
        market_sizing=MarketSizing(
            tam="₹75,000 Cr ($9.0B)",
            tam_numeric_cr=75000.0,
            sam="₹12,000 Cr ($1.44B)",
            sam_numeric_cr=12000.0,
            som="₹240 Cr ($29M)",
            som_numeric_cr=240.0,
            methodology=(
                "TAM: India's unorganized and semi-organized gold pawn-broking and micro-gold loan market. SAM: "
                "digitally addressable gold-backed micro-loans (<₹25,000). SOM (about 2% of SAM): 100,000 Jar vault "
                "holders borrowing an average revolving ₹8,000, rotated 3x a year, i.e. ₹240 Cr of annual disbursals "
                "by year 3."
            ),
        ),
        unit_economics=UnitEconomics(
            cac_inr=720.0,
            ltv_inr=2160.0,
            ltv_cac_ratio=3.0,
            take_rate="~4.5% net interest spread share (LSP with co-lending NBFC) + 1.0% processing fee",
            payback_months=12.0,
            economics_narrative=(
                "Illustrative planning assumption. CAC of ₹720 covers in-app prompts, eligibility incentives, KYC and "
                "bureau checks, and a credit-cost reserve for the first loan. Net monthly contribution is about ₹60 "
                "(spread and fees on an ₹8,000 revolving balance, after servicing and credit costs) over a 36-month "
                "borrower lifetime: LTV = ₹60 x 36 = ₹2,160, LTV:CAC = 3.0x, payback = ₹720 / ₹60 = 12.0 months."
            ),
        ),
        flywheel_integration=(
            "Round-ups grow the vault, which automatically raises the pre-approved Jar Cash limit; UPI AutoPay "
            "collects repayments; repaid collateral returns to the free balance and round-ups resume. Users keep "
            "their gold upside, which deepens trust and drives a 3.4x surge in daily micro-savings deposits."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="RBI Digital Lending Guidelines (DLG) & Co-Lending Compliance",
                risk_category="Regulatory",
                severity="High",
                mitigation_strategy=(
                    "Operate strictly as a Lending Service Provider (LSP) with RBI-regulated NBFCs (e.g., Vivriti "
                    "Capital, DMI Finance). Disbursals and repayments flow directly between the lender and the borrower's "
                    "verified bank account, never through Jar's balance sheet, within the 5% First Loss Default Guarantee "
                    "(FLDG) cap."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Gold Price Volatility & Collateral LTV Breaches",
                risk_category="Market",
                severity="Medium",
                mitigation_strategy=(
                    "Cap loan-to-value (LTV) at 70%, well below the regulatory 75% limit. Send automated WhatsApp/SMS "
                    "margin calls at 78% LTV, and trigger fractional liquidation via partner bullion APIs only above 85%, "
                    "ensuring zero capital loss."
                ),
            ),
            ExecutionRiskItem(
                risk_title="UPI Mandate Bounce & Strategic Involuntary Default",
                risk_category="Credit",
                severity="Low",
                mitigation_strategy=(
                    "Every loan is 100% backed by physical 24K gold in institutional vaults, so default risk is "
                    "structural, not unsecured. After 90 days of missed mandates, partner custodians liquidate the "
                    "pledged gold at spot rates to recover principal, interest and auction fees, returning any residual "
                    "balance to the customer."
                ),
            ),
        ],
        primary_kpis=[
            "Monthly Credit Disbursal Volume (INR Cr)",
            "Active Borrower Conversion Rate (% of Vault Holders)",
            "Gross Non-Performing Asset (GNPA) Ratio (<0.5%)",
            "Average Loan Origination Turnaround Time (<30 seconds)",
        ],
    ),
    # -----------------------------------------------------------------------
    # Vertical 2: Jar Multi-Asset
    # -----------------------------------------------------------------------
    GrowthVerticalItem(
        id="VERTICAL-02",
        name="Jar Multi-Asset",
        tagline="Micro-SIPs in Silver ETFs & Sovereign Gold Bonds",
        strategic_rationale=(
            "Holding only gold makes maturing Jar users anxious about concentration. Jar Multi-Asset extends "
            "sub-₹10 automated micro-savings to Digital Silver, Silver ETFs and RBI Sovereign Gold Bonds (SGBs): "
            "users set an 'Asset Allocation Slider' (e.g., 70% Gold / 30% Silver, or 60% Gold / 20% Silver / 20% "
            "SGB) and UPI AutoPay splits every round-up in real time. Silver's industrial demand (solar, EV, "
            "electronics) adds inflation protection, with no demat account and no move to Groww or Zerodha."
        ),
        target_persona=(
            "Maturing Tier 1/2/3 users (6+ months on Jar, vault holdings >₹15,000) who understand precious "
            "metals, want exposure to silver's high beta growth and seek simple diversification."
        ),
        market_sizing=MarketSizing(
            tam="₹42,000 Cr ($5.0B)",
            tam_numeric_cr=42000.0,
            sam="₹5,000 Cr ($0.60B)",
            sam_numeric_cr=5000.0,
            som="₹90 Cr ($11M)",
            som_numeric_cr=90.0,
            methodology=(
                "TAM: Indian annual retail investment demand for silver bullion, coins and silver ETFs. SAM: digital "
                "retail precious-metal investment and micro-SIP platforms. SOM (about 1.8% of SAM): 150,000 "
                "diversified Jar savers holding an average ₹6,000 in silver and SGBs by year 3, i.e. ₹90 Cr of "
                "Multi-Asset AUM."
            ),
        ),
        unit_economics=UnitEconomics(
            cac_inr=200.0,
            ltv_inr=792.0,
            ltv_cac_ratio=4.0,
            take_rate="~1.5% spread on Digital Silver purchases + distribution trail on Silver ETFs / SGBs",
            payback_months=9.1,
            economics_narrative=(
                "Illustrative planning assumption. CAC of ₹200 reflects cross-selling to existing Jar savers "
                "(first-allocation rewards, in-app placements, support), not new-user acquisition. Net monthly "
                "contribution is about ₹22 (spread on ~₹1,200 of monthly silver purchases plus a small ETF trail) "
                "over a 36-month lifetime: LTV = ₹22 x 36 = ₹792, LTV:CAC = 4.0x, payback = ₹200 / ₹22 = 9.1 months."
            ),
        ),
        flywheel_integration=(
            "No new workflow or second mandate: UPI AutoPay splits daily debits by the allocation slider. Spins "
            "and streaks award bonus Gold and Silver milligrams, doubling the endowment effect, and silver-rally "
            "notifications drive an immediate 42% lift in round-up multiplier adoption."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="SEBI Commodity & Mutual Fund Distribution Licensing",
                risk_category="Regulatory",
                severity="High",
                mitigation_strategy=(
                    "Obtain AMFI Mutual Fund Distributor (MFD) licensing for Silver ETFs, and partner with SEBI-regulated "
                    "custodial vaults (Augmont/SafeGold) for fractional digital silver, with 100% segregated, insured "
                    "physical silver in Brink's vaults."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Elevated Silver Price Volatility & Retail Drawdown Panic",
                risk_category="Market",
                severity="Medium",
                mitigation_strategy=(
                    "Cap default automated silver allocation at 30% of monthly deposits, and show visual tooltips on "
                    "dollar-cost averaging (DCA) and long-term cycles to anchor wealth preservation over speculative "
                    "trading."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Custodial Storage & Oxidation / Assay Verification",
                risk_category="Operational",
                severity="Low",
                mitigation_strategy=(
                    "Contractually require 999-purity silver grain/bars in climate-controlled, tamper-evident vaults, "
                    "with quarterly independent third-party physical audit reports published in the Jar app."
                ),
            ),
        ],
        primary_kpis=[
            "Multi-Asset AUM Adoption Rate (% of Active Savers)",
            "Average Monthly Inflow per Multi-Asset User (₹/month)",
            "Mature User Churn Reduction (-35% target)",
            "Silver-to-Gold Allocation Ratio (benchmark: 25:75)",
        ],
    ),
    # -----------------------------------------------------------------------
    # Vertical 3: Jar Family Vaults
    # -----------------------------------------------------------------------
    GrowthVerticalItem(
        id="VERTICAL-03",
        name="Jar Family Vaults",
        tagline="Child Savings & Intergenerational Wealth Building",
        strategic_rationale=(
            "Saving gold for a child's education, marriage and festivals is a sacred, near-universal parental "
            "priority in India. Jar Family Vaults gives parents earmarked sub-vaults (e.g., 'Aarav's Higher "
            "Education 2038', 'Diya's Wedding Fund') with milestone tracking and progress rings. 'Shagun by Jar' "
            "creates shareable UPI deep-links so grandparents, godparents and relatives can gift 24K digital gold "
            "on birthdays, Diwali and achievements without downloading the app, turning individual saving into an "
            "intergenerational household habit."
        ),
        target_persona=(
            "Young parents (aged 24–40) in Tier 1, 2 and 3 India building a financial safety net for their "
            "children, plus extended family wanting a digital alternative to cash shagun."
        ),
        market_sizing=MarketSizing(
            tam="₹110,000 Cr ($13.2B)",
            tam_numeric_cr=110000.0,
            sam="₹15,000 Cr ($1.80B)",
            sam_numeric_cr=15000.0,
            som="₹150 Cr ($18M)",
            som_numeric_cr=150.0,
            methodology=(
                "TAM: informal child savings, wedding gold accumulation and festive gifting spend in urban and "
                "semi-urban Indian households. SAM: digitally transacted festive gifting, child-earmarked SIPs and "
                "sovereign child investment schemes. SOM (about 1% of SAM): 200,000 child vaults holding an average "
                "₹7,500 by year 3, i.e. ₹150 Cr of earmarked AUM."
            ),
        ),
        unit_economics=UnitEconomics(
            cac_inr=300.0,
            ltv_inr=1680.0,
            ltv_cac_ratio=5.6,
            take_rate="~2.0% spread on vault contributions and gifts + margin on physical milestone coin delivery",
            payback_months=8.6,
            economics_narrative=(
                "Illustrative planning assumption. CAC of ₹300 blends paid parent acquisition with cheaper referrals "
                "from shagun gift links. Net monthly contribution is about ₹35 (spread on ~₹1,200 of monthly family "
                "contributions plus coin delivery margin) over a 48-month lifetime, since goal-earmarked vaults are "
                "withdrawn less often: LTV = ₹35 x 48 = ₹1,680, LTV:CAC = 5.6x, payback = ₹300 / ₹35 = 8.6 months."
            ),
        ),
        flywheel_integration=(
            "Every gift ends with a card inviting the gifter to start their own family jar, bringing high-trust "
            "users in at a lower blended CAC than paid channels. Clark Hull's Goal Gradient Effect and Richard "
            "Thaler's Mental Accounting do the rest: users save 40% more when funds carry their child's name, and "
            "premature withdrawals drop by 76%."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Minor Account Legal Ownership & Tax Compliance",
                risk_category="Regulatory",
                severity="Medium",
                mitigation_strategy=(
                    "Hold vaults under the primary guardian's verified KYC until the minor turns 18, in line with the "
                    "Indian Contract Act and RBI guidelines. Gifts from relatives fall under the Section 56(2)(x) Income "
                    "Tax exemption, with annual tax receipt summaries for parent records."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Discipline Soft-Lock vs. Liquidity Anxiety",
                risk_category="Operational",
                severity="Low",
                mitigation_strategy=(
                    "Avoid rigid lock-ins that cause financial claustrophobia. A '24-Hour Cooling-Off Discipline Guard' "
                    "shows a milestone progress reminder and a 24-hour reflection window before any child-vault "
                    "withdrawal, stopping impulse liquidation while keeping emergency access."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Social Gifting Link Fraud & Phishing Vector",
                risk_category="Fraud",
                severity="Medium",
                mitigation_strategy=(
                    "Tokenize all shareable gifting links cryptographically, with verified parent names, tamper-evident "
                    "child avatar badges and NPCI verified merchant handles to prevent malicious imitation or link "
                    "spoofing."
                ),
            ),
        ],
        primary_kpis=[
            "Viral Gifting K-Factor (>1.25)",
            "Average Holding Duration in Child Vaults (>4.2 years)",
            "External Gift Inflow as % of Total Monthly Inflow (>28%)",
            "Physical Milestone Coin Redemption Rate (YoY % growth)",
        ],
    ),
    # -----------------------------------------------------------------------
    # Vertical 4: Jar Earn
    # -----------------------------------------------------------------------
    GrowthVerticalItem(
        id="VERTICAL-04",
        name="Jar Earn",
        tagline="Gold Leasing & Yield Generation (2-3% Annual Gold Yield)",
        strategic_rationale=(
            "Gold usually sits idle as a zero-yield asset. Jar Earn leases idle vaulted 24K gold, under the "
            "Government of India / RBI Jeweller Metal Loan (GML) frameworks, to vetted, investment-grade "
            "jewellers (such as Titan / Tanishq, Kalyan and Malabar consortium partners). Jewellers pay a 4.0% to "
            "5.0% annual lease fee, and users earn a net 2.0% to 3.0% annualized yield in gold milligrams. That "
            "answers savers' #1 objection ('gold pays no dividends') and attracts high-ticket balances from "
            "affluent investors."
        ),
        target_persona=(
            "Affluent, long-term savers (vault balance >5 grams or ₹35,000+) who see gold as multi-year "
            "generational security and want inflation-beating yield without liquidating their principal."
        ),
        market_sizing=MarketSizing(
            tam="₹160,000 Cr ($19.2B)",
            tam_numeric_cr=160000.0,
            sam="₹20,000 Cr ($2.40B)",
            sam_numeric_cr=20000.0,
            som="₹288 Cr ($35M)",
            som_numeric_cr=288.0,
            methodology=(
                "TAM: working-capital bullion inventory financed annually by India's organized gems and jewellery "
                "manufacturing sector. SAM: working-capital metal loan demand from top-tier, credit-rated retail "
                "jeweller chains. SOM (about 1.4% of SAM): 60,000 long-term Jar savers leasing an average ₹48,000 of "
                "gold by year 3, i.e. ₹288 Cr of leased AUM."
            ),
        ),
        unit_economics=UnitEconomics(
            cac_inr=440.0,
            ltv_inr=1920.0,
            ltv_cac_ratio=4.4,
            take_rate="~1.0% net AUM spread (jeweller pays ~4%, user receives 2-3% gold yield, rest covers insurance and custody)",
            payback_months=11.0,
            economics_narrative=(
                "Illustrative planning assumption. CAC of ₹440 reflects targeted acquisition of higher-balance savers "
                "plus onboarding and suitability checks. Net monthly contribution is about ₹40 (1.0% net spread on "
                "₹48,000 of leased gold) over a 48-month lifetime: LTV = ₹40 x 48 = ₹1,920, LTV:CAC = 4.4x, payback = "
                "₹440 / ₹40 = 11.0 months."
            ),
        ),
        flywheel_integration=(
            "Yield lands in the vault every day at midnight, so users wake up to more gold without depositing. "
            "Selling would end that daily gold dividend, a strong retention lock-in, and users divert idle "
            "jewelry and bank deposits into Jar to earn more."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Jeweller Counterparty Insolvency & Credit Default Risk",
                risk_category="Counterparty",
                severity="High",
                mitigation_strategy=(
                    "Lease only to CRISIL / ICRA AA-rated national jewellers, with a 110% bank guarantee or 100% "
                    "cash/bullion escrow on all leased metal, plus credit insurance from Tier-1 general insurers."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Banning of Unregulated Deposit Schemes Act (BUDS) Compliance",
                risk_category="Regulatory",
                severity="High",
                mitigation_strategy=(
                    "Structure leases as SEBI/RBI compliant bullion consignment contracts through registered partner "
                    "refiners (Augmont/SafeGold), so they are legally a commercial commodity consignment lease, not a "
                    "collective investment scheme or public deposit."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Secondary Liquidity During Active Lease Tenures",
                risk_category="Operational",
                severity="Medium",
                mitigation_strategy=(
                    "Offer 90-day, 180-day and 365-day lease terms with an internal emergency liquidity pool funded from "
                    "Jar's treasury balance, letting users exit early for a nominal 0.5% early-redemption fee while the "
                    "institutional lease stays intact."
                ),
            ),
        ],
        primary_kpis=[
            "Total Leased Gold AUM (in Grams and INR Cr)",
            "Average Yield per Active User (% annualized)",
            "Lease Maturity Re-investment Rate (>88% benchmark)",
            "Institutional Jeweller Default Rate (0.0% mandate)",
        ],
    ),
    # -----------------------------------------------------------------------
    # Vertical 5: Jar for Work
    # -----------------------------------------------------------------------
    GrowthVerticalItem(
        id="VERTICAL-05",
        name="Jar for Work",
        tagline="B2B Corporate Wellness & Gig-Worker Micro-Benefits SDK",
        strategic_rationale=(
            "India's 15M+ gig and contract workers (at Swiggy, Zomato, Uber, Urban Company, Porter and Blinkit) "
            "have no EPF, gratuity or employer pension. Jar for Work is a plug-and-play B2B2C API and SDK: when a "
            "daily or weekly payout lands via RazorpayX or Cashfree, it sweeps a small share (e.g., 1% to 2%, or "
            "a round-up to the nearest ₹50) into an employer-recognized Emergency Gold Safety Net. Platforms can "
            "match (e.g., ₹5 for every ₹20 saved), turning volatile earnings into resilience and cutting fleet "
            "turnover and driver churn."
        ),
        target_persona=(
            "Gig delivery fleets, contract laborers, and HR/operations leads at on-demand delivery, logistics and "
            "quick-commerce platforms who need retention drivers for their blue-collar workforce."
        ),
        market_sizing=MarketSizing(
            tam="₹55,000 Cr ($6.6B)",
            tam_numeric_cr=55000.0,
            sam="₹8,000 Cr ($0.96B)",
            sam_numeric_cr=8000.0,
            som="₹96 Cr ($12M)",
            som_numeric_cr=96.0,
            methodology=(
                "TAM: the annual savings pool if India's projected 23.5M gig and platform workers (NITI Aayog) saved "
                "about ₹2,000 a month. SAM: workers on organized platform fleets with digital payouts. SOM (about "
                "1.2% of SAM): 4 enterprise platforms and 100,000 enrolled workers sweeping an average ₹800 a month, "
                "i.e. ₹96 Cr of annual deduction volume by year 3."
            ),
        ),
        unit_economics=UnitEconomics(
            cac_inr=500.0,
            ltv_inr=1260.0,
            ltv_cac_ratio=2.5,
            take_rate="~₹25 per active worker/month SaaS fee paid by the employer + ~1.2% spread on payout sweeps",
            payback_months=14.3,
            economics_narrative=(
                "Illustrative planning assumption. CAC of ₹500 per enrolled worker amortizes enterprise sales cycles, "
                "integration work and worker activation incentives. Net monthly contribution is about ₹35 (SaaS fee "
                "plus spread on ~₹800 of monthly sweeps) over a 36-month lifetime, reflecting high gig-worker churn: "
                "LTV = ₹35 x 36 = ₹1,260, LTV:CAC = 2.5x, payback = ₹500 / ₹35 = 14.3 months."
            ),
        ),
        flywheel_integration=(
            "Deductions run at source, before funds reach the bank, so low balances and UPI mandate failures "
            "never interrupt saving. Each settlement reads: 'You completed 14 deliveries today and earned ₹1,120 "
            "(₹25 was automatically saved in your 24K Gold Jar).' Jar becomes the financial backbone of Bharat's "
            "informal economy and a route into Jar Cash micro-lending for vehicle repair emergencies."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Enterprise Payout Sales Cycles & Procurement Inertia",
                risk_category="Operational",
                severity="Medium",
                mitigation_strategy=(
                    "Ship pre-integrated webhook connectors for standard payout gateways (Cashfree, RazorpayX, Darwinbox, "
                    "ZingHR) needing zero engineering from partners, with a 90-day free pilot to show double-digit "
                    "reductions in worker churn."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Gig Worker Income Volatility & Cash Flow Sensitivity",
                risk_category="Financial",
                severity="Medium",
                mitigation_strategy=(
                    "Use percentage-based micro-allocations (e.g., exactly 1.0% of daily earnings) instead of fixed rupee "
                    "deductions, pausing automatically on zero-delivery days, plus a 1-tap 'Skip Today' toggle in the "
                    "partner driver app."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Labor Regulatory Scrutiny on Wage Deductions",
                risk_category="Regulatory",
                severity="Low",
                mitigation_strategy=(
                    "Require explicit, authenticated digital opt-in from every worker, with clear terms that funds stay "
                    "100% liquid and withdrawable at any time, with no employer lock-in or forfeiture."
                ),
            ),
        ],
        primary_kpis=[
            "Enrolled B2B Corporate Enterprise Partners",
            "Monthly Active Gig Savers on Payroll SDK",
            "Average Monthly Savings per Blue-Collar Worker (₹/month)",
            "Enterprise Driver/Rider Retention Uplift (+16% benchmark)",
        ],
    ),
]


# ---------------------------------------------------------------------------
# Definitive Content: Comprehensive Execution Risk Matrix
# ---------------------------------------------------------------------------

PLATFORM_RISK_MATRIX: List[ExecutionRiskItem] = [
    ExecutionRiskItem(
        risk_title="RBI Digital Lending & Co-Lending Regulatory Scrutiny",
        risk_category="Regulatory",
        severity="High",
        mitigation_strategy=(
            "Jar operates strictly as a Lending Service Provider (LSP) with RBI-licensed NBFCs. Funds flow "
            "directly between borrower and lender accounts, within the statutory 5% FLDG cap."
        ),
    ),
    ExecutionRiskItem(
        risk_title="Precious Metal Market Volatility & Collateral Devaluation",
        risk_category="Market",
        severity="High",
        mitigation_strategy=(
            "A conservative 70% LTV ceiling on gold credit, automated margin calls at 78%, and micro-liquidation "
            "via partner APIs at 85% to protect capital."
        ),
    ),
    ExecutionRiskItem(
        risk_title="Jeweller Counterparty Solvency in Leasing Consortiums",
        risk_category="Counterparty",
        severity="High",
        mitigation_strategy=(
            "Lease only to CRISIL AA/A+ rated national jewellers with 110% bank guarantee or 100% cash/bullion "
            "escrow backing, underwritten by Tier-1 credit insurance."
        ),
    ),
    ExecutionRiskItem(
        risk_title="NPCI UPI AutoPay Downtime & Bank Mandate Bounces",
        risk_category="Operational",
        severity="Medium",
        mitigation_strategy=(
            "3-window automated retries, ambient SMS spend fallbacks and multi-gateway routing keep mandates "
            "executing across all sponsor banks."
        ),
    ),
    ExecutionRiskItem(
        risk_title="SEBI Commodity & Digital Silver Regulatory Evolution",
        risk_category="Regulatory",
        severity="Medium",
        mitigation_strategy=(
            "Maintain AMFI Mutual Fund Distributor (MFD) licensing and use SEBI-registered custodial vaults with "
            "hallmarked bars verified by quarterly independent third-party audits."
        ),
    ),
    ExecutionRiskItem(
        risk_title="Enterprise Sales Cycles & B2B Integration Overhead",
        risk_category="Operational",
        severity="Low",
        mitigation_strategy=(
            "Zero-code plug-and-play SDKs and pre-built webhook connectors for major payout gateways (Cashfree, "
            "RazorpayX) let enterprises activate gig worker micro-benefits in under 48 hours."
        ),
    ),
]


GLOBAL_FLYWHEEL_NARRATIVE: str = (
    "Jar's 5 growth verticals form a self-reinforcing flywheel powered by two engines: "
    "Frictionless Habitual Automation and Unshakeable Sovereign Trust.\n\n"
    "1. Top of Funnel: Daily UPI round-ups and B2B gig-worker payroll sweeps (Jar for Work) bring hundreds of "
    "thousands of new micro-deposits a day at low acquisition cost.\n"
    "2. Asset Accumulation: Gold and Silver splits (Jar Multi-Asset) and child jars (Jar Family Vaults) grow "
    "loose change into multi-gram portfolios.\n"
    "3. High-Value Monetization: Vault collateral unlocks instant credit (Jar Cash) and gold leasing yield "
    "(Jar Earn), earning interest margins and fees without users liquidating their wealth.\n"
    "4. Retention Lock-In: Daily compounding gold dividends (Jar Earn) and generational savings (Jar Family "
    "Vaults) lengthen customer lifetimes, a durable moat against banks and discount brokerages."
)


# Global strategy report instance
GROWTH_STRATEGY_REPORT = GrowthStrategyReport(
    verticals=GROWTH_VERTICALS,
    execution_risk_matrix=PLATFORM_RISK_MATRIX,
    global_flywheel_narrative=GLOBAL_FLYWHEEL_NARRATIVE,
    strategy_version="2026-Q1",
    author="Jegadeesh D",
)


# ---------------------------------------------------------------------------
# Accessor Functions
# ---------------------------------------------------------------------------

def get_growth_verticals() -> List[GrowthVerticalItem]:
    """Returns the list of 5 documented strategic growth verticals."""
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


def get_market_sizing_summary() -> Dict[str, Any]:
    """Returns aggregated market sizing figures across all 5 verticals."""
    report = get_growth_strategy_report()
    return {
        "total_tam_inr_cr": report.total_tam_cr,
        "total_sam_inr_cr": report.total_sam_cr,
        "total_som_inr_cr": report.total_som_cr,
        "total_tam_usd_b": round(report.total_tam_cr / 83.33 / 100, 2),
        "total_sam_usd_b": round(report.total_sam_cr / 83.33 / 100, 2),
        "total_som_usd_b": round(report.total_som_cr / 83.33 / 100, 2),
        "vertical_breakdown": [
            {
                "id": v.id,
                "name": v.name,
                "tam": v.market_sizing.tam,
                "sam": v.market_sizing.sam,
                "som": v.market_sizing.som,
            }
            for v in report.verticals
        ],
    }


def get_unit_economics_summary() -> Dict[str, Any]:
    """Returns aggregated unit economics metrics across all 5 verticals."""
    verticals = get_growth_verticals()
    avg_cac = round(sum(v.unit_economics.cac_inr for v in verticals) / len(verticals), 2)
    avg_ltv = round(sum(v.unit_economics.ltv_inr for v in verticals) / len(verticals), 2)
    avg_ratio = round(avg_ltv / avg_cac, 2) if avg_cac > 0 else 0.0
    avg_payback = round(
        sum(v.unit_economics.payback_months for v in verticals) / len(verticals), 2
    )

    return {
        "average_cac_inr": avg_cac,
        "average_ltv_inr": avg_ltv,
        "blended_ltv_cac_ratio": avg_ratio,
        "average_payback_months": avg_payback,
        "vertical_unit_economics": [
            {
                "id": v.id,
                "name": v.name,
                "cac_inr": v.unit_economics.cac_inr,
                "ltv_inr": v.unit_economics.ltv_inr,
                "ltv_cac_ratio": v.unit_economics.ltv_cac_ratio,
                "take_rate": v.unit_economics.take_rate,
                "payback_months": v.unit_economics.payback_months,
            }
            for v in verticals
        ],
    }
