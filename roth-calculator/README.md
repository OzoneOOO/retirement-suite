# Roth Conversion Optimizer — Setup Guide

## What This Tool Does

Year-by-year projection of after-tax wealth from age N to a user-defined horizon (typically 90–100). A grid-search optimizer evaluates thousands of Roth conversion policies and identifies which marginal bracket target, IRMAA tier cap, taxable account floor, and conversion window maximizes real terminal wealth. An interactive Streamlit sidebar allows manual scenario testing and single-variable sensitivity tracking.

The simulation models: W-2 income with salary steps, defined benefit pension (CPI-linked), Social Security (both spouses, delay-adjusted), Required Minimum Distributions, Roth conversions, taxable account withdrawals with LTCG realization, a home purchase event with full transaction drag and ongoing housing costs, survivor scenarios, and a fixed-point tax solver that correctly handles the circular dependency between capital gains realization and tax payments.

---

## Prerequisites

```
pip install streamlit pandas numpy altair
```

## Run

From this directory:
```
streamlit run roth_calculator_template.py
```

The app opens in your browser. All inputs are controlled via the sidebar.

---

## Setup Steps

**Step 1: Complete the intake conversation** (`NEW_USER_SETUP.md` at the project root).

**Step 2: Populate the `Inputs` dataclass** (~line 155 in the file). Every field marked `# USER:` needs a real value. The sidebar will be pre-populated with these defaults, so getting the dataclass right means the app opens with sensible starting numbers.

**Step 3: If not a Pennsylvania resident**, search for all `# PA-SPECIFIC:` comments and update the state tax logic. Key locations:
- `PA_RATE = 0.0307` (line ~70) — change to your state's income tax rate
- The `pa_tax = PA_RATE * total_ltcg` line in the simulation loop — PA applies its rate to LTCG; many states treat LTCG differently
- If your state taxes pension or IRA withdrawals, you'll need to add state tax on `pension`, `rmd`, and `extra_trad` income as well

**Step 4: Verify the sidebar matches** — after updating the dataclass, check that the sidebar widget defaults (~line 490+) match. The sidebar values override the dataclass at runtime, so both layers need updating.

---

## Field Reference: `Inputs` Dataclass

### Ages
| Field | Description |
|---|---|
| `age1` | Your current age |
| `age2` | Spouse's age (enter 0 if single, but also set `mfj=False`) |
| `rmd_age` | RMD start: 73 if born 1951–1959; 75 if born 1960+ |
| `horizon_age` | Final age of projection (common: 90, 95, 100) |

### Account Balances (today's dollars)
| Field | Description |
|---|---|
| `trad_tsp` | Traditional 401k / TSP / IRA total |
| `roth_tsp` | Roth 401k / TSP total |
| `roth_ira` | Roth IRA total |
| `taxable` | Taxable brokerage total |
| `taxable_basis` | Cost basis in taxable account (check your most recent statement) |

### Income
| Field | Description |
|---|---|
| `pension` | Annual pension / fixed income at retirement in today's dollars, CPI-linked |
| `ss1_pia` | Your Social Security Primary Insurance Amount at FRA (from ssa.gov statement) |
| `ss2_pia` | Spouse SS PIA at FRA (0 if single) |
| `ss1_claim_age` / `ss2_claim_age` | Planned claiming ages (62–70); delay increases benefit ~8%/yr past FRA |

### Employment Phase
| Field | Description |
|---|---|
| `retirement_age` | Age at which W-2 income stops and pension starts |
| `w2_base_monthly_now` | Current gross monthly pay |
| `promotion_age` / `w2_base_monthly_promo` | Age and pay of next promotion (set both = retirement_age to skip) |
| `pay_step_age` / `w2_base_monthly_step` | Age and pay of next step increase (set both = retirement_age to skip) |
| `annual_raise` | Expected annual pay raise rate (e.g., 0.03) |
| `annual_tsp_contribution` | Annual tax-advantaged contribution (check current IRS limit) |
| `tsp_contribution_roth_frac` | 0.0 = all traditional; 1.0 = all Roth |
| `annual_taxable_contribution_pre/post_promo` | Annual taxable investment savings before/after promotion |

### Spending
| Field | Description |
|---|---|
| `spending_employment` | Annual non-housing spending while working (today's $) |
| `spending_retirement` | Annual non-housing spending in retirement (today's $; housing modeled separately) |

### Housing
| Field | Description |
|---|---|
| `home_purchase_price` | Purchase price in today's dollars (inflated to purchase-year nominal in sim) |
| `home_purchase_age` | Age at purchase (often = retirement_age) |
| `down_payment_pct` | Down payment fraction (0.20 = 20%) |
| `mortgage_rate` | Expected mortgage rate |
| `home_appreciation_rate` | Expected annual home appreciation |
| `transfer_tax_rate` | Buyer's transfer tax — get from your city's Location Constants file |
| `property_tax_rate` | Local property tax rate — from Location Constants |
| `homestead_exemption` | Dollar reduction to assessed value for owner-occupants (0 if not applicable) |
| `hoa_monthly_t0` | Monthly HOA in today's dollars (0 if no HOA) |

---

## What the Optimizer Output Means

**Fill to marginal (retirement):** The optimizer converts from traditional accounts into Roth each year until the next dollar of ordinary income would cross this marginal rate. A value of 0.24 means "fill the 22% bracket completely and stop before entering the 24% bracket."

**IRMAA tier cap:** Limits conversions to keep MAGI below a specified Medicare premium surcharge tier. Tier 0 = no IRMAA; Tier 2 = the second surcharge tier; Tier 5 = no cap. IRMAA applies from age 65 (with a 2-year MAGI lookback — simplified to current-year in this model).

**Taxable floor:** The optimizer keeps at least this much in the taxable account and switches spending to traditional withdrawals once taxable falls below this threshold. Useful if you want a cash buffer.

**Real after-tax wealth at horizon:** The terminal value of all accounts at the horizon age, adjusted for inflation and applying a simple after-tax discount to traditional balances (flat 22% terminal rate assumed). This is the optimizer's objective function.

---

## State Tax Note

The `pa_tax` column in the ledger shows state income tax on capital gains. If you are not a Pennsylvania resident, this column will show an incorrect value until you update the `# PA-SPECIFIC:` lines. The federal tax calculations are unaffected.
