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
│   ├── scrape.py        # Parses a DUPR HTML export → updates data/
│   └── socal_results.csv    # Last scraped raw data (for reference)
└── deploy/
    ├── deploy.sh        # rsync public/ to your droplet
    └── nginx.conf       # Nginx site config
```

---

## Updating the data

1. Go to DUPR, filter to your region, save the page:
   - In Chrome DevTools console: `copy(document.documentElement.outerHTML)`
   - Paste into a text editor, save as e.g. `fresh.html`

2. Run the scraper:
   ```bash
   cd scripts
   pip install beautifulsoup4 pandas   # first time only
   python scrape.py /path/to/fresh.html
   ```

3. This overwrites `public/data/city_data.json` and `public/data/all_players.json`.

4. Deploy (see below).

---

## First-time server setup (DigitalOcean + Porkbun)

### 1. Create a droplet
- Ubuntu 22.04 LTS, any size (the $6/mo basic is fine)
- Add your SSH key during creation

### 2. Point your Porkbun domain to the droplet
In Porkbun DNS settings, add:
- **A record**: `@` → your droplet IP
- **A record**: `www` → your droplet IP
- (DNS propagation takes up to 30 min)

### 3. SSH into the droplet and install Nginx
```bash
ssh root@YOUR_DROPLET_IP

apt update && apt install -y nginx certbot python3-certbot-nginx

# Create the web root
mkdir -p /var/www/dupr-heatmap
```

### 4. Configure Nginx
```bash
# From your local machine:
scp deploy/nginx.conf root@YOUR_DROPLET_IP:/etc/nginx/sites-available/dupr-heatmap

# On the droplet:
ln -s /etc/nginx/sites-available/dupr-heatmap /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

Edit `nginx.conf` first — replace `yourdomain.com` with your actual domain.

### 5. Deploy the site
```bash
# Edit deploy/deploy.sh — set DROPLET_IP to your droplet's IP
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

### 6. Enable HTTPS (free via Let's Encrypt)
```bash
# On the droplet:
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```
Then uncomment the HTTPS block in `nginx.conf` and reload Nginx.

---

## Updating the live site

```bash
# 1. Scrape new data
python scripts/scrape.py /path/to/new_export.html

# 2. Push to server
./deploy/deploy.sh
```

That's it — no build step, no npm, just static files.

---

## Adding new cities

If the scraper warns about missing coordinates, add them to the `COORDS` dict in `scripts/scrape.py`:

```python
"City Name": (latitude, longitude),
```

Use Google Maps or https://www.latlong.net to find coordinates.
