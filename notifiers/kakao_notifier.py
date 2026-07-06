import requests

from . import JobAlert, register


FEED_TEMPLATE = """\
{{
    "object_type": "feed",
    "content": {{
        "title": "채용공고 알림 ({count}건)",
        "description": "{description}",
        "link": {{
            "web_url": "{url}",
            "mobile_web_url": "{url}"
        }}
    }},
    "item_content": {{
        "items": [{items}]
    }},
    "buttons": [
        {{
            "title": "자세히 보기",
            "link": {{
                "web_url": "{url}",
                "mobile_web_url": "{url}"
            }}
        }}
    ]
}}"""


@register("kakao")
class KakaoNotifier:
    SEND_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"

    def __init__(self, config: dict):
        c = config.get("kakao", {})
        self.enabled = c.get("enabled", False)
        self.rest_api_key = c.get("rest_api_key") or ""
        self.access_token = c.get("access_token") or ""

    def send(self, alerts: list[JobAlert]) -> None:
        if not self.enabled:
            return

        if not self.access_token:
            print("  [kakao] no access_token configured, skipping")
            return

        count = len(alerts)
        first = alerts[0]
        if count == 1:
            description = f"{first.company} - {first.title}"
            url = first.url
        else:
            description = (
                f"외 {count - 1}건 · {first.company}, {alerts[1].company} 등"
                if count > 1
                else ""
            )
            url = first.url

        items_json = ""
        for a in alerts[:5]:
            tech = ", ".join(a.tech_stack[:3]) if a.tech_stack else ""
            items_json += (
                '{{"item":"{company}","item_op":"{title} {tech}"}},'.format(
                    company=a.company, title=a.title[:30], tech=tech
                )
            )
        if items_json:
            items_json = items_json.rstrip(",")

        payload_json = FEED_TEMPLATE.format(
            count=count,
            description=description[:150],
            url=url,
            items=items_json,
        )

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        try:
            resp = requests.post(
                self.SEND_URL,
                headers=headers,
                data={"template_object": payload_json},
                timeout=15,
            )
            result = resp.json()
            if resp.status_code == 200 and result.get("result_code") == 0:
                print(f"  [kakao] sent ({count} jobs)")
            else:
                print(f"  [kakao] API error: {result}")
        except Exception as e:
            print(f"  [kakao] request failed: {e}")
