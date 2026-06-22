import json
import re
from .base import BaseExtractor
from bs4 import BeautifulSoup


class JobKoreaExtractor(BaseExtractor):
    @property
    def name(self) -> str:
        return "jobkorea"

    def extract(self, config: dict) -> list[dict]:
        max_n = config.get("max_per_site", 15)
        exclude = config.get("exclude_titles", [])
        inc_keywords = config.get("include_titles", [])
        search = config.get("search", {})
        query = search.get("query", "Java Spring 백엔드 개발자")
        career_lv = search.get("career_level", "경력")
        career_cd = self.career_code(career_lv, self.name)
        import urllib.parse
        career_from = search.get("career_from")
        career_to = search.get("career_to")
        url = (
            "https://www.jobkorea.co.kr/Search/"
            f"?stext={urllib.parse.quote(query)}"
            f"{'&careerType=' + career_cd if career_cd else ''}"
            f"{'&careerMin=' + str(career_from) if career_from is not None else ''}"
            f"{'&careerMax=' + str(career_to) if career_to is not None else ''}"
        )
        html = self.fetch(url)
        if not html:
            return []
        soup = BeautifulSoup(html, "lxml")
        jobs = []
        seen_urls = set()
        for a in soup.select('a[href*="Recruit/GI_Read"]'):
            href = self.make_absolute(a.get("href", ""), "https://www.jobkorea.co.kr")
            href_norm = self.normalize_url(href)
            title = self.clean_title(a.get_text(strip=True), exclude)
            if len(title) < 5:
                continue
            if inc_keywords and not any(kw in title.lower() for kw in inc_keywords):
                continue
            if href_norm in seen_urls:
                continue
            seen_urls.add(href_norm)
            jobs.append({
                "site": self.name,
                "title": title[:80],
                "url": href,
                "url_norm": href_norm,
            })
            if len(jobs) >= max_n:
                break

        # augment with detail page info
        for job in jobs:
            self._augment_detail(job, config)

        return jobs

    def _augment_detail(self, job: dict, config: dict | None = None):
        html = self.fetch(job["url"], timeout=10)
        if not html:
            return
        soup = BeautifulSoup(html, "lxml")

        # ld+json has structured data
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string)
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            org = data.get("hiringOrganization") or {}
            job["company"] = (
                org.get("name", "") if isinstance(org, dict) else ""
            ) or job.get("company", "")
            job["deadline"] = self._parse_deadline_ld(data.get("validThrough", ""))
            job["posted_date"] = data.get("datePosted", "")
            job["career"] = data.get("experienceRequirements", "")
            job["education"] = data.get("educationRequirements", "")
            break

        # fallback: og:title for company
        if not job.get("company"):
            og = soup.select_one('meta[property="og:title"]')
            if og:
                txt = og.get("content", "")
                m = re.match(r"^(.+?)\s+채용", txt)
                if m:
                    job["company"] = m.group(1).strip()

        # extract tech stack from body (between 모집요강 and 복리후생)
        body = soup.get_text()
        m = re.search(r"모집(?:분야|요강).*?(?=복리후생|$)", body, re.DOTALL)
        section = m.group(0) if m else body[:2000]
        job["tech_stack"] = self._extract_tech_stack(section)

        # company info (사원수, 업종) from detail page body
        if config and config.get("company_info", False):
            ci = {}
            idx = body.find("기업 정보")
            if idx >= 0:
                snippet = body[idx:idx+600]
                m_emp = re.search(r'사원수\s*([^\n]+)', snippet)
                if m_emp:
                    ci["employees"] = m_emp.group(1).strip()[:30]
                m_ind = re.search(r'(?:산업\(업종\)|업종)\s*([^\n]+)', snippet)
                if m_ind:
                    ci["industry"] = m_ind.group(1).strip()[:30]
                m_type = re.search(r'기업구분\s*([^\n]+)', snippet)
                if m_type:
                    ci["company_type"] = m_type.group(1).strip()[:30]
            # company profile (설립일, 매출액) from 기업정보 더보기
            profile_link = None
            for a in soup.select('a[href*="/Recruit/Co_Read/"]'):
                profile_link = self.make_absolute(a.get("href", ""), "https://www.jobkorea.co.kr")
                break
            if profile_link:
                profile_html = self.fetch(profile_link, timeout=10)
                if profile_html:
                    p_body = BeautifulSoup(profile_html, "lxml").get_text()
                    m_fd = re.search(r'설립일\s*([\d.]+)', p_body)
                    if m_fd:
                        ci["founded"] = m_fd.group(1).strip()
                    m_rev = re.search(r'매출액\s*([^\n]+)', p_body)
                    if m_rev:
                        rev = m_rev.group(1).strip()
                        if rev and rev != "-":
                            ci["revenue"] = rev
            if ci:
                job["company_info"] = ci

    def _parse_deadline_ld(self, val: str) -> str:
        if not val:
            return ""
        val = val.replace("T23:59", "").replace("T23:59:59", "")
        return val

    def _extract_tech_stack(self, text: str) -> list[str]:
        known_techs = [
            "Java", "Spring", "Spring Boot", "Spring Batch", "Spring Cloud",
            "JPA", "MyBatis", "iBatis", "JSP", "Servlet",
            "Oracle", "MySQL", "MariaDB", "MongoDB", "Redis", "H2", "H2 Database",
            "AWS", "EC2", "S3", "RDS", "Lambda", "CloudFront", "ELB",
            "Docker", "Kubernetes", "Jenkins", "Git", "GitLab", "SVN",
            "JavaScript", "TypeScript", "React", "Vue", "Vue3", "jQuery",
            "Node.js", "Python", "Kotlin", "Go", "JWT",
            "Nexacro", "Linux", "Apache", "Tomcat", "Nginx",
            "RESTful", "REST", "JUnit", "Gradle", "Maven",
            "HTML", "CSS", "CSS3", "HTML5", "Ajax", "JSON", "XML",
        ]
        # Also extract comma-separated techs from patterns like "스킬,Java,Spring"
        text = re.sub(r'(?:스킬|skill)[,:\s]*', ' ', text, flags=re.IGNORECASE)
        found = []
        for tech in sorted(known_techs, key=len, reverse=True):
            if re.search(r'(?:^|[\s,;/])' + re.escape(tech) + r'(?:$|[\s,;/.])', text, re.IGNORECASE):
                found.append(tech)
        return found
