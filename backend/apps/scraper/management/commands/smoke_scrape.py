from __future__ import annotations

import json
from typing import Any

from django.core.management.base import BaseCommand, CommandParser

from apps.scraper.scrape import scrape_site_search


class Command(BaseCommand):
    help = "Smoke-test a scraper (runs Playwright and prints parsed listings)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("query", type=str, help="Search query, e.g. 'iphone 13'")
        parser.add_argument(
            "--site",
            dest="site_slug",
            type=str,
            default="engocha",
            help="Site slug (default: engocha).",
        )
        parser.add_argument(
            "--limit",
            dest="limit",
            type=int,
            default=10,
            help="Max number of listings to print (default: 10).",
        )
        parser.add_argument(
            "--headed",
            dest="headed",
            action="store_true",
            help="Run browser headed (not headless) for debugging.",
        )
        parser.add_argument(
            "--json",
            dest="as_json",
            action="store_true",
            help="Print results as JSON.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        query: str = options["query"]
        site_slug: str = options["site_slug"]
        limit: int = options["limit"]
        headless: bool = not bool(options["headed"])
        as_json: bool = bool(options["as_json"])

        listings = scrape_site_search(query=query, site_slug=site_slug, limit=limit, headless=headless)

        if as_json:
            payload = [
                {
                    "source_url": x.source_url,
                    "title": x.title,
                    "price_text": x.price_text,
                    "price": str(x.price) if x.price is not None else None,
                    "currency": x.currency,
                    "image_url": x.image_url,
                    "availability": x.availability,
                    "source_listing_id": x.source_listing_id,
                }
                for x in listings
            ]
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
            return

        self.stdout.write(self.style.SUCCESS(f"Got {len(listings)} listing(s) from site='{site_slug}' query='{query}'"))
        for i, x in enumerate(listings, start=1):
            self.stdout.write(f"\n#{i}")
            self.stdout.write(f"title: {x.title}")
            self.stdout.write(f"price_text: {x.price_text}")
            self.stdout.write(f"price: {x.price} {x.currency}")
            self.stdout.write(f"url: {x.source_url}")
            if x.image_url:
                self.stdout.write(f"image: {x.image_url}")
