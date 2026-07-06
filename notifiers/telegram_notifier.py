import requests

from . import JobAlert, register


@register("telegram")
class TelegramNotifier:
    SEND_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, config: dict):
        c = config.get("telegram", {})
        self.enabled = c.get("enabled", False)
        self.bot_token = c.get("bot_token") or ""
        self.chat_id = c.get("chat_id") or ""

    def send(self, alerts: list[JobAlert]) -> None:
        if not self.enabled:
            return
        if not self.bot_token or not self.chat_id:
            print("  [telegram] bot_token or chat_id not set, skipping")
            return

        lines = [f"📋 *신규 채용공고 ({len(alerts)}건)*\n"]
        for a in alerts:
            tech = ", ".join(a.tech_stack[:3]) if a.tech_stack else "-"
            lines.append(
                f"▪️ *{a.company}* | {a.site}\n"
                f"   [{a.title}]({a.url})\n"
                f"   경력: {a.career or '-'} · 마감: {a.deadline or '-'}\n"
                f"   기술: {tech}"
            )

        text = "\n\n".join(lines)
        if len(text) > 4000:
            text = text[:4000] + "\n\n… (일부 생략)"

        url = self.SEND_URL.format(token=self.bot_token)
        try:
            resp = requests.post(
                url,
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": False,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                print(f"  [telegram] sent to chat {self.chat_id}")
            else:
                print(f"  [telegram] API error: {resp.json()}")
        except Exception as e:
            print(f"  [telegram] request failed: {e}")
