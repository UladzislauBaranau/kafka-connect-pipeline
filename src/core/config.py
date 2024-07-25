from functools import cache

from core import settings
from core.enums.enviroment import EnvironmentTypesEnum as EnvTypes

environments = {
    EnvTypes.LOCAL: settings.LocalSettings,
    EnvTypes.DEV: settings.DevelopmentSettings,
    EnvTypes.PROD: settings.ProductionSettings,
}


@cache
def get_settings() -> None:
    app_env = settings.BaseAppSettings().ENVIRONMENT
    return environments[app_env]()  # type:ignore


settings = get_settings()  # type:ignore
