import re
from .base import BaseExtractor
from bs4 import BeautifulSoup


class SaraminExtractor(BaseExtractor):
    @property
    def name(self) -> str:
        return "saramin"

    def extract(self, config: dict) -> list[dict]:
        max_n = config.get("max_per_site", 15)
        exclude = config.get("exclude_titles", [])
        inc_keywords = config.get("include_titles", [])
        search = config.get("search", {})
        query = search.get("query", "")
        import urllib.parse
        site_cfg = config.get("sites", {}).get(self.name, {})
        cat_code = site_cfg.get("category_code", "235")
        # 사람인: category_code 기반 + career_level + keyword 필터
        career_lv = search.get("career_level", "")
        career_cd = self.career_code(career_lv, self.name)
        career_from = search.get("career_from")
        # 사람인 연차별 코드: 3=1년, 4=2년, ... 12=10년이상
        # career_from이 설정되면 career_level보다 우선
        if career_from is not None and career_lv != "신입":
            if career_from >= 10:
                career_cd = "12"
            elif career_from >= 1:
                career_cd = str(career_from + 2)
        url = (
            f"https://www.saramin.co.kr/zf_user/jobs/list/job-category"
            f"?cat_kewd={cat_code}"
            f"{'&career_level=' + career_cd if career_cd else ''}"
            f"{'&keyword=' + urllib.parse.quote(query) if query else ''}"
        )
        html = self.fetch(url)
        if not html:
            return []
        soup = BeautifulSoup(html, "lxml")
        jobs = []
        seen_urls = set()

        for item in soup.select("div.list_item"):
            job = self._parse_item(item, exclude, inc_keywords)
            if not job:
                continue
            if job["url_norm"] in seen_urls:
                continue
            seen_urls.add(job["url_norm"])
            jobs.append(job)
            if len(jobs) >= max_n:
                break
            if len(jobs) >= max_n:
                break

        return jobs

    def _parse_item(self, item, exclude, inc_keywords) -> dict | None:
        # 회사명
        company = ""
        el = item.select_one("div.col.company_nm a.str_tit")
        if el:
            company = el.get_text(strip=True)

        # 공고 제목 + 링크
        title = ""
        url = ""
        el = item.select_one("div.job_tit a.str_tit")
        if el:
            title = self.clean_title(el.get_text(strip=True), exclude)
            url = self.make_absolute(el.get("href", ""), "https://www.saramin.co.kr")

        if not title or not url:
            return None
        if inc_keywords and not any(kw in title.lower() for kw in inc_keywords):
            return None

        # 기술스택
        tech_stack = []
        for span in item.select("div.job_meta span.job_sector span"):
            t = span.get_text(strip=True)
            if t and t not in ("", ","):
                tech_stack.append(t)

        # 경력/고용형태
        career = ""
        el = item.select_one("p.career")
        if el:
            career = el.get_text(strip=True)

        # 학력
        education = ""
        el = item.select_one("p.education")
        if el:
            education = el.get_text(strip=True)

        # 근무지
        location = ""
        el = item.select_one("p.work_place")
        if el:
            location = el.get_text(strip=True)

        # 마감일
        deadline = ""
        el = item.select_one("span.date")
        if el:
            deadline = el.get_text(strip=True)

        # 등록일 (상대적)
        registered = ""
        el = item.select_one("span.deadlines")
        if el:
            registered = el.get_text(strip=True)

        # 배지 (급성장중, 코스닥 등)
        badge = ""
        el = item.select_one("div.job_badge span")
        if el:
            badge = el.get_text(strip=True)

        return {
            "site": self.name,
            "company": company,
            "title": title[:80],
            "url": url,
            "url_norm": self.normalize_url(url),
            "tech_stack": tech_stack,
            "career": career,
            "education": education,
            "location": location,
            "deadline": deadline,
            "registered": registered,
            "badge": badge,
        }
