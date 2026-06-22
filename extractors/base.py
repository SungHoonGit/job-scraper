from abc import ABC, abstractmethod
import re
import requests
import time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}


class BaseExtractor(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def extract(self, config: dict) -> list[dict]:
        ...

    def fetch(self, url: str, headers_extra: dict | None = None, timeout: int = 15) -> str | None:
        h = {**HEADERS, **(headers_extra or {})}
        try:
            r = requests.get(url, headers=h, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"  [{self.name}] fetch error: {e}")
            return None

    def fetch_json(self, url: str, headers_extra: dict | None = None, timeout: int = 10) -> dict | None:
        h = {**HEADERS, **{"Accept": "application/json, text/plain, */*"}, **(headers_extra or {})}
        try:
            r = requests.get(url, headers=h, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  [{self.name}] json error: {e}")
            return None

    @staticmethod
    def normalize_url(url: str) -> str:
        # Strip tracking query params for known sites
        track_params = [
            "adsCategoryItem", "utm_source", "utm_medium", "utm_campaign",
            "ref", "Oem_Code", "logpath", "stext", "listno", "sc",
            "view_type", "searchword", "searchType",
        ]
        if "?" in url:
            base, qs = url.split("?", 1)
            params = qs.split("&")
            kept = [p for p in params if p.split("=")[0] not in track_params]
            url = base + ("?" + "&".join(kept) if kept else "")
        url = url.rstrip("&?")
        return url

    @staticmethod
    def clean_title(raw: str, exclude: list[str] | None = None) -> str:
        if exclude:
            for kw in exclude:
                raw = raw.replace(kw, "")
        raw = re.sub(r'\s+', ' ', raw).strip()
        return raw

    @staticmethod
    def make_absolute(href: str, base: str = "") -> str:
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            return base.rstrip("/") + href
        return base.rstrip("/") + "/" + href

    @staticmethod
    def career_code(career_level: str, site: str) -> str:
        mapping = {
            "jobkorea": {"신입": "1", "경력": "2", "전체": ""},
            "saramin": {"신입": "1", "경력": "2", "전체": ""},
            "incruit": {"신입": "1", "경력": "2", "전체": ""},
        }
        return mapping.get(site, {}).get(career_level, "")

    @staticmethod
    def parse_deadline_saramin(raw: str) -> str:
        """사람인 마감일 '~07.08(수)' → '2026-07-08'"""
        m = re.search(r'(\d{2})\.(\d{2})\.?(\d{2})?', raw)
        if m:
            mm, dd = m.group(1), m.group(2)
            return f"2026-{mm}-{dd}"
        return ""

    @staticmethod
    def parse_career_years(text: str) -> tuple:
        """Parse career text like '경력2~5년', '신입', '경력 3년 이상' into (min, max)."""
        if not text:
            return (None, None)
        text = text.strip()
        if text == "신입":
            return (0, 0)
        m = re.search(r'(?:경력)?\s*(\d+)\s*~\s*(\d+)\s*년', text)
        if m:
            return (int(m.group(1)), int(m.group(2)))
        m = re.search(r'(?:경력)?\s*(\d+)\s*년\s*(?:이상|↑)', text)
        if m:
            return (int(m.group(1)), None)
        m = re.search(r'(?:경력)?\s*(\d+)\s*년(?:\s*차)?', text)
        if m:
            y = int(m.group(1))
            return (y, y)
        if "경력" in text:
            return (None, None)
        return (None, None)

    @staticmethod
    def is_deadline_passed(deadline_str: str) -> bool:
        """Check if deadline has passed"""
        from datetime import datetime
        if not deadline_str:
            return False
        today = datetime.now()
        for fmt in ("%Y-%m-%d", "%Y.%m.%d"):
            try:
                dt = datetime.strptime(deadline_str.strip(), fmt)
                return dt < today
            except ValueError:
                continue
        return False
