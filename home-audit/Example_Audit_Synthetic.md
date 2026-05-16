> **SYNTHETIC EXAMPLE — for format reference only.**
> All values, rates, and addresses in this document are fabricated.
> Use the format and table structure here as a template; the financial
> engine (`Relocation_Audit_Engine_v2.2.txt`) defines all calculations.
> Replace every value with real data from your completed Location Constants file.

---

## CITY AUDIT: LAKEWOOD CITY, [STATE] — 1400 EXAMPLE BOULEVARD, UNIT 2B

**PURCHASE ASSUMPTIONS:**

- Property Type: Condominium, existing construction (mid-rise, 45 units)
- Built: 2008 | ~1,100 sq ft | HOA: $420/month
- Purchase Price: $450,000
- Financing: 20% down, conventional 30-year fixed at [Mortgage Rate]%
- Loan Amount: $360,000

---

**TOTAL INITIAL EQUITY INVESTMENT (TIEI):**

| Component | Calculation | Amount |
|-----------|------------|--------|
| Down Payment | $450,000 × 20% | $90,000 |
| Statutory Leakage | $450,000 × [Transfer Tax Rate]% | $[X] |
| Service Leakage | $450,000 × 1.5% | $6,750 |
| Acquisition Condition Allowance | $450,000 × 2.0% | $9,000 |
| **TIEI Total** | | **$[X]** |

---

**TIER 2 CALCULATION AUDIT:**

- Starting Liquid Principal: $[USER'S STARTING CAPITAL]
- Less TIEI: -$[TIEI Total]
- Capital Available for T2: **$[Starting Capital − TIEI]**
- T2I Annual: $[Capital] × 4% = **$[X]**
- T2I Monthly: **$[X]**
- Tax-Deferred Portion (40%): $[X] (no tax)
- Taxable Portion (60% LTCG): $[X] × [State LTCG Rate]% = $[X] annual state tax

---

**COMBINED MONTHLY INCOME (T=0):**

| Component | Amount |
|-----------|--------|
| Tier 1 (Pension / Fixed Income) | $[USER'S T1 MONTHLY] |
| Tier 2 (Portfolio Withdrawal) | $[T2I Monthly] |
| **Total** | **$[T1 + T2I]** |

---

**MONTHLY HOUSING COST ITEMIZATION:**

| Component | Calculation | Monthly |
|-----------|------------|---------|
| **P&I** | $360,000 @ [Rate]%, 360 months | $[X] |
| Net Property Tax | ($450,000 − [Homestead Exemption]) × [Property Tax Rate]% ÷ 12 | $[X] |
| HOA | Confirmed | $420 |
| Maintenance | MAX($450,000 × 0.3%, $450,000 × 1.75% − $5,040) | $[X] |
| **Total (excl. P&I)** | | **$[X]** |

*Note: homestead exemption applied per [City] Constants — confirm applicability for condo ownership in this jurisdiction.*

---

**CITY-ADJUSTED MONTHLY EXPENSES (CAME):**

- Baseline Monthly Expense Budget: $[USER'S BMEB]
- Numbeo Index: [From Location Constants — e.g., 103.4]
- CAME: $[BMEB] × [Numbeo/100] = **$[X]**

---

**FISCAL DRAG (Annual, T=0):**

| Item | Calculation | Annual |
|------|-----------|--------|
| State Income Tax (T1 Pension) | [Exempt per [State] statute / or T1 × [Rate]%] | $[X] |
| State Income Tax (T2 LTCG, 60%) | $[T2I × 60%] × [LTCG Rate]% | $[X] |
| Local Wage/Income Tax | [Exempt / T1 × [Rate]% / etc.] | $[X] |
| Sales Tax | $[CAME] × 12 × [Combined Sales Tax Rate]% | $[X] |
| **Total Annual Fiscal Drag** | | **$[X]** |
| **Monthly Fiscal Drag** | $[Annual] ÷ 12 | **$[X]** |

---

**MONTHLY SURPLUS CALCULATION:**

| Line | Amount |
|------|--------|
| Combined Monthly Income | $[T1 + T2I] |
| Less: CAME | -$[CAME] |
| Less: Housing (excl. P&I) | -$[Housing excl P&I] |
| Less: Monthly Fiscal Drag | -$[Fiscal Drag / 12] |
| **GROWING_MONTHLY_0** | **$[X]** |
| Less: Monthly P&I | -$[P&I] |
| **Year 0 Monthly Surplus/Deficit** | **$[X]** |

---

**30-YEAR TERMINAL WEALTH ANALYSIS:**

| Component | Calculation | Amount |
|-----------|------------|--------|
| Home Equity @ T30 | $450,000 × (1 + [Appreciation Rate])^30 | $[X] |
| Portfolio @ T30 | $[Capital Available for T2] × (1.03)^30 | $[X] |
| FV of Surplus Stream | (see below) | $[X] |
| **Terminal Nominal Wealth** | | **$[X]** |

**FV Surplus Calculation Breakdown:**

- GROWING_ANNUAL_0: $[GROWING_MONTHLY_0 × 12]
- FIXED_ANNUAL: $[P&I × 12]
- FV Growing (CPI-growing surplus stream at 7%): $[X]
- FV Fixed (level P&I at 7%): $[X]
- **Net FV_SURPLUS: $[X]**

---

**WEALTH TARGETS & DELTAS:**

| Metric | Nominal | Real (T0 $) |
|--------|---------|------------|
| **ATV Target** | $[Starting Capital × 1.03^30] | $[Starting Capital] |
| **Terminal Wealth** | $[X] | $[X] |
| **Wealth Delta** | $[Terminal − ATV] | $[Real Delta] |
| **Wealth Delta Index** | [Delta / Annual Combined Income]x annual income | — |

---

**RESIDENCY ZONE: [Compounding / Balanced / Lifestyle / Hard Failure]**

| Buffer Metric | Value | Assessment |
|---------------|-------|------------|
| **Year 0 Monthly Surplus** | $[X] | [Positive — modest buffer / Negative — deficit] |
| **Expense Buffer Ratio** | [X]% | [Comfortable / Tight / Inverted] |
| **Year 15 Buffer** | [X]% | [Positive / Still recovering] |

**Zone Rationale:** [One paragraph explaining the zone assignment. Reference the
specific numbers that drove it — surplus amount, terminal wealth vs. ATV, and
which financial lever is the key sensitivity.]

**Cashflow-Neutral Down Payment:**

| Metric | Value |
|---|---|
| Required Down Payment | [X]% of purchase price |
| Down Payment $ | $[X] |
| TIEI at this DP | $[X] |
| % of Liquid Wealth Consumed (TIEI basis) | [X]% |
| % of Liquid Wealth Consumed (DP only basis) | [X]% |

*[Or: "Already cashflow-neutral or positive at 20% default — metric N/A." / "No cashflow-neutral down payment exists — carrying costs structurally exceed net income."]*

---

**LIFESTYLE AUDIT:**

**Walkability (Grocery-Specific):**
[3–5 sentences of confirmed fact. Name specific stores and walking distances.]
Status: [2–3 sentence verdict. Bold the leading verdict phrase only for risk findings.]

**Transit Utility:**
[3–5 sentences. Name transit lines, walk time to nearest stop, Walk Score and Transit Score if available. Note whether the $0 vehicle assumption is satisfied (both scores ≥ threshold).]
Status: [verdict]

**Pedestrian Water Access:**
[3–5 sentences. Nearest waterfront/park with water, walking distance.]
Status: [verdict]

**Distance to Entertainment:**
[3–5 sentences. Named cultural venues, restaurants, parks within walking distance.]
Status: [verdict]

**Vertical Burden (Aging-In-Place Implications):**
[3–5 sentences. Elevator access, interior stair count, unit floor, confirm single-floor layout.]
Status: [verdict]

**Lot Size & Outdoor Space:**
[3–5 sentences. Private balcony, common roof deck, shared courtyard. Confirm from floor plan if needed.]
Status: [verdict or "**Data absent.** Confirm at walkthrough."]

**Primary Façade Orientation & Solar Load:**
[3–5 sentences. Cardinal direction of primary windows. Summer solar gain/glare vs. winter passive solar.]
Status: [verdict]

**Block Surface & Access Character:**
[3–5 sentences. Sidewalk material, grade, through-traffic level. Aging-in-place relevance.]
Status: [verdict]

**Property-Specific Envelope Features Beyond Standard:**
[3–5 sentences. Appliances, finishes, mechanicals, builder warranty if new construction.]
Status: [verdict]

**Premium Feature Inventory & Replacement-Cost Exposure:**
[3–5 sentences. Identify high-cost items and their expected replacement windows.]
Status: [verdict]

**Below-Grade Space & Hydrology (Mandatory Diligence Item):**
[3–5 sentences. Basement/below-grade risk, flood zone, building waterproofing.]
Status: [verdict. Bold if risk is material.]

**HOA Scope & Exclusions:**
[3–5 sentences. What HOA covers. What it explicitly excludes. Reserve fund status if available.]
Status: [verdict. Bold reserve adequacy concern if unknown.]

**Building Age & Major Capex Cycle Alignment:**
[3–5 sentences. Built year, major system ages, expected replacement windows within 30-year hold.]
Status: [verdict]

**Parking Inventory:**
[3–5 sentences. Deeded vs. leased space, EV charging, monthly cost if leased.]
Status: [verdict]

**Block-Level Crime:**
[3–5 sentences. Neighborhood crime rate, specific block character, any acute risk vectors.]
Status: [verdict]

**Sanitation & Street-Cleaning:**
[3–5 sentences. HOA vs. owner responsibility for sidewalk/trash. Pest pressure.]
Status: [verdict]

**Nearest Public Green Space:**
[3–5 sentences. Named park, acreage, walking distance, quality.]
Status: [verdict]

**Catchment School:**
[3–5 sentences. Public school catchment — affects resale buyer pool even for retirees with no children.]
Status: [verdict or "**Data absent.** Confirm at phila.gov/schools or local equivalent."]

**Healthcare Proximity:**
[3–5 sentences. Nearest acute care hospital, distance, and whether your coverage (Tricare / Medicare / other) is accepted.]
Status: [verdict]

**Acoustic Exposure (Mandatory Diligence Item):**
[3–5 sentences. Noise sources: traffic, rail, flight path, entertainment district, construction.]
Status: [**Mandatory diligence item.** Specify walk-through times required.]

---

**THE ADVERSARIAL AUDIT: STRUCTURAL RISKS TO 30-YEAR RESIDENCY**

Identify a minimum of three structural risks. For EVERY risk, use this exact four-part structure:

**RISK #1: [RISK NAME]**

*Mechanism:* [How the risk functions — the structural cause.]

*Exposure:* [The specific dollar or lifestyle impact. Be concrete.]

*Hard Failure Condition:* [The specific threshold where the plan collapses.]

*Likelihood:* **[Low / Moderate / High]** One sentence rationale follows.

---

**RISK #2: [RISK NAME]**

*Mechanism:* [...]

*Exposure:* [...]

*Hard Failure Condition:* [...]

*Likelihood:* **[Low / Moderate / High]** [rationale]

---

**RISK #3: [RISK NAME]**

*Mechanism:* [...]

*Exposure:* [...]

*Hard Failure Condition:* [...]

*Likelihood:* **[Low / Moderate / High]** [rationale]

---

*End Audit.*
