from pathlib import Path

from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings

from core.enums.enviroment import EnvironmentTypesEnum

PROJECT_DIR = Path(__file__).parent.parent.parent


class BaseAppSettings(BaseSettings):
    # ENV
    ENVIRONMENT: EnvironmentTypesEnum = Field(
        EnvironmentTypesEnum.PROD, validation_alias="API_ENVIRONMENT"
    )
    DEBUG: bool = True

    # APPSFLYER
    APPSFLYER_API_URL: HttpUrl = "https://hq1.appsflyer.com/api"  # type: ignore[assignment]
    APPSFLYER_TOKEN: SecretStr = "appsflyer_token"  # type: ignore[assignment]
    APPLICATION_ID_IOS: str = "application_id_ios"
    APPLICATION_ID_ANDROID: str = "application_id_android"

    class Config:
        env_file = PROJECT_DIR / ".env"


class LocalSettings(BaseAppSettings):
    TITLE: str = "Local environment"


class DevelopmentSettings(BaseAppSettings):
    TITLE: str = "Development environment"


class ProductionSettings(BaseAppSettings):
    DEBUG: bool = False
