from .jobkorea import JobKoreaExtractor
from .saramin import SaraminExtractor
from .wanted import WantedExtractor
from .jumpit import JumpitExtractor
from .incruit import IncruitExtractor
from .remember import RememberExtractor

EXTRACTORS = {
    "jobkorea": JobKoreaExtractor,
    "saramin": SaraminExtractor,
    "wanted": WantedExtractor,
    "jumpit": JumpitExtractor,
    "incruit": IncruitExtractor,
    "remember": RememberExtractor,
}

__all__ = ["EXTRACTORS"]
