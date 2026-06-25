# dupr-heatmap

Interactive SoCal pickleball DUPR player heatmap. Filter by DUPR rating and age, click cities to see players, search by name.

## Project structure

```
dupr-heatmap/
├── public/              # Static site — this is what gets deployed
│   ├── index.html       # The map app
│   └── data/
│       ├── city_data.json    # Players grouped by city with lat/lng
│       └── all_players.json  # Flat player list for search autocomplete
├── scripts/
│   ├── fetch_dupr.py    # Opens browser, logs in, scrolls + saves HTML
│   ├── scrape.py        # Parses a DUPR HTML export → updates data/
│   └── socal_results.csv    # Last scraped raw data (for reference)
├── deploy/
│   ├── deploy.sh        # rsync public/ to your droplet
│   └── nginx.conf       # Nginx site config (reference only — site uses Caddy)
└── .venv/               # Python virtual environment (not committed)
```

---

## First-time Python setup

The scripts require a virtual environment. Run this once from the project root:

```bash
cd ~/Desktop/pickle-bot/dupr-heatmap

python3 -m venv .venv
source .venv/bin/activate

pip install playwright beautifulsoup4 pandas
playwright install chromium
```

> **Every new terminal session:** run `source .venv/bin/activate` before using any scripts.

---

## Updating the data

This is the regular workflow once everything is set up.

### Option A — automated (recommended)

```bash
source .venv/bin/activate
python scripts/fetch_dupr.py
```

This opens a real Chrome window. Log in to DUPR, make sure your filters are set
(location: Irvine CA, 100mi, Men, Doubles, DUPR 4–8, Age 19–50), then press Enter
in the terminal. The script scrolls through all players automatically and saves a
timestamped HTML file to `scripts/`.

### Option B — manual

1. Go to [dashboard.dupr.com/dashboard/browse/players](https://dashboard.dupr.com/dashboard/browse/players), apply your filters
2. In Chrome DevTools console: `copy(document.documentElement.outerHTML)`
3. Paste into a text editor and save as e.g. `fresh.html`

### Then parse + deploy

```bash
# Parse the HTML → updates public/data/*.json
python scripts/scrape.py scripts/dupr_export_TIMESTAMP.html

# Deploy to the live site
./deploy/deploy.sh

# Commit
git add .
git commit -m "update player data"
git push
```

---

## Server setup (DigitalOcean + Porkbun)

The site runs on a DigitalOcean droplet at `67.205.139.219` using **Caddy** (not Nginx)
for HTTPS. It's served at `dupr.pickle-play-bot.xyz`.

### Caddy config (on the droplet)

```
dupr.pickle-play-bot.xyz {
    root * /var/www/dupr-heatmap
    file_server
    encode gzip
}
```

Added to `/etc/caddy/Caddyfile` alongside the other sites. Caddy handles HTTPS automatically.

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

---

## Manually adding players

Some players don't appear in DUPR scrape results (e.g. your own account). Add them
to the `MANUAL_PLAYERS` list at the top of `scripts/scrape.py`:

```python
MANUAL_PLAYERS = [
    {"name": "Evan Su", "score": 4.173, "age": 37, "city": "Torrance"},
    {"name": "Another Player", "score": 4.5, "age": 25, "city": "Irvine"},
]
```

These are injected automatically every time `scrape.py` runs. If a player from
`MANUAL_PLAYERS` ever shows up in the scraped data, they won't be duplicated.

---

## Adding new cities

If the scraper warns about missing coordinates, add them to the `COORDS` dict in `scripts/scrape.py`:

```python
"City Name": (latitude, longitude),
```

Use Google Maps or https://www.latlong.net to find coordinates.
