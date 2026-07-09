import os
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from ..core.ports import JsonMap, WebSearchPort


def build_web_search_adapter() -> WebSearchPort | None:
    enabled = os.getenv("WEB_SEARCH_ENABLED", "false").lower().strip() == "true"
    return WebSearchAdapter.from_env() if enabled else None


class WebSearchAdapter(WebSearchPort):
    def __init__(self, base_url: str, timeout: float, max_results: int, user_agent: str) -> None:
        self.base_url = base_url
        self.timeout = httpx.Timeout(timeout)
        self.max_results = max(1, max_results)
        self.headers = {"User-Agent": user_agent}

    @classmethod
    def from_env(cls: type["WebSearchAdapter"]) -> "WebSearchAdapter":
        base_url = _required_env("WEB_SEARCH_BASE_URL")
        timeout = float(os.getenv("WEB_SEARCH_TIMEOUT_SECONDS", "8"))
        max_results = int(os.getenv("WEB_SEARCH_MAX_RESULTS", "3"))
        user_agent = _required_env("WEB_SEARCH_USER_AGENT")
        return cls(base_url=base_url, timeout=timeout, max_results=max_results, user_agent=user_agent)

    async def search(self, query: str) -> list[JsonMap]:
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            resp = await client.get(self.base_url, params={"q": query}, headers=self.headers)
            resp.raise_for_status()
        parser = SearchHtmlParser(self.max_results)
        parser.feed(resp.text)
        return parser.results[: self.max_results]


class SearchHtmlParser(HTMLParser):
    def __init__(self, max_results: int) -> None:
        super().__init__()
        self.max_results = max_results
        self.results: list[JsonMap] = []
        self._field, self._href = "", ""
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        classes = attr.get("class", "")
        if tag == "a" and "result__a" in classes:
            self._start("title", attr.get("href", ""))
        elif "result__snippet" in classes:
            self._start("snippet", "")

    def handle_data(self, data: str) -> None:
        if self._field:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._field == "title" and tag == "a":
            self._finish_title()
        elif self._field == "snippet" and tag in {"a", "div"}:
            self._finish_snippet()

    def _start(self, field: str, href: str) -> None:
        self._field, self._href, self._buffer = field, href, []

    def _finish_title(self) -> None:
        if len(self.results) < self.max_results:
            self.results.append({"title": _clean("".join(self._buffer)), "url": _clean_url(self._href), "snippet": ""})
        self._start("", "")

    def _finish_snippet(self) -> None:
        if self.results and not self.results[-1].get("snippet"):
            self.results[-1]["snippet"] = _clean("".join(self._buffer))
        self._start("", "")


def _clean(text: str) -> str:
    return " ".join(text.split())


def _clean_url(url: str) -> str:
    parsed = urlparse(url)
    target = parse_qs(parsed.query).get("uddg", [url])[0]
    return unquote(target)


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value
