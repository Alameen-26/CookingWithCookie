"""Optional web search used to ground Ask Cookie's general cooking answers.

Only general cooking, recipe and nutrition questions are searched. Facts
about Cooking with Cookie itself (menu, allergens, prices, ordering) always
come from the local database, never from the web.

Providers are pluggable: each one is a function that takes (query, api_key,
max_results, timeout) and returns a list of {"title", "url", "snippet"} dicts.
Choose one with SEARCH_PROVIDER (tavily or brave) and set SEARCH_API_KEY.
Uses only the Python standard library, so there is nothing extra to install.
"""
import json
import logging
import os
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 6  # seconds; the chat answers without web results if slower
MAX_RESULTS = 3
MAX_SNIPPET_LENGTH = 400
MAX_QUERY_LENGTH = 200
USER_AGENT = "CookingWithCookie/1.0"


def _http_json(url, payload=None, headers=None, timeout=DEFAULT_TIMEOUT):
    """GET (payload None) or POST JSON to url and return the decoded JSON."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    request.add_header("User-Agent", USER_AGENT)
    request.add_header("Accept", "application/json")
    if data:
        request.add_header("Content-Type", "application/json")
    for name, value in (headers or {}).items():
        request.add_header(name, value)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def search_tavily(query, api_key, max_results, timeout):
    """Tavily Search API (https://tavily.com)."""
    data = _http_json(
        "https://api.tavily.com/search",
        payload={"query": query, "max_results": max_results, "search_depth": "basic"},
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=timeout,
    )
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
        for r in data.get("results", [])
    ]


def search_brave(query, api_key, max_results, timeout):
    """Brave Search API (https://brave.com/search/api/)."""
    params = urllib.parse.urlencode({"q": query, "count": max_results})
    data = _http_json(
        f"https://api.search.brave.com/res/v1/web/search?{params}",
        headers={"X-Subscription-Token": api_key},
        timeout=timeout,
    )
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("description", "")}
        for r in data.get("web", {}).get("results", [])
    ]


PROVIDERS = {"tavily": search_tavily, "brave": search_brave}


def search_settings():
    """Return (provider function, api key), or (None, None) if search is off."""
    api_key = os.environ.get("SEARCH_API_KEY", "").strip()
    name = os.environ.get("SEARCH_PROVIDER", "").strip().lower() or "tavily"
    provider = PROVIDERS.get(name)
    if not api_key or provider is None:
        return None, None
    return provider, api_key


def search_enabled():
    return search_settings()[0] is not None


def clean_results(results, max_results=MAX_RESULTS):
    """Keep well-formed http(s) results, drop duplicates and trim snippets."""
    cleaned, seen = [], set()
    for result in results:
        if not isinstance(result, dict):
            continue
        url = str(result.get("url") or "").strip()
        if not url.startswith(("https://", "http://")) or url in seen:
            continue
        seen.add(url)
        title = " ".join(str(result.get("title") or url).split())[:150]
        snippet = " ".join(str(result.get("snippet") or "").split())
        if len(snippet) > MAX_SNIPPET_LENGTH:
            snippet = snippet[:MAX_SNIPPET_LENGTH].rsplit(" ", 1)[0] + "…"
        cleaned.append({"title": title, "url": url, "snippet": snippet})
        if len(cleaned) >= max_results:
            break
    return cleaned


def web_search(query, max_results=MAX_RESULTS, timeout=None):
    """Search the web. Returns [] if search is off, slow or fails."""
    provider, api_key = search_settings()
    if provider is None:
        return []
    if timeout is None:
        timeout = float(os.environ.get("SEARCH_TIMEOUT_SECONDS", "") or DEFAULT_TIMEOUT)
    query = " ".join(query.split())[:MAX_QUERY_LENGTH]
    try:
        return clean_results(provider(query, api_key, max_results, timeout), max_results)
    except Exception as error:  # timeout, network, bad key, unexpected JSON...
        logger.warning("Web search failed, answering without it: %s", error)
        return []
