import urllib.parse
from .base import BaseExtractor
from bs4 import BeautifulSoup


class IncruitExtractor(BaseExtractor):
    @property
    def name(self) -> str:
        return "incruit"

    def extract(self, config: dict) -> list[dict]:
        max_n = config.get("max_per_site", 10)
        exclude = config.get("exclude_titles", [])
        inc_keywords = config.get("include_titles", [])
        search = config.get("search", {})
        query = search.get("query", "")
        kw = urllib.parse.quote(query) if query else "Java"
        career_lv = search.get("career_level", "경력")
        career_cd = self.career_code(career_lv, self.name)
        url = (
            "https://job.incruit.com/jobdb/list/searchjob.asp"
            f"?keyword={kw}&career={career_cd or 2}"
        )
        html = self.fetch(url)
        if not html:
            return []
        soup = BeautifulSoup(html, "lxml")
        jobs = []
        for a in soup.select('a[href*="jobdb_list"]'):
            href = self.make_absolute(a.get("href", ""), "https://www.incruit.com")
            href_norm = self.normalize_url(href)
            title = self.clean_title(a.get_text(strip=True), exclude)
            if len(title) < 5:
                continue
            if not any(kw in title.lower() for kw in inc_keywords):
                continue
            jobs.append({
                "site": self.name,
                "title": title[:80],
                "url": href,
                "url_norm": href_norm,
            })
            if len(jobs) >= max_n:
                break
        # try another selector pattern
        if len(jobs) == 0:
            for a in soup.select('a[href*="Recruit"]'):
                href = self.make_absolute(a.get("href", ""), "https://www.incruit.com")
                href_norm = self.normalize_url(href)
                title = self.clean_title(a.get_text(strip=True), exclude)
                if len(title) < 5:
                    continue
                if not any(kw in title.lower() for kw in inc_keywords):
                    continue
                jobs.append({
                    "site": self.name,
                    "title": title[:80],
                    "url": href,
                    "url_norm": href_norm,
                })
                if len(jobs) >= max_n:
                    break
        return jobs
