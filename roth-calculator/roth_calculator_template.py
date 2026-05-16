"""Roth conversion optimizer — interactive Streamlit app.

Run: streamlit run roth_calculator_template.py

TEMPLATE: All personal defaults in the Inputs dataclass and sidebar widgets are
illustrative placeholder values. Replace them with your own data before running.
See README.md for field explanations and NEW_USER_SETUP.md for the intake guide.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt


# ---------------------------------------------------------------------------
# Tax tables (2025 MFJ baseline; adjusted forward by inflation in the sim)
# ---------------------------------------------------------------------------

FED_BRACKETS_MFJ = [
    (0,        0.10),
    (23_850,   0.12),
    (96_950,   0.22),
    (206_700,  0.24),
    (394_600,  0.32),
    (501_050,  0.35),
    (751_600,  0.37),
]
FED_BRACKETS_SINGLE = [
    (0,        0.10),
    (11_925,   0.12),
    (48_475,   0.22),
    (103_350,  0.24),
    (197_300,  0.32),
    (250_525,  0.35),
    (626_350,  0.37),
]
STD_DED_MFJ = 30_000
STD_DED_SINGLE = 15_000

LTCG_BRACKETS_MFJ = [(0, 0.0), (96_700, 0.15), (600_050, 0.20)]
LTCG_BRACKETS_SINGLE = [(0, 0.0), (48_350, 0.15), (533_400, 0.20)]

NIIT_THRESHOLD_MFJ = 250_000
NIIT_THRESHOLD_SINGLE = 200_000
NIIT_RATE = 0.038

# IRMAA 2025 — MAGI thresholds (MFJ) and combined Part B + D annual surcharge per person
IRMAA_TIERS_MFJ = [
    (0,        0),
    (212_000,  1_055),
    (266_000,  2_640),
    (334_000,  4_226),
    (400_000,  5_811),
    (750_000,  6_343),
]
IRMAA_TIERS_SINGLE = [
    (0,        0),
    (106_000,  1_055),
    (133_000,  2_640),
    (167_000,  4_226),
    (200_000,  5_811),
    (500_000,  6_343),
]

# SS taxability thresholds (not inflation indexed in current law)
SS_PROV_LOW_MFJ, SS_PROV_HIGH_MFJ = 32_000, 44_000
SS_PROV_LOW_SINGLE, SS_PROV_HIGH_SINGLE = 25_000, 34_000

# PA-SPECIFIC: Pennsylvania flat income tax rate.
# PA exempts pension, SS, and IRA/401k withdrawals after 59½ from state income tax.
# PA taxes LTCG at this same flat rate (no preferential rate for capital gains).
# If not a PA resident, update this rate and review all # PA-SPECIFIC: logic below.
PA_RATE = 0.0307

# Uniform Lifetime Table (post-SECURE 2.0). Age -> divisor.
ULT = {
    73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0, 79: 21.1,
    80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2,
    87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8, 93: 10.1,
    94: 9.5,  95: 8.9,  96: 8.4,  97: 7.8,  98: 7.3,  99: 6.8,  100: 6.4,
}


# ---------------------------------------------------------------------------
# Tax calculations
# ---------------------------------------------------------------------------

def bracketed_tax(income: float, brackets: list[tuple[float, float]]) -> float:
    if income <= 0:
        return 0.0
    tax = 0.0
    for i, (floor, rate) in enumerate(brackets):
        ceiling = brackets[i + 1][0] if i + 1 < len(brackets) else float("inf")
        if income > floor:
            tax += (min(income, ceiling) - floor) * rate
        else:
            break
    return tax


def ltcg_tax(ord_taxable: float, ltcg: float, brackets: list[tuple[float, float]]) -> float:
    if ltcg <= 0:
        return 0.0
    tax = 0.0
    remaining = ltcg
    base = max(ord_taxable, 0)
    for i, (floor, rate) in enumerate(brackets):
        ceiling = brackets[i + 1][0] if i + 1 < len(brackets) else float("inf")
        room = max(0, ceiling - max(base, floor))
        if base + remaining <= floor:
            break
        if base >= ceiling:
            continue
        slab = min(remaining, room)
        tax += slab * rate
        remaining -= slab
        base += slab
        if remaining <= 0:
            break
    return tax


def ss_taxable(ss_benefit: float, other_income: float, mfj: bool) -> float:
    if ss_benefit <= 0:
        return 0.0
    provisional = other_income + 0.5 * ss_benefit
    low, high = (SS_PROV_LOW_MFJ, SS_PROV_HIGH_MFJ) if mfj else (SS_PROV_LOW_SINGLE, SS_PROV_HIGH_SINGLE)
    if provisional <= low:
        return 0.0
    if provisional <= high:
        return min(0.5 * (provisional - low), 0.5 * ss_benefit)
    tier1 = min(0.5 * (high - low), 0.5 * ss_benefit)
    tier2 = 0.85 * (provisional - high)
    return min(tier1 + tier2, 0.85 * ss_benefit)


def irmaa_surcharge(magi: float, n_people: int, tiers: list[tuple[float, float]]) -> float:
    sur = 0.0
    for floor, amt in tiers:
        if magi >= floor:
            sur = amt
    return sur * n_people


def rmd_factor(age: int) -> Optional[float]:
    if age < 73:
        return None
    return ULT.get(age, ULT[100])


# ---------------------------------------------------------------------------
# Inputs / Policy / Simulation
# ---------------------------------------------------------------------------

# ============================================================
# TEMPLATE DEFAULTS — Replace every value in this dataclass
# with your own data before running. See README.md for field
# explanations and NEW_USER_SETUP.md for the intake guide.
# ============================================================

@dataclass
class Inputs:
    # Ages
    age1: int = 55          # USER: your current age
    age2: int = 53          # USER: spouse age (enter 0 if single)
    rmd_age: int = 75       # USER: 73 if born 1951-1959; 75 if born 1960+ (SECURE 2.0)
    horizon_age: int = 95   # USER: final age for the projection (common: 90, 95, 100)

    # Filing
    mfj: bool = True        # USER: True = married filing jointly; False = single

    # Balances (today's dollars)
    trad_tsp: float = 200_000    # USER: traditional 401k / TSP / IRA balance today
    roth_tsp: float = 50_000     # USER: Roth 401k / TSP balance today
    roth_ira: float = 25_000     # USER: Roth IRA balance today
    taxable: float = 500_000     # USER: taxable brokerage account balance today
    taxable_basis: float = 350_000  # USER: cost basis in taxable account (check recent statement)

    # Income streams (retirement-phase; pension starts at retirement_age)
    pension: float = 48_000      # USER: annual pension / fixed income at retirement (today's $, CPI-linked)
    ss1_pia: float = 24_000      # USER: your Social Security PIA at full retirement age (from ssa.gov)
    ss2_pia: float = 20_000      # USER: spouse SS PIA at FRA (enter 0 if single or no SS)
    ss1_claim_age: int = 67      # USER: your planned SS claiming age (62-70)
    ss2_claim_age: int = 67      # USER: spouse planned SS claiming age (62-70)

    # Employment phase (W-2 income while age1 < retirement_age)
    retirement_age: int = 58             # USER: age at which W-2 income stops and pension starts
    w2_base_monthly_now: float = 8_000.0  # USER: current gross monthly pay
    promotion_age: int = 56               # USER: age of next promotion or major pay increase (set = retirement_age to skip)
    w2_base_monthly_promo: float = 9_000.0  # USER: post-promotion monthly gross pay
    pay_step_age: int = 57                  # USER: age of next pay step (set = retirement_age to skip)
    w2_base_monthly_step: float = 8_400.0   # USER: post-step monthly gross pay
    annual_raise: float = 0.03              # USER: expected annual pay raise rate (e.g., 0.03 = 3%)

    # Contributions during employment (real $/yr)
    annual_tsp_contribution: float = 23_500.0   # USER: annual tax-advantaged contribution (2025 IRS limit = $23,500; check current limit)
    tsp_contribution_roth_frac: float = 1.0     # USER: 0.0 = all traditional, 1.0 = all Roth, 0.5 = split
    annual_taxable_contribution_pre_promo: float = 30_000.0   # USER: annual taxable investment before promotion
    annual_taxable_contribution_post_promo: float = 40_000.0  # USER: annual taxable investment after promotion

    # Spending (real $) — two phases (non-housing)
    spending_employment: float = 30_000    # USER: annual non-housing spending while employed (today's $)
    spending_retirement: float = 36_000    # USER: annual non-housing spending in retirement (today's $)

    # Home purchase (set home_purchase_price=0 to disable)
    home_purchase_age: int = 58             # USER: age at which you plan to buy (often = retirement_age)
    home_purchase_price: float = 600_000    # USER: purchase price in today's dollars — inflated to purchase-year nominal in the sim
    down_payment_pct: float = 0.20          # USER: down payment as a fraction (0.20 = 20%)
    mortgage_rate: float = 0.065            # USER: expected mortgage rate (e.g., 0.065 = 6.5%)
    mortgage_term_years: int = 30           # USER: loan term (15, 20, or 30 years)
    home_appreciation_rate: float = 0.03    # USER: expected annual home appreciation (e.g., 0.03 = 3%)

    # Transaction drag — from your city's Location Constants file
    transfer_tax_rate: float = 0.020        # USER: buyer's transfer tax rate — see Location Constants Template
    service_leakage_rate: float = 0.015     # Standard closing cost rate (1.5% — do not change)
    acquisition_allowance_rate: float = 0.020  # Acquisition condition allowance (2.0% — do not change)

    # Ongoing housing costs — from your city's Location Constants file
    property_tax_rate: float = 0.012        # USER: your city's property tax rate — see Location Constants Template
    homestead_exemption: float = 0          # USER: homestead exemption value (dollar reduction to assessed value; 0 if not applicable)
    hoa_monthly_t0: float = 0.0             # USER: monthly HOA in today's dollars (0 if no HOA)
    maintenance_floor_rate: float = 0.003   # Standard maintenance floor (0.3% of purchase price — do not change)
    maintenance_ceiling_rate: float = 0.0175  # Standard maintenance ceiling (1.75% of PP — do not change)

    # Capital market assumptions (nominal)
    return_trad: float = 0.06
    return_roth: float = 0.06
    return_taxable: float = 0.055     # slight drag for tax-cost
    taxable_div_yield: float = 0.020  # qualified dividends thrown off annually
    inflation: float = 0.025

    # Behavior
    pay_tax_from_taxable: bool = True  # vs. withhold from conversion (retirement only — employment always pays from W-2 cash)
    tcja_extended: bool = True         # if False, brackets revert in 2026

    def n_people(self, year_idx: int, death_age: Optional[int]) -> int:
        if death_age is None:
            return 2
        if self.age1 + year_idx >= death_age:
            return 1
        return 2


@dataclass
class Policy:
    fill_to_marginal: float = 0.24        # retirement-phase: convert until next $ crosses this rate
    fill_to_marginal_emp: float = 0.12    # employment-phase target (W-2 already fills lower brackets)
    start_age: int = 46
    stop_age: int = 73
    irmaa_tier_cap: int = 2               # max IRMAA tier to allow (0 = no IRMAA, 5 = no cap)
    taxable_floor: float = 0.0            # keep at least this much in taxable; switch spending to Trad when at floor (real $)


def adjust_brackets(brackets: list[tuple[float, float]], factor: float) -> list[tuple[float, float]]:
    return [(floor * factor, rate) for floor, rate in brackets]


def adjust_tiers(tiers: list[tuple[float, float]], factor: float) -> list[tuple[float, float]]:
    return [(floor * factor, amt * factor) for floor, amt in tiers]


def amortize(loan_amount: float, annual_rate: float, term_years: int) -> tuple[float, list[float]]:
    """Standard fixed-rate amortization. Returns (monthly_PI, year_end_balances)."""
    if loan_amount <= 0 or annual_rate <= 0 or term_years <= 0:
        return 0.0, [0.0] * max(term_years, 0)
    r = annual_rate / 12
    n = term_years * 12
    monthly_pi = loan_amount * r * (1 + r) ** n / ((1 + r) ** n - 1)
    balances = []
    bal = loan_amount
    for _ in range(term_years):
        for _ in range(12):
            interest = bal * r
            bal -= (monthly_pi - interest)
        balances.append(max(0.0, bal))
    return monthly_pi, balances


def simulate(inp: Inputs, pol: Policy, death_age: Optional[int] = None) -> pd.DataFrame:
    rows = []
    # Account balances (nominal)
    trad = inp.trad_tsp
    roth_tsp = inp.roth_tsp
    roth_ira = inp.roth_ira
    taxable = inp.taxable
    basis = inp.taxable_basis

    years = inp.horizon_age - inp.age1 + 1
    inflation = inp.inflation

    # House purchase state
    house_owned = False
    mortgage_balance = 0.0
    monthly_pi = 0.0
    year_end_balances: list[float] = []
    home_value = 0.0
    purchase_pp_nominal = 0.0
    hoa_annual_t0_nominal = 0.0

    for y in range(years):
        infl_factor = (1 + inflation) ** y
        age1 = inp.age1 + y
        age2 = inp.age2 + y
        n_people = inp.n_people(y, death_age)
        mfj = inp.mfj and n_people == 2

        # Phase: employment until retirement_age, then retirement
        is_employed = age1 < inp.retirement_age

        # W-2 income (nominal) — walks the pay scale, grows at annual_raise
        w2_income = 0.0
        if is_employed:
            base_monthly = inp.w2_base_monthly_now
            for evt_age, evt_pay in sorted([
                (inp.promotion_age, inp.w2_base_monthly_promo),
                (inp.pay_step_age, inp.w2_base_monthly_step),
            ]):
                if age1 >= evt_age:
                    base_monthly = evt_pay
            w2_income = base_monthly * 12 * (1 + inp.annual_raise) ** y

        # Pension (CPI) — only after retirement
        pension = inp.pension * infl_factor if not is_employed else 0.0
        # SS (CPI), each spouse if alive and claimed
        ss1 = inp.ss1_pia * infl_factor if age1 >= inp.ss1_claim_age else 0
        ss2 = inp.ss2_pia * infl_factor if age2 >= inp.ss2_claim_age else 0
        if death_age is not None and age1 >= death_age:
            # Survivor takes the larger benefit
            ss1, ss2 = max(ss1, ss2), 0
            pension = pension * 0.55  # rough survivor assumption (50–100% varies)

        # Inflation-adjusted brackets / tiers / std deduction
        fed_br = adjust_brackets(FED_BRACKETS_MFJ if mfj else FED_BRACKETS_SINGLE, infl_factor)
        ltcg_br = adjust_brackets(LTCG_BRACKETS_MFJ if mfj else LTCG_BRACKETS_SINGLE, infl_factor)
        irmaa_br = adjust_tiers(IRMAA_TIERS_MFJ if mfj else IRMAA_TIERS_SINGLE, infl_factor)
        std_ded = (STD_DED_MFJ if mfj else STD_DED_SINGLE) * infl_factor
        niit_thr = (NIIT_THRESHOLD_MFJ if mfj else NIIT_THRESHOLD_SINGLE) * infl_factor

        # TCJA sunset (revert to roughly +15% bracket structure pre-2018, simplified: bump rates)
        if not inp.tcja_extended and (2026 + y) >= 2026:
            fed_br = [(f, r + (0.03 if 0.12 <= r <= 0.28 else 0.0)) for f, r in fed_br]

        # Required minimum distribution
        rmd = 0.0
        f = rmd_factor(age1) if age1 >= inp.rmd_age else None
        if f is not None:
            rmd = trad / f

        # Taxable account dividends (qualified, assume all)
        qdiv = taxable * inp.taxable_div_yield

        # Decide conversion amount under the policy
        # Phase-switched fill rate: employment vs retirement
        fill_rate = pol.fill_to_marginal_emp if is_employed else pol.fill_to_marginal

        conversion = 0.0
        if pol.start_age <= age1 <= pol.stop_age:
            # Ordinary income before conversion (W-2 is ordinary income too)
            ss_tax_base = ss_taxable(ss1 + ss2, w2_income + pension + rmd, mfj)
            ord_pre = w2_income + pension + rmd + ss_tax_base
            taxable_income_pre = max(0, ord_pre - std_ded)

            # Walk up brackets to find headroom
            target_marginal = fill_rate + 1e-9
            ceiling_taxable_income = 0.0
            for i, (floor, rate) in enumerate(fed_br):
                if rate <= target_marginal:
                    ceiling_taxable_income = fed_br[i + 1][0] if i + 1 < len(fed_br) else float("inf")
            headroom_bracket = max(0, ceiling_taxable_income - taxable_income_pre)

            # IRMAA cap
            magi_pre = ord_pre  # simplification; ignores tax-exempt interest
            # MAGI lookback is 2 years — simplified to current year here
            irmaa_ceiling = float("inf")
            # IRMAA only matters at 65+ (2-year MAGI lookback → cap binds from age 63)
            if pol.irmaa_tier_cap < len(irmaa_br) - 1 and age1 >= 63:
                irmaa_ceiling = irmaa_br[pol.irmaa_tier_cap + 1][0] - 1
            headroom_irmaa = max(0, irmaa_ceiling - magi_pre)

            conversion = min(headroom_bracket, headroom_irmaa, trad - rmd)
            conversion = max(conversion, 0)

        # Home purchase event (once, at home_purchase_age)
        purchase_tiei = 0.0
        if not house_owned and age1 == inp.home_purchase_age and inp.home_purchase_price > 0:
            purchase_pp_nominal = inp.home_purchase_price * infl_factor
            dp = purchase_pp_nominal * inp.down_payment_pct
            statutory = purchase_pp_nominal * inp.transfer_tax_rate
            service = purchase_pp_nominal * inp.service_leakage_rate
            acquisition = purchase_pp_nominal * inp.acquisition_allowance_rate
            purchase_tiei = dp + statutory + service + acquisition
            loan_amount = purchase_pp_nominal - dp
            monthly_pi, year_end_balances = amortize(loan_amount, inp.mortgage_rate, inp.mortgage_term_years)
            mortgage_balance = loan_amount
            hoa_annual_t0_nominal = inp.hoa_monthly_t0 * 12 * infl_factor
            home_value = purchase_pp_nominal
            house_owned = True

        # Recurring housing cost (nominal $ this year)
        housing_cost = 0.0
        if house_owned:
            annual_pi = monthly_pi * 12 if mortgage_balance > 0 else 0.0
            years_since_purchase = age1 - inp.home_purchase_age
            cpi_since_purchase = (1 + inflation) ** years_since_purchase
            assessed = max(0.0, purchase_pp_nominal - inp.homestead_exemption)
            annual_property_tax = assessed * inp.property_tax_rate * cpi_since_purchase
            annual_hoa = hoa_annual_t0_nominal * cpi_since_purchase
            maint_floor = purchase_pp_nominal * inp.maintenance_floor_rate
            maint_ceiling = max(0.0, purchase_pp_nominal * inp.maintenance_ceiling_rate - hoa_annual_t0_nominal) * cpi_since_purchase
            annual_maint = max(maint_floor, maint_ceiling)
            housing_cost = annual_pi + annual_property_tax + annual_hoa + annual_maint

        # Compute spending need and required taxable / Trad withdrawals
        # Phase-switched spending: employment vs retirement (non-housing)
        spend_real = inp.spending_employment if is_employed else inp.spending_retirement
        spend_need = spend_real * infl_factor + housing_cost + purchase_tiei
        cash_in = w2_income + pension + ss1 + ss2 + rmd  # before conversion tax
        # Conversion: comes out of trad, goes into roth_ira; tax owed on it
        trad_after_rmd = trad - rmd
        conversion = min(conversion, trad_after_rmd)

        # Build taxable income with conversion (W-2 is ordinary income)
        ord_income = w2_income + pension + rmd + conversion
        ss_tax_amt = ss_taxable(ss1 + ss2, ord_income, mfj)
        agi_ord = ord_income + ss_tax_amt

        # Spending shortfall covered first by taxable account, then trad (extra), then roth
        shortfall = max(0, spend_need - (cash_in))
        ltcg_realized = 0.0

        # Withdraw from taxable for spending, but respect the policy floor (real $, inflated to nominal)
        floor_nom = pol.taxable_floor * infl_factor
        available_taxable = max(0, taxable - floor_nom)
        from_taxable = min(shortfall, available_taxable)
        if from_taxable > 0 and taxable > 0:
            gain_frac = max(0, 1 - basis / taxable) if taxable > 0 else 0
            ltcg_realized += from_taxable * gain_frac
            basis -= from_taxable * (1 - gain_frac)
            taxable -= from_taxable
            shortfall -= from_taxable

        # Then extra Trad withdrawal if needed
        extra_trad = min(shortfall, trad_after_rmd - conversion)
        if extra_trad > 0:
            ord_income += extra_trad
            ss_tax_amt = ss_taxable(ss1 + ss2, ord_income, mfj)
            agi_ord = ord_income + ss_tax_amt
            shortfall -= extra_trad

        # Then Roth (Roth IRA first, then Roth TSP)
        from_roth = 0.0
        if shortfall > 0:
            take = min(shortfall, roth_ira)
            roth_ira -= take
            from_roth += take
            shortfall -= take
        if shortfall > 0:
            take = min(shortfall, roth_tsp)
            roth_tsp -= take
            from_roth += take
            shortfall -= take

        # 10% early withdrawal penalty on cash distributions before 59½.
        # Conversions (Trad→Roth rollovers) are NOT distributions — no penalty.
        early_penalty = 0.10 * (extra_trad + from_roth) if age1 < 59 else 0.0

        # Federal income tax (fixed in this loop — depends only on ordinary income)
        taxable_income = max(0, agi_ord - std_ded)
        fed_tax = bracketed_tax(taxable_income, fed_br)

        # Fixed-point tax solver: paying tax from taxable realizes more LTCG, raising tax.
        # Iterate until tax-payment-induced LTCG converges. gain_frac is constant within a
        # year (proportional withdrawals preserve the basis ratio), so this converges quickly.
        ltcg_from_spending = ltcg_realized
        # During employment, conversion tax is paid from W-2 cash (no LTCG realization).
        # In retirement, fall back to the user-selected behavior.
        pay_tax_from_taxable_now = inp.pay_tax_from_taxable and not is_employed
        gain_frac_now = max(0, 1 - basis / taxable) if (taxable > 0 and pay_tax_from_taxable_now) else 0.0
        tax_payment_gain = 0.0
        cg_tax = niit = pa_tax = irmaa = 0.0
        magi = agi_ord
        total_tax = fed_tax
        for _ in range(8):
            total_ltcg = ltcg_from_spending + qdiv + tax_payment_gain
            cg_tax = ltcg_tax(taxable_income, total_ltcg, ltcg_br)
            magi = agi_ord + total_ltcg
            niit = NIIT_RATE * max(0, min(total_ltcg, magi - niit_thr))
            # PA-SPECIFIC: PA taxes LTCG at the flat rate (no preferential capital gains rate).
            # If not a PA resident, adjust this line to use your state's LTCG rate or remove it.
            pa_tax = PA_RATE * total_ltcg
            irmaa = irmaa_surcharge(magi, n_people if any([ss1, ss2]) and age1 >= 65 else 0, irmaa_br)
            total_tax = fed_tax + cg_tax + niit + pa_tax + irmaa + early_penalty
            new_payment_gain = total_tax * gain_frac_now
            if abs(new_payment_gain - tax_payment_gain) < 1.0:
                tax_payment_gain = new_payment_gain
                break
            tax_payment_gain = new_payment_gain

        # Update ltcg_realized so the ledger shows the full picture (spending + tax-payment gains)
        ltcg_realized = ltcg_from_spending + tax_payment_gain

        # Pay conversion tax: from taxable (preferred) or withheld from conversion.
        # Employment phase always uses the "pay from W-2 cash" path regardless of toggle.
        roth_added = conversion
        if not pay_tax_from_taxable_now and not is_employed:
            # Approximate: withhold marginal cost of conversion from the conversion itself
            tax_on_conv = conversion * fill_rate
            roth_added = max(0, conversion - tax_on_conv)

        # Apply movements
        trad -= (rmd + conversion + extra_trad)
        roth_ira += roth_added

        # Net cash flow into / out of taxable
        # RMD lands in taxable if not spent. Same for excess pension/SS/W-2.
        net_cash = (cash_in - spend_need) + (qdiv)  # qdiv stays in taxable acct as cash if not spent
        if is_employed:
            # Taxes paid from W-2 cash flow — reduce net_cash, leave taxable basis alone
            net_cash -= total_tax
        else:
            # Retirement: pay all taxes from taxable (basis decremented proportionally;
            # gain already captured in ltcg_realized via the fixed-point solver above).
            if pay_tax_from_taxable_now and total_tax > 0 and taxable > 0:
                basis -= total_tax * (1 - gain_frac_now)
            taxable -= total_tax
        if net_cash > 0:
            taxable += net_cash
            basis += net_cash  # treat as new basis (cash added)
        elif net_cash < 0:
            # W-2 wasn't enough to cover spending + tax: draw shortfall from taxable.
            shortfall_cash = -net_cash
            draw = min(shortfall_cash, taxable)
            if draw > 0 and taxable > 0:
                gain_frac_d = max(0, 1 - basis / taxable)
                basis -= draw * (1 - gain_frac_d)
                taxable -= draw
        # If taxable went negative, pull from Roth IRA to cover (last resort)
        if taxable < 0:
            deficit = -taxable
            taxable = 0
            pull = min(deficit, roth_ira)
            roth_ira -= pull
            deficit -= pull
            if deficit > 0:
                roth_tsp -= min(deficit, roth_tsp)

        # Grow accounts (end-of-year)
        trad *= (1 + inp.return_trad)
        roth_ira *= (1 + inp.return_roth)
        roth_tsp *= (1 + inp.return_roth)
        # Taxable: total return less the dividend already paid out
        taxable *= (1 + inp.return_taxable - inp.taxable_div_yield)
        # Basis can't exceed market value
        basis = min(basis, taxable)

        # Employment-phase contributions (added end-of-year, in real $ scaled to nominal)
        if is_employed:
            roth_frac = inp.tsp_contribution_roth_frac
            tsp_contrib_nom = inp.annual_tsp_contribution * infl_factor
            trad += tsp_contrib_nom * (1 - roth_frac)
            roth_tsp += tsp_contrib_nom * roth_frac
            tax_contrib_real = (inp.annual_taxable_contribution_pre_promo
                                if age1 < inp.promotion_age
                                else inp.annual_taxable_contribution_post_promo)
            tax_contrib_nom = tax_contrib_real * infl_factor
            taxable += tax_contrib_nom
            basis += tax_contrib_nom  # new contributions = full basis

        # Home value appreciation & mortgage amortization (end-of-year)
        if house_owned:
            home_value *= (1 + inp.home_appreciation_rate)
            yr_idx = age1 - inp.home_purchase_age
            if 0 <= yr_idx < len(year_end_balances):
                mortgage_balance = year_end_balances[yr_idx]
            else:
                mortgage_balance = 0.0
        home_equity_nominal = max(0.0, home_value - mortgage_balance) if house_owned else 0.0

        total_nominal = trad + roth_ira + roth_tsp + taxable + home_equity_nominal
        # After-tax wealth: discount Trad by an assumed terminal rate; home equity counts at full nominal value
        terminal_rate = 0.22
        after_tax_nominal = trad * (1 - terminal_rate) + roth_ira + roth_tsp + (
            taxable - max(0, taxable - basis) * 0.15
        ) + home_equity_nominal
        real_after_tax = after_tax_nominal / infl_factor

        rows.append({
            "year": 2026 + y,
            "age": age1,
            "phase": "employment" if is_employed else "retirement",
            "w2": w2_income,
            "pension": pension,
            "ss": ss1 + ss2,
            "rmd": rmd,
            "conversion": conversion,
            "spend_taxable": from_taxable,
            "spend_trad": extra_trad,
            "spend_roth": from_roth,
            "ltcg_realized": ltcg_realized,
            "qdiv": qdiv,
            "ltcg_rate": (cg_tax + niit + pa_tax) / (ltcg_realized + qdiv) if (ltcg_realized + qdiv) > 0 else 0.0,
            "ord_income": ord_income,
            "ss_taxable": ss_tax_amt,
            "agi": magi,
            "fed_tax": fed_tax,
            "cg_tax": cg_tax,
            "niit": niit,
            "pa_tax": pa_tax,
            "irmaa": irmaa,
            "early_penalty": early_penalty,
            "total_tax": total_tax,
            "trad": trad,
            "roth": roth_ira + roth_tsp,
            "taxable": taxable,
            "housing_cost": housing_cost,
            "tiei_purchase": purchase_tiei,
            "home_value": home_value,
            "mortgage_balance": mortgage_balance,
            "total": total_nominal,
            "real_after_tax": real_after_tax,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Optimizer (grid search over policy parameters)
# ---------------------------------------------------------------------------

MARGINAL_GRID = [0.0, 0.12, 0.15, 0.22, 0.24, 0.25, 0.27, 0.32, 0.35]
EMP_MARGINAL_GRID = [0.0, 0.10, 0.12, 0.22]  # employment-phase: tighter grid (W-2 anchors low brackets)
IRMAA_GRID = [0, 2, 5]                        # base / mid / uncapped
FLOOR_GRID = [0, 100_000, 250_000, 500_000, 1_000_000]


def optimize(inp: Inputs, death_age: Optional[int]) -> tuple[Policy, float, pd.DataFrame]:
    best_score = -float("inf")
    best_pol = None
    best_df = None
    # Always start at current age (no benefit to delaying — conversions are cheapest now)
    start_grid = [inp.age1]
    stop_grid = list(range(inp.rmd_age - 5, inp.rmd_age + 5))
    for marg_emp in EMP_MARGINAL_GRID:
        for marg in MARGINAL_GRID:
            for irmaa_cap in IRMAA_GRID:
                for start in start_grid:
                    for stop in stop_grid:
                        if stop < start:
                            continue
                        for floor in FLOOR_GRID:
                            pol = Policy(fill_to_marginal=marg,
                                         fill_to_marginal_emp=marg_emp,
                                         start_age=start, stop_age=stop,
                                         irmaa_tier_cap=irmaa_cap,
                                         taxable_floor=floor)
                            df = simulate(inp, pol, death_age)
                            score = df["real_after_tax"].iloc[-1]
                            if score > best_score:
                                best_score = score
                                best_pol = pol
                                best_df = df
    return best_pol, best_score, best_df


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Roth Conversion Optimizer", layout="wide")

if "changelog" not in st.session_state:
    st.session_state.changelog = []
if "prev_inp" not in st.session_state:
    st.session_state.prev_inp = None
st.title("Roth Conversion Optimizer")
st.caption("Template defaults — update Inputs dataclass or use sidebar. See README.md for field explanations.")

with st.sidebar:
    st.header("Household")
    age1 = st.number_input("Your age", 40, 90, 55)           # USER: your current age
    age2 = st.number_input("Spouse age", 40, 90, 53)         # USER: spouse age (0 if single)
    mfj = st.checkbox("Married filing jointly", True)
    horizon = st.number_input("Plan horizon (final age)", 80, 105, 95)
    rmd_age = st.selectbox("RMD start age", [73, 75], index=1)

    st.header("Employment phase")
    retirement_age = st.number_input("Retirement age (W-2 stops, pension starts)", age1, 75, 58)
    w2_now = st.number_input("Current monthly base pay", 0, 50_000, 8_000, step=100)     # USER
    promo_age = st.number_input("Promotion age", age1, retirement_age, min(56, retirement_age))
    w2_promo = st.number_input("Post-promotion monthly base", 0, 50_000, 9_000, step=100)  # USER
    step_age = st.number_input("Pay step age", age1, retirement_age, min(57, retirement_age))
    w2_step = st.number_input("Post-step monthly base", 0, 50_000, 8_400, step=100)       # USER
    raise_pct = st.slider("Annual pay raise", 0.0, 6.0, 3.0, 0.5, format="%.1f%%")
    tsp_contrib = st.number_input("Annual TSP contribution (real)", 0, 30_000, 23_500, step=500)
    tsp_roth_pct = st.slider("TSP contribution Roth %", 0, 100, 100, 5)
    tax_contrib_pre = st.number_input("Annual taxable contrib pre-promo (real)", 0, 200_000, 30_000, step=1_000)   # USER
    tax_contrib_post = st.number_input("Annual taxable contrib post-promo (real)", 0, 200_000, 40_000, step=1_000)  # USER

    st.header("Balances (today)")
    trad_tsp = st.number_input("Traditional TSP/401k/IRA", 0, 10_000_000, 200_000, step=10_000)   # USER
    roth_tsp = st.number_input("Roth TSP/401k", 0, 10_000_000, 50_000, step=10_000)               # USER
    roth_ira = st.number_input("Roth IRA", 0, 10_000_000, 25_000, step=10_000)                    # USER
    taxable = st.number_input("Taxable account", 0, 10_000_000, 500_000, step=10_000)             # USER
    basis = st.number_input("Taxable cost basis", 0, 10_000_000, 350_000, step=10_000)            # USER

    st.header("Income (real, today's $)")
    pension = st.number_input("Pension / fixed income (CPI-linked)", 0, 500_000, 48_000, step=1_000)   # USER
    ss1 = st.number_input("Your SS at FRA", 0, 100_000, 24_000, step=500)                               # USER
    ss2 = st.number_input("Spouse SS at FRA", 0, 100_000, 20_000, step=500)                            # USER
    ss1_age = st.slider("Your SS claim age", 62, 70, 67)
    ss2_age = st.slider("Spouse SS claim age", 62, 70, 67)

    st.header("Spending & Returns")
    spending_emp = st.number_input("Annual spending during employment (real)", 0, 500_000, 30_000, step=1_000,  # USER
                                   help="Non-housing spending while working.")
    spending_ret = st.number_input("Non-housing retirement spending (real)", 0, 500_000, 36_000, step=1_000,   # USER
                                   help="Food, utilities, insurance, travel, healthcare. Housing is computed separately in the Housing section.")
    real_ret_pct = st.slider("Real return (all accounts)", 0.0, 12.0, 5.5, 0.5, format="%.1f%%")
    div_yield_pct = st.slider("Taxable dividend yield", 0.0, 5.0, 2.0, 0.1, format="%.1f%%")
    inflation_pct = st.slider("Inflation", 0.0, 6.0, 3.0, 0.5, format="%.1f%%")

    real_ret = real_ret_pct / 100
    div_yield = div_yield_pct / 100
    inflation = inflation_pct / 100
    nominal_ret = (1 + real_ret) * (1 + inflation) - 1

    st.header("Housing (home purchase at retirement)")
    home_pp = st.number_input("Purchase price (today's $; 0 = no purchase)", 0, 5_000_000, 600_000, step=25_000)  # USER
    home_age = st.number_input("Purchase age", age1, horizon, retirement_age)
    dp_pct = st.slider("Down payment %", 5, 100, 20) / 100
    mort_rate = st.slider("Mortgage rate", 0.0, 12.0, 6.5, 0.05, format="%.2f%%") / 100   # USER
    mort_term = st.selectbox("Mortgage term (years)", [15, 20, 30], index=2)
    appr_rate = st.slider("Home appreciation rate", -5.0, 8.0, 3.0, 0.25, format="%.2f%%") / 100
    hoa_mo = st.number_input("HOA (monthly, real)", 0, 10_000, 0, step=50)
    prop_tax_pct = st.slider("Property tax rate", 0.0, 4.0, 1.2, 0.01, format="%.4f%%") / 100  # USER: from Location Constants
    homestead = st.number_input("Homestead exemption (dollar reduction to assessed value)", 0, 500_000, 0, step=10_000)  # USER: from Location Constants
    with st.expander("Transaction drag (from Location Constants)"):
        statutory_pct = st.number_input("Statutory leakage (buyer transfer tax) %", 0.0, 10.0, 2.0, step=0.001) / 100  # USER: from Location Constants
        service_pct = st.number_input("Service leakage % (closing)", 0.0, 5.0, 1.5, step=0.1) / 100
        acq_pct = st.number_input("Acquisition condition allowance %", 0.0, 10.0, 2.0, step=0.1) / 100
    with st.expander("Maintenance rates (protocol defaults)"):
        maint_floor = st.number_input("Maintenance floor (% of PP, not inflated)", 0.0, 2.0, 0.3, step=0.05) / 100
        maint_ceiling = st.number_input("Maintenance ceiling (% of PP, inflated)", 0.0, 5.0, 1.75, step=0.05) / 100

    st.header("Tax assumptions")
    tcja = st.checkbox("TCJA brackets extended", False)
    pay_from_taxable = st.checkbox("Pay conversion tax from taxable account", True)

    st.header("Survivor scenarios")
    death_choices = st.multiselect("Compare 'first death at age' scenarios",
                                    [None, 75, 80, 85, 90],
                                    default=[None, 80])

inp = Inputs(
    age1=age1, age2=age2, mfj=mfj, horizon_age=horizon, rmd_age=rmd_age,
    trad_tsp=trad_tsp, roth_tsp=roth_tsp, roth_ira=roth_ira,
    taxable=taxable, taxable_basis=min(basis, taxable),
    pension=pension, ss1_pia=ss1, ss2_pia=ss2,
    ss1_claim_age=ss1_age, ss2_claim_age=ss2_age,
    retirement_age=retirement_age,
    w2_base_monthly_now=w2_now,
    promotion_age=promo_age,
    w2_base_monthly_promo=w2_promo,
    pay_step_age=step_age,
    w2_base_monthly_step=w2_step,
    annual_raise=raise_pct / 100,
    annual_tsp_contribution=tsp_contrib,
    tsp_contribution_roth_frac=tsp_roth_pct / 100,
    annual_taxable_contribution_pre_promo=tax_contrib_pre,
    annual_taxable_contribution_post_promo=tax_contrib_post,
    spending_employment=spending_emp,
    spending_retirement=spending_ret,
    home_purchase_age=home_age,
    home_purchase_price=home_pp,
    down_payment_pct=dp_pct,
    mortgage_rate=mort_rate,
    mortgage_term_years=mort_term,
    home_appreciation_rate=appr_rate,
    transfer_tax_rate=statutory_pct,
    service_leakage_rate=service_pct,
    acquisition_allowance_rate=acq_pct,
    property_tax_rate=prop_tax_pct,
    homestead_exemption=homestead,
    hoa_monthly_t0=hoa_mo,
    maintenance_floor_rate=maint_floor,
    maintenance_ceiling_rate=maint_ceiling,
    return_trad=nominal_ret, return_roth=nominal_ret,
    return_taxable=nominal_ret, taxable_div_yield=div_yield,
    inflation=inflation, tcja_extended=tcja, pay_tax_from_taxable=pay_from_taxable,
)

# Change log: diff inp against previous run, record if exactly one field changed
_inp_dict = asdict(inp)
if st.session_state.prev_inp is not None:
    _changed = [(k, st.session_state.prev_inp[k], _inp_dict[k])
                for k in _inp_dict if _inp_dict[k] != st.session_state.prev_inp[k]]
    if len(_changed) == 1:
        st.session_state._pending_change = _changed[0]
    else:
        st.session_state._pending_change = None
else:
    st.session_state._pending_change = None
st.session_state.prev_inp = _inp_dict

# Baseline (no conversions in either phase)
baseline_pol = Policy(fill_to_marginal=0.0, fill_to_marginal_emp=0.0,
                      start_age=age1, stop_age=age1, irmaa_tier_cap=0)


def milestone_rules(inp: Inputs):
    raw = [
        (inp.retirement_age, "Retire"),
        (59,                 "59½"),
        (62,                 "SS min"),
        (63,                 "IRMAA"),
        (65,                 "Medicare"),
        (inp.ss1_claim_age,  "SS"),
        (inp.rmd_age,        "RMD"),
    ]
    by_age: dict[int, str] = {}
    for age, lbl in raw:
        by_age[age] = f"{by_age[age]}/{lbl}" if age in by_age else lbl
    m = pd.DataFrame(sorted(by_age.items()), columns=["age", "milestone"])
    rules = alt.Chart(m).mark_rule(color="gray", strokeDash=[4, 4], opacity=0.5).encode(x="age:Q")
    labels = alt.Chart(m).mark_text(
        angle=270, align="left", baseline="middle", fontSize=9, color="gray", dy=-4
    ).encode(x="age:Q", y=alt.value(8), text="milestone:N")
    return rules + labels


def render_detail(label, df, baseline_df, inp: Inputs):
    st.subheader(f"Detail: {label}")
    col1, col2 = st.columns([1, 1])
    with col1:
        log_bal = st.checkbox("Log scale (balances)", key=f"log_bal_{label}")
    with col2:
        log_wealth = st.checkbox("Log scale (real_after_tax)", key=f"log_wealth_{label}")

    chart_data = df.melt(id_vars=["age"], value_vars=["trad", "roth", "taxable"],
                         var_name="account", value_name="balance")
    m_rules = milestone_rules(inp)
    if log_bal:
        chart_data_log = chart_data[chart_data["balance"] > 0]
        bal_chart = alt.Chart(chart_data_log).mark_line().encode(
            x="age:Q",
            y=alt.Y("balance:Q", scale=alt.Scale(type="log")),
            color="account:N",
        ).properties(height=250)
    else:
        bal_chart = alt.Chart(chart_data).mark_area().encode(
            x="age:Q",
            y=alt.Y("balance:Q", stack="zero"),
            color="account:N",
        ).properties(height=250)
    st.altair_chart((bal_chart + m_rules).resolve_scale(y="independent"), use_container_width=True)

    compare = pd.DataFrame({
        "age": df["age"],
        "this scenario": df["real_after_tax"],
        "no conversions": baseline_df["real_after_tax"],
    }).melt(id_vars=["age"], var_name="scenario", value_name="real_after_tax")
    y_enc_wealth = alt.Y("real_after_tax:Q",
                         scale=alt.Scale(type="log") if log_wealth else alt.Scale())
    line = alt.Chart(compare).mark_line().encode(
        x="age:Q", y=y_enc_wealth, color="scenario:N"
    ).properties(height=250)
    st.altair_chart((line + m_rules).resolve_scale(y="independent"), use_container_width=True)

    st.subheader("Year-by-year ledger")
    st.markdown("""
**Column guide:**
- **Spending sources**: spend_taxable/trad/roth = cash withdrawn from each account type for living expenses
- **Taxable activity**: ltcg_realized = *gains* realized on taxable withdrawals (spending + tax payment); qdiv = dividends; cg_tax = federal LTCG tax; ltcg_rate = all-in rate (fed + NIIT + state)
- **Ordinary income**: conversion = traditional→Roth amount; ord_income = total ordinary income (pension + SS + RMD + conversion); agi = AGI after SS taxability adjustment
- **Taxes**: fed_tax = federal ordinary income tax; irmaa = Medicare premium surcharges; early_penalty = 10% pre-59½ penalty on Trad/Roth cash distributions (not conversions); total_tax = all taxes (fed ord + fed LTCG + NIIT + state + IRMAA + penalty)
- **Bottom line**: real_after_tax = inflation-adjusted after-tax wealth (terminal value of all accounts)

*Key insight*: ltcg_realized is *gain dollars*, not cash dollars. Total taxable cash drawn ≈ (spend_taxable + total_tax). The fixed-point iteration ensures tax payments' LTCG is included in ltcg_realized and taxed.
    """)
    show_cols = ["year", "age", "phase", "w2", "pension", "ss", "rmd", "conversion",
                 "housing_cost", "tiei_purchase",
                 "spend_taxable", "spend_trad", "spend_roth",
                 "ltcg_realized", "qdiv", "cg_tax", "ltcg_rate",
                 "ord_income", "agi", "fed_tax", "irmaa", "early_penalty", "total_tax",
                 "trad", "roth", "taxable", "home_value", "mortgage_balance",
                 "real_after_tax"]
    fmt = {c: "${:,.0f}" for c in show_cols if c not in ("year", "age", "phase", "ltcg_rate")}
    fmt["ltcg_rate"] = "{:.1%}"
    st.dataframe(df[show_cols].style.format(fmt), height=500)


tab_opt, tab_manual, tab_log = st.tabs(["Optimal policies", "Manual scenario", "Change log"])

with tab_opt:
    st.subheader("Optimal policies by survivor scenario")
    cols = st.columns(max(1, len(death_choices)))
    results = []
    for col, death in zip(cols, death_choices):
        with col:
            label = "Both alive through horizon" if death is None else f"First death at {death}"
            st.markdown(f"**{label}**")
            with st.spinner("Optimizing..."):
                pol, score, df = optimize(inp, death)
            baseline_df = simulate(inp, baseline_pol, death)
            baseline_score = baseline_df["real_after_tax"].iloc[-1]
            delta = score - baseline_score
            st.metric("Real after-tax wealth at horizon",
                      f"${score:,.0f}",
                      f"{delta:+,.0f} vs no conversions")
            st.write(f"- Fill to marginal (employment): **{pol.fill_to_marginal_emp:.0%}**")
            st.write(f"- Fill to marginal (retirement): **{pol.fill_to_marginal:.0%}**")
            st.write(f"- Convert ages: **{pol.start_age}–{pol.stop_age}**")
            st.write(f"- IRMAA tier cap: **{pol.irmaa_tier_cap}**")
            st.write(f"- Taxable floor: **${pol.taxable_floor:,.0f}**")
            results.append((label, pol, df, baseline_df))

    if results:
        # Log the change once we have the "both alive" terminal wealth
        _both_alive = next((r for r in results if "Both alive" in r[0]), results[0])
        _wealth = _both_alive[2]["real_after_tax"].iloc[-1]
        _survivor_results = [r for r in results if "Both alive" not in r[0]]
        _survivor_wealth = _survivor_results[-1][2]["real_after_tax"].iloc[-1] if _survivor_results else None
        if st.session_state._pending_change is not None:
            field_name, old_val, new_val = st.session_state._pending_change
            entry = {"Changed": f"{field_name}: {old_val} → {new_val}", "Both alive": _wealth}
            if _survivor_wealth is not None:
                entry["Survivor"] = _survivor_wealth
            st.session_state.changelog.insert(0, entry)
            st.session_state.changelog = st.session_state.changelog[:5]

        render_detail(results[0][0], results[0][2], results[0][3], inp)

with tab_manual:
    st.subheader("Manual scenario — set the policy yourself")
    c1, c2, c3 = st.columns(3)
    with c1:
        m_fill_emp = st.selectbox("Fill bracket (employment)",
                                  [0.0, 0.10, 0.12, 0.22, 0.24],
                                  index=2, format_func=lambda x: f"{x:.0%}")
        m_fill = st.selectbox("Fill bracket (retirement)",
                              [0.0, 0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37],
                              index=4, format_func=lambda x: f"{x:.0%}")
        m_irmaa = st.selectbox("IRMAA tier cap (5 = no cap)",
                               [0, 1, 2, 3, 4, 5], index=2)
    with c2:
        m_start = st.number_input("Convert start age", age1, horizon, age1)
        m_stop = st.number_input("Convert stop age", age1, horizon, min(rmd_age - 1, horizon))
    with c3:
        m_floor = st.number_input("Taxable floor ($)", 0, 10_000_000, 0, step=25_000)
        m_death = st.selectbox("Survivor scenario",
                               [None, 75, 80, 85, 90],
                               format_func=lambda x: "Both alive" if x is None else f"First death at {x}")

    m_pol = Policy(fill_to_marginal=m_fill, fill_to_marginal_emp=m_fill_emp,
                   start_age=m_start, stop_age=m_stop,
                   irmaa_tier_cap=m_irmaa, taxable_floor=m_floor)
    m_df = simulate(inp, m_pol, m_death)
    m_baseline = simulate(inp, baseline_pol, m_death)
    m_score = m_df["real_after_tax"].iloc[-1]
    m_base_score = m_baseline["real_after_tax"].iloc[-1]
    st.metric("Real after-tax wealth at horizon",
              f"${m_score:,.0f}",
              f"{m_score - m_base_score:+,.0f} vs no conversions")
    render_detail("manual scenario", m_df, m_baseline, inp)

with tab_log:
    st.subheader("Recent input changes")
    if st.session_state.changelog:
        log_df = pd.DataFrame(st.session_state.changelog)
        wealth_cols = [c for c in log_df.columns if c != "Changed"]
        st.dataframe(
            log_df.style.format({c: "${:,.0f}" for c in wealth_cols}),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("No changes recorded yet — adjust a single input and the result will appear here.")
    if st.button("Clear log"):
        st.session_state.changelog = []
        st.rerun()

st.caption("v1 caveats: IRMAA uses current-year MAGI (real lookback is 2 years); "
           "TCJA-sunset toggle uses a simplified +3pp bump on middle brackets; "
           "survivor pension reduction is a flat 55% placeholder; terminal Trad value "
           "discounted at flat 22% to compute 'after-tax' wealth. "
           "Employment phase: W-2 income modeled with pay-scale steps; conversion tax "
           "paid from W-2 cash flow (no LTCG realization); spouse W-2 income not modeled.")
