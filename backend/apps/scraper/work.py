from __future__ import annotations
from abc import ABC, abstractmethod
import json
from urllib.parse import quote_plus, urlencode
from urllib.parse import urlencode
import requests
from bs4 import BeautifulSoup






class BaseScraper(ABC):

    @abstractmethod
    async def search(self, query: str, page, limit: int = 10) -> list[dict]:
        pass

    def build_url(self, base: str, path: str) -> str:
        if path and not path.startswith("http"):
            return base + path
        return path

    def clean_price(self, price: str) -> str:
        return price.strip().replace("\n", " ") if price else ""

    def clean_title(self, title: str) -> str:
        return title.strip() if title else ""


class EngochaScraper(BaseScraper):
    BASE_URL = "https://engocha.com"

    async def search(self, query: str, page, limit: int = 10) -> list[dict]:
        q = quote_plus(query or "")
        results = []
        page_num = 1

        while len(results) < limit:
            # engocha uses ?qr=...&page=1 for pagination
            url = f"{self.BASE_URL}/search?qr={q}&page={page_num}"
            await page.goto(url)

            # wait for cards or bail if nothing loads
            try:
                await page.wait_for_selector(".listingcolumn.normal", timeout=8000)
            except Exception:
                break  # no more results

            cards = await page.query_selector_all(".col-md-12.listingcolumn.normal")

            if not cards:
                break  # no results on this page, stop

            for card in cards:
                if len(results) >= limit:
                    break

                title_el = await card.query_selector(".listingdetail a")
                price_el = await card.query_selector("span.price")
                image_el = await card.query_selector(".photocontainer img")
                link_el  = await card.query_selector(".listingdetail a")

                # --- image: try data-src first (lazy load), fall back to src ---
                image_url = ""
                if image_el:
                    image_url = (
                        await image_el.get_attribute("data-src")
                        or await image_el.get_attribute("src")
                        or ""
                    )

                # --- product url: make absolute if relative ---
                raw_url = await link_el.get_attribute("href") if link_el else ""
                full_url = (
                    self.BASE_URL + raw_url
                    if raw_url and not raw_url.startswith("http")
                    else raw_url
                )

                results.append({
                    "title":       self.clean_title(await title_el.inner_text() if title_el else ""),
                    "price":       self.clean_price(await price_el.inner_text() if price_el else ""),
                    "image_url":   image_url,
                    "product_url": full_url,
                    "site":        "engocha",
                })

            page_num += 1  # go to next page

        return results[:limit]  # never return more than asked








class JijiScraper(BaseScraper):
    BASE_URL = "https://jiji.com.et"

    async def search(self, query: str, page, limit: int = 10) -> list[dict]:
        q = quote_plus(query or "")
        results = []
        page_num = 1

        while len(results) < limit:
            url = f"{self.BASE_URL}/mobile-phones?query={q}&page={page_num}"
            await page.goto(url)

            try:
                await page.wait_for_selector(
                    ".b-adverts-gallery-listing__item", timeout=10000
                )
            except Exception:
                break

            await page.wait_for_timeout(1500)

            cards = await page.query_selector_all(
                ".b-adverts-gallery-listing__item.js-advert-list-item"
            )

            if not cards:
                break

            for card in cards:
                if len(results) >= limit:
                    break

                # ── TITLE ────────────────────────────────────────────
                title_el = await card.query_selector(".b-list-advert-base__data-title")
                if not title_el:
                    img_el = await card.query_selector("img")
                    title = await img_el.get_attribute("alt") if img_el else ""
                else:
                    title = await title_el.inner_text()

                # ── PRICE ────────────────────────────────────────────
                price_el = await card.query_selector(".qa-advert-price")
                price = self.clean_price(
                    await price_el.inner_text() if price_el else ""
                )

                # ── IMAGE ────────────────────────────────────────────
                image_url = ""
                source_el = await card.query_selector("source[type='image/webp']")
                if source_el:
                    srcset = await source_el.get_attribute("srcset") or ""
                    image_url = srcset.split(",")[0].strip().split(" ")[0]
                if not image_url:
                    img_el = await card.query_selector("img")
                    if img_el:
                        image_url = (
                            await img_el.get_attribute("data-src")
                            or await img_el.get_attribute("src")
                            or ""
                        )

                # ── PRODUCT URL ──────────────────────────────────────
                link_el = await card.query_selector("a[href*='mobile-phones']")
                raw_url = await link_el.get_attribute("href") if link_el else ""
                full_url = (
                    self.BASE_URL + raw_url
                    if raw_url and not raw_url.startswith("http")
                    else raw_url
                )

                # ════════════════════════════════════════════════════
                #  VARIABLE 1 — "specs"
                #  Structured key facts: condition, brand, RAM etc.
                #  These are the label/value pairs from the listing card
                # ════════════════════════════════════════════════════
                specs_parts = []

                # condition badge: "Brand New"
                label_els = await card.query_selector_all(
                    ".b-list-advert-base__bottom-wrapper span"
                )
                for el in label_els:
                    text = (await el.inner_text()).strip()
                    if text:
                        specs_parts.append(text)

                # seller trust badge: "5+ YEARS ON JIJI", "DIAMOND"
                badge_els = await card.query_selector_all(
                    ".b-list-advert-base__pkg-label, "
                    ".b-adverts-gallery-listing__item-seller"
                )
                for el in badge_els:
                    text = (await el.inner_text()).strip()
                    if text:
                        specs_parts.append(text)

                specs = " | ".join(filter(None, specs_parts))

                # ════════════════════════════════════════════════════
                #  VARIABLE 2 — "description"
                #  The long text body under the title:
                #  "Samsung Galaxy A34 5G Dimensity 1080 chipset
                #   100% Original Brand New Super AMOLED Display 120HZ..."
                # ════════════════════════════════════════════════════
                description = ""
                desc_el = await card.query_selector(
                    ".b-list-advert-base__description-text"
                )
                if desc_el:
                    description = (await desc_el.inner_text()).strip()

                # ════════════════════════════════════════════════════
                #  VARIABLE 3 — "location"
                #  Where the seller is: "Addis Ababa, Bole"
                #  + how long ago posted: "2 hours ago"
                # ════════════════════════════════════════════════════
                location = ""
                location_el = await card.query_selector(
                    ".b-list-advert-base__attrs"
                )
                if location_el:
                    location = (await location_el.inner_text()).strip()

                results.append({
                    "title":       self.clean_title(title),
                    "price":       price,
                    "image_url":   image_url,
                    "product_url": full_url,
                    "specs":       specs,         # condition, badges
                    "description": description,   # long text body
                    "location":    location,      # city + time posted
                    "site":        "jiji",
                })

            page_num += 1

        return results[:limit]












class GefiiraScraper(BaseScraper):
    BASE_URL = "https://qefiira.com"  # note: qefiira not gefiira

    async def search(self, query: str, page, limit: int = 10) -> list[dict]:
        results = []
        page_num = 1

        while len(results) < limit:

            # ── BUILD URL ──────────────────────────────────────────
            params = {
                "directory_action":            "search",
                "handler":                     "directorypress_listings_handler",
                "include_categories_children": "1",
                "s":                           query,
                "paged":                       page_num,
            }
            url = f"{self.BASE_URL}/listings/?{urlencode(params)}"

            # ── OPEN PAGE ──────────────────────────────────────────
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector(
                    "article.directorypress-listing", timeout=10000
                )
                await page.wait_for_timeout(1000)
            except Exception:
                break

            cards = await page.query_selector_all("article.directorypress-listing")
            if not cards:
                break

            for card in cards:
                if len(results) >= limit:
                    break

                # ── TITLE ──────────────────────────────────────────
                title = ""
                title_el = await card.query_selector(
                    "header.directorypress-listing-title a"
                )
                if title_el:
                    title = self.clean_title(await title_el.inner_text())

                # ── PRODUCT URL ────────────────────────────────────
                full_url = ""
                if title_el:
                    full_url = await title_el.get_attribute("href") or ""

                # ── IMAGE ──────────────────────────────────────────
                image_url = ""
                img_el = await card.query_selector(
                    "figure.directorypress-listing-figure img"
                )
                if img_el:
                    image_url = (
                        await img_el.get_attribute("src")
                        or await img_el.get_attribute("data-src")
                        or ""
                    )

                # ── PRICE ──────────────────────────────────────────
                # <span class="field-content symbol-left">ETB 53550</span>
                price = ""
                price_el = await card.query_selector(
                    "span.field-content.symbol-left"
                )
                if price_el:
                    price = self.clean_price(await price_el.inner_text())

                # ══════════════════════════════════════════════════
                # VARIABLE 1 — specs
                # FIXED/NEGOTIABLE + Featured + category name
                # ══════════════════════════════════════════════════
                specs_parts = []

                # FIXED or NEGOTIABLE — read from the full price wrapper text
                price_wrapper = await card.query_selector(
                    ".directorypress-field-id-9"
                )
                if price_wrapper:
                    pw_text = (await price_wrapper.inner_text()).upper()
                    if "FIXED" in pw_text:
                        specs_parts.append("FIXED")
                    elif "NEGOTIABLE" in pw_text:
                        specs_parts.append("NEGOTIABLE")

                # Featured — check article's own class list
                card_classes = await card.get_attribute("class") or ""
                if "has-featured" in card_classes:
                    specs_parts.append("Featured")

                # Category name shown on card
                # e.g "Mobile Phones", "Electronics", "Vehicles"
                category_el = await card.query_selector(
                    ".listing-bottom-meta .field-content:not(.symbol-left)"
                )
                if category_el:
                    cat = (await category_el.inner_text()).strip()
                    if cat and cat not in ["FIXED", "NEGOTIABLE"]:
                        specs_parts.append(cat)

                specs = " | ".join(filter(None, specs_parts))

                # ══════════════════════════════════════════════════
                # VARIABLE 2 — description
                # date posted + views + ID shown under title
                # "March 29, 2026  Views: 313  Id: 18831"
                # ══════════════════════════════════════════════════
                description = ""
                desc_el = await card.query_selector(".grid-exerpt-field")
                if desc_el:
                    description = (await desc_el.inner_text()).strip()

                # ══════════════════════════════════════════════════
                # VARIABLE 3 — location
                # "Ethiopia" or "Addis Ababa, Ethiopia"
                # ══════════════════════════════════════════════════
                location = ""
                location_el = await card.query_selector(".grid-fields-location")
                if location_el:
                    location = (await location_el.inner_text()).strip()

                # ── VIEWS ──────────────────────────────────────────
                views = ""
                views_el = await card.query_selector("p.listing-views")
                if views_el:
                    views = (await views_el.inner_text()).strip()

                results.append({
                    "title":       title,
                    "price":       price,
                    "image_url":   image_url,
                    "product_url": full_url,
                    "specs":       specs,
                    "description": description,
                    "location":    location,
                    "views":       views,
                    "site":        "gefiira",
                })

            page_num += 1

        return results[:limit]






class AshewaScraper(BaseScraper):
    BASE_URL = "https://ashewa.com"

    async def search(self, query: str, page, limit: int = 10) -> list[dict]:
        results = []
        page_num = 1

        while len(results) < limit:

            # ── BUILD URL ──────────────────────────────────────────
            # Ashewa uses 'search' instead of 'name' for standard search input queries
            params = {
                "search": query,
            }
            url = f"{self.BASE_URL}/shop/sidebar/list?{urlencode(params)}"

            # ── OPEN PAGE ──────────────────────────────────────────
            try:
                # Changed wait_until to 'load' to ensure the Javascript application kicks off
                await page.goto(url, wait_until="load", timeout=30000)
                
                # Use a more flexible class matching string layout to find the items
                await page.wait_for_selector(
                    "div.product", timeout=15000
                )
                await page.wait_for_timeout(2000) # Give structural assets an extra 2s to breathe
            except Exception as e:
                print(f"[AshewaScraper] Navigation or layout wait timeout: {e}")
                break

            # ── QUERY CARDS ────────────────────────────────────────
            # Capture elements that contain the product list/grid items broadly
            cards = await page.query_selector_all("div.product")
            if not cards:
                print("[AshewaScraper] No card items found matching the selector layout.")
                break

            for card in cards:
                if len(results) >= limit:
                    break

                try:
                    # ── TITLE & PRODUCT URL ──────────────────────────
                    title = ""
                    full_url = ""
                    
                    # Target explicit relative product URLs
                    title_el = await card.query_selector("a[href*='/product/']")
                    if title_el:
                        title = self.clean_title(await title_el.inner_text())
                        href = await title_el.get_attribute("href") or ""
                        full_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

                    # Safeguard edge cases where empty template boxes render
                    if not title:
                        continue

                    # ── IMAGE ────────────────────────────────────────
                    image_url = ""
                    img_el = await card.query_selector("img")
                    if img_el:
                        image_url = (
                            await img_el.get_attribute("src")
                            or await img_el.get_attribute("data-src")
                            or ""
                        )

                    # ── PRICE ────────────────────────────────────────
                    price = ""
                    # Grab elements tracking currency definitions string text
                    price_el = await card.query_selector("div.order-md-last, .product-price, span:has-text('ETB')")
                    if price_el:
                        price_text = await price_el.inner_text()
                        if price_text:
                            price_lines = [line.strip() for line in price_text.split("\n") if "ETB" in line]
                            price_raw = price_lines[0] if price_lines else price_text
                            price = self.clean_price(price_raw)

                    # ── SPECS (Badges/Labels) ────────────────────────
                    specs_parts = []
                    label_els = await card.query_selector_all("span.product-label")
                    for label in label_els:
                        text = (await label.inner_text()).strip()
                        if text:
                            specs_parts.append(text)
                    
                    specs = " | ".join(filter(None, specs_parts))

                    # ── DESCRIPTION / SITE ATTRIBUTES ────────────────
                    description = title
                    location = "Addis Ababa, Ethiopia"
                    views = ""

                    results.append({
                        "title":       title,
                        "price":       price,
                        "image_url":   image_url,
                        "product_url": full_url,
                        "specs":       specs,
                        "description": description,
                        "location":    location,
                        "views":       views,
                        "site":        "ashewa",
                    })

                except Exception as card_error:
                    print(f"[AshewaScraper] Card parsing error skipped: {card_error}")
                    continue

            # Break safely if we reached limits or processed initial page items
            if len(results) >= limit or page_num >= 1: 
                break
                
            page_num += 1

        return results[:limit]



class AddisberScraper(BaseScraper):
    BASE_URL = "https://addisber.com"

    async def search(self, query: str, page, limit: int = 10) -> list[dict]:
        results = []
        page_num = 1
        MAX_RETRIES = 3

        while len(results) < limit:

            params = {
                "s": query,
                "post_type": "product",
                "product_cat": "0",
                "paged": page_num
            }
            url = f"{self.BASE_URL}/?{urlencode(params)}"

            navigated = False
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    
                    # ── CHECK FOR CLOUDFLARE CHALLENGE ──────────────
                    # Wait a moment and check if we're on a challenge page
                    await page.wait_for_timeout(3000)
                    
                    is_challenge = await page.query_selector("input[name='cf-turnstile-response'], #challenge-form, .cf-browser-verification")
                    if is_challenge:
                        print(f"[AddisberScraper] Cloudflare challenge detected, waiting for it to resolve... (attempt {attempt})")
                        # Give Cloudflare time to auto-resolve (stealth usually handles this)
                        await page.wait_for_timeout(8000)
                    
                    await page.wait_for_selector("li.product-col", timeout=20000)
                    await page.wait_for_timeout(1500)
                    navigated = True
                    break
                except Exception as e:
                    print(f"[AddisberScraper] Attempt {attempt}/{MAX_RETRIES} failed: {e}")
                    if attempt < MAX_RETRIES:
                        print(f"[AddisberScraper] Retrying in 3s...")
                        await page.wait_for_timeout(3000)
                    else:
                        print(f"[AddisberScraper] All retries exhausted for page {page_num}.")

            if not navigated:
                break

            cards = await page.query_selector_all("li.product-col")
            if not cards:
                print("[AddisberScraper] No card items found matching product list selectors.")
                break

            for card in cards:
                if len(results) >= limit:
                    break

                try:
                    title = ""
                    full_url = ""

                    title_el = await card.query_selector("a.data-link, div.product-image a")
                    if title_el:
                        href = await title_el.get_attribute("href") or ""
                        full_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
                        title_text = await title_el.get_attribute("aria-label")
                        if title_text:
                            title = self.clean_title(title_text.replace("\u201c", "").replace("\u201d", ""))

                    if not title:
                        desc_el = await card.query_selector("div.product-content")
                        if desc_el:
                            title = self.clean_title(await desc_el.inner_text())

                    if not title:
                        continue

                    image_url = ""
                    img_el = await card.query_selector("div.product-image img")
                    if img_el:
                        image_url = (
                            await img_el.get_attribute("src")
                            or await img_el.get_attribute("data-src")
                            or ""
                        )

                    price = ""
                    price_el = await card.query_selector("span.price, div.product-content")
                    if price_el:
                        price_text = await price_el.inner_text()
                        if price_text:
                            price_lines = [line.strip() for line in price_text.split("\n") if "Br" in line]
                            price_raw = price_lines[0] if price_lines else price_text
                            price = self.clean_price(price_raw)

                    specs_parts = []
                    card_classes = await card.get_attribute("class") or ""
                    if "instock" in card_classes:
                        specs_parts.append("In Stock")
                    elif "outofstock" in card_classes:
                        specs_parts.append("Out of Stock")
                    specs = " | ".join(filter(None, specs_parts))

                    results.append({
                        "title":       title,
                        "price":       price,
                        "image_url":   image_url,
                        "product_url": full_url,
                        "specs":       specs,
                        "description": title,
                        "location":    "Ethiopia",
                        "views":       "",
                        "site":        "addisber",
                    })

                except Exception as card_error:
                    print(f"[AddisberScraper] Element extract parsing skipped: {card_error}")
                    continue

            if len(results) >= limit:
                break

            page_num += 1

        return results[:limit]


class AradaMartScraper(BaseScraper):
    """Scraper for aradamart.net (Wix Stores).

    The site uses stable `data-hook` attributes (e.g. `grid-layout-item`, `item-price`).
    This scraper pulls title, price, image and product URL from the search results grid.
    """

    BASE_URL = "https://aradamart.net"

    async def _extract_first_text(self, page, selectors: list[str]) -> str:
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if not el:
                    continue
                text = (await el.inner_text()).strip()
                if text:
                    return text
            except Exception:
                continue
        return ""

    async def _enrich_product_details(self, detail_page, full_url: str) -> tuple[str, str]:
        """Return (specs, description) for a product page."""

        await detail_page.goto(full_url, wait_until="domcontentloaded", timeout=60000)
        await detail_page.wait_for_timeout(800)

        # Wix product pages commonly expose stable `data-hook` attributes.
        description = await self._extract_first_text(
            detail_page,
            [
                "[data-hook='product-description']",
                "[data-hook='description']",
                "[data-hook*='description']",
                "#productDescription",
                "article [data-hook*='richText']",
                "main [data-testid*='rich-text']",
            ],
        )

        if not description:
            # Many Wix product pages omit a visible description; use meta/OG description as a fallback.
            try:
                meta = await detail_page.query_selector("meta[name='description']")
                description = (await meta.get_attribute("content") or "").strip() if meta else ""
            except Exception:
                description = ""

        if not description:
            try:
                og = await detail_page.query_selector("meta[property='og:description']")
                description = (await og.get_attribute("content") or "").strip() if og else ""
            except Exception:
                description = ""

        specs_parts: list[str] = []

        # Breadcrumbs can provide category-ish context.
        try:
            breadcrumb_links = await detail_page.query_selector_all(
                "[data-hook*='breadcrumbs'] a, nav[aria-label*='Breadcrumb'] a"
            )
            crumbs = []
            for a in breadcrumb_links:
                t = (await a.inner_text()).strip()
                if t and t.lower() not in {"home"}:
                    crumbs.append(t)
            if crumbs:
                specs_parts.append(" > ".join(crumbs))
        except Exception:
            pass

        # Options (size/color/etc.) are often labeled with data-hook containing "option".
        try:
            option_nodes = await detail_page.query_selector_all(
                "[data-hook*='option'] label, [data-hook*='option'] [data-hook*='label'], [data-hook*='option'] span"
            )
            option_texts = []
            for n in option_nodes:
                t = (await n.inner_text()).strip()
                if t and 1 < len(t) <= 80:
                    option_texts.append(t)
            # de-dupe while preserving order
            seen = set()
            option_texts_deduped = []
            for t in option_texts:
                key = t.lower()
                if key in seen:
                    continue
                seen.add(key)
                option_texts_deduped.append(t)
            if option_texts_deduped:
                specs_parts.append(" | ".join(option_texts_deduped[:8]))
        except Exception:
            pass

        specs = " | ".join([p for p in specs_parts if p])
        return specs, description

    async def _extract_image_url_from_node(self, node) -> str:
        if not node:
            return ""

        async def get_attr(name: str) -> str:
            try:
                return await node.get_attribute(name) or ""
            except Exception:
                return ""

        image_url = (
            await get_attr("data-src")
            or await get_attr("src")
            or ""
        )

        # If src is a placeholder (e.g. data URI), try srcset.
        if not image_url or image_url.startswith("data:"):
            srcset = await get_attr("srcset")
            if srcset:
                image_url = srcset.split(",")[0].strip().split(" ")[0]

        # Wix sometimes stores structured info in JSON attributes.
        if not image_url or image_url.startswith("data:"):
            info = await get_attr("data-image-info") or await get_attr("data-image-json")
            if info:
                try:
                    data = json.loads(info)
                    if isinstance(data, dict):
                        image_url = (
                            data.get("url")
                            or (data.get("imageData") or {}).get("url")
                            or (data.get("imageData") or {}).get("uri")
                            or image_url
                        )
                except Exception:
                    pass

        if not image_url or image_url.startswith("data:"):
            image_url = await get_attr("data-pin-media") or image_url

        return image_url

    async def _extract_main_product_image(self, page) -> str:
        candidates = [
            "img[data-hook*='product-image']",
            "img[data-hook*='gallery']",
            "main img[srcset]",
            "main img[src]",
        ]
        for sel in candidates:
            try:
                node = await page.query_selector(sel)
                if not node:
                    continue
                url = await self._extract_image_url_from_node(node)
                if url and not url.startswith("data:"):
                    return url
            except Exception:
                continue
        return ""

    async def search(self, query: str, page, limit: int = 10) -> list[dict]:
        q = quote_plus(query or "")
        url = f"{self.BASE_URL}/search?q={q}"

        # Occasionally Playwright can hit transient network-change errors on Wix sites.
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                last_err = None
                break
            except Exception as e:
                last_err = e
                if "ERR_NETWORK_CHANGED" in str(e) and attempt < 2:
                    await page.wait_for_timeout(1200)
                    continue
                raise

        try:
            await page.wait_for_selector("li[data-hook='grid-layout-item']", timeout=20000)
        except Exception:
            return []

        # Wix grids often lazy-load more items as you scroll.
        max_scrolls = 25
        last_count = 0
        for _ in range(max_scrolls):
            cards = await page.query_selector_all("li[data-hook='grid-layout-item']")
            if len(cards) >= limit:
                break
            if len(cards) == last_count:
                await page.wait_for_timeout(500)
            last_count = len(cards)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(800)

        cards = await page.query_selector_all("li[data-hook='grid-layout-item']")
        results: list[dict] = []

        for card in cards:
            if len(results) >= limit:
                break

            # Title + URL
            title = ""
            raw_url = ""
            title_link = await card.query_selector("a[data-hook='product-item-title']")
            if title_link:
                title = await title_link.inner_text()
                raw_url = await title_link.get_attribute("href") or ""
            else:
                # Fallback: any product page link
                a = await card.query_selector("a[href*='/product-page/']")
                if a:
                    title = (await a.inner_text()) or (await a.get_attribute("title") or "")
                    raw_url = await a.get_attribute("href") or ""

            title = self.clean_title(title)
            if not title and not raw_url:
                continue

            full_url = self.build_url(self.BASE_URL, raw_url)

            # Price
            price = ""
            price_el = await card.query_selector("[data-hook='item-price']")
            if not price_el:
                price_el = await card.query_selector("[data-hook='product-item-price-to-pay']")
            if price_el:
                price = self.clean_price(await price_el.inner_text())

            # Image
            image_url = ""
            img = await card.query_selector("img")
            if img:
                image_url = await self._extract_image_url_from_node(img)

            results.append({
                "title": title,
                "price": price,
                "image_url": image_url,
                "product_url": full_url,
                "specs": "",
                "description": "",
                "location": "",
                "views": "",
                "site": "aradamart",
            })

        # Enrich specs/description by visiting product pages.
        if results:
            detail_page = await page.context.new_page()
            try:
                for item in results:
                    full_url = item.get("product_url") or ""
                    if not full_url:
                        continue
                    try:
                        specs, description = await self._enrich_product_details(detail_page, full_url)
                        if specs:
                            item["specs"] = specs
                        if description:
                            item["description"] = description

                        # If card images are lazy/placeholder, pull the main image from product page.
                        if not item.get("image_url") or str(item.get("image_url", "")).startswith("data:"):
                            main_image = await self._extract_main_product_image(detail_page)
                            if main_image:
                                item["image_url"] = main_image
                    except Exception:
                        continue
            finally:
                await detail_page.close()

        return results[:limit]




class MekinaScraper(BaseScraper):
    """Scraper for mekina.net (Next.js car marketplace).

    The site uses Tailwind CSS class selectors and a Swiper-based image slider.
    This scraper pulls title, price, image, specs, and product URL from car listing pages.
    """

    BASE_URL = "https://www.mekina.net"

    async def _extract_first_text(self, page, selectors: list[str]) -> str:
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if not el:
                    continue
                text = (await el.inner_text()).strip()
                if text:
                    return text
            except Exception:
                continue
        return ""

    async def _enrich_product_details(self, detail_page, full_url: str) -> tuple[str, str]:
        """Return (specs, description) for a car listing page."""

        await detail_page.goto(full_url, wait_until="domcontentloaded", timeout=60000)
        await detail_page.wait_for_timeout(1000)

        description = await self._extract_first_text(
            detail_page,
            [
                "section[class*='description']",
                "div[class*='description']",
                "p[class*='description']",
                "meta[name='description']",
            ],
        )

        if not description:
            try:
                meta = await detail_page.query_selector("meta[name='description']")
                description = (await meta.get_attribute("content") or "").strip() if meta else ""
            except Exception:
                description = ""

        if not description:
            try:
                og = await detail_page.query_selector("meta[property='og:description']")
                description = (await og.get_attribute("content") or "").strip() if og else ""
            except Exception:
                description = ""

        specs_parts: list[str] = []

        # Specifications table: rows with label/value pairs (Brand, Model, Year, Fuel, etc.)
        try:
            spec_rows = await detail_page.query_selector_all(
                "div[class*='Specifications'] div[class*='grid'] > div, "
                "section div[class*='grid'] > div"
            )
            spec_pairs: list[str] = []
            labels_seen: list[str] = []
            values_seen: list[str] = []
            for row in spec_rows:
                text = (await row.inner_text()).strip()
                if text:
                    # Alternate label/value pattern
                    if len(labels_seen) == len(values_seen):
                        labels_seen.append(text)
                    else:
                        values_seen.append(text)
                        spec_pairs.append(f"{labels_seen[-1]}: {text}")
            if spec_pairs:
                specs_parts.append(" | ".join(spec_pairs))
        except Exception:
            pass

        # Fallback: try dl/dt/dd pairs
        if not specs_parts:
            try:
                dts = await detail_page.query_selector_all("dt")
                dds = await detail_page.query_selector_all("dd")
                pairs = []
                for dt, dd in zip(dts, dds):
                    label = (await dt.inner_text()).strip()
                    value = (await dd.inner_text()).strip()
                    if label and value:
                        pairs.append(f"{label}: {value}")
                if pairs:
                    specs_parts.append(" | ".join(pairs))
            except Exception:
                pass

        # Location / seller type
        try:
            seller_type = await self._extract_first_text(
                detail_page,
                [
                    "span[class*='broker']",
                    "span[class*='seller']",
                    "div[class*='seller-type']",
                ],
            )
            if seller_type:
                specs_parts.append(f"Seller: {seller_type}")
        except Exception:
            pass

        specs = " | ".join([p for p in specs_parts if p])
        return specs, description

    async def _extract_image_url_from_node(self, node) -> str:
        if not node:
            return ""

        async def get_attr(name: str) -> str:
            try:
                return await node.get_attribute(name) or ""
            except Exception:
                return ""

        # mekina uses Next.js Image with srcset; prefer highest-res srcset entry
        srcset = await get_attr("srcset")
        if srcset:
            # srcset entries: "url Xw, url Yw" — pick the last (largest)
            entries = [e.strip() for e in srcset.split(",") if e.strip()]
            if entries:
                return entries[-1].strip().split(" ")[0]

        image_url = await get_attr("src") or ""
        if image_url and not image_url.startswith("data:"):
            return image_url

        image_url = await get_attr("data-src") or ""
        return image_url

    async def _extract_main_product_image(self, page) -> str:
        """Pull the first slide image from the Swiper carousel on the listing page."""
        candidates = [
            "div.swiper-slide-active img",
            "div[class*='swiper-slide'] img",
            "main img[srcset]",
            "main img[src]",
        ]
        for sel in candidates:
            try:
                node = await page.query_selector(sel)
                if not node:
                    continue
                url = await self._extract_image_url_from_node(node)
                if url and not url.startswith("data:"):
                    # mekina Next.js image URLs may be relative — make absolute
                    if url.startswith("/"):
                        url = self.BASE_URL + url
                    return url
            except Exception:
                continue
        return ""

    async def search(self, query: str, page, limit: int = 10) -> list[dict]:
        q = quote_plus(query or "")
        url = f"{self.BASE_URL}/cars/search?s={q}"

        last_err: Exception | None = None
        for attempt in range(3):
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                last_err = None
                break
            except Exception as e:
                last_err = e
                if "ERR_NETWORK_CHANGED" in str(e) and attempt < 2:
                    await page.wait_for_timeout(1200)
                    continue
                raise

        # Wait for the client-rendered listing cards to hydrate.
        cards_ready = False
        for _ in range(40):
            try:
                cards = await page.query_selector_all("div.grid a[href^='/cars/']")
                cards = [c for c in cards if await self._is_listing_link(c)]
                if cards:
                    cards_ready = True
                    break
            except Exception:
                pass
            await page.wait_for_timeout(500)

        if not cards_ready:
            print("[MekinaScraper] No car listing cards found after initial load.")
            return []

        # Scroll to lazy-load more cards
        max_scrolls = 25
        last_count = 0
        for _ in range(max_scrolls):
            cards = await page.query_selector_all("div.grid a[href^='/cars/']")
            cards = [c for c in cards if await self._is_listing_link(c)]
            if len(cards) >= limit:
                break
            if len(cards) == last_count:
                await page.wait_for_timeout(500)
            last_count = len(cards)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(800)

        cards = await page.query_selector_all("div.grid a[href^='/cars/']")
        cards = [c for c in cards if await self._is_listing_link(c)]

        results: list[dict] = []
        seen_urls: set[str] = set()

        for card in cards:
            if len(results) >= limit:
                break

            raw_url = await card.get_attribute("href") or ""
            full_url = self.build_url(self.BASE_URL, raw_url)

            if not full_url or full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # Title — h2 or h3 inside the card, or the card's aria-label
            title = ""
            for title_sel in [
                "p.line-clamp-2",
                "p",
                "h2",
                "h3",
                "h1",
                "[class*='title']",
                "[class*='name']",
            ]:
                try:
                    el = await card.query_selector(title_sel)
                    if el:
                        title = (await el.inner_text()).strip()
                        if title:
                            break
                except Exception:
                    continue
            if not title:
                try:
                    img = await card.query_selector("img[alt]")
                    if img:
                        title = (await img.get_attribute("alt") or "").strip()
                except Exception:
                    pass
            if not title:
                title = await card.get_attribute("aria-label") or ""

            title = self.clean_title(title)

            # Price — look for ETB amounts
            price = ""
            for price_sel in [
                "span.text-xs.font-semibold.text-white",
                "div.absolute.bottom-0.left-0.right-0 span",
                "[class*='price']",
                "span[class*='ETB']",
                "p[class*='price']",
            ]:
                try:
                    el = await card.query_selector(price_sel)
                    if el:
                        price_text = self.clean_price(await el.inner_text())
                        if price_text and any(token in price_text.upper() for token in ["ETB", "USD", "$"]):
                            price = price_text
                            break
                        if price:
                            break
                except Exception:
                    continue

            if not price:
                try:
                    text_nodes = await card.query_selector_all("span, div, p")
                    for node in text_nodes:
                        text = self.clean_price(await node.inner_text())
                        if text and any(token in text.upper() for token in ["ETB", "USD", "$"]):
                            price = text
                            break
                except Exception:
                    pass

            # Image — first img inside the card
            image_url = ""
            try:
                img = await card.query_selector("img")
                if img:
                    image_url = await self._extract_image_url_from_node(img)
                    if image_url and image_url.startswith("/"):
                        image_url = self.BASE_URL + image_url
            except Exception:
                pass

            if not title and not full_url:
                continue

            results.append({
                "title": title,
                "price": price,
                "image_url": image_url,
                "product_url": full_url,
                "specs": "",
                "description": "",
                "location": "",
                "views": "",
                "site": "mekina",
            })

        # Enrich by visiting each listing page
        if results:
            detail_page = await page.context.new_page()
            try:
                for item in results:
                    full_url = item.get("product_url") or ""
                    if not full_url:
                        continue
                    try:
                        specs, description = await self._enrich_product_details(detail_page, full_url)
                        if specs:
                            item["specs"] = specs
                        if description:
                            item["description"] = description

                        # Extract views count ("87 car buyers looking online right now")
                        try:
                            views_el = await detail_page.query_selector(
                                "div[class*='rounded'] p, span[class*='views'], div[class*='viewers']"
                            )
                            if views_el:
                                views_text = (await views_el.inner_text()).strip()
                                if any(c.isdigit() for c in views_text):
                                    item["views"] = views_text
                        except Exception:
                            pass

                        # Upgrade placeholder image with actual listing photo
                        if not item.get("image_url") or str(item.get("image_url", "")).startswith("data:"):
                            main_image = await self._extract_main_product_image(detail_page)
                            if main_image:
                                item["image_url"] = main_image

                        # Location / city
                        try:
                            loc = await self._extract_first_text(
                                detail_page,
                                [
                                    "[class*='location']",
                                    "span[class*='city']",
                                    "div[class*='address']",
                                ],
                            )
                            if loc:
                                item["location"] = loc
                        except Exception:
                            pass

                    except Exception:
                        continue
            finally:
                await detail_page.close()

        return results[:limit]

    async def _is_listing_link(self, anchor) -> bool:
        """Return True only for car listing links (not nav/brand/category links)."""
        try:
            href = await anchor.get_attribute("href") or ""
            # Listing URLs look like /cars/make-model-year-...-<numeric-id>
            # Exclude pure brand/filter pages like /cars/toyota
            parts = [p for p in href.split("/") if p]
            if len(parts) < 2:
                return False
            # Must have at least one hyphenated slug with a digit (the listing ID suffix)
            last = parts[-1]
            return "-" in last and any(c.isdigit() for c in last)
        except Exception:
            return False










class HellooMarketScraper(BaseScraper):
    BASE_URL = "https://helloomarket.com"

    async def search(self, query: str, page, limit: int = 10) -> list[dict]:
        results = []
        page_num = 0  # OpenCart uses &start=0, 20, 40 (not page numbers)

        while len(results) < limit:

            # ── BUILD URL ──────────────────────────────────────────
            # OpenCart search URL:
            # /index.php?route=product/search&search=laptop&start=0&limit=20
            params = {
                "route":  "product/search",
                "search": query,
                "start":  page_num * 20,   # 0, 20, 40, 60...
                "limit":  20,
            }
            url = f"{self.BASE_URL}/index.php?{urlencode(params)}"

            # ── OPEN PAGE ──────────────────────────────────────────
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector(
                    ".product-block", timeout=10000
                )
                await page.wait_for_timeout(500)
            except Exception:
                break

            # ── GET ALL CARDS ──────────────────────────────────────
            # from your HTML:
            # <div class="product-items first_item_tm" style="width: 316px;">
            #   <div class="product-block product-thumb transition" ...>
            #     <div class="product-block-inner">
            #       <div class="image">...</div>
            #       <div class="product-details">
            #         <div class="caption">
            #           <h4><a href="...">title</a></h4>
            #           <p class="price">ETB1,387.00</p>
            #           <div class="rating">...</div>
            cards = await page.query_selector_all(".product-block.product-thumb")

            if not cards:
                break

            for card in cards:
                if len(results) >= limit:
                    break

                # ── TITLE ──────────────────────────────────────────
                # <h4><a href="...">Genuine Leather Women's Shoulder Bag</a></h4>
                title = ""
                title_el = await card.query_selector("div.caption h4 a")
                if title_el:
                    title = self.clean_title(await title_el.inner_text())

                # ── PRODUCT URL ────────────────────────────────────
                # href="https://helloomarket.com/index.php?route=product/product&product_id=5989"
                full_url = ""
                if title_el:
                    full_url = await title_el.get_attribute("href") or ""
                # make absolute if relative
                if full_url and not full_url.startswith("http"):
                    full_url = self.BASE_URL + full_url

                # ── IMAGE ──────────────────────────────────────────
                # <div class="image">
                #   <img src="https://helloomarket.com/image/cache/...jpg">
                # </div>
                image_url = ""
                img_el = await card.query_selector("div.image img")
                if img_el:
                    image_url = (
                        await img_el.get_attribute("src")
                        or await img_el.get_attribute("data-src")
                        or ""
                    )

                # ── PRICE ──────────────────────────────────────────
                # <p class="price">ETB1,387.00</p>
                price = ""
                price_el = await card.query_selector("p.price")
                if price_el:
                    price = self.clean_price(await price_el.inner_text())

                # ══════════════════════════════════════════════════
                # VARIABLE 1 — specs
                # rating stars count + any badge on card
                # ══════════════════════════════════════════════════
                specs_parts = []

                # star rating — count filled stars
                # <div class="rating">
                #   <span class="fa fa-star"></span> × N
                # </div>
                rating_el = await card.query_selector("div.rating")
                if rating_el:
                    # count filled star spans
                    stars = await card.query_selector_all(
                        "div.rating .fa-star"
                    )
                    filled = await card.query_selector_all(
                        "div.rating .fa-star.checked, "
                        "div.rating .fa-star-o + .fa-star, "
                        "div.rating span[class='fa fa-star']"
                    )
                    if stars:
                        specs_parts.append(f"Rating: {len(filled)}/{len(stars)} stars")

                # "ADD TO CART" button present = in stock
                cart_el = await card.query_selector("button[onclick*='cart.add']")
                if cart_el:
                    specs_parts.append("In Stock")

                specs = " | ".join(filter(None, specs_parts))

                # ══════════════════════════════════════════════════
                # VARIABLE 2 — description
                # This site doesn't show description on cards
                # so we store the product ID from the URL
                # e.g "product_id=5989"
                # ══════════════════════════════════════════════════
                description = ""
                if "product_id=" in full_url:
                    product_id = full_url.split("product_id=")[-1].split("&")[0]
                    description = f"product_id={product_id}"

                # ══════════════════════════════════════════════════
                # VARIABLE 3 — location
                # helloomarket doesn't show per-listing location on cards
                # but it's an Ethiopian marketplace so we set default
                # ══════════════════════════════════════════════════
                location = "Ethiopia"

                # ── VIEWS ──────────────────────────────────────────
                # not shown on cards on this site
                views = ""

                results.append({
                    "title":       title,
                    "price":       price,
                    "image_url":   image_url,
                    "product_url": full_url,
                    "specs":       specs,        # rating + stock status
                    "description": description,  # product_id
                    "location":    location,     # Ethiopia (default)
                    "views":       views,        # not available on cards
                    "site":        "helloomarket",
                })

            page_num += 1

        return results[:limit]









class BrundoScraper(BaseScraper):
    BASE_URL = "https://brundo.net"

    async def search(self, query: str, page, limit: int = 10) -> list[dict]:
        results = []
        page_num = 1

        while len(results) < limit:

            # ── BUILD URL ──────────────────────────────────────────
            # WooCommerce search URL:
            # /?s=laptop&post_type=product&paged=1
            params = {
                "s":         query,
                "post_type": "product",
                "paged":     page_num,
            }
            url = f"{self.BASE_URL}/?{urlencode(params)}"

            # ── OPEN PAGE ──────────────────────────────────────────
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector(
                    "li.wvs-archive-product-wrapper", timeout=10000
                )
                await page.wait_for_timeout(1500)  # let lazy images load
            except Exception:
                break

            # ── GET ALL CARDS ──────────────────────────────────────
            # <li class="wvs-archive-product-wrapper product type-product
            #            post-109000 status-publish first instock
            #            product_cat-formal-shoes has-post-thumbnail
            #            shipping-taxable purchasable product-type-variable">
            cards = await page.query_selector_all("li.wvs-archive-product-wrapper")

            if not cards:
                break

            for card in cards:
                if len(results) >= limit:
                    break

                # ── TITLE ──────────────────────────────────────────
                # <h2 class="woocommerce-loop-product__title">
                #   <a class="woocommerce-LoopProduct-link ...">
                #     Bruno Marc Men'S Maxflex Fashion Dress Sneakers
                #   </a>
                # </h2>
                title = ""
                title_el = await card.query_selector(
                    "h2.woocommerce-loop-product__title a"
                )
                if title_el:
                    title = self.clean_title(await title_el.inner_text())

                # ── PRODUCT URL ────────────────────────────────────
                # <a href="https://brundo.net/product/bruno-marc-mens-maxflex-.../">
                full_url = ""
                if title_el:
                    full_url = await title_el.get_attribute("href") or ""
                # fallback to the wrapper link
                if not full_url:
                    link_el = await card.query_selector(
                        "a.woocommerce-LoopProduct-link"
                    )
                    if link_el:
                        full_url = await link_el.get_attribute("href") or ""

                # ── IMAGE ──────────────────────────────────────────
                # Images are lazy-loaded two ways on this site:
                # WAY 1: <span data-bg="https://...jpg" class="product-loop-hover-image rocket-lazyload">
                # WAY 2: <img src="https://...jpg" class="product-loop-image ...">
                image_url = ""

                # try the real <img> first
                img_el = await card.query_selector(
                    ".product-loop-image-wrapper img"
                )
                if img_el:
                    image_url = (
                        await img_el.get_attribute("src")
                        or await img_el.get_attribute("data-lazy-src")
                        or await img_el.get_attribute("data-src")
                        or ""
                    )

                # fallback: span with data-bg (hover image)
                if not image_url:
                    span_el = await card.query_selector("span[data-bg]")
                    if span_el:
                        image_url = await span_el.get_attribute("data-bg") or ""

                # ── PRICE ──────────────────────────────────────────
                # <span class="woocommerce-Price-amount amount">
                #   <bdi>11,584.30 Br</bdi>
                # </span>
                # some products show a range: "16,005.08 Br – 16,005.08 Br"
                price = ""
                price_el = await card.query_selector(
                    "span.woocommerce-Price-amount.amount"
                )
                if price_el:
                    price = self.clean_price(await price_el.inner_text())

                # ══════════════════════════════════════════════════
                # VARIABLE 1 — specs
                # stock status + product type + category from li classes
                # ══════════════════════════════════════════════════
                specs_parts = []

                card_classes = await card.get_attribute("class") or ""

                # stock status from li class
                if "instock" in card_classes:
                    specs_parts.append("In Stock")
                elif "outofstock" in card_classes:
                    specs_parts.append("Out of Stock")

                # product type: simple / variable / external
                if "product-type-variable" in card_classes:
                    specs_parts.append("Variable Product")
                elif "product-type-simple" in card_classes:
                    specs_parts.append("Simple Product")

                # on-sale badge
                sale_el = await card.query_selector(".onsale")
                if sale_el:
                    specs_parts.append("ON SALE")

                # rating
                rating_el = await card.query_selector(
                    ".star-rating span[style*='width']"
                )
                if rating_el:
                    # WooCommerce sets width % for rating
                    # 100% = 5 stars, 80% = 4 stars etc.
                    style = await rating_el.get_attribute("style") or ""
                    if "width:" in style:
                        width_str = style.split("width:")[1].split("%")[0].strip()
                        try:
                            stars = round(float(width_str) / 20)
                            specs_parts.append(f"Rating: {stars}/5 stars")
                        except ValueError:
                            pass

                specs = " | ".join(filter(None, specs_parts))

                # ══════════════════════════════════════════════════
                # VARIABLE 2 — description
                # WooCommerce doesn't show description on listing cards
                # We extract the product category from the li class
                # e.g "product_cat-formal-shoes" → "formal shoes"
                # ══════════════════════════════════════════════════
                description = ""
                for cls in card_classes.split():
                    if cls.startswith("product_cat-"):
                        cat = cls.replace("product_cat-", "").replace("-", " ")
                        description = f"Category: {cat}"
                        break

                # ══════════════════════════════════════════════════
                # VARIABLE 3 — location
                # Brundo is an Ethiopian store, no per-listing location
                # ══════════════════════════════════════════════════
                location = "Ethiopia"

                # ── VIEWS ──────────────────────────────────────────
                # not shown on listing cards
                views = ""

                results.append({
                    "title":       title,
                    "price":       price,
                    "image_url":   image_url,
                    "product_url": full_url,
                    "specs":       specs,
                    "description": description,
                    "location":    location,
                    "views":       views,
                    "site":        "brundo",
                })

            page_num += 1

        return results[:limit]
    






class DeamatScraper(BaseScraper):
    BASE_URL = "https://www.daamat.com"

    async def search(self, query: str, page, limit: int = 10) -> list[dict]:
        results = []
        page_num = 1

        while len(results) < limit:

            # ── BUILD URL ──────────────────────────────────────────
            # Deamat's public search route currently returns 404.
            # The homepage renders the live catalog cards, so we load it
            # and filter the cards locally.
            url = f"{self.BASE_URL}/"

            # ── OPEN PAGE ──────────────────────────────────────────
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # wait for product cards — React needs time to render
                await page.wait_for_selector(
                    "a[href*='/shops/deamat/products/']", timeout=12000
                )
                await page.wait_for_timeout(1500)
            except Exception:
                break

            # ── GET ALL CARDS ──────────────────────────────────────
            # <a class="block space-y-3 w-44"
            #    href="/shops/deamat/products/airfiber-60-long-range"
            #    data-discover="true">
            #   <img src="/products/airfiber-long-range.avif" ...>
            #   <div class="text-gray-500 space-y-1">
            #     <p class="line-clamp-2 text-sm font-semibold truncate">
            #       airFiber 60 Long-Range
            #     </p>
            #     <p class="text-xs line-clamp-4 text-gray-400 h-16">
            #       description text...
            #     </p>
            #   </div>
            #   <button>Add to Cart</button>
            # </a>
            cards = await page.query_selector_all(
                "a[href*='/products/']"
            )

            # filter out nav links — only cards that have an img inside
            product_cards = []
            for card in cards:
                img = await card.query_selector("img")
                if img:
                    product_cards.append(card)

            if not product_cards:
                break

            for card in product_cards:
                if len(results) >= limit:
                    break

                # ── TITLE ──────────────────────────────────────────
                # <p class="line-clamp-2 text-sm font-semibold truncate">
                #   airFiber 60 Long-Range
                # </p>
                title = ""
                title_el = await card.query_selector(
                    "p.line-clamp-2.font-semibold"
                )
                if not title_el:
                    title_el = await card.query_selector(
                        "p.font-semibold"
                    )
                if title_el:
                    title = self.clean_title(await title_el.inner_text())

                # ── PRODUCT URL ────────────────────────────────────
                # href="/shops/deamat/products/airfiber-60-long-range"
                full_url = ""
                raw_url = await card.get_attribute("href") or ""
                if raw_url.startswith("http"):
                    full_url = raw_url
                elif raw_url:
                    full_url = f"{self.BASE_URL}/{raw_url.lstrip('/')}"

                # ── IMAGE ──────────────────────────────────────────
                # <img width="100" height="100"
                #      alt="airFiber 60 Long-Range"
                #      class="object-cover h-28 w-36 rounded
                #             opacity-80 border border-gray-100/50 bg-gray-50"
                #      src="/products/airfiber-long-range.avif">
                image_url = ""
                img_el = await card.query_selector("img.object-cover")
                if not img_el:
                    img_el = await card.query_selector("img")
                if img_el:
                    raw_img = (
                        await img_el.get_attribute("src")
                        or await img_el.get_attribute("data-src")
                        or ""
                    )
                    # make absolute
                    if raw_img and not raw_img.startswith("http"):
                        image_url = f"{self.BASE_URL}/{raw_img.lstrip('/')}"
                    else:
                        image_url = raw_img

                # ── PRICE ──────────────────────────────────────────
                # shown as: ETB 32,456.99  ETB 35,703.00 (strikethrough)
                price = ""
                # Current price is the first <p> inside the flex row.
                price_el = await card.query_selector(
                    "div.flex.space-x-2 p:not(.line-through)"
                )
                if not price_el:
                    price_el = await card.query_selector(
                        "div.flex.space-x-2 p"
                    )
                if not price_el:
                    price_el = await card.query_selector("span.price")
                if not price_el:
                    price_el = await card.query_selector("[class*='price']")
                if price_el:
                    price = self.clean_price(await price_el.inner_text())

                # ══════════════════════════════════════════════════
                # VARIABLE 1 — specs
                # original price (if on sale) + shop name
                # ══════════════════════════════════════════════════
                specs_parts = []

                # original/old price (strikethrough = was on sale)
                old_price_el = await card.query_selector(
                    "span.line-through"
                )
                if old_price_el:
                    old_price = (await old_price_el.inner_text()).strip()
                    if old_price:
                        specs_parts.append(f"Was: {old_price}")
                        specs_parts.append("ON SALE")

                # shop name from URL e.g "/shops/deamat/products/..."
                if "/shops/" in raw_url:
                    shop = raw_url.split("/shops/")[1].split("/")[0]
                    specs_parts.append(f"Shop: {shop}")

                # "Add to Cart" button = in stock
                cart_btn = await card.query_selector("button")
                if cart_btn:
                    btn_text = (await cart_btn.inner_text()).strip().lower()
                    if "add to cart" in btn_text:
                        specs_parts.append("In Stock")
                    elif "out of stock" in btn_text:
                        specs_parts.append("Out of Stock")

                specs = " | ".join(filter(None, specs_parts))

                # ══════════════════════════════════════════════════
                # VARIABLE 2 — description
                # <p class="text-xs line-clamp-4 text-gray-400 h-16">
                #   Long-range 60 GHz radio system that pairs in PtP mode
                #   or connects to a Wave AP as a client in PtMP mode.
                # </p>
                # ══════════════════════════════════════════════════
                description = ""
                desc_el = await card.query_selector(
                    "p.text-xs.line-clamp-4"
                )
                if not desc_el:
                    desc_el = await card.query_selector(
                        "p.text-gray-400"
                    )
                if desc_el:
                    description = (await desc_el.inner_text()).strip()

                # ══════════════════════════════════════════════════
                # VARIABLE 3 — location
                # Deamat is Ethiopian, no per-card location shown
                # ══════════════════════════════════════════════════
                location = "Ethiopia"

                # views not shown on cards
                views = ""

                results.append({
                    "title":       title,
                    "price":       price,
                    "image_url":   image_url,
                    "product_url": full_url,
                    "specs":       specs,
                    "description": description,
                    "location":    location,
                    "views":       views,
                    "site":        "deamat",
                })

            page_num += 1

        return results[:limit]



class EthioSuQScraper(BaseScraper):
    BASE_URL = "https://ethiosuq.com"

    async def search(self, query: str, page, limit: int = 10) -> list[dict]:
        results = []
        page_num = 1

        while len(results) < limit:
            params = {
                "s": query,
                "post_type": "product",
                "paged": page_num,
            }
            url = f"{self.BASE_URL}/?{urlencode(params)}"

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector("li.product", timeout=12000)
                await page.wait_for_timeout(1200)
            except Exception:
                break

            cards = await page.query_selector_all("li.product")
            product_cards = []
            for card in cards:
                try:
                    link_el = await card.query_selector("a[href*='/product/']")
                    img_el = await card.query_selector("img")
                    if link_el and img_el:
                        product_cards.append(card)
                except Exception:
                    continue

            if not product_cards:
                break

            for card in product_cards:
                if len(results) >= limit:
                    break

                title = ""
                title_el = await card.query_selector("h2.woocommerce-loop-product__title a")
                if not title_el:
                    title_el = await card.query_selector("h2.woocommerce-loop-product__title")
                if title_el:
                    title = self.clean_title(await title_el.inner_text())

                if not title:
                    img_el = await card.query_selector("img[alt]")
                    if img_el:
                        title = self.clean_title(await img_el.get_attribute("alt") or "")

                full_url = ""
                if title_el:
                    full_url = await title_el.get_attribute("href") or ""
                if not full_url:
                    link_el = await card.query_selector("a.woocommerce-LoopProduct-link")
                    if not link_el:
                        link_el = await card.query_selector("a[href*='/product/']")
                    if link_el:
                        full_url = await link_el.get_attribute("href") or ""

                if full_url and not full_url.startswith("http"):
                    full_url = f"{self.BASE_URL}/{full_url.lstrip('/')}"

                image_url = ""
                img_el = await card.query_selector("img")
                if img_el:
                    image_url = (
                        await img_el.get_attribute("src")
                        or await img_el.get_attribute("data-src")
                        or await img_el.get_attribute("data-lazy-src")
                        or ""
                    )
                    if image_url and not image_url.startswith("http"):
                        image_url = f"{self.BASE_URL}/{image_url.lstrip('/')}"

                price = ""
                price_el = await card.query_selector("span.woocommerce-Price-amount.amount")
                if not price_el:
                    price_el = await card.query_selector("p.price span.woocommerce-Price-amount")
                if price_el:
                    price = self.clean_price(await price_el.inner_text())

                specs_parts = []
                card_classes = await card.get_attribute("class") or ""
                if "instock" in card_classes:
                    specs_parts.append("In Stock")
                elif "outofstock" in card_classes:
                    specs_parts.append("Out of Stock")

                if "product-type-variable" in card_classes:
                    specs_parts.append("Variable Product")
                elif "product-type-simple" in card_classes:
                    specs_parts.append("Simple Product")

                sale_el = await card.query_selector(".onsale")
                if sale_el:
                    specs_parts.append("ON SALE")

                for cls in card_classes.split():
                    if cls.startswith("product_cat-"):
                        cat = cls.replace("product_cat-", "").replace("-", " ")
                        specs_parts.append(f"Category: {cat}")
                        break

                specs = " | ".join(filter(None, specs_parts))

                description = ""
                desc_el = await card.query_selector(".product_short_desc, .product-description, .woocommerce-loop-product__title")
                if desc_el:
                    description = (await desc_el.inner_text()).strip()

                location = "Ethiopia"
                views = ""

                results.append({
                    "title":       title,
                    "price":       price,
                    "image_url":   image_url,
                    "product_url": full_url,
                    "specs":       specs,
                    "description": description,
                    "location":    location,
                    "views":       views,
                    "site":        "ethiosuq",
                })

            page_num += 1

        return results[:limit]
    