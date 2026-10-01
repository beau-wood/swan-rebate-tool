# Swan Rebate Tool

This is a single static page (`index.html`) that estimates Energize CT heat pump rebates for a project and lists matching Daikin models from the Energize CT Heat Pump Qualified Product List. It has no backend, makes no fetches, and keeps all its data in two constants at the top of the file.

**To update RULES:** edit the `RULES` array in `index.html` by hand against the current Energize CT pages and rebate forms. Set `verifiedOn` to the date you checked, and keep `sourceUrl` pointing at the page each number came from.

**To update MODELS:**
1. Download the new QPL Excel file from https://energizect.com/HPQPL ("complete list of eligible equipment") to `data/hpqpl.xlsx`. The site blocks scripted downloads, so use a browser.
2. Run `python scripts/hpqpl_to_json.py > data/models.json` (needs pandas and openpyxl).
3. Replace the array between `/*MODELS*/` and `/*END MODELS*/` in `index.html` with the contents of `data/models.json`.

Then run `python scripts/verify.py` (needs Playwright) to re-check the test scenarios. See `NOTES.md` for the column mapping and the open questions.
