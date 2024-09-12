from functools import cache

from core.enums.enviroment import EnvironmentTypesEnum as EnvTypes
from core.settings import DevelopmentSettings, LocalSettings, ProductionSettings

environments = {
    EnvTypes.LOCAL: LocalSettings,
    EnvTypes.DEV: DevelopmentSettings,
    EnvTypes.PROD: ProductionSettings,
}


@cache
def get_settings() -> LocalSettings | DevelopmentSettings | ProductionSettings:
    app_env = settings.BaseAppSettings().ENVIRONMENT
    return environments[app_env]()


settings = get_settings()
