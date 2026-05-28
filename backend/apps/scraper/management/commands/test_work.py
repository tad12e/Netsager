

import asyncio
import json
from django.core.management.base import BaseCommand
from playwright.async_api import async_playwright
try:
    # Older versions of playwright-stealth exposed a function named `stealth_async`.
    from playwright_stealth import stealth_async  # type: ignore
except ImportError:  # pragma: no cover
    # Newer versions expose a `Stealth` class with an `apply_stealth_async` method.
    from playwright_stealth import Stealth

    async def stealth_async(page):
        await Stealth().apply_stealth_async(page)

from apps.scraper.work import (
    EngochaScraper,
    JijiScraper,
    GefiiraScraper,
    AshewaScraper,
    AddisberScraper,
    AradaMartScraper,
    MekinaScraper,
    HellooMarketScraper,
    BrundoScraper,
    DeamatScraper,
    EthioSuQScraper,
)


class Command(BaseCommand):
    help = "Test asynchronous scrapers from work.py"

    def add_arguments(self, parser):
        parser.add_argument("query", type=str, help="The search term (e.g., 'iphone')")
        parser.add_argument(
            "--site",
            type=str, # type: ignore
            default="mekina",
            help="Site to scrape: 'engocha', 'jiji', 'gefiira', 'ashewa', 'addisber', 'aradamart', 'mekina', 'hellomarket', 'brundo', 'deamat', or 'ethiosuq' (default: mekina)",
        )
        parser.add_argument(
            "--headed",
            action="store_true",
            help="Run browser in headed mode to see the action",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum number of items to scrape",
        )
        parser.add_argument(
            "--slow-mo",
            type=int,
            default=0,
            help="Slow down Playwright operations (ms) for debugging",
        )
        parser.add_argument(
            "--save",
            type=str,
            help="Save results to a JSON file (e.g., results.json)",
        )

    def handle(self, *args, **options):
        query = options["query"]
        headed = options["headed"]
        limit = options["limit"]
        slow_mo = options["slow_mo"]
        save_path = options["save"]
        site = options["site"].lower()

        self.stdout.write(f"Testing {site} scraper with query: {query} (limit: {limit})...")
        if headed:
            self.stdout.write(self.style.NOTICE(f"Running in HEADED mode with {slow_mo}ms slow-mo..."))

        results = asyncio.run(self.run_scraper(site, query, not headed, limit, slow_mo))

        if not results:
            self.stdout.write(self.style.WARNING("No results found or scraper failed."))
            return

        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4, ensure_ascii=False)
            self.stdout.write(self.style.SUCCESS(f"Saved {len(results)} results to {save_path}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully found {len(results)} results from {site}:"))

        for i, item in enumerate(results, 1):
            self.stdout.write(self.style.HTTP_INFO(f"\n--- Result #{i} ---"))
            self.stdout.write(f"Title: {item.get('title')}")
            self.stdout.write(f"Price: {item.get('price')}")
            self.stdout.write(f"URL:   {item.get('product_url')}")
            if item.get("image_url"):
                self.stdout.write(f"Image: {item.get('image_url')}")

            for field in ["specs", "location", "description", "views"]:
                val = item.get(field)
                if val:
                    label = field.capitalize()
                    display_val = (val[:100] + "...") if len(val) > 100 else val
                    self.stdout.write(self.style.NOTICE(f"{label}: {display_val}"))

    async def run_scraper(self, site, query, headless, limit, slow_mo):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless, slow_mo=slow_mo)

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                # ── EXTRA HEADERS to look more like a real browser ──
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                }
            )
            page = await context.new_page()

            # ── APPLY STEALTH RIGHT AFTER PAGE CREATION ─────────────
            await stealth_async(page)

            scrapers = {
                "engocha": EngochaScraper,
                "jiji": JijiScraper,
                "gefiira": GefiiraScraper,
                "ashewa": AshewaScraper,
                "addisber": AddisberScraper,
                "aradamart": AradaMartScraper,
                "mekina": MekinaScraper,
                "hellomarket": HellooMarketScraper,
                "helloomarket": HellooMarketScraper,
                "brundo": BrundoScraper,
                "deamat": DeamatScraper,
                "ethiosuq": EthioSuQScraper,
            }

            scraper_class = scrapers.get(site, EngochaScraper)
            scraper = scraper_class()

            try:
                return await scraper.search(query, page, limit=limit)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error during scraping for site '{site}': {e}"))
                import traceback
                self.stdout.write(self.style.ERROR(f"Scraper Error: {e}\n{traceback.format_exc()}"))
                return []
            finally:
                await browser.close()