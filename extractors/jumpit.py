import urllib.parse
from .base import BaseExtractor
from bs4 import BeautifulSoup


class JumpitExtractor(BaseExtractor):
    @property
    def name(self) -> str:
        return "jumpit"

    def extract(self, config: dict) -> list[dict]:
        max_n = config.get("max_per_site", 10)
        search = config.get("search", {})
        query = search.get("query", "")
        kw = urllib.parse.quote(query) if query else "Java"
        jobs = []
        # 점핏 API
        api_url = (
            "https://www.jumpit.co.kr/api/v1/posts"
            f"?keyword={kw}"
        )
        data = self.fetch_json(api_url, {"Referer": "https://www.jumpit.co.kr/"})
        result_list = None
        if isinstance(data, list):
            result_list = data
        elif isinstance(data, dict):
            for key in ("result", "data", "posts", "items", "list", "contents"):
                if isinstance(data.get(key), list):
                    result_list = data[key]
                    break
        if result_list is not None:
            for job in result_list:
                if len(jobs) >= max_n:
                    break
                jid = job.get("id", "") or job.get("positionId", "")
                if not jid:
                    continue
                href = f"https://www.jumpit.co.kr/position/{jid}"
                title = job.get("title", "") or job.get("position", "") or ""
                company = job.get("companyName", "") or job.get("company", "") or ""
                full_title = f"[{company}] {title}" if company else title
                jobs.append({
                    "site": self.name,
                    "title": full_title[:80],
                    "url": href,
                    "url_norm": href,
                })
            return jobs

        # fallback HTML
        html = self.fetch(
            f"https://www.jumpit.co.kr/search?keyword={kw}",
        )
        if not html:
            return []
        soup = BeautifulSoup(html, "lxml")
        for a in soup.select('a[href*="/position/"]'):
            href = self.make_absolute(a.get("href", ""), "https://www.jumpit.co.kr")
            title = self.clean_title(a.get_text(strip=True))
            if len(title) < 3:
                continue
            jobs.append({
                "site": self.name,
                "title": title[:80],
                "url": href,
                "url_norm": href,
            })
            if len(jobs) >= max_n:
                break
        return jobs
