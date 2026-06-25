#!/usr/bin/env python3
"""
DUPR scraper — opens a real browser, lets you log in manually,
then automatically applies filters, scrolls through all players,
and saves the page HTML for scrape.py to process.

Usage:
    pip install playwright
    playwright install chromium
    python fetch_dupr.py

Output:
    dupr_export.html  (in the same directory as this script)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# ── Config ────────────────────────────────────────────────────────────────
URL = "https://dashboard.dupr.com/dashboard/browse/players"

FILTERS = {
    "location":   "Irvine, CA, USA",
    "distance_mi": 100,
    "gender":     "Men",
    "type":       "Doubles",
    "dupr_min":   4.0,
    "dupr_max":   8.0,
    "age_min":    19,
    "age_max":    50,
}

OUTPUT_DIR = Path(__file__).parent
# ─────────────────────────────────────────────────────────────────────────


async def wait_for_players(page, timeout=15000):
    """Wait until at least one player card is visible."""
    await page.wait_for_selector(
        "div.flex.flex-col.gap-y-2.mt-6 > div",
        timeout=timeout
    )


async def count_players(page):
    return await page.eval_on_selector_all(
        "div.flex.flex-col.gap-y-2.mt-6 > div",
        "els => els.length"
    )


async def scroll_to_bottom(page):
    """Scroll until no new players load."""
    print("Scrolling to load all players...")
    prev_count = 0
    stale_rounds = 0

    while True:
        count = await count_players(page)
        print(f"  {count} players loaded...", end="\r")

        if count == prev_count:
            stale_rounds += 1
            if stale_rounds >= 3:
                break
        else:
            stale_rounds = 0
            prev_count = count

        # Scroll the player list container if it's scrollable, else scroll page
        await page.evaluate("""() => {
            // Try scrolling the inner list container first
            const container = document.querySelector('div.flex.flex-col.gap-y-2.mt-6');
            if (container) {
                let el = container.parentElement;
                while (el) {
                    if (el.scrollHeight > el.clientHeight) {
                        el.scrollTop = el.scrollHeight;
                        return;
                    }
                    el = el.parentElement;
                }
            }
            window.scrollTo(0, document.body.scrollHeight);
        }""")
        await asyncio.sleep(1.5)

    final_count = await count_players(page)
    print(f"\n  Done — {final_count} players loaded.")
    return final_count


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        # ── Step 1: Manual login ──────────────────────────────────────
        print("Opening DUPR...")
        await page.goto(URL)

        print("\n" + "="*55)
        print("  Please log in to DUPR in the browser window.")
        print("  Once you're on the player browse page, press Enter here.")
        print("="*55)
        input()

        # ── Step 2: Apply filters ─────────────────────────────────────
        print("\nApplying filters — please watch the browser.")
        print("If the script gets stuck on a filter, set it manually")
        print("and press Enter to continue.\n")

        try:
            # Location
            print("Setting location...")
            loc_input = page.locator("input[placeholder*='Location'], input[placeholder*='location'], input[placeholder*='City']").first
            await loc_input.click()
            await loc_input.fill("")
            await loc_input.type(FILTERS["location"], delay=80)
            await asyncio.sleep(1.5)
            # Pick first autocomplete suggestion
            suggestion = page.locator("[class*='suggestion'], [class*='dropdown'] li, [role='option']").first
            if await suggestion.is_visible():
                await suggestion.click()
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  Location filter: could not set automatically ({e})")
            input("  Set location manually then press Enter...")

        try:
            # Gender — look for a Men/Male toggle or select
            print("Setting gender to Men...")
            men_btn = page.locator("button:has-text('Men'), label:has-text('Men'), [value='Men'], [value='MALE']").first
            if await men_btn.is_visible(timeout=3000):
                await men_btn.click()
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  Gender filter: could not set automatically ({e})")
            input("  Set gender manually then press Enter...")

        try:
            # Doubles checkbox
            print("Checking Doubles...")
            doubles = page.locator("label:has-text('Doubles') input[type='checkbox'], input[type='checkbox'][value*='ouble']").first
            if await doubles.is_visible(timeout=3000):
                if not await doubles.is_checked():
                    await doubles.click()
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  Doubles filter: could not set automatically ({e})")
            input("  Set doubles manually then press Enter...")

        print("\nFilters applied (some may need manual adjustment).")
        print("Make sure all your filters are set correctly in the browser.")
        input("Press Enter when the player list looks right and has loaded...")

        # ── Step 3: Scroll to load all players ────────────────────────
        try:
            await wait_for_players(page)
        except Exception:
            print("Warning: could not detect player cards — make sure the list is visible.")
            input("Press Enter to continue anyway...")

        total = await scroll_to_bottom(page)

        # ── Step 4: Save HTML ─────────────────────────────────────────
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_DIR / f"dupr_export_{timestamp}.html"

        print(f"\nSaving HTML to {output_path}...")
        html = await page.content()
        output_path.write_text(html, encoding="utf-8")

        print(f"\n✓ Saved {output_path.stat().st_size / 1024 / 1024:.1f} MB")
        print(f"✓ {total} players captured")
        print(f"\nNow run:")
        print(f"  python scrape.py {output_path.name}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
