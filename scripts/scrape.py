#!/usr/bin/env python3
"""
DUPR heatmap scraper.

Usage:
    python scrape.py <path_to_html_file>

Outputs:
    ../public/data/city_data.json
    ../public/data/all_players.json
    socal_results.csv  (alongside this script, for reference)
"""

import sys
import json
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup

# ── Paths ─────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).parent
DATA_DIR    = SCRIPT_DIR.parent / "public" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── City coordinates ──────────────────────────────────────────────────────
COORDS = {
    "Agoura Hills":(34.1364,-118.7617),"Alhambra":(34.0953,-118.127),"Aliso Viejo":(33.5676,-117.7267),
    "Altadena":(34.190,-118.1314),"Anaheim":(33.8353,-117.9145),"Arcadia":(34.1397,-118.0353),
    "Azusa":(34.1336,-117.9075),"Baldwin Park":(34.0853,-117.9606),"Beaumont":(33.9294,-116.9772),
    "Bell":(33.977,-118.1867),"Bell Canyon":(34.1997,-118.7289),"Bell Gardens":(33.9653,-118.1514),
    "Bellflower":(33.8817,-118.117),"Bermuda Dunes":(33.7436,-116.2928),"Beverly Hills":(34.0736,-118.4004),
    "Bonita":(32.6628,-117.0317),"Brea":(33.9167,-117.9006),"Buena Park":(33.8669,-117.9981),
    "Burbank":(34.1808,-118.3089),"Calabasas":(34.1513,-118.6601),"Calimesa":(34.0,-117.0642),
    "Camarillo":(34.2158,-119.0375),"Canyon Lake":(33.6847,-117.2703),"Carlsbad":(33.1581,-117.3506),
    "Carpinteria":(34.3994,-119.5083),"Carson":(33.8317,-118.282),"Casa de Oro-Mount Helix":(32.7653,-116.9547),
    "Cathedral City":(33.7797,-116.4653),"Cerritos":(33.8583,-118.0647),"Cherry Valley":(33.9742,-116.9775),
    "Chino":(34.0122,-117.6889),"Chino Hills":(33.9908,-117.7228),"Chula Vista":(32.6401,-117.0842),
    "Claremont":(34.0997,-117.7198),"Compton":(33.8958,-118.2201),"Corona":(33.8753,-117.5664),
    "Coronado":(32.6859,-117.1831),"Costa Mesa":(33.6645,-117.9059),"Coto de Caza":(33.5964,-117.5892),
    "Covina":(34.09,-117.8883),"Culver City":(34.0211,-118.3964),"Cypress":(33.8169,-118.0375),
    "Dana Point":(33.4697,-117.6981),"Del Mar":(32.9595,-117.2714),"Diamond Bar":(33.9994,-117.81),
    "Downey":(33.9401,-118.1331),"Eastvale":(33.9628,-117.583),"El Cajon":(32.7948,-116.9625),
    "El Monte":(34.0686,-118.0275),"El Segundo":(33.9192,-118.4165),"Encinitas":(33.0369,-117.292),
    "Escondido":(33.1192,-116.9739),"Fallbrook":(33.3736,-117.152),"Fontana":(34.0922,-117.435),
    "Fountain Valley":(33.7092,-117.9536),"French Valley":(33.5928,-117.0819),"Fullerton":(33.8703,-117.9242),
    "Garden Grove":(33.7783,-117.9311),"Gardena":(33.8883,-118.3089),"Glendale":(34.1425,-118.2551),
    "Glendora":(34.1361,-117.8653),"Hacienda Heights":(33.9933,-117.9692),"Hawthorne":(33.9164,-118.3526),
    "Helendale":(34.7397,-117.3339),"Hemet":(33.7475,-116.9719),"Hermosa Beach":(33.8622,-118.3995),
    "Hesperia":(34.4264,-117.3009),"Hidden Hills":(34.1611,-118.6603),"HUNTINGTN BCH":(33.6603,-117.9992),
    "Huntington Beach":(33.6603,-117.9992),"Indio":(33.7206,-116.2156),"Inglewood":(33.9617,-118.3531),
    "Irvine":(33.6846,-117.8265),"Jurupa Valley":(33.9972,-117.4855),
    "La Cañada Flintridge":(34.1997,-118.2003),"La Crescenta-Montrose":(34.2319,-118.2356),
    "La Habra":(33.9319,-117.9461),"La Mesa":(32.7678,-117.0228),"La Mirada":(33.9172,-118.012),
    "La Palma":(33.8464,-118.0467),"La Quinta":(33.6633,-116.31),"La Verne":(34.1008,-117.7681),
    "Ladera Ranch":(33.5592,-117.6328),"Laguna Beach":(33.5422,-117.7831),"Laguna Hills":(33.6028,-117.6931),
    "Laguna Niguel":(33.5225,-117.705),"Laguna Woods":(33.6097,-117.7253),"Lake Elsinore":(33.6681,-117.3273),
    "Lake Forest":(33.6469,-117.6892),"Lakeside":(32.8578,-116.9225),"Lakewood":(33.8536,-118.1339),
    "Lancaster":(34.6868,-118.1542),"Loma Linda":(34.0483,-117.2736),"Long Beach":(33.7701,-118.1937),
    "Los Angeles":(34.0522,-118.2437),"Los Angeles County":(34.0522,-118.2437),
    "Lynwood":(33.9303,-118.2117),"Malibu":(34.0259,-118.7798),"Manhattan Beach":(33.8847,-118.4109),
    "Marina del Rey":(33.9806,-118.4517),"Menifee":(33.6908,-117.1611),"Mission Viejo":(33.6217,-117.6711),
    "Monrovia":(34.1442,-117.9981),"Montclair":(34.0775,-117.6897),"Montebello":(34.0153,-118.1134),
    "Montecito":(34.4361,-119.6353),"Monterey Park":(34.0633,-118.1228),"Moorpark":(34.2858,-118.8814),
    "Moreno Valley":(33.9425,-117.2297),"Murrieta":(33.5539,-117.2139),"National City":(32.6781,-117.0992),
    "Newport Beach":(33.6189,-117.9289),"Norco":(33.9311,-117.5489),"North Tustin":(33.7614,-117.7942),
    "Norwalk":(33.9022,-118.0814),"Nuevo":(33.8017,-117.1497),"Oak Park":(34.1811,-118.7617),
    "Oceanside":(33.1959,-117.3795),"Ojai":(34.4481,-119.2428),"Ontario":(34.0633,-117.6509),
    "Orange":(33.7879,-117.8531),"Orange County":(33.7175,-117.8311),"Oxnard":(34.1975,-119.1771),
    "Palm Desert":(33.7225,-116.3753),"Palm Springs":(33.8303,-116.5453),"Palmdale":(34.5794,-118.1165),
    "Palos Verdes Estates":(33.7867,-118.3928),"Pasadena":(34.1478,-118.1445),"Perris":(33.7825,-117.2286),
    "Pico Rivera":(33.9831,-118.0967),"Placentia":(33.8722,-117.8703),"Pomona":(34.0553,-117.7522),
    "Poway":(32.9628,-117.0359),"Ramona":(33.0422,-116.8731),"Rancho Bernardo":(33.015,-117.0736),
    "Rancho Cucamonga":(34.1064,-117.5931),"Rancho Mirage":(33.7397,-116.4122),
    "Rancho Mission Viejo":(33.5017,-117.6125),"Rancho Palos Verdes":(33.7444,-118.387),
    "Rancho Santa Margarita":(33.6408,-117.6022),"Redlands":(34.0556,-117.1825),
    "Redondo Beach":(33.8492,-118.3884),"Riverside":(33.9533,-117.3961),
    "Rolling Hills Estates":(33.7875,-118.3578),"Rosemead":(34.0803,-118.0728),
    "Rowland Heights":(33.9764,-117.9056),"Running Springs":(34.2086,-117.1086),
    "San Bernardino":(34.1083,-117.2898),"San Bernardino County":(34.1083,-117.2898),
    "San Clemente":(33.4269,-117.6111),"San Diego":(32.7157,-117.1611),
    "San Diego County":(32.9595,-116.9739),"San Dimas":(34.1067,-117.8089),
    "San Gabriel":(34.0961,-118.1058),"San Juan Capistrano":(33.5017,-117.6625),
    "San Marcos":(33.1434,-117.1661),"San Ysidro":(32.5544,-117.0428),
    "Santa Ana":(33.7455,-117.8678),"Santa Barbara":(34.4208,-119.6982),
    "Santa Clarita":(34.3917,-118.5426),"Santa Monica":(34.0195,-118.4912),
    "Santa Paula":(34.3542,-119.0597),"Santa Rosa Valley":(34.2456,-118.9011),
    "Santee":(32.8386,-116.9739),"Seal Beach":(33.7414,-118.1047),"Sierra Madre":(34.1619,-118.0528),
    "Signal Hill":(33.8047,-118.167),"Simi Valley":(34.2694,-118.7814),
    "Solana Beach":(32.9595,-117.2653),"South Gate":(33.9547,-118.212),
    "South Pasadena":(34.1161,-118.1303),"Spring Valley":(32.745,-116.9994),
    "Stanton":(33.8025,-118.0003),"Sun Valley":(34.2175,-118.3781),"Temecula":(33.4936,-117.1484),
    "Temple City":(34.1022,-118.0583),"Thousand Oaks":(34.1706,-118.8376),
    "Torrance":(33.8358,-118.3406),"Trabuco Canyon":(33.6597,-117.5939),"Tustin":(33.7458,-117.8261),
    "Upland":(34.0975,-117.6484),"Valinda":(34.0378,-117.9331),"Ventura":(34.2746,-119.229),
    "Ventura County":(34.2746,-119.229),"Villa Park":(33.8147,-117.8131),"Vista":(33.2,-117.2425),
    "Walnut":(34.0214,-117.8603),"West Covina":(34.0686,-117.939),"West Hollywood":(34.09,-118.3617),
    "Westlake Village":(34.1622,-118.8194),"Westminster":(33.7514,-117.9939),
    "Whittier":(33.9792,-118.0328),"Wildomar":(33.5986,-117.28),"Winchester":(33.7028,-117.0886),
    "Woodland Hills":(34.1684,-118.6058),"Woodcrest":(33.8917,-117.3322),
    "Yorba Linda":(33.8886,-117.8131),"Yucca Valley":(34.1142,-116.432),
}


def scrape_html(html_path: str) -> pd.DataFrame:
    from bs4 import BeautifulSoup
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
        if name or score:
            results.append({"name": name, "code": code, "score": score, "location": loc, "age_gender": ag})

    df = pd.DataFrame(results)
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["city"]  = df["location"].str.split(",").str[0].str.strip().fillna("Unknown")
    df["age"]   = df["age_gender"].str.extract(r"^(\d+)").astype(float)
    return df


def build_outputs(df: pd.DataFrame):
    df = df[df["city"] != "Unknown"].copy()

    # city_data.json — grouped by city with coords
    city_players: dict = {}
    for city, group in df.groupby("city"):
        players = group.sort_values("score", ascending=False)[["name", "score", "age"]].values.tolist()
        city_players[city] = [
            [p[0], round(float(p[1]), 3) if pd.notna(p[1]) else None,
             int(p[2]) if pd.notna(p[2]) else None]
            for p in players
        ]

    missing = [c for c in city_players if c not in COORDS]
    if missing:
        print(f"WARNING: No coordinates for {len(missing)} cities — they will be excluded from the map:")
        for c in sorted(missing):
            print(f"  {c} ({len(city_players[c])} players) — add to COORDS in scrape.py")

    city_data = []
    for city, players in city_players.items():
        if city in COORDS:
            lat, lng = COORDS[city]
            city_data.append({"city": city, "lat": lat, "lng": lng, "players": players})

    # all_players.json — flat list for search autocomplete
    all_players = []
    for _, row in df.iterrows():
        all_players.append({
            "name":  row["name"],
            "score": round(float(row["score"]), 3) if pd.notna(row["score"]) else None,
            "age":   int(row["age"]) if pd.notna(row["age"]) else None,
            "city":  row["city"],
        })
    all_players.sort(key=lambda x: x["name"].lower())

    # Write outputs
    city_data_path   = DATA_DIR / "city_data.json"
    all_players_path = DATA_DIR / "all_players.json"
    csv_path         = SCRIPT_DIR / "socal_results.csv"

    with open(city_data_path, "w", encoding="utf-8") as f:
        json.dump(city_data, f)
    with open(all_players_path, "w", encoding="utf-8") as f:
        json.dump(all_players, f)
    df.to_csv(csv_path, index=False)

    total_mapped = sum(len(c["players"]) for c in city_data)
    print(f"\nDone!")
    print(f"  Cities mapped:  {len(city_data)}")
    print(f"  Players mapped: {total_mapped} / {len(df)}")
    print(f"  Score range:    {df['score'].min():.3f} – {df['score'].max():.3f}")
    print(f"  Age range:      {int(df['age'].min())} – {int(df['age'].max())}")
    print(f"\nOutputs written to:")
    print(f"  {city_data_path}")
    print(f"  {all_players_path}")
    print(f"  {csv_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scrape.py <path_to_html_file>")
        sys.exit(1)
    df = scrape_html(sys.argv[1])
    build_outputs(df)
