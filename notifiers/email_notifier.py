import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from . import JobAlert, register


@register("email")
class EmailNotifier:
    def __init__(self, config: dict):
        c = config.get("email", {})
        self.enabled = c.get("enabled", False)
        self.smtp_host = c.get("smtp_host", "smtp.gmail.com")
        self.smtp_port = c.get("smtp_port", 587)
        self.use_tls = c.get("use_tls", True)
        self.username = c.get("username") or ""
        self.password = c.get("password") or ""
        self.from_addr = c.get("from_addr") or self.username
        self.to_addrs = c.get("to_addrs", [])

    def _build_html(self, alerts: list[JobAlert]) -> str:
        rows = ""
        for a in alerts:
            tech = ", ".join(a.tech_stack[:5]) if a.tech_stack else "-"
            rows += (
                f"<tr>"
                f"<td>{a.company}</td>"
                f"<td>{a.site}</td>"
                f"<td><a href='{a.url}'>{a.title}</a></td>"
                f"<td>{a.career}</td>"
                f"<td>{a.deadline}</td>"
                f"<td>{tech}</td>"
                f"</tr>\n"
            )
        return f"""\
<html><body style="font-family:sans-serif;">
<h2>📋 신규 채용공고 ({len(alerts)}건)</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%">
<tr style="background:#f0f0f0">
<th>회사명</th><th>사이트</th><th>제목</th><th>경력</th><th>마감일</th><th>기술스택</th>
</tr>
{rows}
</table>
</body></html>"""

    def send(self, alerts: list[JobAlert]) -> None:
        if not self.enabled:
            return
        if not self.to_addrs:
            print("  [email] no recipients configured, skipping")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"채용공고 알림 ({len(alerts)}건)"
        msg["From"] = self.from_addr
        msg["To"] = ", ".join(self.to_addrs)

        plain = "\n".join(
            f"[{a.site}] {a.company} - {a.title}\n  {a.url}"
            for a in alerts
        )
        html = self._build_html(alerts)

        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))

        try:
            if self.use_tls:
                ctx = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as s:
                    s.starttls(context=ctx)
                    s.login(self.username, self.password)
                    s.sendmail(self.from_addr, self.to_addrs, msg.as_string())
            else:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=15) as s:
                    s.login(self.username, self.password)
                    s.sendmail(self.from_addr, self.to_addrs, msg.as_string())
            print(f"  [email] sent to {', '.join(self.to_addrs)}")
        except Exception as e:
            print(f"  [email] failed: {e}")
