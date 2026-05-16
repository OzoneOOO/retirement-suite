# Individual Home Audit — Workflow Guide

## What This Tool Does

Runs a 30-year terminal wealth analysis on a specific property purchase. The financial engine produces a standardized verdict — **Compounding**, **Balanced**, **Lifestyle**, or **Hard Failure** — for any property in any city for any user profile. The verdict answers: given my income, capital, and spending, can I afford to own this home for 30 years without depleting my wealth?

---

## Before You Run Any Audit

**Step zero: complete the Location Constants file for your target city.**

Copy `Location_Constants_Template.txt`, rename it `[CityName]_Constants.txt`, and fill in every `[FILL IN]` field from primary sources. Rates that cannot be confirmed should be flagged with `(E)` for estimated and noted explicitly — the engine will compute mechanically correct results but the confidence flags matter for decision-making.

Do not run any audits without a completed constants file. Every calculation in the engine depends on those rates.

---

## Running an Audit

When the user says **"Audit [address]"**, follow this sequence:

1. **Read** `Relocation_Audit_Engine_v2.2.txt` — this is the financial engine. All formula definitions, calculation logic, and output format requirements are here.
2. **Read** `[CityName]_Constants.txt` — all location-specific rates for the audit.
3. **Read** `Example_Audit_Synthetic.md` — format reference. The output table structure must match this exactly.
4. **Execute** the two-step logic gate:
   - Iteration 1: Establish the City-Specific Capital Profile (TIEI → T2I → Monthly Surplus)
   - Iteration 2: Project 30-Year Terminal Wealth and assign the Residency Zone
5. **Save** the completed audit as `[yymmdd] [City] [Address].md` in an `Audits/` subfolder.
6. **Update** `Financial_Summary.csv` with the 12 summary fields (see below).

---

## Core Financial Inputs (from intake conversation)

These values come from `NEW_USER_SETUP.md` Phase 1 and must be consistent across all audits:

| Input | Description |
|---|---|
| Starting Liquid Principal | Total investable capital available at T=0 |
| Tier 1 Monthly Income | Fixed monthly income (pension, annuity, etc.) in today's dollars |
| Baseline Monthly Expense Budget (BMEB) | Non-housing monthly spending in today's dollars |

**Important:** TIEI is recalculated from scratch for every single audit. Do not carry forward TIEI from a prior audit.

---

## Key Rules

**Tax abatements:** Do not model tax abatements. Treat all properties as fully taxable. The only exception is the homestead exemption for confirmed owner-occupants, per the city's rules.

**Professional maintenance only:** Zero owner labor credit. The maintenance calculation uses market-rate labor: `MAX(PP × 0.003, PP × 0.0175 − Annual HOA)`.

**Vehicle cost:** $0/month vehicle assumption is valid only if Walk Score ≥ 90 AND Transit Score ≥ 70 are both confirmed for the specific address. If either threshold is missed, add an appropriate vehicle cost to BMEB.

**Data Confidence Notices:** When any input is estimated rather than confirmed, flag it explicitly with `(E)` and state the basis for the estimate. Do not silently use estimates as if they were confirmed figures.

**Single-pass execution:** Once Section V (the output) is rendered, stop. Do not re-verify or loop back. A "what-if" scenario is a new, independent T=0 audit.

---

## Financial Summary CSV — 12 Fields

Maintain `Financial_Summary.csv` with one row per audited property and these columns:

| Column | Description |
|---|---|
| Address | Full street address and unit |
| Property Type | Condo / Townhouse / Single-family / Co-op |
| Purchase Price | Dollar amount |
| Zone | Compounding / Balanced / Lifestyle / Hard Failure |
| Combined Monthly Income | T1 + T2I at T=0 |
| GROWING_MONTHLY_0 | Monthly income minus non-P&I housing and fiscal drag |
| Year 0 Monthly Surplus | GROWING_MONTHLY_0 minus P&I |
| Expense Buffer Ratio | Year 0 Surplus / Combined Monthly Income |
| Year 15 Buffer | (GROWING_MONTHLY_15 − FIXED_MONTHLY) / Combined Monthly Income_15 |
| Real Wealth Delta | Terminal Wealth Delta in today's dollars |
| Wealth Delta Index | Wealth Delta / (Combined Monthly Income × 12) |
| Terminal Real Liquidity | Terminal Nominal Wealth / Inflation Factor (real dollars) |

---

## Zone Definitions

**Compounding:** Monthly surplus is strongly positive. Liquid principal compounds aggressively. The home effectively pays for itself while growing wealth.

**Balanced:** Monthly surplus is modestly positive or negative. Terminal Nominal Wealth is well above the Absolute Terminal Value (ATV) target. The plan works but with a thinner margin.

**Lifestyle:** Monthly surplus is negative but Terminal Nominal Wealth is still above ATV. The plan survives but requires drawing down principal to fund the carrying cost — acceptable if the lifestyle value justifies it.

**Hard Failure:** Monthly surplus is structurally negative at all down payment levels AND Terminal Nominal Wealth falls below ATV. Do not proceed with this property without significant price negotiation or a fundamental change to the income/spending profile.

---

## Cashflow-Neutral Down Payment

The engine solves algebraically for the down payment percentage that produces exactly $0 monthly surplus. This is a useful sensitivity metric — it tells you how much capital you'd need to deploy to break even on cash flow. If the neutral down payment exceeds 100% of purchase price (no solution exists), the property is a structural Hard Failure regardless of down payment.

---

## See Also

- `Relocation_Audit_Engine_v2.2.txt` — the complete financial engine specification
- `Location_Constants_Template.txt` — the rates file template
- `Example_Audit_Synthetic.md` — format reference with placeholder values
- `NEW_USER_SETUP.md` (project root) — intake guide for establishing the financial profile
