# New User Setup — Intake Guide

This document is written for the implementing Claude instance. Run through these five phases in a single intake conversation with the user **before touching any tool file**. Record the answers — they drive every tool in the suite.

Do not begin modifying defaults, filling in constants, or creating any audit files until the intake conversation is complete. The answers from this conversation are the single source of truth that keeps all three tools consistent.

---

## Phase 1 — Core Financial Profile (all three tools)

These answers feed every tool. Get them first.

**Q1. Starting liquid investable net worth:**
Ask for the dollar amount they could deploy toward housing and investments at retirement. Clarify: this excludes existing home equity (if any), vehicles, and illiquid assets. This is the "Starting Liquid Principal" used in the home audit engine and the account balance inputs for the Roth calculator.

**Q2. Defined benefit pension or equivalent fixed income:**
- Do they have a pension, annuity, or other guaranteed income stream?
- If yes: monthly gross amount in today's dollars at retirement start age, COLA-linked (CPI-adjusted) or flat nominal, and at what age it begins.
- This is Tier 1 income in the audit engine and the `pension` field in the Roth calculator.

**Q3. Social Security estimates:**
- Expected benefit at full retirement age (FRA) for themselves.
- If married or filing jointly, spouse's expected benefit at FRA.
- Planned claiming ages for each.
- Source: Social Security statement at ssa.gov is the most reliable input. Estimated amounts from memory are acceptable but note the uncertainty.

**Q4. Baseline monthly spending in retirement (non-housing):**
- Ask for today's dollars, excluding housing (rent/mortgage, property tax, HOA, maintenance).
- Include: food, utilities, healthcare supplements, transportation, travel, personal care.
- This is the Baseline Monthly Expense Budget (BMEB) in the audit engine and `spending_retirement` in the Roth calculator.

**Q5. Target home purchase price range:**
- Approximate range they are considering.
- This determines whether the audit engine will produce Compounding, Balanced, Lifestyle, or Hard Failure verdicts at various down payment levels.
- Note whether they are thinking condo, townhouse, single-family, or co-op.

---

## Phase 2 — Roth Conversion Calculator Specifics (Tool 1)

**Q6. Ages:**
- Current age (primary person) and spouse's age (enter 0 if single filing).
- Planned retirement age (when W-2 income stops and pension begins).
- Desired "horizon age" — the final year of the projection (common choices: 90, 95, 100).
- RMD start age: 73 if born 1951–1959; 75 if born 1960 or later (SECURE 2.0).

**Q7. Account balances today (in today's dollars):**
- Traditional 401k / TSP / IRA balance
- Roth 401k / TSP balance
- Roth IRA balance
- Taxable brokerage account balance
- Cost basis in the taxable account (ask for their best estimate; check recent statements)

**Q8. Employment phase (if currently working):**
- Current gross monthly income
- Any expected salary changes before retirement (promotions, step increases, merit raises) — at what age and what new monthly amount
- Annual savings rate: how much to tax-advantaged accounts per year, and how much to taxable per year
- Does their employer offer traditional pre-tax and Roth contributions? What is their current split?
- Annual raise expectation (percent)

**Q9. State of residence:**
This is critical. The calculator has Pennsylvania tax logic built in. Ask:
- What state will they live in during retirement (or where they live now if not moving)?
- Does that state tax pension income? IRA/401k withdrawals? Social Security? Long-term capital gains?
- If not Pennsylvania: flag that `# PA-SPECIFIC:` lines in `roth_calculator_template.py` will need adjustment.

**Q10. TCJA bracket extension expectation:**
- Do they expect the Tax Cuts and Jobs Act brackets to be extended past their current 2025 sunset? (Default: no extension modeled.) This is a judgment call — note whichever they prefer.

---

## Phase 3 — Home Audit Specifics (Tool 2)

**Q11. Target city or cities for property purchase:**
- Which city (or cities) are they actively considering for their retirement home?
- For each city, the implementing Claude must fill in `Location_Constants_Template.txt` before running any audits. The template lists exactly what rates are needed.

**Q12. Healthcare:**
- Do they have Tricare, a retiree health benefit, or equivalent coverage that removes healthcare from their monthly expense budget?
- The audit engine's BMEB defaults to excluding healthcare. Adjust if the user pays for their own health insurance in retirement.

**Q13. Vehicle assumption:**
- The audit engine assumes $0/month vehicle cost if Walk Score ≥ 90 AND Transit Score ≥ 70 are both confirmed for the specific address. If the target city and neighborhoods are less walkable, the user should budget a monthly vehicle cost to add to BMEB.

---

## Phase 4 — City Research Framework (Tool 3)

**Q14. Candidate cities:**
- Full list of cities to research (may overlap with Phase 3 cities).
- Any cities already eliminated and why — helps establish the research filters.

**Q15. Four baseline cities:**
- The weather research uses four "baseline cities" in Section 10 only (the cross-city comparison section). These should be cities the user knows well — former homes, family locations, or places with personally meaningful climate reference points.
- Examples: "I grew up in Minneapolis," "I lived in Phoenix for 10 years," etc.
- These are the only four cities that may be referenced by name in other tabs' Section 10 content.

**Q16. Hard dealbreakers:**
- Are there absolute disqualifiers? Examples:
  - "No city below 40°N latitude" (heat)
  - "Must be a blue state for political stability"
  - "Must allow EU residency visa pathway"
  - Walkability minimums, water body requirements, etc.
- Note these in the project's CLAUDE.md as explicit research filters.

**Q17. Personal research filters to document:**
- Health conditions that affect climate sensitivity (e.g., heat intolerance, respiratory conditions affecting air quality weighting, seasonal affective disorder history)
- Legal and visa requirements (if considering international cities)
- Cultural priorities (LGBTQ+ safety, language, community type)
- These should be recorded in the project's own CLAUDE.md so they are applied consistently across all city research.

---

## Phase 5 — Synthesis (What to Do After the Intake)

Once the intake conversation is complete, take these steps in order:

1. **Populate the Roth calculator:** Open `roth-calculator/roth_calculator_template.py` and replace the `# USER:` defaults in the `Inputs` dataclass with the user's actual numbers from Q6–Q10. Apply the same values to the matching sidebar widget defaults (~line 672+). If the user is not in Pennsylvania, identify and update all `# PA-SPECIFIC:` lines.

2. **Fill Location Constants:** For each target city from Q11, create `[CityName]_Constants.txt` in `home-audit/` by copying `Location_Constants_Template.txt` and researching each `[FILL IN]` field. Confirm every rate from a primary source (state/city revenue department, Zillow, Numbeo). Do not run property audits without completed constants.

3. **Update the HTML files:** In both `city-research/retirement_weather_template.html` and `retirement_politics_template.html`, update the header text to remove the word "Template" if desired, and set the four baseline cities in the `baselines-box` div of the weather file. Update `compliance_scanner.py` with the `BASELINE_CITIES` list from Q15.

4. **Set up the project CLAUDE.md:** Create a `CLAUDE.md` inside the user's own project directory (distinct from this master file) documenting the personal filters from Q17, their confirmed baseline cities, and any hard dealbreakers from Q16. This becomes the project-level memory that persists across all future city research sessions.

5. **Test the Roth calculator:** Run `streamlit run roth_calculator_template.py` and confirm the sidebar shows the user's actual numbers, the simulation runs without errors, and the optimizer produces reasonable output.

6. **Run the compliance scanner:** From `city-research/`, run `python compliance_scanner.py` against both HTML template files. Confirm CLEAN output before adding any real city content.
