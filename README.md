# Field Shift — Mongolia Wheat-Belt Rotation Desk

NASA Space Apps Challenge 2026 · Field Shift: Adapting Farms with NASA Data

A farmer-friendly tool for comparing crop rotations in Mongolia's wheat belt, using
NASA POWER climate data that updates itself every month.

## How the automatic data works

1. `data/locations.json` lists the areas (name, province, latitude, longitude).
2. Once a month, GitHub Actions runs `scripts/power_summary.py`. It downloads daily
   NASA POWER weather (2001 to last year) for each area and works out summer rain,
   dry-year rain, frost-free days, July temperature, spring wind and their ranges.
3. It saves the results to `data/climate.json` and commits the file.
4. The website (`index.html`) loads `data/climate.json` when it opens. If the file
   is missing, it shows saved estimates and says so.

"Use my location" asks NASA POWER directly for the farmer's exact spot. If the
browser blocks that request, the site picks the nearest listed area instead.

## Set up (about 10 minutes, once)

1. Create a new **public** repository on GitHub and upload all these files,
   keeping the folders (`.github/workflows/`, `data/`, `scripts/`).
2. **Settings → Actions → General → Workflow permissions:** choose
   *Read and write permissions* and save.
3. **Actions tab → Update NASA data → Run workflow.** Wait a few minutes until it
   turns green. A new `data/climate.json` appears in the repository.
4. **Settings → Pages:** Source *Deploy from a branch*, branch `main`, folder
   `/ (root)`, save. After a minute your site is live at
   `https://<your-username>.github.io/<repository-name>/`.

The site's header then shows "NASA weather data, updated <date>" with a green dot.

## Add an area

Add a line to `data/locations.json`, for example:

```json
"myarea": { "name": "My area", "aimag": "Selenge", "lat": 49.00, "lon": 106.00 }
```

Then run the workflow again (step 3).

## Data and limits

- NASA POWER: https://power.larc.nasa.gov/ (daily point API, community `AG`).
  Each value covers roughly 55 × 40 km and cannot show differences between fields.
- Crop values (water need, frost-free days needed, soil and income indices) are
  rough classroom estimates for a local agronomist to check.
- The tool does not forecast yields or prices and supports, never replaces,
  farmers' judgment and local expertise.
