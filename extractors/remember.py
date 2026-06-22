import urllib.parse
from .base import BaseExtractor
from bs4 import BeautifulSoup


class RememberExtractor(BaseExtractor):
    @property
    def name(self) -> str:
        return "remember"

    def extract(self, config: dict) -> list[dict]:
        max_n = config.get("max_per_site", 5)
        search = config.get("search", {})
        query = search.get("query", "")
        kw = urllib.parse.quote(query) if query else "Java"
        # 리멤버는 모바일 앱 기반 SPA — API 시도
        api_url = f"https://www.remember.co.kr/api/recruits?keyword={kw}&page=1&size=10"
        data = self.fetch_json(api_url, {"Referer": "https://www.remember.co.kr/"})
        if data and isinstance(data.get("data"), list):
            jobs = []
            for job in data["data"]:
                if len(jobs) >= max_n:
                    break
                jid = job.get("id", "")
                if not jid:
                    continue
                href = f"https://www.remember.co.kr/recruit/{jid}"
                title = job.get("title", "") or ""
                company = job.get("companyName", "") or ""
                full_title = f"[{company}] {title}" if company else title
                jobs.append({
                    "site": self.name,
                    "title": full_title[:80],
                    "url": href,
                    "url_norm": href,
                })
            return jobs

        # fallback HTML (unlikely to work for SPA)
        html = self.fetch(
            f"https://www.remember.co.kr/search?keyword={kw}",
        )
        if not html:
            print(f"  [{self.name}] SPA — requires browser automation. Disable or use manually.")
            return []
        soup = BeautifulSoup(html, "lxml")
        jobs = []
        for a in soup.select('a[href*="/recruit/"]'):
            href = self.make_absolute(a.get("href", ""), "https://www.remember.co.kr")
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
