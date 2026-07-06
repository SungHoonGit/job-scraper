#!/usr/bin/env python3
"""
Job Scraper — Modular job posting collector for Korean job sites.

Usage:
    python3 job_scraper.py                        # normal run
    python3 job_scraper.py --dry-run              # preview only, no files written
    python3 job_scraper.py --rebuild              # rebuild history.md from daily/
    python3 job_scraper.py --profile react        # use daily/react/ + history.react.md
    python3 job_scraper.py --profile java --rebuild  # rebuild specific profile

Profile can also be set via config.json: { "profile": "react", ... }
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta

from extractors import EXTRACTORS
from extractors.base import BaseExtractor
from notifiers import NOTIFIERS, JobAlert
import notifiers.console       # noqa: F401 — register built-in notifiers
import notifiers.email_notifier  # noqa: F401
import notifiers.kakao_notifier  # noqa: F401
import notifiers.telegram_notifier  # noqa: F401

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_config():
    path = os.path.join(SCRIPT_DIR, "config.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve(path: str) -> str:
    return os.path.expanduser(path)


def _profile(config) -> str:
    p = config.get("profile") or ""
    return p.strip()


def get_daily_dir(config) -> str:
    d = resolve(config.get("output_dir", SCRIPT_DIR))
    p = _profile(config)
    return os.path.join(d, "daily", p) if p else os.path.join(d, "daily")


def get_history_path(config) -> str:
    d = resolve(config.get("output_dir", SCRIPT_DIR))
    p = _profile(config)
    if p:
        return os.path.join(d, f"history.{p}.md")
    return os.path.join(d, "history.md")


def notify(config, title: str, msg: str):
    nc = config.get("notification", True)
    if isinstance(nc, dict) and not nc.get("enabled", True):
        return
    elif not nc:
        return
    if sys.platform == "darwin":
        subprocess.run(["osascript", "-e", f'display notification "{msg}" with title "{title}"'])
    else:
        print(f"  [notify] {title}: {msg}")


def get_notifiers(config):
    nc = config.get("notification")
    if not nc:
        return []
    channels_config = nc if isinstance(nc, dict) else {}
    if not channels_config.get("channels"):
        return []

    instances = []
    for name, cls in NOTIFIERS.items():
        if name == "console":
            continue
        instance = cls(channels_config["channels"])
        instances.append(instance)
    return instances


def build_alerts(jobs: list[dict]) -> list[JobAlert]:
    return [
        JobAlert(
            company=j.get("company", ""),
            title=j.get("title", ""),
            url=j.get("url_norm") or j["url"],
            site=j.get("site", ""),
            career=j.get("career", ""),
            deadline=j.get("deadline", ""),
            tech_stack=j.get("tech_stack") or [],
            company_info=j.get("company_info"),
        )
        for j in jobs
    ]


def load_seen_urls(config) -> set:
    seen = set()
    daily_dir = get_daily_dir(config)
    if not os.path.isdir(daily_dir):
        return seen
    retention = config.get("retention_days", 14)
    cutoff = datetime.now() - timedelta(days=retention)
    for fname in os.listdir(daily_dir):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(daily_dir, fname)
        # skip files older than retention
        try:
            fdate = datetime.strptime(fname.replace(".md", ""), "%Y-%m-%d")
            if fdate < cutoff:
                continue
        except ValueError:
            pass
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                for m in re.finditer(r"https?://[^\s\)\]\>]+", line):
                    seen.add(BaseExtractor.normalize_url(m.group(0).rstrip(")")))
    return seen


def fmt(val: str, maxlen=30) -> str:
    val = (val or "").replace("|", "·").strip()
    if len(val) > maxlen:
        val = val[:maxlen-1] + "…"
    return val


def fmt_tech(techs) -> str:
    if not techs:
        return "-"
    if isinstance(techs, list):
        return ", ".join(techs[:5])
    return fmt(str(techs), 30)


def _search_label(config) -> str:
    s = config.get("search", {})
    q = s.get("query", "")
    cf = s.get("career_from")
    ct = s.get("career_to")
    if cf is not None and ct is not None:
        career_label = f"{cf}년~{ct}년차"
    elif cf is not None:
        career_label = f"{cf}년차 이상"
    elif ct is not None:
        career_label = f"{ct}년차 이하"
    else:
        career_label = s.get("career_level", "")
    return f"{q} {career_label}".strip()


def append_daily(config, jobs: list[dict]):
    daily_dir = get_daily_dir(config)
    os.makedirs(daily_dir, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    now_ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    fpath = os.path.join(daily_dir, f"{today}.md")

    header = ("| 회사명 | 사이트 | 제목 | 경력 | 마감일 | 기술스택 | 기업정보 |\n"
              "|---|---|---|---|---|---|---|\n")
    rows = []
    for j in jobs:
        company = fmt(j.get("company", ""), 20)
        site = j.get("site", "")
        title = fmt(j.get("title", ""), 35)
        career = fmt(j.get("career", ""), 15)
        deadline = fmt(j.get("deadline", ""), 15)
        tech = fmt_tech(j.get("tech_stack"))
        ci = j.get("company_info") or {}
        ci_parts = [ci.get(k, "") for k in ("employees", "industry", "founded") if ci.get(k)]
        ci_str = fmt(" / ".join(ci_parts), 30) if ci_parts else "-"
        clean_url = BaseExtractor.normalize_url(j["url"])
        rows.append(
            f"| {company} | {site} | [{title}]({clean_url})"
            f" | {career} | {deadline} | {tech} | {ci_str} |\n"
        )

    with open(fpath, "a", encoding="utf-8") as f:
        label = _search_label(config)
        if os.path.getsize(fpath) == 0 or f.tell() == 0:
            f.write(f"# {today} 수집 — {label}\n\n")
        else:
            f.write(f"## {label}\n\n")
        f.write(f"### {now_ts} (총 {len(jobs)}건)\n\n")
        f.write(header)
        for r in rows:
            f.write(r)
        f.write("\n")

    print(f"  → appended {len(jobs)} jobs to {fpath}")


def rebuild_history(config):
    daily_dir = get_daily_dir(config)
    hist_path = get_history_path(config)
    retention = config.get("retention_days", 14)
    cutoff = datetime.now() - timedelta(days=retention)

    entries = []
    if not os.path.isdir(daily_dir):
        os.makedirs(daily_dir, exist_ok=True)
    for fname in sorted(os.listdir(daily_dir), reverse=True):
        if not fname.endswith(".md"):
            continue
        try:
            fdate = datetime.strptime(fname.replace(".md", ""), "%Y-%m-%d")
            if fdate < cutoff:
                # remove old file
                os.remove(os.path.join(daily_dir, fname))
                continue
        except ValueError:
            continue
        fpath = os.path.join(daily_dir, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        # strip the "# YYYY-MM-DD 수집" heading from daily file
        content = re.sub(r'^#\s+\d{4}-\d{2}-\d{2}\s+수집\n+', '', content)
        if content:
            entries.append(f"## {fname.replace('.md', '')}\n\n{content}")

    with open(hist_path, "w", encoding="utf-8") as f:
        p = _profile(config)
        heading = f"# 수집 히스토리 — {p}" if p else "# 수집 히스토리"
        f.write(f"{heading}\n\n")
        f.write(f"> 최근 {retention}일간 자동 수집된 공고\n\n")
        f.write("---\n\n")
        if entries:
            f.write("\n".join(entries))
        else:
            f.write("수집 내역 없음\n")

    print(f"  → rebuilt {hist_path} ({len(entries)} days)")


def main():
    config = load_config()
    dry_run = "--dry-run" in sys.argv
    rebuild = "--rebuild" in sys.argv
    # CLI --profile overrides config's profile field
    for i, arg in enumerate(sys.argv):
        if arg == "--profile" and i + 1 < len(sys.argv):
            config["profile"] = sys.argv[i + 1]

    if rebuild:
        rebuild_history(config)
        return

    p = _profile(config)
    profile_tag = f" [{p}]" if p else ""
    print(f"=== Job Scraper Run{profile_tag}: {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    seen = load_seen_urls(config)
    all_new = []

    exclude_closed = config.get("search", {}).get("exclude_closed", True)
    inc_keywords = config.get("include_titles", [])

    for site_key, site_conf in config.get("sites", {}).items():
        if not site_conf.get("enabled", False):
            continue
        extractor_cls = EXTRACTORS.get(site_key)
        if not extractor_cls:
            print(f"  [?] unknown site: {site_key}, skipping")
            continue
        extractor = extractor_cls()
        jobs = extractor.extract(config)
        site_new = 0
        for job in jobs:
            url_key = job.get("url_norm") or job["url"]
            if url_key in seen:
                continue
            if exclude_closed and BaseExtractor.is_deadline_passed(job.get("deadline", "")):
                continue
            if inc_keywords and not any(kw in job["title"].lower() for kw in inc_keywords):
                continue
            seen.add(url_key)
            all_new.append(job)
            site_new += 1
            print(f"  [+] {job['site']}: {job['title'][:60]}")
        print(f"  [{site_key}] total {len(jobs)}, new {site_new}")

    # Filter by career years if configured
    career_from = config.get("search", {}).get("career_from")
    career_to = config.get("search", {}).get("career_to")
    if career_from is not None or career_to is not None:
        filtered = []
        for job in all_new:
            c_text = job.get("career", "")
            c_min, c_max = BaseExtractor.parse_career_years(c_text)
            if c_min is None:
                filtered.append(job)
            else:
                if career_from is not None and c_max is not None and c_max < career_from:
                    continue
                if career_to is not None and c_min is not None and c_min > career_to:
                    continue
                filtered.append(job)
        dropped = len(all_new) - len(filtered)
        if dropped:
            print(f"  [filter] career range: dropped {dropped} jobs")
        all_new = filtered

    if not all_new:
        print("No new jobs found.")
        if not dry_run:
            rebuild_history(config)
        return

    if dry_run:
        print(f"\n[Dry-Run] Would add {len(all_new)} jobs.")
        return

    append_daily(config, all_new)
    rebuild_history(config)

    msg = f"{len(all_new)}개 신규 공고 발견"
    notify(config, "Job Scraper", msg)

    alerts = build_alerts(all_new)
    for n in get_notifiers(config):
        n.send(alerts)

    print(f"Done. {len(all_new)} new jobs.")


if __name__ == "__main__":
    main()
