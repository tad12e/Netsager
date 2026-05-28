from __future__ import annotations

from abc import ABC, abstractmethod

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable, Iterable, Optional
from urllib.parse import quote_plus, urljoin, urlparse

from django.db import transaction
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from apps.products.models import Product
from .models import ProductListing, SourceSite


@dataclass(frozen=True)
class ScrapedListing:
	source_url: str
	title: str
	price_text: str = ""
	price: Optional[Decimal] = None
	currency: str = "ETB"
	image_url: str = ""
	availability: bool = True
	source_listing_id: str = ""


_PRICE_RE = re.compile(r"(\d[\d,\s]{0,20}\d)")


SearchUrlBuilder = Callable[[str], str]


@dataclass(frozen=True)
class SiteDefinition:
	slug: str
	name: str
	base_url: str
	build_search_url: Optional[SearchUrlBuilder] = None


def _build_engocha_search_url(query: str) -> str:
	q = quote_plus(query)
	return f"https://engocha.com/search?qr={q}"


def _not_implemented_search_url(slug: str) -> SearchUrlBuilder:
	def _builder(_: str) -> str:
		raise NotImplementedError(
			f"Search URL builder not implemented for site_slug='{slug}'. "
			"Add a build_search_url function for this site."
		)
	return _builder


SITE_DEFINITIONS: dict[str, SiteDefinition] = {
	"engocha": SiteDefinition(
		slug="engocha",
		name="Engocha",
		base_url="https://engocha.com",
		build_search_url=_build_engocha_search_url,
	),
	"jiji": SiteDefinition(slug="jiji", name="Jiji Ethiopia", base_url="https://jiji.com.et"),
	"qefira": SiteDefinition(slug="qefira", name="Qefira", base_url="https://qefiira.com/"),
	"sheger": SiteDefinition(slug="sheger", name="Sheger", base_url="https://sheger.net"),
	"ashewa": SiteDefinition(slug="ashewa", name="Ashewa", base_url="https://ashewa.com"),
	"addisber": SiteDefinition(slug="addisber", name="Addisber", base_url="https://addisber.com"),
	"afrotie": SiteDefinition(slug="afrotie", name="Afrotie", base_url="https://afrotie.com"),
	"delala": SiteDefinition(slug="delala", name="Delala", base_url="https://delala.com"),

	"aradamart": SiteDefinition(slug="aradamart", name="Aradamart", base_url="https://aradamart.net"),
	"mekina": SiteDefinition(slug="mekina", name="Mekina", base_url="https://mekina.net"),
	"megebeya": SiteDefinition(slug="megebeya", name="Megebeya", base_url="https://megebeya.com"),
	
	"brundo": SiteDefinition(slug="brundo", name="Brundo", base_url="https://brundo.net/home/"),
	
	"hellomarket": SiteDefinition(slug="hellomarket", name="HelloMarket", base_url="https://helloomarket.com/"),
	
	"deliveraddis": SiteDefinition(slug="deliveraddis", name="Deliver Addis", base_url="https://deliveraddis.com"),
	"zmall": SiteDefinition(slug="zmall", name="Zmall", base_url="https://zmall.com.et"),
	"deamat": SiteDefinition(slug="deamat", name="Deamat", base_url="https://deamat.com"),
}


def supported_site_slugs() -> list[str]:
	return sorted(SITE_DEFINITIONS.keys())


def get_site_definition(site_slug: str) -> SiteDefinition:
	key = (site_slug or "").strip().lower()
	if key not in SITE_DEFINITIONS:
		raise ValueError(f"Unknown site_slug: {site_slug}")
	return SITE_DEFINITIONS[key]


def site_search_url(site_slug: str, query: str) -> str:
	site = get_site_definition(site_slug)
	if site.slug == "jiji":
		q = quote_plus(query)
		return f"https://jiji.com.et/search?query={q}"

	builder = site.build_search_url or _not_implemented_search_url(site.slug)
	return builder(query)


def _normalize_space(value: str) -> str:
	return re.sub(r"\s+", " ", (value or "").strip())


def _extract_id_from_url(url: str) -> str:
	try:
		parsed = urlparse(url)
		# Keep last path segment as a stable-ish id.
		segment = (parsed.path or "").rstrip("/").split("/")[-1]
		return segment[:200]
	except Exception:
		return ""


def _parse_price(price_text: str) -> Optional[Decimal]:
	text = _normalize_space(price_text)
	if not text:
		return None

	match = _PRICE_RE.search(text.replace("\xa0", " "))
	if not match:
		return None

	numeric = match.group(1)
	numeric = numeric.replace(",", "")
	numeric = numeric.replace(" ", "")
	try:
		return Decimal(numeric)
	except (InvalidOperation, ValueError):
		return None


_KNOWN_BRANDS = [
	"Apple",
	"Samsung",
	"Tecno",
	"Infinix",
	"Xiaomi",
	"Huawei",
	"Oppo",
	"Vivo",
	"Nokia",
	"Realme",
	"Google",
]


def _extract_brand_model(title: str) -> tuple[str, str]:
	clean = _normalize_space(title)
	lower = clean.lower()

	for brand in _KNOWN_BRANDS:
		if brand.lower() in lower:
			# naive model extraction: keep up to 4 tokens after the brand
			parts = clean.split()
			try:
				idx = next(i for i, token in enumerate(parts) if token.lower() == brand.lower())
			except StopIteration:
				idx = 0
			model = " ".join(parts[idx + 1: idx + 5]).strip()
			return brand, model

	# iPhone model often doesn't include "Apple"
	if "iphone" in lower:
		parts = clean.split()
		idx = next((i for i, token in enumerate(parts) if token.lower().startswith("iphone")), 0)
		model = " ".join(parts[idx: idx + 4]).strip()
		return "Apple", model

	return "", ""


def _site_search_url(site_slug: str, query: str) -> str:
	"""Backward-compatible wrapper; use site_search_url instead."""
	return site_search_url(site_slug, query)


def _extract_listings_from_page(page, base_url: str, limit: int) -> list[ScrapedListing]:
	# Heuristic extraction that works across many listing UIs:
	# look for anchors that contain an h3/h4 (title), then read nearby price/image.
	anchors = page.locator("a[href]:has(h3), a[href]:has(h4)")
	count = min(anchors.count(), max(0, limit))
	results: list[ScrapedListing] = []
	seen: set[str] = set()

	for i in range(count):
		a = anchors.nth(i)
		href = a.get_attribute("href") or ""
		if not href:
			continue
		url = urljoin(base_url, href)
		if url in seen:
			continue
		seen.add(url)

		title_locator = a.locator("h3, h4").first
		title = _normalize_space(title_locator.inner_text() if title_locator.count() else a.inner_text())
		if not title:
			continue

		# Try to find the nearest card container and read a price-like text.
		card = a.locator("xpath=ancestor::*[self::article or self::div][1]")
		price_text = ""
		if card.count():
			card_text = _normalize_space(card.first.inner_text() or "")
			# Keep a short slice (avoid huge blocks)
			price_text = card_text[:200]

		img = a.locator("img").first
		image_url = ""
		if img.count():
			image_url = (
				img.get_attribute("src")
				or img.get_attribute("data-src")
				or img.get_attribute("data-lazy")
				or ""
			)

		parsed_price = _parse_price(price_text)
		results.append(
			ScrapedListing(
				source_url=url,
				title=title,
				price_text=price_text,
				price=parsed_price,
				currency="ETB",
				image_url=image_url,
				availability=True,
				source_listing_id=_extract_id_from_url(url),
			)
		)

	return results


def scrape_site_search(query: str, site_slug: str = "jiji", limit: int = 30, headless: bool = True) -> list[ScrapedListing]:
	url = site_search_url(site_slug, query)
	base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

	with sync_playwright() as playwright:
		browser = playwright.chromium.launch(headless=headless)
		context = browser.new_context(
			viewport={"width": 1365, "height": 768},
			locale="en-US",
		)
		page = context.new_page()
		try:
			page.goto(url, wait_until="domcontentloaded", timeout=45_000)
			page.wait_for_timeout(1500)
			return _extract_listings_from_page(page, base_url=base_url, limit=limit)
		except PlaywrightTimeoutError:
			return []
		finally:
			context.close()
			browser.close()


def upsert_scraped_listings(
	*,
	listings: Iterable[ScrapedListing],
	site_slug: str,
	site_name: Optional[str] = None,
	base_url: str = "",
) -> list[ProductListing]:
	site, _ = SourceSite.objects.get_or_create(
		slug=site_slug,
		defaults={
			"name": site_name or site_slug.title(),
			"base_url": base_url,
		},
	)

	stored: list[ProductListing] = []
	with transaction.atomic():
		for item in listings:
			brand, model_name = _extract_brand_model(item.title)
			product = None
			if item.title:
				product, _ = Product.objects.get_or_create(
					name=item.title[:255],
					defaults={
						"brand": brand,
						"model_name": model_name,
					},
				)

			listing, _ = ProductListing.objects.update_or_create(
				source=site_slug,
				source_url=item.source_url,
				defaults={
					"source_site": site,
					"product": product,
					"source_listing_id": item.source_listing_id,
					"title": item.title[:500],
					"price_text": item.price_text[:100],
					"price": item.price,
					"currency": (item.currency or "ETB")[:10],
					"image_url": item.image_url,
					"availability": item.availability,
				},
			)
			stored.append(listing)

	return stored


def scrape_and_store(query: str, site_slug: str = "jiji", limit: int = 30, headless: bool = True) -> list[int]:
	listings = scrape_site_search(query=query, site_slug=site_slug, limit=limit, headless=headless)
	search_url = _site_search_url(site_slug, query)
	base_url = f"{urlparse(search_url).scheme}://{urlparse(search_url).netloc}"
	stored = upsert_scraped_listings(listings=listings, site_slug=site_slug, base_url=base_url)
	return [obj.id for obj in stored]



class BaseScraper(ABC):
    
    @abstractmethod
    async def search(self, query: str, page) -> list[dict]:
        """
        Scrape search results for a given query.
        
        Args:
            query: the search term e.g. "iphone"
            page:  Playwright page object

        Returns:
            list of dicts, each with:
            {
                "title":       str,
                "price":       str,
                "image_url":   str,
                "product_url": str,
                "site":        str
            }
        """
        pass

    def build_url(self, base: str, path: str) -> str:
        """Helper — turns relative URLs into absolute ones."""
        if path and not path.startswith("http"):
            return base + path
        return path

    def clean_price(self, price: str) -> str:
        """Helper — strips whitespace and newlines from price text."""
        return price.strip().replace("\n", " ") if price else ""

    def clean_title(self, title: str) -> str:
        """Helper — strips whitespace from title text."""
        return title.strip() if title else ""


class EngochaScraper(BaseScraper):
    async def search(self, query, page):
        await page.goto(f"https://engocha.com/search?qr={query}")
        await page.wait_for_selector(".listingcolumn.normal")

        cards = await page.query_selector_all(".col-md-12.listingcolumn.normal")
        results = []

        for card in cards:
            title = await card.query_selector(".listingdetail a")
            price = await card.query_selector("span.price")
            image = await card.query_selector(".photocontainer img")
            link  = await card.query_selector(".listingdetail a")

            raw_url = await link.get_attribute("href") if link else ""

            # make sure it's a full URL not a relative path
            if raw_url and not raw_url.startswith("http"):
                full_url = "https://engocha.com" + raw_url
            else:
                full_url = raw_url

            results.append({
                "title":       await title.inner_text() if title else "",
                "price":       await price.inner_text() if price else "",
                "image_url":   await image.get_attribute("src") if image else "",
                "product_url": full_url,
                "site":        "engocha"
            })

        return results