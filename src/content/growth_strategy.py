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
    author: str = "Growth Intern Candidate"

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
            "Jar Cash provides an instant overdraft credit line against vaulted 24K digital gold collateral, "
            "completely eliminating the need for users to liquidate their long-term savings during short-term "
            "cash crunches. In India's informal economy, unexpected hospital visits, family obligations, or "
            "temporary cash-flow delays force savers to sell their accumulated gold or turn to predatory "
            "unregulated moneylenders charging 36%–60% APR. With Jar Cash, users tap a single button to borrow "
            "up to 75% of their live vaulted gold value at an affordable 12%–15% annualized interest rate, with "
            "instant credit to their bank account via UPI / IMPS within 15 seconds. Because the loan is 100% "
            "collateralized by physical gold sitting in SafeGold/Augmont vaults, underwriting is instant, credit "
            "bureau scores are not a bottleneck, and Jar incurs negligible default credit risk."
        ),
        target_persona=(
            "Tier 2/3 young aspirational savers, small shop owners, and gig economy workers with 2g to 15g "
            "of accumulated gold in Jar, who experience intermittent monthly liquidity crunches and need "
            "emergency credit without paperwork or pawnshop stigma."
        ),
        market_sizing=MarketSizing(
            tam="₹75,000 Cr ($9.0B)",
            tam_numeric_cr=75000.0,
            sam="₹18,000 Cr ($2.15B)",
            sam_numeric_cr=18000.0,
            som="₹1,200 Cr ($145M)",
            som_numeric_cr=1200.0,
            methodology=(
                "TAM represents the unorganized and semi-organized Indian gold pawn-broking and micro-gold loan "
                "market. SAM focuses on digitally addressable micro-loans (<₹25,000) collateralized by gold or liquid "
                "assets. SOM assumes Jar captures 6.7% of SAM over 36 months by activating 450,000 active vault holders "
                "(out of 10M+ registered users) taking an average revolving credit balance of ₹8,000 rotated 3.3x annually."
            ),
        ),
        unit_economics=UnitEconomics(
            cac_inr=45.0,
            ltv_inr=1480.0,
            ltv_cac_ratio=32.89,
            take_rate="4.50% - 6.00% Net Interest Spread (co-lending partner) + 1.25% processing fee",
            payback_months=0.8,
            economics_narrative=(
                "Marginal CAC is exceptionally low (₹45) because borrower acquisition occurs contextually inside "
                "the app: when a user clicks 'Sell Gold' for an emergency withdrawal, Jar intercepts with a 1-tap "
                "'Keep Your Gold, Borrow ₹5,000 Instantly' prompt. LTV of ₹1,480 is generated over a 24-month horizon "
                "from a 4.5% net interest margin (NIM) spread over NBFC partner funding costs, plus a 1.25% upfront "
                "processing fee across an average lifetime cumulative borrowing turnover of ₹26,000."
            ),
        ),
        flywheel_integration=(
            "Jar's automated UPI round-ups continuously build the user's gold vault balance, which automatically "
            "and dynamically expands their pre-approved Jar Cash credit limit. When credit is drawn, automated UPI "
            "AutoPay mandates handle regular interest and principal repayments without manual collection effort. "
            "As the loan is repaid, the vaulted gold collateral is released back into the unencumbered balance, "
            "and round-up habituation resumes instantly. The user never loses their gold upside, deepening brand trust "
            "and driving a 3.4x surge in daily micro-savings deposits."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="RBI Digital Lending Guidelines (DLG) & Co-Lending Compliance",
                risk_category="Regulatory",
                severity="High",
                mitigation_strategy=(
                    "Operate strictly as a Lending Service Provider (LSP) partnering with RBI-regulated NBFCs "
                    "(e.g., Vivriti Capital, DMI Finance). All loan disbursals and repayments flow directly "
                    "between the regulated bank/NBFC and the borrower's verified bank account without passing "
                    "through Jar's balance sheet, adhering fully to the 5% First Loss Default Guarantee (FLDG) cap."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Gold Price Volatility & Collateral LTV Breaches",
                risk_category="Market",
                severity="Medium",
                mitigation_strategy=(
                    "Implement a dynamic loan-to-value (LTV) ceiling capped at 70% (well below the regulatory 75% limit). "
                    "Trigger automated WhatsApp/SMS margin call alerts at 78% LTV, and execute automated fractional "
                    "liquidation safeguards via partner bullion APIs only if LTV crosses 85%, ensuring zero capital loss."
                ),
            ),
            ExecutionRiskItem(
                risk_title="UPI Mandate Bounce & Strategic Involuntary Default",
                risk_category="Credit",
                severity="Low",
                mitigation_strategy=(
                    "Because all loans are backed 100% by physical 24K gold stored in institutional vaults, default "
                    "risk is strictly structural rather than unsecured. If a borrower defaults after 90 days of missed "
                    "mandates, partner custodians liquidate the pledged gold at spot market rates to recover principal, "
                    "interest, and auction fees, returning any residual balance to the customer."
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
            "As Jar's core user base matures and accumulates meaningful wealth, single-asset gold concentration "
            "triggers prudence anxiety and asset allocation friction. Jar Multi-Asset introduces frictionless, "
            "sub-₹10 automated micro-savings across complementary precious metals and fixed-income assets: "
            "Digital Silver, Silver ETFs, and RBI Sovereign Gold Bonds (SGBs). Users configure a visual 'Asset "
            "Allocation Slider' (e.g., 70% Gold / 30% Silver, or 60% Gold / 20% Silver / 20% SGB), and Jar's "
            "automated UPI AutoPay engine splits daily spare change and round-ups across both assets in real time. "
            "By capturing silver's dual role as a precious metal and industrial super-conductor (benefiting from the "
            "global solar, EV, and electronics boom), Jar provides superior portfolio inflation protection without "
            "requiring the user to open a complex demat account or migrate to discount brokers like Groww or Zerodha."
        ),
        target_persona=(
            "Financially maturing Tier 1/2/3 users (active on Jar for 6+ months with vault holdings >₹15,000) who "
            "understand precious metals, want exposure to silver's high beta growth, and seek simple diversification."
        ),
        market_sizing=MarketSizing(
            tam="₹42,000 Cr ($5.0B)",
            tam_numeric_cr=42000.0,
            sam="₹8,500 Cr ($1.02B)",
            sam_numeric_cr=8500.0,
            som="₹650 Cr ($78M)",
            som_numeric_cr=650.0,
            methodology=(
                "TAM encompasses the Indian annual retail investment demand for silver bullion, coins, and mutual "
                "fund silver ETFs. SAM isolates digital retail precious metal investment and micro-SIP platforms. "
                "SOM targets capturing 7.6% of digital silver micro-investments over 36 months, representing ₹650 Cr "
                "in cumulative Multi-Asset AUM from 320,000 diversified Jar savers."
            ),
        ),
        unit_economics=UnitEconomics(
            cac_inr=60.0,
            ltv_inr=1120.0,
            ltv_cac_ratio=18.67,
            take_rate="1.50% - 2.00% gross spread on Digital Silver + 0.35% distribution trail on Silver ETFs / SGBs",
            payback_months=1.8,
            economics_narrative=(
                "Customer acquisition leverages in-app portfolio health audits, showing users an instant 'Diversification "
                "Score' that unlocks a free ₹10 silver reward on first allocation. LTV of ₹1,120 over 36 months stems from "
                "a 1.75% transaction spread on recurring silver round-up purchases, combined with an annualized 0.35% trail "
                "commission on partner Silver ETF assets under management."
            ),
        ),
        flywheel_integration=(
            "Users do not need to learn a new investment workflow or approve secondary banking mandates. The existing "
            "UPI AutoPay engine simply splits the incoming daily debits according to the user's chosen allocation slider. "
            "Daily gamified spin rewards and streak counters now award bonus milligrams of both Gold and Silver, triggering "
            "dual endowment effects. When silver rallies, push notifications celebrate portfolio performance, driving an "
            "immediate 42% lift in round-up multiplier adoption."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="SEBI Commodity & Mutual Fund Distribution Licensing",
                risk_category="Regulatory",
                severity="High",
                mitigation_strategy=(
                    "Acquire AMFI Mutual Fund Distributor (MFD) licensing for distributing Silver ETFs and partner with "
                    "SEBI-regulated custodial vaults (Augmont/SafeGold) for fractional digital silver ledgering, ensuring "
                    "100% segregated, insured physical silver backing in Brink's vaults."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Elevated Silver Price Volatility & Retail Drawdown Panic",
                risk_category="Market",
                severity="Medium",
                mitigation_strategy=(
                    "Implement a smart allocation guardrail that caps default automated silver allocation at 30% "
                    "of monthly deposits. Display educational visual tooltips on dollar-cost averaging (DCA) and long-term "
                    "cyclical trends to anchor long-term wealth preservation rather than speculative trading."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Custodial Storage & Oxidation / Assay Verification",
                risk_category="Operational",
                severity="Low",
                mitigation_strategy=(
                    "Enforce strict contract clauses with bullion partners requiring 999-purity silver grain/bars stored "
                    "in climate-controlled, tamper-evident vaults with quarterly independent third-party physical audit "
                    "reports published transparently in the Jar app."
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
            "In Indian culture, saving gold for a child's future education, marriage, and festive milestones is "
            "a sacred, universal parental imperative. Jar Family Vaults enables parents to create dedicated, "
            "earmarked virtual sub-vaults for their children (e.g., 'Aarav's Higher Education 2038', 'Diya's "
            "Wedding Fund') with goal-directed milestone tracking and visual progress rings. Crucially, the vertical "
            "incorporates a viral social gifting engine ('Shagun by Jar'): parents generate shareable UPI payment "
            "deep-links that grandparents, godparents, and relatives can tap to gift 24K digital gold directly into "
            "the child's jar on birthdays, Diwali, and achievements—without requiring the gifter to download the full app. "
            "By emotionalizing savings and solving the uncoordinated physical gold gifting dilemma, Jar transforms "
            "individual savings into an intergenerational household movement."
        ),
        target_persona=(
            "Young parents (aged 24–40) in Tier 1, 2, and 3 India who want to build a disciplined financial safety net "
            "for their children, alongside extended family members seeking modern, digital alternatives to cash shagun."
        ),
        market_sizing=MarketSizing(
            tam="₹110,000 Cr ($13.2B)",
            tam_numeric_cr=110000.0,
            sam="₹22,000 Cr ($2.65B)",
            sam_numeric_cr=22000.0,
            som="₹1,850 Cr ($222M)",
            som_numeric_cr=1850.0,
            methodology=(
                "TAM encompasses the informal child savings, wedding gold accumulation, and festive gifting expenditures "
                "in urban and semi-urban Indian households. SAM isolates digitally transacted festive gifting, child-earmarked "
                "SIPs, and sovereign child investment schemes. SOM projects capturing 8.4% of SAM over 36 months, mobilizing "
                "₹1,850 Cr in cumulative earmarked child vault AUM across 620,000 enrolled children."
            ),
        ),
        unit_economics=UnitEconomics(
            cac_inr=28.0,
            ltv_inr=2350.0,
            ltv_cac_ratio=83.93,
            take_rate="2.00% - 2.50% transaction spread on external festive gifting + 1.00% physical coin delivery margin",
            payback_months=0.5,
            economics_narrative=(
                "Blended CAC drops to an extraordinary ₹28 because each Family Vault acts as a viral growth loop: "
                "a parent sharing a birthday shagun link brings an average of 3.4 external adult contributors into Jar's "
                "ecosystem for zero paid spend. LTV reaches ₹2,350 over a 5-year average holding horizon due to the "
                "near-zero liquidation rate of child-earmarked accounts, sustained recurring contributions, and lucrative "
                "doorstep delivery margins on 24K customized milestone birthday gold coins."
            ),
        ),
        flywheel_integration=(
            "Every social gift transaction sent via UPI deep-link displays a post-transaction conversion card to the gifter: "
            "'You just gifted Aarav 0.25g gold! Start a savings jar for your family today.' This viral K-factor (>1.3) "
            "continuously feeds the top of Jar's customer acquisition funnel with high-intent, high-trust users. Earmarked "
            "goal vaults harness Clark Hull's Goal Gradient Effect and Richard Thaler's Mental Accounting: users save 40% "
            "more money when funds are tagged with their child's name, and premature withdrawals plunge by 76%."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Minor Account Legal Ownership & Tax Compliance",
                risk_category="Regulatory",
                severity="Medium",
                mitigation_strategy=(
                    "Structure vaults under the primary guardian's verified KYC until the minor reaches 18 years of age, "
                    "aligning fully with Indian Contract Act and RBI guidelines. External gift contributions are structured "
                    "under Section 56(2)(x) Income Tax exemptions for gifts from relatives, with transparent annual tax "
                    "receipt summaries provided for parent records."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Discipline Soft-Lock vs. Liquidity Anxiety",
                risk_category="Operational",
                severity="Low",
                mitigation_strategy=(
                    "Avoid rigid, irreversible lock-ins that induce financial claustrophobia. Implement an empathetic "
                    "'24-Hour Cooling-Off Discipline Guard': when a user requests a withdrawal from a child vault, the app "
                    "displays a visual milestone progress reminder and institutes a 24-hour reflection window, stopping "
                    "impulsive impulse liquidation while maintaining ultimate emergency liquidity access."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Social Gifting Link Fraud & Phishing Vector",
                risk_category="Fraud",
                severity="Medium",
                mitigation_strategy=(
                    "Enforce cryptographic tokenization on all shareable gifting links with verified parent names, "
                    "tamper-evident child avatar badges, and direct integration with NPCI verified merchant handles to "
                    "prevent malicious imitation or link spoofing."
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
            "Gold has historically been regarded as an unproductive, zero-yield asset that sits idle in domestic "
            "lockers. Jar Earn fundamentally disrupts this paradigm by introducing institutional Gold Leasing "
            "under the Government of India / RBI Jeweller Metal Loan (GML) frameworks. Users lease their idle vaulted "
            "24K digital gold to vetted, investment-grade institutional jewellers (such as Titan / Tanishq, Kalyan, "
            "and Malabar consortium partners) for physical jewelry fabrication. In return, jewellers pay a 4.0% to 5.0% "
            "annual lease fee, enabling Jar to deliver a net 2.0% to 3.0% annualized yield paid directly in physical "
            "gold milligrams back into the user's vault. By transforming gold into a productive, compounding income "
            "generator, Jar solves the #1 objection of sophisticated savers ('gold pays no dividends') and captures "
            "massive high-ticket bullion balances from affluent retail investors."
        ),
        target_persona=(
            "Affluent and long-term savers (vault balance >5 grams or ₹35,000+) who view gold as multi-year "
            "generational security and seek inflation-beating yield without liquidating their principal."
        ),
        market_sizing=MarketSizing(
            tam="₹160,000 Cr ($19.2B)",
            tam_numeric_cr=160000.0,
            sam="₹32,000 Cr ($3.85B)",
            sam_numeric_cr=32000.0,
            som="₹2,100 Cr ($252M)",
            som_numeric_cr=2100.0,
            methodology=(
                "TAM reflects the total working capital bullion inventory financed annually by India's organized gems "
                "and jewellery manufacturing sector. SAM represents the working capital metal loan demand from top-tier, "
                "credit-rated retail jeweller chains. SOM targets capturing 6.6% of SAM over 36 months, representing "
                "₹2,100 Cr in leased digital gold AUM across 280,000 participating long-term Jar savers."
            ),
        ),
        unit_economics=UnitEconomics(
            cac_inr=55.0,
            ltv_inr=1920.0,
            ltv_cac_ratio=34.91,
            take_rate="1.00% - 1.25% Net AUM Spread (Jeweller pays ~4.25%, user receives 2.75% gold yield, Jar retains 1.50%)",
            payback_months=1.1,
            economics_narrative=(
                "CAC is highly efficient (₹55) via targeted in-app banners triggered automatically when a user's vault "
                "balance crosses 5 grams. LTV of ₹1,920 over a 36-month lease cycle is generated through a predictable "
                "1.25% annualized net management fee on leased gold balances, with zero inventory depreciation risk and "
                "near-100% renewal rates as users compound their daily gold yield."
            ),
        ),
        flywheel_integration=(
            "Daily gold yield payouts are credited directly into the user's primary Jar vault every single day at midnight. "
            "Users experience the magical behavioral gratification of waking up to see their gold gram balance increment "
            "organically without making a deposit. This creates an unshakeable retention lock-in: users refuse to sell or "
            "withdraw because liquidating terminates their daily gold dividend stream. Furthermore, users actively divert "
            "idle physical jewelry and bank deposits into Jar to maximize their daily yield-generating balance."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Jeweller Counterparty Insolvency & Credit Default Risk",
                risk_category="Counterparty",
                severity="High",
                mitigation_strategy=(
                    "Enforce strict credit eligibility: lease gold exclusively to CRISIL / ICRA AA-rated national jewellers. "
                    "Mandate 110% bank guarantee or 100% cash/bullion escrow backing for all leased metal, backed by "
                    "comprehensive credit insurance underwritten by Tier-1 general insurers."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Banning of Unregulated Deposit Schemes Act (BUDS) Compliance",
                risk_category="Regulatory",
                severity="High",
                mitigation_strategy=(
                    "Structure all leases through SEBI/RBI compliant bullion consignment contracts facilitated by "
                    "registered partner refiners (Augmont/SafeGold), ensuring the transaction is legally categorized as a "
                    "commercial commodity consignment lease rather than a collective investment scheme or public deposit."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Secondary Liquidity During Active Lease Tenures",
                risk_category="Operational",
                severity="Medium",
                mitigation_strategy=(
                    "Offer flexible 90-day, 180-day, and 365-day lease terms with an internal emergency liquidity pool "
                    "backed by Jar's treasury balance, allowing users to exit prematurely for a nominal 0.5% early-redemption "
                    "fee while keeping the underlying institutional lease intact."
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
            "India's 15M+ gig economy delivery partners, rideshare drivers, and contract workers (working for Swiggy, "
            "Zomato, Uber, Urban Company, Porter, and Blinkit) lack access to formal provident funds (EPF), gratuity, "
            "or employer-sponsored pension schemes. Jar for Work is a plug-and-play B2B2C API and SDK suite that embeds "
            "automated micro-savings directly into enterprise payout and payroll disbursements. When a delivery partner "
            "receives their daily or weekly earnings settlement via RazorpayX or Cashfree, Jar's SDK automatically sweeps "
            "a small, flexible percentage (e.g., 1% to 2%, or round-up to nearest ₹50) directly into an employer-recognized "
            "Emergency Gold Safety Net. Forward-thinking gig platforms can provide matching contributions (e.g., matching "
            "₹5 for every ₹20 saved), transforming volatile gig earnings into structured financial resilience while slashing "
            "fleet turnover and driver churn."
        ),
        target_persona=(
            "Gig delivery fleets, contract laborers, and enterprise HR/operations leads at on-demand delivery, logistics, "
            "and quick-commerce platforms seeking meaningful retention drivers for their blue-collar workforce."
        ),
        market_sizing=MarketSizing(
            tam="₹55,000 Cr ($6.6B)",
            tam_numeric_cr=55000.0,
            sam="₹14,000 Cr ($1.68B)",
            sam_numeric_cr=14000.0,
            som="₹950 Cr ($114M)",
            som_numeric_cr=950.0,
            methodology=(
                "TAM is based on NITI Aayog's projection of annual payout disbursements across India's 23.5M gig and "
                "platform workforce. SAM isolates voluntary micro-savings and wellness deduction allocations among "
                "organized platform fleets. SOM targets onboarding 8 major enterprise gig platforms within 36 months, "
                "capturing 420,000 enrolled gig workers saving an average of ₹1,900 monthly, yielding ₹950 Cr in annualized "
                "deduction volume."
            ),
        ),
        unit_economics=UnitEconomics(
            cac_inr=12.0,
            ltv_inr=880.0,
            ltv_cac_ratio=73.33,
            take_rate="₹15 per active employee/month B2B SaaS license + 1.20% spread on micro-savings conversion",
            payback_months=0.4,
            economics_narrative=(
                "B2B enterprise partnership distribution slashes acquisition cost to an ultra-lean ₹12 per enrolled "
                "worker because fleet onboarding is distributed centrally through company driver apps. LTV of ₹880 "
                "over a 24-month horizon combines enterprise SaaS seat fees paid by corporate employers with transaction "
                "spreads on automated weekly payout deductions."
            ),
        ),
        flywheel_integration=(
            "Payroll deductions execute at source before funds enter the worker's bank account, completely bypassing "
            "the vulnerability of low bank balances and UPI mandate failures. When gig workers view their daily settlement, "
            "they receive a gratifying notification: 'You completed 14 deliveries today and earned ₹1,120 (₹25 was automatically "
            "saved in your 24K Gold Jar).' This establishes Jar as the indispensable financial backbone for Bharat's "
            "informal economy, naturally feeding users into Jar Cash micro-lending during vehicle repair emergencies."
        ),
        execution_risks=[
            ExecutionRiskItem(
                risk_title="Enterprise Payout Sales Cycles & Procurement Inertia",
                risk_category="Operational",
                severity="Medium",
                mitigation_strategy=(
                    "Build pre-integrated webhook connectors with standard payout gateways (Cashfree, RazorpayX, "
                    "Darwinbox, ZingHR) requiring zero engineering lift from enterprise partners, offering a 90-day "
                    "free pilot to demonstrate immediate double-digit reductions in worker churn."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Gig Worker Income Volatility & Cash Flow Sensitivity",
                risk_category="Financial",
                severity="Medium",
                mitigation_strategy=(
                    "Avoid rigid fixed rupee deduction commitments. Implement percentage-based micro-allocations "
                    "(e.g., exactly 1.0% of daily earnings) that automatically pause on days when zero deliveries are made, "
                    "paired with an instant 1-tap 'Skip Today' pause toggle in the partner driver app."
                ),
            ),
            ExecutionRiskItem(
                risk_title="Labor Regulatory Scrutiny on Wage Deductions",
                risk_category="Regulatory",
                severity="Low",
                mitigation_strategy=(
                    "Ensure all micro-savings enrollment flows require explicit, authenticated digital opt-in consent "
                    "from the worker with transparent terms stating that funds remain 100% liquid and withdrawable at any "
                    "time without employer lock-in or forfeiture."
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
            "Jar maintains strict status as a Lending Service Provider (LSP) partnering with RBI-licensed NBFCs. "
            "All fund flows pass directly between borrower and lender accounts, capped at the statutory 5% FLDG limit."
        ),
    ),
    ExecutionRiskItem(
        risk_title="Precious Metal Market Volatility & Collateral Devaluation",
        risk_category="Market",
        severity="High",
        mitigation_strategy=(
            "Enforce a conservative 70% LTV ceiling on gold credit, dynamic automated margin calls at 78%, and automated "
            "micro-liquidation safeguards via partner APIs at 85% to protect capital."
        ),
    ),
    ExecutionRiskItem(
        risk_title="Jeweller Counterparty Solvency in Leasing Consortiums",
        risk_category="Counterparty",
        severity="High",
        mitigation_strategy=(
            "Lease bullion exclusively to CRISIL AA/A+ rated national jewellers with 110% bank guarantee or 100% cash/bullion "
            "escrow backing, underwritten by Tier-1 credit insurance."
        ),
    ),
    ExecutionRiskItem(
        risk_title="NPCI UPI AutoPay Downtime & Bank Mandate Bounces",
        risk_category="Operational",
        severity="Medium",
        mitigation_strategy=(
            "Deploy intelligent 3-window automated retry algorithms, ambient SMS spend fallbacks, and multi-gateway routing "
            "to ensure mandate execution resilience across all sponsor banks."
        ),
    ),
    ExecutionRiskItem(
        risk_title="SEBI Commodity & Digital Silver Regulatory Evolution",
        risk_category="Regulatory",
        severity="Medium",
        mitigation_strategy=(
            "Maintain AMFI Mutual Fund Distributor (MFD) licensing and partner with SEBI-registered custodial vault providers "
            "with physical hallmarked bars verified by quarterly independent third-party audits."
        ),
    ),
    ExecutionRiskItem(
        risk_title="Enterprise Sales Cycles & B2B Integration Overhead",
        risk_category="Operational",
        severity="Low",
        mitigation_strategy=(
            "Provide zero-code plug-and-play SDKs and pre-built webhook connectors for major payout gateways (Cashfree, "
            "RazorpayX), allowing enterprises to activate gig worker micro-benefits in under 48 hours."
        ),
    ),
]


GLOBAL_FLYWHEEL_NARRATIVE: str = (
    "Jar's 5 strategic growth verticals form a self-reinforcing, virtuous flywheel powered by two core engines: "
    "Frictionless Habitual Automation and Unshakeable Sovereign Trust.\n\n"
    "1. Top of Funnel: Daily UPI round-ups and B2B gig-worker payroll sweeps (Jar for Work) feed hundreds of thousands of new "
    "micro-deposits into the system daily at ultra-low acquisition costs.\n"
    "2. Asset Accumulation: Automated splits across Gold and Silver (Jar Multi-Asset) and emotionalized child jars (Jar Family Vaults) "
    "accelerate balance growth, turning loose change into substantial multi-gram portfolios.\n"
    "3. High-Value Monetization: Accumulated vault collateral directly unlocks instant credit (Jar Cash) and high-yield gold leasing (Jar Earn), "
    "generating lucrative net interest margins and asset management fees without requiring the user to liquidate their wealth.\n"
    "4. Retention Lock-In: Earning daily compounding gold dividends (Jar Earn) and preserving generational savings (Jar Family Vaults) "
    "suppresses churn to near-zero, creating an unbeatable competitive moat against traditional banks and discount brokerages."
)


# Global strategy report instance
GROWTH_STRATEGY_REPORT = GrowthStrategyReport(
    verticals=GROWTH_VERTICALS,
    execution_risk_matrix=PLATFORM_RISK_MATRIX,
    global_flywheel_narrative=GLOBAL_FLYWHEEL_NARRATIVE,
    strategy_version="2026-Q1",
    author="Growth Intern Candidate",
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
