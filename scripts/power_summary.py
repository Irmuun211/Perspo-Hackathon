"""
Field Shift: download NASA POWER data and write data/climate.json for the website.

Runs automatically every month through GitHub Actions
(.github/workflows/update-nasa-data.yml). You can also run it yourself:

    pip install requests
    python scripts/power_summary.py

It reads the areas in data/locations.json, downloads DAILY NASA POWER
Agroclimatology (community=AG) data from 2001 to the last complete year,
and saves the summary numbers the site uses. To add an area, add a line to
data/locations.json; the next run includes it.
"""
import datetime
import json
import pathlib
import statistics
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOCATIONS_FILE = ROOT / "data" / "locations.json"
OUTPUT_FILE = ROOT / "data" / "climate.json"

START = 2001
END = datetime.date.today().year - 1          # last complete year
PARAMS = "PRECTOTCORR,T2M,T2M_MIN,WS2M"
URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


def fetch(lat, lon, tries=3):
    for attempt in range(tries):
        try:
            r = requests.get(URL, params={
                "parameters": PARAMS, "community": "AG", "latitude": lat, "longitude": lon,
                "start": f"{START}0101", "end": f"{END}1231", "format": "JSON",
            }, timeout=300)
            r.raise_for_status()
            js = r.json()
            return js["properties"]["parameter"], js["geometry"]["coordinates"][2]
        except (requests.RequestException, KeyError, ValueError) as e:
            if attempt == tries - 1:
                raise
            print(f"  retrying after error: {e}")
            time.sleep(20)


def valid(v):
    return v is not None and v > -900                 # NASA POWER fill value is -999


def summarize(p):
    summer_rain, ffd, july_t, wind = [], [], [], []
    for y in range(START, END + 1):
        days = sorted(k for k in p["T2M_MIN"] if k.startswith(str(y)))
        jja = [p["PRECTOTCORR"][d] for d in days if d[4:6] in ("06", "07", "08")]
        if len(jja) >= 90 and all(valid(v) for v in jja):
            summer_rain.append(sum(jja))
        # Frost-free window: last day T2M_MIN <= 0 before 1 Jul -> first day <= 0 from 1 Jul
        tmin = [(d, p["T2M_MIN"][d]) for d in days if valid(p["T2M_MIN"][d])]
        spring = [i for i, (d, v) in enumerate(tmin) if d[4:] < "0701" and v <= 0]
        autumn = [i for i, (d, v) in enumerate(tmin) if d[4:] >= "0701" and v <= 0]
        if spring and autumn:
            ffd.append(autumn[0] - spring[-1] - 1)
        jul = [p["T2M"][d] for d in days if d[4:6] == "07" and valid(p["T2M"][d])]
        if jul:
            july_t.append(statistics.mean(jul))
        am = [p["WS2M"][d] for d in days if d[4:6] in ("04", "05") and valid(p["WS2M"][d])]
        if am:
            wind.append(statistics.mean(am))
    return {
        "summerRain": round(statistics.mean(summer_rain)),
        "dryRain": round(statistics.quantiles(summer_rain, n=4)[0]),
        "ffd": round(statistics.mean(ffd)),
        "julyT": round(statistics.mean(july_t), 1),
        "springWind": round(statistics.mean(wind), 1),
        "rainMin": round(min(summer_rain)), "rainMax": round(max(summer_rain)),
        "ffdMin": min(ffd), "ffdMax": max(ffd),
        "yearsUsed": len(summer_rain),
    }


def main():
    places = json.loads(LOCATIONS_FILE.read_text(encoding="utf-8"))
    out = {
        "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "source": "NASA POWER daily point API, community AG",
        "period": {"start": START, "end": END},
        "locations": {},
    }
    for key, info in places.items():
        print(f"Downloading {info['name']} ({info['lat']}, {info['lon']}) ...")
        p, elev = fetch(info["lat"], info["lon"])
        s = summarize(p)
        print(f"  {s['yearsUsed']} complete years, summer rain {s['summerRain']} mm, frost-free {s['ffd']} d")
        out["locations"][key] = {**info, "elev": round(elev), **s}
    OUTPUT_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
