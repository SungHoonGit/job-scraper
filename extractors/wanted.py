from .base import BaseExtractor


class WantedExtractor(BaseExtractor):
    @property
    def name(self) -> str:
        return "wanted"

    def extract(self, config: dict) -> list[dict]:
        max_n = config.get("max_per_site", 15)
        search = config.get("search", {})
        career_from = search.get("career_from")
        years_param = career_from if career_from is not None else -1
        jobs = []
        api_url = (
            "https://www.wanted.co.kr/api/chaos/navigation/v1/results"
            f"?job_group_id=518&years={years_param}&locations=all&country=kr"
            "&job_sort=job.latest_order&limit=50&offset=0"
        )
        data = self.fetch_json(api_url, {"Referer": "https://www.wanted.co.kr/"})
        if not data or not isinstance(data.get("data"), list):
            return jobs

        for job in data["data"]:
            if len(jobs) >= max_n:
                break
            jid = job.get("id", "")
            if not jid:
                continue
            href = f"https://www.wanted.co.kr/wd/{jid}"
            title = job.get("position", "") or ""
            company = ""
            if isinstance(job.get("company"), dict):
                company = job.get("company", {}).get("name", "") or ""
            full_title = f"[{company}] {title}" if company else title
            annual_from = job.get("annual_from")
            annual_to = job.get("annual_to")
            career = ""
            if annual_from is not None and annual_to is not None:
                career = f"경력{annual_from}~{annual_to}년"
            elif annual_from is not None:
                career = f"경력{annual_from}년~"
            jobs.append({
                "site": self.name,
                "title": full_title[:80],
                "url": href,
                "url_norm": href,
                "career": career,
                "company": company,
            })
        return jobs
