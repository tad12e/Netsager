import hashlib
import ipaddress
from urllib.parse import urlparse

import requests
from celery.result import AsyncResult
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.scraper.tasks import scrape_all_task, scrape_task
from apps.scraper.scrape import supported_site_slugs


def _cache_key(site_slug: str, query: str) -> str:
	normalized = " ".join((query or "").strip().lower().split())
	digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()
	return f"scrape:{site_slug}:{digest}"


def _bulk_cache_key(query: str) -> str:
	normalized = " ".join((query or "").strip().lower().split())
	digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()
	return f"scrape:all:{digest}"


class SearchView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		query = (request.query_params.get("q") or "").strip()
		site = (request.query_params.get("site") or "jiji").strip().lower()
		limit = int(request.query_params.get("limit") or 30)

		if not query:
			return Response({"detail": "q is required"}, status=400)

		if site not in supported_site_slugs():
			return Response(
				{"detail": "unsupported site", "supported_sites": supported_site_slugs()},
				status=400,
			)

		key = _cache_key(site, query)
		cached = cache.get(key)
		if cached is not None:
			return Response({"status": "cached", "results": cached})

		async_result = scrape_task.delay(query, site, limit, True)
		return Response({"status": "queued", "task_id": async_result.id}, status=202)


class SearchAllView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		query = (request.query_params.get("q") or "").strip()
		limit = int(request.query_params.get("limit") or 30)
		headless = (request.query_params.get("headless") or "true").strip().lower() not in {"0", "false", "no"}

		if not query:
			return Response({"detail": "q is required"}, status=400)

		key = _bulk_cache_key(query)
		cached = cache.get(key)
		if cached is not None:
			return Response({"status": "cached", "query": query, "results": cached})

		async_result = scrape_all_task.delay(query, limit, headless)
		return Response({"status": "queued", "task_id": async_result.id, "query": query}, status=202)


class TaskStatusView(APIView):
	permission_classes = [AllowAny]

	def get(self, request, task_id: str):
		result = AsyncResult(task_id)
		payload = {"task_id": task_id, "state": result.state}

		if result.successful():
			payload["status"] = "done"
			payload["results"] = result.result
		elif result.failed():
			payload["status"] = "failed"
			payload["error"] = str(result.result)
		else:
			payload["status"] = "pending"

		return Response(payload)


class ImageProxyView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		url = (request.query_params.get("url") or "").strip()
		if not url:
			return Response({"detail": "url is required"}, status=400)

		parsed = urlparse(url)
		if parsed.scheme not in {"http", "https"}:
			return Response({"detail": "invalid url scheme"}, status=400)
		if not parsed.netloc:
			return Response({"detail": "invalid url host"}, status=400)

		host = parsed.hostname.lower() if parsed.hostname else ""
		try:
			ipaddress.ip_address(host)
			return Response({"detail": "ip hosts not allowed"}, status=400)
		except ValueError:
			pass

		allowed = {h.lower() for h in getattr(settings, "IMAGE_PROXY_ALLOWED_HOSTS", [])}
		if allowed and host not in allowed:
			return Response({"detail": "host not allowed"}, status=400)

		try:
			upstream = requests.get(url, timeout=15)
			content_type = upstream.headers.get("Content-Type") or "application/octet-stream"
			return HttpResponse(
				upstream.content,
				content_type=content_type,
				status=upstream.status_code,
			)
		except requests.RequestException:
			return Response({"detail": "unable to fetch image"}, status=400)
