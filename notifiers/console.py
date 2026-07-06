from . import JobAlert, register


@register("console")
class ConsoleNotifier:
    def send(self, alerts: list[JobAlert]) -> None:
        print(f"\n  [notify] 총 {len(alerts)}건의 신규 채용공고")
        for a in alerts:
            print(f"    · [{a.site}] {a.company} - {a.title}")
            print(f"      {a.url}")
