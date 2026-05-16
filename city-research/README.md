# City Research Framework

## What This Tool Does

Produces two structured HTML research documents — one for weather/climate and one for politics/governance — that evaluate candidate retirement cities across standardized dimensions. Each city lives in its own isolated panel. The documents are designed for side-by-side research, not ranking.

---

## The Isolation Rule (Non-Negotiable)

Within sections 1–9 of the weather file and all 8 sections of the politics file, **no city panel may reference any other target city by name.** Each panel must stand entirely on its own.

The only permitted cross-city reference zone is **Section 10 of the weather file** ("Comparisons"), which is explicitly designed for side-by-side climate data.

Baseline cities (your four personal reference points for weather comparisons) are exempt from this rule and may appear anywhere.

**Run `compliance_scanner.py` and get a CLEAN result before every delivery or commit.**

---

## Directory Contents

| File | Purpose |
|---|---|
| `retirement_weather_template.html` | Weather/climate research document — stub with one placeholder city panel |
| `retirement_politics_template.html` | Politics/governance research document — stub with one placeholder city panel |
| `compliance_scanner.py` | Isolation Rule enforcer — scans both files for cross-city violations |
| `TONE_GUIDE.md` | Voice and style guide — must be followed when writing all panel content |

---

## Adding a City

### Step 1 — Weather file

1. Copy the stub city panel (`<div id="tab-cityname">`) in `retirement_weather_template.html`.
2. Replace all `[City Name]` tokens and `tab-cityname` with the city's actual name and ID.
3. Fill in all 10 sections following the Isolation Rule and the tone guide.
4. Add a `<button>` for the city in the tab bar.
5. Add a column to the Summary table.

### Step 2 — Politics file

Same process in `retirement_politics_template.html` — 8 sections plus the Notable Factor box.

### Step 3 — Scanner configuration

Open `compliance_scanner.py` and update:

```python
BASELINE_CITIES = [
    'Your City A',   # The four reference cities used in Section 10 comparisons
    'Your City B',
    'Your City C',
    'Your City D',
]

WEATHER_TARGET_CITIES = {
    'tab-cityname': 'City Name',   # one entry per city panel div
}

POLITICS_TARGET_CITIES = {
    'tab-cityname': 'City Name',
}

WEATHER_SEARCH_TERMS = [
    'City Name', 'City Adjective',   # all name variants to scan for
]

POLITICS_SEARCH_TERMS = [
    'City Name', 'City Adjective',
]
```

### Step 4 — Scan

```
python compliance_scanner.py
```

Result must be `CLEAN` before the files leave your machine.

---

## Weather File — Section Structure

| Section | Topic |
|---|---|
| 1 | Overview |
| 2 | Temperature Profile |
| 3 | Precipitation |
| 4 | Sunshine and Cloud Cover |
| 5 | Humidity |
| 6 | Wind |
| 7 | Severe Weather and Natural Hazards |
| 8 | Air Quality |
| 9 | Retirement-Specific Health Considerations |
| 10 | Comparisons ← **only section where target cities may cross-reference each other** |

---

## Politics File — Section Structure

| Section | Topic |
|---|---|
| 1 | Overview |
| 2 | Fiscal Condition |
| 3 | Taxation |
| 4 | Governance and Reform |
| 5 | Public Safety |
| 6 | Housing Policy |
| 7 | Retirement-Specific Considerations |
| 8 | Political Environment |
| Notable Factor | Synthesis — one observation that holds the complexity together |

---

## Tone

All panel content must follow `TONE_GUIDE.md`. The short version:

- Quantify everything that can be quantified. Use actual figures.
- Name the mechanism, not just the outcome.
- Translate findings to retirement specifically.
- State what is true, not what sounds balanced.
- Present politically charged topics as structural facts, not positions.

---

## SAD Index (Summary Dimension)

The Summary panel uses a Seasonal Affective Disorder index to compare cities across climate dimensions. The formula weights sun hours, cloud days, precipitation, and temperature comfort into a single score. Document the formula in the Summary panel's header comment so future editors can reproduce it.

---

## See Also

- `TONE_GUIDE.md` — full voice and style rules with examples
- `compliance_scanner.py` — Isolation Rule enforcer
- `../CLAUDE.md` — master onboarding for the full suite
- `../NEW_USER_SETUP.md` — intake guide (Phase 4 covers city research setup)
