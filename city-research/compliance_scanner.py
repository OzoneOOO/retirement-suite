"""Isolation Rule compliance scanner for retirement city research HTML files.

The Isolation Rule: within sections 1-9 of the weather file (or sections 1-8
of the politics file), no city panel may reference any other target city by name.
Section 10 of the weather file is the ONLY permitted cross-city comparison section.

Usage:
  python compliance_scanner.py

The script scans both HTML files in this directory and reports any violations.
A CLEAN result means no cross-city references were found in the restricted sections.
Fix all violations before delivering or committing any HTML update.
"""

import re

# USER: Add your four baseline cities here — these are the reference cities used
# in weather Section 10 comparisons only. They are allowed in all sections because
# they are external reference points, not target cities being evaluated.
BASELINE_CITIES = [
    'City A',   # USER: replace with your first baseline city (e.g., 'San Diego')
    'City B',   # USER: replace with your second baseline city
    'City C',   # USER: replace with your third baseline city
    'City D',   # USER: replace with your fourth baseline city
]

# USER: Add each target city tab here as you add it to the HTML files.
# Format: 'tab-cityid': 'City Name'
# The cityid must match the id attribute of the city's <div> element.
# Example: 'tab-portland': 'Portland'
WEATHER_TARGET_CITIES = {
    # 'tab-cityname': 'City Name',  # ADD: one entry per city tab
}

POLITICS_TARGET_CITIES = {
    # 'tab-cityname': 'City Name',  # ADD: one entry per city tab
}

# USER: Add all city name variants to search for (include common abbreviations
# and gentilics — e.g., 'Portland', 'Portlander', 'Portlandian').
# Add variants for all target cities.
WEATHER_SEARCH_TERMS = [
    # 'CityName', 'CityNameAdjective',  # ADD: one block per city
]

POLITICS_SEARCH_TERMS = [
    # 'CityName', 'CityNameAdjective',  # ADD: one block per city
]


def scan_weather_file(filepath: str, target_cities: dict, search_terms: list) -> list[str]:
    """Scan weather HTML for isolation violations in sections 1-9.
    Section 10 is explicitly exempt (cross-city comparisons are required there).
    """
    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    # Strip script blocks before scanning
    content_no_script = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL)

    if not target_cities:
        return ['INFO: No target cities configured — add entries to WEATHER_TARGET_CITIES to enable scanning.']

    panel_splits = re.split(r'(?=<div id="tab-)', content_no_script)
    violations = []

    for chunk in panel_splits:
        id_match = re.search(r'<div id="(tab-[^"]+)"', chunk)
        if not id_match:
            continue
        panel_id = id_match.group(1)
        if panel_id not in target_cities:
            continue
        panel_city = target_cities[panel_id]

        # Only search up to (but not including) Section 10
        sec10_match = re.search(r'10\.\s+Comparisons', chunk)
        searchable = chunk[:sec10_match.start()] if sec10_match else chunk

        for term in search_terms:
            # Skip if the term is or is part of the panel city's own name
            if term.lower() in panel_city.lower() or panel_city.lower() in term.lower():
                continue
            # Skip baseline cities (they are permitted as reference points)
            if any(term.lower() in b.lower() or b.lower() in term.lower() for b in BASELINE_CITIES):
                continue

            pos_match = re.search(re.escape(term), searchable, re.IGNORECASE)
            if pos_match:
                pos = pos_match.start()
                ctx = searchable[max(0, pos - 100):pos + 120].replace('\n', ' ').strip()
                violations.append(f"VIOLATION: '{term}' in {panel_city} panel (pre-Section 10)")
                violations.append(f"  ...{ctx}...")
                violations.append("")

    return violations


def scan_politics_file(filepath: str, target_cities: dict, search_terms: list) -> list[str]:
    """Scan politics HTML for isolation violations.
    Politics has no Section 10 — the entire panel is subject to the Isolation Rule.
    """
    with open(filepath, encoding='utf-8') as f:
        content = f.read()

    # Strip script blocks before scanning
    content_no_script = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL)

    if not target_cities:
        return ['INFO: No target cities configured — add entries to POLITICS_TARGET_CITIES to enable scanning.']

    panel_splits = re.split(r'(?=<div id="tab-)', content_no_script)
    violations = []

    for chunk in panel_splits:
        id_match = re.search(r'<div id="(tab-[^"]+)"', chunk)
        if not id_match:
            continue
        panel_id = id_match.group(1)
        if panel_id not in target_cities:
            continue
        panel_city = target_cities[panel_id]

        # Entire panel is searchable (no Section 10 exemption)
        searchable = chunk

        for term in search_terms:
            if term.lower() in panel_city.lower() or panel_city.lower() in term.lower():
                continue
            if any(term.lower() in b.lower() or b.lower() in term.lower() for b in BASELINE_CITIES):
                continue

            pos_match = re.search(re.escape(term), searchable, re.IGNORECASE)
            if pos_match:
                pos = pos_match.start()
                ctx = searchable[max(0, pos - 100):pos + 120].replace('\n', ' ').strip()
                violations.append(f"VIOLATION: '{term}' in {panel_city} panel")
                violations.append(f"  ...{ctx}...")
                violations.append("")

    return violations


def main():
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    weather_file = os.path.join(script_dir, 'retirement_weather_template.html')
    politics_file = os.path.join(script_dir, 'retirement_politics_template.html')

    # --- Weather scan ---
    print("=" * 60)
    print("WEATHER FILE SCAN")
    print("=" * 60)
    if os.path.exists(weather_file):
        weather_violations = scan_weather_file(weather_file, WEATHER_TARGET_CITIES, WEATHER_SEARCH_TERMS)
        if weather_violations:
            for v in weather_violations:
                print(v)
        else:
            print("CLEAN — no cross-target-city violations found in sections 1-9.")
    else:
        print(f"File not found: {weather_file}")

    print()

    # --- Politics scan ---
    print("=" * 60)
    print("POLITICS FILE SCAN")
    print("=" * 60)
    if os.path.exists(politics_file):
        politics_violations = scan_politics_file(politics_file, POLITICS_TARGET_CITIES, POLITICS_SEARCH_TERMS)
        if politics_violations:
            for v in politics_violations:
                print(v)
        else:
            print("CLEAN — no cross-target-city violations found.")
    else:
        print(f"File not found: {politics_file}")


if __name__ == '__main__':
    main()
