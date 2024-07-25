from enum import StrEnum
from functools import cache
from operator import attrgetter


class AppsflyerReportsAPIEnum(StrEnum):
    NON_ORGANIC_INSTALLS_REPORT_API = "installs_report"
    NON_ORGANIC_IN_APP_EVENTS_REPORT_API = "in_app_events_report"

    ORGANIC_INSTALLS_REPORT_API = "organic_installs_report"
    ORGANIC_IN_APP_EVENTS_REPORT_API = "organic_in_app_events_report"

    @classmethod
    @cache
    def values(cls) -> tuple[str, ...]:
        return tuple(map(attrgetter("value"), cls))


class AdditionalFieldsEnum(StrEnum):
    MATCH_TYPE = "match_type"
