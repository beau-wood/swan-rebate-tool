# NOTES

## Questions to take back (for your colleague / Energize CT)

These are also shown as footnotes on the page where they apply.

1. **Commercial rate as of Sep 1, 2026?** The commercial Energy Optimization page headline says "up to $1,750/ton" (ASHP) and "up to $2,500/ton" (VRF), and says $1,650 / $2,250 applied to installs Jan 1–Aug 31, 2026. The 2026 form (Rev. 12/25) and the page's own process list still say $1,650 / $2,250. **The tool uses the lower, written-on-the-form figures ($1,650 / $2,250).** If Energize CT (800-918-9369, CommercialHPRebates@ri-message.com) confirms the higher rates, change `ratePerTon` in RULES.
2. **Do packaged rooftop heat pumps get the commercial ASHP rate?** No separate RTU measure exists. The tool assumes yes, because the QPL lists "Single Packaged Roof Top Units (Commercial Only)" under air source heat pumps.
3. **GSHP efficiency.** The QPL rates ground source by GLHP EER/COP, not IEER, so the tool can't filter GSHP by minimum efficiency and shows no efficiency column. Minimums: 17.1 EER / 3.6 COP brine-to-air; 16.1 EER / 3.0–3.1 COP brine-to-water.
4. **Water source HP:** no Energize CT measure found on the commercial or residential pages, so the tool shows "no incentive". Worth asking whether WSHPs are handled through a custom or new-construction path.
5. **Not covered by this tool:**
   - Express Cool Choice, the commercial ASHP/VRF rebate when *not* displacing fossil fuel, e.g. replacing an existing heat pump.
   - Commercial new construction and major renovation (Energy Conscious Blueprint / New Construction program).
   - Multifamily (has its own pages; pre-approval required).

## Decisions made at the Step 2 gate (Beau, 2026-09-30)

- Residential is low priority. The two reachable residential ASHP rules are kept as drafted. The residential GSHP rule was dropped, because the form always derives `commercial` for GSHP, so the rule could never match.
- Commercial rates: the conservative form figures (above).
- **`fuel` in RULES can be an array**, and `matchRule` uses `r.fuel === "any" || r.fuel.includes(fuel)`. Why: commercial Energy Optimization pays only when replacing oil, propane, gas, or electric resistance, and replacing an existing heat pump gets $0. A single value couldn't say "these four but not heat pump".
- `verifiedOn` = 2026-09-30 (as-of date for all rules).
- **Added a `footnotes` field to rules**, rendered as "Notes" on the result card. (Beau asked for these caveats on the page.)
- **Minimum-efficiency label** reads "EER2" for packaged rooftop units. Those QPL rows carry EER2, not IEER, which is what `ratingFor` already falls back to.

## Sources and access

- energizect.com sits behind a Cloudflare bot challenge (HTTP 403, `cf-mitigated: challenge`) for curl/WebFetch.
  Everything was read through a real Chrome session (Claude in Chrome), per Beau's OK.
- `data/hpqpl.xlsx` = "Click here for a complete list of eligible equipment" on /HPQPL
  → `https://www.energizect.com/media/33396/download`. QPL dated **9/23/26** (Read Me sheet).
- Rebate forms saved in `data/rules/`:
  - `CI_Heat_Pump_Energy_Optimization.pdf` — commercial EO form, 2026, Rev. 12/25 (linked from the commercial EO page; hosted on energizect.my.site.com, the program's Salesforce portal)
  - `1-0458 Resi Energy Optimization Rebate 0926 FILL.pdf` — residential EO, Rev. 09/26 (media/19011)
  - `1-0553 - Heat Pump Rebate_FILLABLE.pdf` — residential ASHP, Rev. 04/26 (media/12241)
  - `1-0276 Ground Source Heat Pump_FILLABLE_0.pdf` — residential GSHP, Rev. 04/26 (media/12236)

### Spec URLs vs. reality (checked 2026-09-30)

| Spec URL | Result |
|---|---|
| `.../heat-pumps/commercial-air-source` | redirects to a **login page** (unpublished) |
| `.../heat-pumps/commercial-energy-optimization` | live — the commercial page now covering ASHP, VRF, and GSHP |
| `.../heat-pumps/ground-source-commercial` | **redirects** to commercial-energy-optimization |
| `.../heat-pumps/ground-source-residential` | live |
| `.../heating-cooling/heat-pumps` (landing) | **404** |
| residential ASHP | found at `.../heat-pumps/residential-air-source`, which points fossil/resistance replacements to `.../heat-pumps/residential-energy-optimization` |

## HPQPL → MODELS column mapping

Brand filter: the brand column contains "daikin" (case-insensitive). Header row = the row containing that brand column name.
`tons` = AHRI cooling capacity ÷ 12,000, rounded to the nearest 0.5 (halves round up).
`capacityRatio17f` = (17°F heating capacity) ÷ (47°F heating capacity), both straight from QPL columns, rounded to 2 dp. It's a derived ratio, not a listed rating, and the page doesn't display it.
Ratings of 0 or blank → null.

| Sheet | Daikin rows | equipment | indoor | model | indoorModel | capacity (→ tons) | seer2 | hspf2 | eer2 | ieer | cop5f |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ASHP < 5.4 Tons | 769 (340 after merging exact dupes) | ashp | Indoor Type | Outdoor Unit Model Number | Indoor Unit Model Number(s) | Cooling Capacity (AFull) - Single or High Stage (95F), btuh | SEER2 | HSPF2 (Region IV) | EER2 (AFull) - Single or High Stage (95F) | — | Heating COP at 5°F as calculated by M1 |
| High Velocity ASHP | **0** | ashp | (fixed: ducted) | | | | | | | | |
| ASHP >= 5.4 Tons | 666 | ashp_large | — → `any` | Outdoor Unit Model Number | Indoor Unit Model Number | Cooling Capacity (95F) | — | — | — (sheet has EER, not EER2) | IEER | — |
| Single Packaged Roof Top Units | 105 | **rtu_hp** (not in spec enum, see below) | Indoor Type | Outdoor Unit Model Number | — | Cooling Capacity (AFull)… (95F), btuh | SEER2 | HSPF2 (Region IV) | EER2 (AFull)… | — | Heating COP at 5°F… |
| Air Source VRF | 944 | vrf | Indoor Type | System Model Number | — | Cooling Capacity (95F) | — | — | — (sheet has EER, not EER2) | IEER | — |
| Ground Source HP | 849 | gshp | — → `any` | Outdoor Unit Model Number | Indoor Unit Model Number(s) | Full Load GLHP Cooling Capacity (Btuh) | — | — | — | — | — |
| Ground Source HP Resi | 1,403 (846 merged into commercial rows) | gshp | — → `any` | Outdoor Unit Model Number | Indoor Unit Model Number(s) | Full Load GLHP Cooling Capacity (Btuh) | — | — | — | — | — |
| Air to Water HPs | 2 — **skipped** (no app category) | | | | | | | | | | |
| Integrated Controls | 10 — **skipped** (controls) | | | | | | | | | | |
| Read Me | — skipped | | | | | | | | | | |

Indoor Type mapping: Centrally-Ducted / Ducted Indoor Units / Mini-Splits(Ducted) → `ducted`; Non-Ducted Indoor Units / Mini-Splits(Non-Ducted) → `ductless`; Mixed Ducted and Non-Ducted Indoor Units → `mixed`.

Total MODELS: 2,964 rows (after dropping GSHP rows without GLHP ratings).

### Things I wasn't sure about (models)

- **RTU sheet → `rtu_hp`.** The spec's enum has no RTU value, but the form has a "Packaged HP rooftop" option. Without this mapping that option could never list models.
- **EER is not EER2.** The VRF, ≥5.4-ton and GSHP sheets report EER (or GLHP EER), not EER2, so `eer2` is null there. VRF and ≥5.4-ton units still filter on IEER. **GSHP models have no rating in the schema at all**, so the minimum-efficiency filter does nothing for GSHP, and the table shows only model and tons.
- **497 residential GSHP rows have no GLHP rating** (water-loop/ground-water ratings only) and are **dropped**. The QPL Read Me says GSHP qualification is based on GLHP ratings. Also, with null tons they would have passed every tonnage filter and buried the real matches. MODELS is now 2,964 rows.
- **Exact duplicates were merged.** Rows identical in every output field (mostly the GSHP commercial/residential overlap) are merged, with both sheet names joined in `sourceSheet`.
- **No "Date No Longer Eligible" date has passed.** Rows dated 1/1/2027 and 1/1/2028 are kept. The script drops a row once its date passes.
- **Same model, multiple rows.** One outdoor model appears once per indoor pairing (and per indoor type for VRF), so the table repeats outdoor models.

## Rules: background on the open questions

- **Commercial "up to" rates conflict with the form and with the page itself.** ASHP: $1,750 "up to" vs. $1,650 (Jan–Aug installs, and the form). VRF: $2,500 "up to" vs. $2,250 (Jan–Aug installs, the form, and the page's own process list). GSHP: $4,000 everywhere.
- **Commercial and residential programs both exclude replacing an existing heat pump** (commercial outright; residential pays only $250/ton for it). The spec's `fuel` is a single value, so a rule with `fuel: "any"` would wrongly pay full rate on a heat-pump replacement. The draft uses arrays.
- **Residential GSHP can't be reached**: the spec derives track from equipment (only `ashp` is residential).
- **Commercial split ASHP can't be reached**: `ashp` always maps to residential.
- **No rule for water source HP.** No WSHP measure is on any of the pages or forms.
- **RTU rule is an inference** from the commercial ASHP measure plus the QPL listing RTUs as an air-source category.
- **Not modeled:**
  - Express Cool Choice, the commercial non-displacing ASHP/VRF rebate (form on energizect.force.com, outside the pages in scope).
  - Commercial new construction (routed to the Energy Conscious Blueprint program).
  - Multifamily.
  - The residential $500 insulation bonus.
  - NEHPA point-of-sale incentives.

## Took longer than expected

- **Cloudflare challenge.** Everything had to go through the browser.
- **Stale spec URLs.** The spec's URLs had moved, redirected or were behind a login.
- **PDF transfer.** Chrome blocked multiple programmatic downloads from one page and the tool output filter blocks base64, so each PDF was downloaded by navigating to it directly.
