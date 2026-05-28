from __future__ import annotations

import asyncio
import hashlib
from typing import Any

from celery import shared_task
from django.core.cache import cache
from playwright.async_api import async_playwright

try:
    from playwright_stealth import stealth_async  # type: ignore
except ImportError:  # pragma: no cover
    from playwright_stealth import Stealth

    async def stealth_async(page):
        await Stealth().apply_stealth_async(page)

from apps.scraper.scrape import supported_site_slugs
from apps.scraper.work import (
    AddisberScraper,
    AradaMartScraper,
    AshewaScraper,
    BrundoScraper,
    DeamatScraper,
    EngochaScraper,
    EthioSuQScraper,
    GefiiraScraper,
    HellooMarketScraper,
    JijiScraper,
    MekinaScraper,
)


SCRAPER_CLASSES: dict[str, type] = {
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


def _normalize_query(query: str) -> str:
    return " ".join((query or "").strip().lower().split())


def _cache_key(site_slug: str, query: str) -> str:
    digest = hashlib.md5(_normalize_query(query).encode("utf-8")).hexdigest()
    return f"scrape:{site_slug}:{digest}"


def _bulk_cache_key(query: str) -> str:
    digest = hashlib.md5(_normalize_query(query).encode("utf-8")).hexdigest()
    return f"scrape:all:{digest}"


def _serialize_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "title": item.get("title", ""),
            "price": item.get("price", ""),
            "image_url": item.get("image_url", ""),
            "product_url": item.get("product_url", ""),
            "specs": item.get("specs", ""),
            "description": item.get("description", ""),
            "location": item.get("location", ""),
            "views": item.get("views", ""),
            "site": item.get("site", ""),
        }
        for item in results
    ]


async def _run_scraper(scraper_class: type, query: str, limit: int, headless: bool) -> list[dict[str, Any]]:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not.A.Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            },
        )
        page = await context.new_page()
        await stealth_async(page)

        try:
            scraper = scraper_class()
            results = await scraper.search(query, page, limit=limit)
            return _serialize_results(results)
        finally:
            await context.close()
            await browser.close()


async def _run_all_scrapers(query: str, limit: int, headless: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)

        for site_slug in supported_site_slugs():
            scraper_class = SCRAPER_CLASSES.get(site_slug)
            if not scraper_class:
                payload[site_slug] = {"error": "scraper not implemented"}
                continue

            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not.A.Brand";v="99"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                },
            )
            page = await context.new_page()
            await stealth_async(page)

            try:
                scraper = scraper_class()
                results = await scraper.search(query, page, limit=limit)
                serialized = _serialize_results(results)
                payload[site_slug] = serialized
                cache.set(_cache_key(site_slug, query), serialized)
            except Exception as exc:
                payload[site_slug] = {"error": str(exc)}
            finally:
                await context.close()

        await browser.close()

    cache.set(_bulk_cache_key(query), payload)
    return payload


@shared_task(name="apps.scraper.scrape_task")
def scrape_task(query: str, site_slug: str = "jiji", limit: int = 30, headless: bool = True) -> list[dict[str, Any]]:
    site_slug = (site_slug or "").strip().lower()
    if site_slug not in SCRAPER_CLASSES:
        raise ValueError(f"Unsupported site_slug: {site_slug}")

    results = asyncio.run(_run_scraper(SCRAPER_CLASSES[site_slug], query, limit, headless))
    cache.set(_cache_key(site_slug, query), results)
    return results


@shared_task(name="apps.scraper.scrape_all_task")
def scrape_all_task(query: str, limit: int = 30, headless: bool = True) -> dict[str, Any]:
    return asyncio.run(_run_all_scrapers(query, limit, headless))