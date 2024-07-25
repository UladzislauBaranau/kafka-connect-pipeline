from enum import StrEnum
from functools import cache
from operator import attrgetter


class SystemSignalsEnum(StrEnum):
    SIGNAL_INTERRUPT = "SIGINT"
    SIGNAL_TERMINATE = "SIGTERM"

    @classmethod
    @cache
    def values(cls) -> tuple[str, ...]:
        return tuple(map(attrgetter("value"), cls))
