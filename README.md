# dupr-heatmap

Interactive SoCal pickleball DUPR player heatmap. Filter by DUPR rating and age, click cities to see players, search by name.

Live at: https://dupr.pickle-play-bot.xyz

---

## Project structure

```
dupr-heatmap/
├── public/                   # Static site — this is what gets deployed
│   ├── index.html            # The map app
│   └── data/
│       ├── city_data.json    # Players grouped by city with lat/lng (generated)
│       └── all_players.json  # Flat player list for search autocomplete (generated)
├── scripts/
│   ├── fetch_dupr.py         # Opens browser, lets you log in, auto-scrolls + saves HTML
│   ├── scrape.py             # Parses HTML export → merges into DB → rebuilds JSON
│   └── players_db.csv        # Versioned player database — source of truth (commit this)
├── deploy/
│   ├── deploy.sh             # rsync public/ to your droplet
│   └── nginx.conf            # Reference only — site uses Caddy
└── .venv/                    # Python virtual environment (not committed)
```

---

## First-time Python setup

Run this once from the project root:

```bash
cd ~/Desktop/pickle-bot/dupr-heatmap

python3 -m venv .venv
source .venv/bin/activate

pip install playwright beautifulsoup4 pandas
playwright install chromium
```

> **Every new terminal session:** run `source .venv/bin/activate` before using any scripts.

---

## How the data pipeline works

```
fetch_dupr.py         →   dupr_export_TIMESTAMP.html
      ↓
scrape.py             →   players_db.csv  (versioned, keyed by DUPR ID)
      ↓                          ↓
                        city_data.json + all_players.json
                                   ↓
                             deploy.sh
                                   ↓
                          dupr.pickle-play-bot.xyz
```

**`players_db.csv`** is the source of truth. Every player ever scraped lives here with the date their data was last seen. Each run merges new data in — existing players get updated scores and timestamps, new players get added, and players not in the latest scrape are preserved from previous runs.

Columns: `id, name, score, location, age_gender, last_scraped`

- `id` — the 6-character DUPR ID (e.g. `LWPRRJ`). Used to match players across scrapes.
- `last_scraped` — ISO date of the most recent scrape that included this player, or `manual` for manually added players.

---

## Regular update workflow

### Step 1 — Fetch fresh HTML from DUPR

```bash
source .venv/bin/activate
python scripts/fetch_dupr.py
```

This opens a real Chrome window. Log in to DUPR, apply your filters, then press Enter in the terminal. The script scrolls through all players automatically and saves a timestamped HTML file to `scripts/`.

**Filters to apply on DUPR:**
- Location: Irvine, CA, USA · 100 mi
- Gender: Men
- Type: Doubles
- DUPR rating: 4–8
- Age: 19–50

Alternatively, do it manually:
1. Go to [dashboard.dupr.com/dashboard/browse/players](https://dashboard.dupr.com/dashboard/browse/players) and apply the filters above
2. In Chrome DevTools console: `copy(document.documentElement.outerHTML)`
3. Paste into a text editor, save as e.g. `scripts/fresh.html`

### Step 2 — Parse and merge into the database

```bash
python scripts/scrape.py scripts/dupr_export_TIMESTAMP.html
```

This will:
- Parse all players from the HTML
- Merge into `players_db.csv` — new players added, existing players updated with fresh score + today's date
- Rebuild `public/data/city_data.json` and `public/data/all_players.json`
- Print a summary of how many players were added vs updated

### Step 3 — Deploy

```bash
./deploy/deploy.sh
```

### Step 4 — Commit

```bash
git add .
git commit -m "update player data $(date +%Y-%m-%d)"
git push
```

---

## Manually adding players

Some players don't appear in DUPR scrape results (e.g. your own account). Add them
to the `MANUAL_PLAYERS` list at the top of `scripts/scrape.py`:

```python
MANUAL_PLAYERS = [
    {"id": "MANUAL_EVAN", "name": "Evan Su", "score": 4.173, "age": 37,
     "location": "Torrance, CA, US", "age_gender": "37 • M"},
]
```

Use a unique fake ID prefixed with `MANUAL_` so they're never confused with real DUPR IDs and never overwritten by a scrape. These are injected into the DB with `last_scraped: manual`.

---

## Adding new cities

If the scraper warns about missing coordinates, add them to the `COORDS` dict in `scripts/scrape.py`:

```python
"City Name": (latitude, longitude),
```

Use Google Maps or https://www.latlong.net to find coordinates.

---

## Server setup (DigitalOcean + Porkbun)

The site runs on a DigitalOcean droplet at `67.205.139.219` using **Caddy** for automatic HTTPS.

### Caddy config (`/etc/caddy/Caddyfile` on the droplet)

```
dupr.pickle-play-bot.xyz {
    root * /var/www/dupr-heatmap
    file_server
    encode gzip
}
```

### DNS (Porkbun)

A record: `dupr` → `67.205.139.219`

### Web root ownership

```bash
sudo mkdir -p /var/www/dupr-heatmap
sudo chown bot:bot /var/www/dupr-heatmap
```

### deploy.sh settings

```bash
DROPLET_IP="67.205.139.219"
DROPLET_USER="bot"
REMOTE_PATH="/var/www/dupr-heatmap"
```