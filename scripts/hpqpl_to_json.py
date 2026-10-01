"""Convert the Energize CT Heat Pump Qualified Product List (data/hpqpl.xlsx)
into the MODELS constant used by index.html.

Usage:  python scripts/hpqpl_to_json.py > models.json
        (per-sheet counts go to stderr; the JSON array goes to stdout)

The column-to-field mapping lives in SHEETS below and is documented in NOTES.md.
Every rating comes straight from a QPL column; a field is null when that sheet has
no matching column. Nothing is estimated.
"""
import datetime
import json
import math
import sys
from pathlib import Path

import pandas as pd

XLSX = Path(__file__).resolve().parent.parent / "data" / "hpqpl.xlsx"

# Indoor Type values seen in the QPL -> app indoor category.
INDOOR = {
    "centrally-ducted": "ducted",
    "ducted indoor units": "ducted",
    "mini-splits(ducted)": "ducted",
    "non-ducted indoor units": "ductless",
    "mini-splits(non-ducted)": "ductless",
    "mixed ducted and non-ducted indoor units": "mixed",
}

# Per sheet: equipment category, brand column, and which QPL column feeds each field.
# None = the sheet has no such column -> field is null.
SHEETS = {
    "ASHP < 5.4 Tons": dict(
        equipment="ashp", brand="Brand Name", indoor="Indoor Type",
        model="Outdoor Unit Model Number", indoorModel="Indoor Unit Model Number(s)",
        capacity="Cooling Capacity (AFull) - Single or High Stage (95F), btuh",
        seer2="SEER2", hspf2="HSPF2 (Region IV)",
        eer2="EER2 (AFull) - Single or High Stage (95F)", ieer=None,
        cop5f="Heating COP at 5°F as calculated by M1",
        cap17="Heating Capacity at 17°F as calculated by M1", cap47="Heating Capacity (47F), btuh",
    ),
    "High Velocity ASHP": dict(
        equipment="ashp", brand="Outdoor Unit Brand Name", indoor=None, indoorFixed="ducted",
        model="Outdoor Unit Model Number", indoorModel="Indoor Unit Model Number(s)",
        capacity="Cooling Capacity (AFull) - Single or High Stage (95F), btuh",
        seer2="SEER2", hspf2="HSPF2 (Region IV)", eer2=None, ieer=None,
        cop5f="Heating COP at 5°F as calculated by M1",
        cap17=None, cap47=None,
    ),
    "ASHP >= 5.4 Tons": dict(
        equipment="ashp_large", brand="Brand Name", indoor=None,
        model="Outdoor Unit Model Number", indoorModel="Indoor Unit Model Number",
        capacity="Cooling Capacity (95F)",
        seer2=None, hspf2=None, eer2=None, ieer="IEER", cop5f=None,
        cap17="Heating Capacity at 17°F", cap47="Heating Capacity at 47°F",
    ),
    "Single Packaged Roof Top Units": dict(
        equipment="rtu_hp", brand="Brand Name", indoor="Indoor Type",
        model="Outdoor Unit Model Number", indoorModel=None,
        capacity="Cooling Capacity (AFull) - Single or High Stage (95F), btuh",
        seer2="SEER2", hspf2="HSPF2 (Region IV)",
        eer2="EER2 (AFull) - Single or High Stage (95F)", ieer=None,
        cop5f="Heating COP at 5°F as calculated by M1",
        cap17="Heating Capacity at 17°F as calculated by M1",
        cap47="Heating Capacity (H1Full) - Single or High Stage (47F), btuh",
    ),
    "Air Source VRF": dict(
        equipment="vrf", brand="Outdoor Unit Brand Name", indoor="Indoor Type",
        model="System Model Number", indoorModel=None,
        capacity="Cooling Capacity (95F)",
        seer2=None, hspf2=None, eer2=None, ieer="IEER", cop5f=None,
        cap17="Low Heating Capacity (17F)", cap47="High Heating Capacity (47F)",
    ),
    "Ground Source HP": dict(
        equipment="gshp", brand="Brand Name", indoor=None,
        model="Outdoor Unit Model Number", indoorModel="Indoor Unit Model Number(s)",
        capacity="Full Load GLHP Cooling Capacity (Btuh)",
        seer2=None, hspf2=None, eer2=None, ieer=None, cop5f=None, cap17=None, cap47=None,
    ),
    "Ground Source HP Resi": dict(
        equipment="gshp", brand="Brand Name", indoor=None,
        model="Outdoor Unit Model Number", indoorModel="Indoor Unit Model Number(s)",
        capacity="Full Load GLHP Cooling Capacity (Btuh)",
        seer2=None, hspf2=None, eer2=None, ieer=None, cop5f=None, cap17=None, cap47=None,
    ),
}
SKIPPED_SHEETS = {
    "Read Me": "notes only",
    "Air to Water HPs": "no matching equipment category in the app",
    "Integrated Controls": "controls, not heat pumps",
}


def find_header_row(raw, brand_col):
    for i, row in raw.iterrows():
        if brand_col in [str(v).strip() for v in row.values]:
            return i
    raise ValueError(f"header with {brand_col!r} not found")


def num(v):
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) or f == 0 else f


def text(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    s = str(v).strip()
    return s or None


def round_half(x):
    return math.floor(x * 2 + 0.5) / 2


def expired(v, today):
    if v is None or (isinstance(v, float) and math.isnan(v)) or not str(v).strip() or str(v) == "None":
        return False
    d = pd.to_datetime(v, errors="coerce")
    return not pd.isna(d) and d.date() < today


def main():
    today = datetime.date.today()
    book = pd.read_excel(XLSX, sheet_name=None, header=None, dtype=object)
    models, seen = [], {}
    for sheet, raw in book.items():
        if sheet not in SHEETS:
            print(f"{sheet}: skipped ({SKIPPED_SHEETS.get(sheet, 'unknown sheet')})", file=sys.stderr)
            continue
        cfg = SHEETS[sheet]
        hi = find_header_row(raw, cfg["brand"])
        df = raw.iloc[hi + 1:].copy()
        df.columns = [str(c).strip() for c in raw.iloc[hi].values]
        col = lambda key: df[cfg[key]] if cfg.get(key) else None  # noqa: E731
        for key in ("brand", "model", "capacity", "indoor", "indoorModel", "seer2", "hspf2",
                    "eer2", "ieer", "cop5f", "cap17", "cap47"):
            if cfg.get(key) and cfg[key] not in df.columns:
                raise KeyError(f"{sheet}: column {cfg[key]!r} missing")
        daikin = df[df[cfg["brand"]].astype(str).str.contains("daikin", case=False, na=False)]
        n_expired = 0
        n_dup = 0
        n_no_glhp = 0
        for _, r in daikin.iterrows():
            if "Date No Longer Eligible" in df.columns and expired(r["Date No Longer Eligible"], today):
                n_expired += 1
                continue
            get = lambda key: r[cfg[key]] if cfg.get(key) else None  # noqa: E731
            cap = num(get("capacity"))
            # GSHP qualification is based on AHRI ground-loop (GLHP) ratings (QPL Read Me, note 7).
            # Rows with only water-loop / ground-water ratings have no GLHP capacity: not a qualifying GSHP.
            if cfg["equipment"] == "gshp" and not cap:
                n_no_glhp += 1
                continue
            c17, c47 = num(get("cap17")), num(get("cap47"))
            if cfg.get("indoor"):
                indoor = INDOOR.get((text(get("indoor")) or "").lower(), "any")
            else:
                indoor = cfg.get("indoorFixed", "any")
            m = {
                "brand": "Daikin",
                "model": text(get("model")),
                "indoorModel": text(get("indoorModel")),
                "equipment": cfg["equipment"],
                "indoor": indoor,
                "tons": round_half(cap / 12000) if cap else None,
                "seer2": num(get("seer2")),
                "hspf2": num(get("hspf2")),
                "eer2": num(get("eer2")),
                "ieer": num(get("ieer")),
                "cop5f": num(get("cop5f")),
                "capacityRatio17f": round(c17 / c47, 2) if c17 and c47 else None,
                "hpqpl": True,
                "sourceSheet": sheet,
            }
            # The commercial and residential GSHP sheets list many identical units; keep one
            # row and record both sheets.
            key = json.dumps({k: v for k, v in m.items() if k != "sourceSheet"}, sort_keys=True)
            if key in seen:
                prev = seen[key]
                if sheet not in prev["sourceSheet"]:
                    prev["sourceSheet"] += "; " + sheet
                n_dup += 1
                continue
            seen[key] = m
            models.append(m)
        print(f"{sheet}: {len(daikin)} Daikin rows, {n_expired} past 'Date No Longer Eligible', "
              f"{n_dup} exact duplicates merged, {n_no_glhp} GSHP rows without GLHP rating dropped", file=sys.stderr)
    models.sort(key=lambda m: (m["equipment"], m["tons"] or 0, m["model"] or ""))
    print(f"total MODELS: {len(models)}", file=sys.stderr)
    print("[\n" + ",\n".join(json.dumps(m, ensure_ascii=False) for m in models) + "\n]")


if __name__ == "__main__":
    main()
