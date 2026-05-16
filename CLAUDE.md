# Retirement Suite — Master Onboarding

## What This Package Is

This is a reusable framework for retirement planning built around three interlocking tools: a Roth conversion optimizer, a property audit engine, and a city research framework. Every tool is a template — the user must supply their own financial data, personal preferences, and target locations. Nothing here is ready to run as-is. Reading `NEW_USER_SETUP.md` and completing the intake conversation first is mandatory.

---

## Read This First

**Before modifying any file: read `NEW_USER_SETUP.md` and complete the intake conversation with the user.** That document walks through five phases of questions that establish the user's financial profile. The answers from that conversation are used to populate the Roth calculator, fill the Location Constants, and set up the city research framework. Starting tool setup before the intake is complete will produce inconsistent results across tools.

---

## Tool 1: Roth Conversion Calculator

**What it does:** Year-by-year projection of after-tax wealth across multiple Roth conversion strategies. A grid-search optimizer finds the conversion policy (marginal bracket target, IRMAA tier cap, taxable floor, start/stop ages) that maximizes real terminal wealth at a user-defined horizon age. An interactive Streamlit sidebar allows real-time what-if analysis.

**What it requires from the user:**
- Current ages (self and spouse)
- Account balances by type: traditional 401k/TSP/IRA, Roth 401k/TSP, Roth IRA, taxable brokerage, and cost basis in taxable
- Income streams: pension amount, Social Security PIA estimates, claiming ages
- Employment timeline: current income, salary trajectory, retirement age, annual savings amounts
- Spending: annual non-housing spending (employment phase and retirement phase)
- Housing: purchase price, down payment, mortgage rate, location-specific rates (from Location Constants)
- State of residence — see State Tax Warning below

**Run command:** `streamlit run roth_calculator_template.py` from inside the `roth-calculator/` folder.

**Key architectural note:** Public-law tax tables (federal brackets, IRMAA tiers, RMD Uniform Lifetime Table, SS taxability thresholds) are already populated and should not be changed. Only the `Inputs` dataclass defaults and the matching sidebar widget defaults need personal data.

**See:** `roth-calculator/README.md` for field-by-field setup guide.

---

## Tool 2: Individual Home / Property Audit

**What it does:** Runs a 30-year terminal wealth analysis on a specific property purchase. The financial engine (TIEI → Tier 2 income → surplus stream → terminal wealth → zone classification) is fixed methodology — it produces a standardized Compounding / Balanced / Lifestyle / Hard Failure verdict for any property, in any city, for any user profile.

**What it requires from the user:**
- Starting liquid capital (the amount available to invest minus what goes into the home)
- Monthly Tier 1 income (pension, annuity, or other fixed income at retirement)
- Baseline monthly expense budget (non-housing spending)
- Target city — the Location Constants file for that city must be completed before any audit runs
- Individual property details: purchase price, property type, HOA, applicable local rates

**Workflow:** When the user says "Audit [address]": (1) read `Relocation_Audit_Engine_v2.2.txt`, (2) read the city's completed constants file, (3) read `Example_Audit_Synthetic.md` for format reference, (4) execute the audit, (5) save as `[yymmdd] [City] [Address].md` in an `Audits/` subfolder, (6) update `Financial_Summary.csv` with the 12 summary fields.

**Key rule:** Do not model tax abatements. Treat all properties as fully taxable. Apply homestead exemption only for owner-occupants per the city's rules.

**See:** `home-audit/README.md` for the full workflow and all 12 CSV fields.

---

## Tool 3: City Research Framework

**What it does:** Maintains two HTML research documents (weather and politics) that cover candidate retirement cities across 18 standardized dimensions. Each city gets its own tab. A Python compliance scanner enforces an Isolation Rule: within sections 1–9 (weather) or 1–8 (politics), all claims must stand alone using only external references — no cross-city comparisons are allowed. Section 10 of the weather file is the only place where target cities may be compared directly.

**What it requires from the user:**
- List of cities to research
- Four "baseline" cities — places personally meaningful to the user that serve as comparison anchors in weather Section 10 (e.g., former home cities or places the user knows well)
- Research sources and level of depth desired
- Any personal filters to note (health conditions affecting climate sensitivity, legal residency requirements, cultural priorities)

**Key rule:** The Isolation Rule is non-negotiable. Run `compliance_scanner.py` before delivering any HTML update. Do not present or commit a version that does not produce a CLEAN result.

**See:** `city-research/README.md` for workflow, section structure, scanner usage, and the SAD Days Index formula.

---

## Shared Financial Assumptions

> **These three inputs must be consistent across all three tools:**
> - Starting liquid capital (or capital remaining after home purchase)
> - Primary fixed income at retirement (pension / Tier 1)
> - Baseline monthly non-housing spending

If the Roth calculator uses a different spending figure than the home audit engine, the projections will diverge and produce contradictory conclusions. Establish these numbers during the intake conversation and carry them consistently.

---

## State Tax Warning

The Roth conversion calculator has **Pennsylvania-specific tax logic** embedded in the simulation engine, not just the defaults. Every PA-specific line is marked with a `# PA-SPECIFIC:` comment. If the user is **not** a Pennsylvania resident, search for all `# PA-SPECIFIC:` comments and adjust the logic for the user's actual state. Key PA rules that may differ:

- PA flat income tax rate: 3.07%
- PA fully exempts military pension, SS, and IRA/401k withdrawals after age 59½ from state income tax
- PA taxes long-term capital gains at the same flat rate as ordinary income (no preferential rate)

Non-PA states may tax pensions, have graduated income tax rates, or have no income tax at all. Incorrect state tax logic will corrupt every year's calculation in the simulation.
