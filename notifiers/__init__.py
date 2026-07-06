from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class JobAlert:
    company: str
    title: str
    url: str
    site: str
    career: str = ""
    deadline: str = ""
    tech_stack: list[str] = field(default_factory=list)
    company_info: dict | None = None


class BaseNotifier(Protocol):
    def send(self, alerts: list[JobAlert]) -> None: ...


NOTIFIERS: dict[str, type[BaseNotifier]] = {}


def register(name: str):
    def decorator(cls):
        NOTIFIERS[name] = cls
        return cls
    return decorator
