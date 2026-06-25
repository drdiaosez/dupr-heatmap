#!/usr/bin/env python3
"""
DUPR heatmap scraper.

Usage:
    python scrape.py <path_to_html_file>

Flow:
    1. Parse the HTML export
    2. Merge into players_db.csv (versioned, keyed by DUPR ID)
       - New players are added
       - Existing players are updated if the new scrape is more recent
    3. Rebuild public/data/city_data.json and all_players.json from the DB

Outputs:
    scripts/players_db.csv         — versioned player database (commit this)
    public/data/city_data.json
    public/data/all_players.json
"""

import sys
import json
import time
import urllib.request
import urllib.parse
import pandas as pd
from pathlib import Path
from datetime import date
from bs4 import BeautifulSoup

# ── Paths ─────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent
DATA_DIR    = SCRIPT_DIR.parent / "public" / "data"
DB_PATH      = SCRIPT_DIR / "players_db.csv"
CITIES_PATH  = SCRIPT_DIR / "cities.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Manually added players (keyed by fake ID, won't be overwritten) ───────
MANUAL_PLAYERS = [
    {"id": "MANUAL_EVAN", "name": "Evan Su", "score": 4.173, "age": 37,
     "location": "Torrance, CA, US", "age_gender": "37 • M"},
]

# ── City coordinates — loaded from cities.json ───────────────────────────
def load_coords() -> dict:
    if CITIES_PATH.exists():
        with open(CITIES_PATH) as f:
            data = json.load(f)
        return {city: (v["lat"], v["lng"]) for city, v in data.items()}
    return {}


def geocode_city(city: str):
    """Look up lat/lng using OpenStreetMap Nominatim (free, no API key needed)."""
    query = urllib.parse.urlencode({"q": f"{city}, California, USA", "format": "json", "limit": 1})
    url = f"https://nominatim.openstreetmap.org/search?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "dupr-heatmap/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            results = json.loads(resp.read())
        if results:
            return (float(results[0]["lat"]), float(results[0]["lon"]))
    except Exception as e:
        print(f"    Geocode error for {city}: {e}")
    return None


def save_coords(coords: dict):
    out = {city: {"lat": lat, "lng": lng} for city, (lat, lng) in sorted(coords.items())}
    with open(CITIES_PATH, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)


DB_COLUMNS = ["id", "name", "score", "location", "age_gender", "last_scraped"]


# ── Step 1: Parse HTML ────────────────────────────────────────────────────
def scrape_html(html_path: str) -> pd.DataFrame:
    print(f"Parsing {html_path} ...")
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    container = soup.select_one("div.flex.flex-col.gap-y-2.mt-6")
    if not container:
        print("ERROR: Could not find row container in HTML.")
        sys.exit(1)

    rows = container.find_all("div", recursive=False)
    print(f"Found {len(rows)} rows.")

    results = []
    for row in rows:
        name_span  = row.select_one("div.flex.flex-col > div > span.text-navy-900:not(.text-opacity-50)")
        code_span  = row.select_one("span.text-navy-900.text-opacity-50.hidden")
        score_span = row.select_one("div.flex.gap-x-1.items-center > div:nth-child(1) > span")
        loc_span   = row.select_one("span.text-xs.font-normal.text-navy-900.text-opacity-80")
        ag_span    = row.select_one("span.text-xs.font-normal.text-navy-900.text-opacity-60")
        name  = name_span.get_text(strip=True)  if name_span  else None
        code  = code_span.get_text(strip=True)  if code_span  else None
        score = score_span.get_text(strip=True) if score_span else None
        loc   = loc_span.get_text(strip=True)   if loc_span   else None
        ag    = ag_span.get_text(strip=True)    if ag_span    else None
        if (name or score) and code:
            results.append({"id": code, "name": name, "score": score,
                            "location": loc, "age_gender": ag})

    df = pd.DataFrame(results)
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["last_scraped"] = date.today().isoformat()
    return df


# ── Step 2: Merge into versioned DB ──────────────────────────────────────
def merge_into_db(new_df: pd.DataFrame) -> pd.DataFrame:
    today = date.today().isoformat()

    # Load existing DB or create empty one
    if DB_PATH.exists():
        db = pd.read_csv(DB_PATH, dtype={"id": str})
        print(f"Loaded existing DB: {len(db)} players")
    else:
        db = pd.DataFrame(columns=DB_COLUMNS)
        print("Creating new players_db.csv")

    # Add manual players if not already in DB
    manual_ids = {p["id"] for p in MANUAL_PLAYERS}
    for p in MANUAL_PLAYERS:
        if p["id"] not in db["id"].values:
            db = pd.concat([db, pd.DataFrame([{
                "id":           p["id"],
                "name":         p["name"],
                "score":        p["score"],
                "location":     p["location"],
                "age_gender":   p["age_gender"],
                "last_scraped": "manual",
            }])], ignore_index=True)

    # Merge: update existing rows, append new ones
    added = updated = 0
    new_df = new_df.dropna(subset=["id"])

    for _, row in new_df.iterrows():
        pid = row["id"]
        if pid in manual_ids:
            continue  # never overwrite manual players
        mask = db["id"] == pid
        if mask.any():
            # Update existing — always take the new scrape as more recent
            db.loc[mask, "name"]         = row["name"]
            db.loc[mask, "score"]        = row["score"]
            db.loc[mask, "location"]     = row["location"]
            db.loc[mask, "age_gender"]   = row["age_gender"]
            db.loc[mask, "last_scraped"] = today
            updated += 1
        else:
            db = pd.concat([db, pd.DataFrame([{
                "id":           pid,
                "name":         row["name"],
                "score":        row["score"],
                "location":     row["location"],
                "age_gender":   row["age_gender"],
                "last_scraped": today,
            }])], ignore_index=True)
            added += 1

    print(f"  {added} new players added, {updated} updated")
    db.to_csv(DB_PATH, index=False)
    print(f"  DB saved → {DB_PATH} ({len(db)} total players)")
    return db


# ── Step 3: Build public JSON outputs from DB ─────────────────────────────
def build_outputs(db: pd.DataFrame):
    db = db.copy()
    db["score"] = pd.to_numeric(db["score"], errors="coerce")
    db["city"]  = db["location"].str.split(",").str[0].str.strip().fillna("Unknown").replace("", "Unknown")
    db["age"]   = db["age_gender"].str.extract(r"^(\d+)").astype(float)

    # all_players.json — flat list for search (everyone, including no-city)
    all_players = []
    for _, row in db.iterrows():
        if pd.notna(row["score"]):
            all_players.append({
                "name":         row["name"],
                "score":        round(float(row["score"]), 3),
                "age":          int(row["age"]) if pd.notna(row["age"]) else None,
                "city":         row["city"],
                "last_scraped": row["last_scraped"],
            })
    all_players.sort(key=lambda x: x["name"].lower())

    # city_data.json — grouped by city with coords
    city_df = db[db["city"] != "Unknown"].copy()
    city_players: dict = {}
    for city, group in city_df.groupby("city"):
        players = group.sort_values("score", ascending=False)[["name", "score", "age"]].values.tolist()
        city_players[city] = [
            [p[0], round(float(p[1]), 3) if pd.notna(p[1]) else None,
             int(p[2]) if pd.notna(p[2]) else None]
            for p in players
        ]

    # Auto-geocode any cities not yet in cities.json
    coords = load_coords()
    missing = [c for c in city_players if c not in coords]
    if missing:
        print(f"\nGeocoding {len(missing)} new cities...")
        for city in sorted(missing):
            print(f"  Looking up: {city}...", end=" ", flush=True)
            result = geocode_city(city)
            if result:
                coords[city] = result
                print(f"\u2192 {result[0]:.4f}, {result[1]:.4f}")
            else:
                print("\u2192 not found, skipping")
            time.sleep(1.1)  # Nominatim rate limit: 1 req/sec
        save_coords(coords)
        print(f"  cities.json updated ({len(coords)} cities total)")

    city_data = []
    for city, players in city_players.items():
        if city in coords:
            lat, lng = coords[city]
            city_data.append({"city": city, "lat": lat, "lng": lng, "players": players})
        else:
            print(f"  Skipping {city} ({len(players)} players) — could not geocode")
    # Write outputs
    with open(DATA_DIR / "city_data.json", "w", encoding="utf-8") as f:
        json.dump(city_data, f)
    with open(DATA_DIR / "all_players.json", "w", encoding="utf-8") as f:
        json.dump(all_players, f)

    total_mapped = sum(len(c["players"]) for c in city_data)
    valid_scores = db["score"].dropna()
    print(f"\nDone!")
    print(f"  Total in DB:    {len(db)}")
    print(f"  Cities mapped:  {len(city_data)}")
    print(f"  Players mapped: {total_mapped}")
    print(f"  Score range:    {valid_scores.min():.3f} – {valid_scores.max():.3f}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scrape.py <path_to_html_file>")
        sys.exit(1)
    new_df = scrape_html(sys.argv[1])
    db     = merge_into_db(new_df)
    build_outputs(db)
