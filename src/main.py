import asyncio

from core.config import settings
from core.logger import logger
from core.utils.appsflyer_reports_process import pull_appsflyer_reports

logger.info(
    f"The pulling of AppsFlyer reports has been started with the following settings: {settings}"
)
asyncio.run(pull_appsflyer_reports)
