import asyncio
import os
import signal
from asyncio import Task
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import cached_property
from typing import Literal, Never, TypeVar

import aiofiles
import aiohttp
from aiohttp import ClientSession, ClientTimeout

from core.config import settings
from core.enums.appsflyer import AdditionalFieldsEnum, AppsflyerReportsAPIEnum
from core.enums.system_signals import SystemSignalsEnum
from core.exceptions import GracefulExit, TooManyRetries
from core.logger import logger

Report = TypeVar("Report", dict, str)


@dataclass(frozen=True, slots=True)
class AppsFlyerReferenceInfo:
    """
    Dataclass to hold information about an AppsFlyer reference.

    Attributes:
        reference (str): The constructed reference URL.
        application_id (str): The application ID (iOS or Android).
        report_api (str): The API endpoint for the report.
    """

    reference: str
    application_id: str
    report_api: str


class AppsFlyerReference:
    """
    Class to manage AppsFlyer reference information and URLs.

    Class variables:
        appsflyer_reports_api (tuple): Tuple containing available AppsFlyer report APIs.
        additional_fields (str): Additional fields to be included in the reference URL.
        appsflyer_token (str): The token used for authenticating with AppsFlyer API.
        appsflyer_api_url (str): The base URL for AppsFlyer API endpoints.
        application_id_ios (str): The unique identifier for the iOS application within AppsFlyer.
        application_id_android (str): The unique identifier for the Android application within AppsFlyer.
        date_start (datetime): The start date for the reporting period, defaults to yesterday.
        date_stop (datetime): The end date for the reporting period, defaults to two days ago.
    """

    appsflyer_reports_api: tuple[str, ...] = AppsflyerReportsAPIEnum.values()
    additional_fields: str = AdditionalFieldsEnum.MATCH_TYPE
    appsflyer_token: str = settings.APPSFLYER_TOKEN
    appsflyer_api_url: str = settings.APPSFLYER_API_URL
    application_id_ios: str = settings.APPLICATION_ID_IOS
    application_id_android: str = settings.APPLICATION_ID_ANDROID
    date_start: datetime = datetime.now() - timedelta(days=1)
    date_stop: datetime = date_start - timedelta(days=1)

    @cached_property
    def request_header(self) -> dict[Literal["accept", "authorization"], str]:
        return {
            "accept": "text/csv",
            "authorization": f"Bearer {self.appsflyer_token}",
        }

    def _create_reference_info(
        self, application_id: str, report_api: str
    ) -> AppsFlyerReferenceInfo:
        reference = (
            f"{self.appsflyer_api_url}/raw-data/export/app/"
            f"{application_id}/{report_api}/"
            f"v5?from={self.date_start.strftime('%Y-%m-%d')}&to={self.date_stop.strftime('%Y-%m-%d')}&"
            f"additional_fields={self.additional_fields}"
        )
        return AppsFlyerReferenceInfo(
            reference=reference, application_id=application_id, report_api=report_api
        )

    def _create_references_for_application(
        self, application_id: str
    ) -> dict[str, Sequence[str]]:
        reference_for_application: dict[str, Sequence[str]] = {}

        for report_api in self.appsflyer_reports_api:
            reference_info = self._create_reference_info(application_id, report_api)

            reference_for_application[reference_info.reference] = (
                reference_info.application_id,
                reference_info.report_api,
            )

        return reference_for_application

    @property
    def _get_references_for_ios(self) -> dict[str, Sequence[str]]:
        return self._create_references_for_application(self.application_id_ios)

    @property
    def _get_references_for_android(self) -> dict[str, Sequence[str]]:
        return self._create_references_for_application(self.application_id_android)

    @cached_property
    def get_all_references_for_all_applications(self) -> dict[str, Sequence[str]]:
        return {
            **self._get_references_for_ios,
            **self._get_references_for_android,
        }


class ProcessAppsflyerReport:
    """
    Class to process AppsFlyer reports asynchronously.

    Instance variables:
        appsflyer_reports (Iterable[Task]): An iterable of asyncio Task objects representing the reports.
    """

    def __init__(self, appsflyer_reports: Iterable[Task]):
        self.appsflyer_reports = appsflyer_reports

    @staticmethod
    async def _save_report(report_result: Report):
        if content_disposition := report_result.headers.get("Content-Disposition"):
            filename = content_disposition.split("filename=")[-1].strip('"')
            filepath = os.path.join("./reports", "unprocessed", filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            async with aiofiles.open(filepath, mode="ab") as f:
                while chunk := await report_result.content.read(1024):
                    await f.write(chunk)

            logger.info(f"CSV report saved: {filename} at {filepath}")
        else:
            logger.error("Content-Disposition header not found, cannot save CSV report")

    async def process_reports(self):
        for report in self.appsflyer_reports:
            if report.exception() is None:
                await self._save_report(report.result())
            else:
                report.cancel()


class PullAppsFlyerReport:
    """
    Class to manage the process of pulling and retrying AppsFlyer reports.

    Class variables:
        system_signals (tuple): Tuple containing the system signals to handle for graceful shutdown.
        _session_timeout (ClientTimeout): Timeout settings for aiohttp ClientSession.
        appsflyer_reference (AppsFlyerReference): Reference information and URLs for AppsFlyer.
        request_header (dict): HTTP request headers for the AppsFlyer API.
        appsflyer_all_references (callable): Method to get all AppsFlyer references for all applications.
    """

    system_signals: tuple[str, ...] = SystemSignalsEnum.values()
    session_timeout: ClientTimeout = aiohttp.ClientTimeout(total=10.0, connect=6.0)
    appsflyer_reference: AppsFlyerReference = AppsFlyerReference()
    request_header = appsflyer_reference.request_header
    appsflyer_all_references = (
        appsflyer_reference.get_all_references_for_all_applications
    )

    def __shutdown(self) -> Never:
        """Raise the GracefulExit exception to initiate a graceful shutdown."""
        raise GracefulExit

    def __shutdown_events(self):
        """Set up event loop signal handlers to handle graceful shutdown signals."""
        loop = asyncio.get_event_loop()
        for signal_name in ("SIGINT", "SIGTERM"):
            loop.add_signal_handler(getattr(signal, signal_name), self.__shutdown)

    async def create_tasks_for_request(self, session: ClientSession) -> Sequence[Task]:
        return [
            asyncio.create_task(
                session.get(reference, headers=self.request_header),  # type: ignore
                name=reference,
            )
            for reference in self.appsflyer_all_references
        ]

    async def _create_tasks_for_retry_request(
        self, session: ClientSession, tasks: Iterable[Task]
    ) -> Sequence[Task]:
        return [
            asyncio.create_task(
                session.get(task.get_name(), headers=self.request_header),  # type: ignore
                name=task.get_name(),
            )
            for task in tasks
        ]

    async def _retry_pending_reports(
        self,
        session: ClientSession,
        pending_reports: Iterable[Task],
        retry_attempts: int = 3,
        retry_interval: float = 3.0,
    ):
        for attempt in range(retry_attempts):
            logger.info(f"Retrying pending reports, attempt {attempt + 1}")

            retry_tasks = await self._create_tasks_for_retry_request(
                session, tasks=pending_reports
            )
            done_retry_reports, pending_retry_reports = await asyncio.wait(
                retry_tasks, timeout=5.0
            )

            logger.info(f"Number of done reports: {len(done_retry_reports)}")
            logger.info(f"Number of pending reports: {len(pending_retry_reports)}")

            await asyncio.sleep(retry_interval)
            await ProcessAppsflyerReport(done_retry_reports).process_reports()

            if not pending_retry_reports:
                logger.info("All reports have been retrieved successfully")
                break
            pending_reports = pending_retry_reports

        else:
            for report in pending_reports:
                report.cancel()
            logger.error(
                "Failed to retrieve reports after multiple retry attempts. Raise TooManyRetries exception"
            )
            raise TooManyRetries()

    async def pull_reports(self):
        async with aiohttp.ClientSession(timeout=self.session_timeout) as session:
            self.__shutdown_events()

            tasks = await self.create_tasks_for_request(session)
            done_reports, pending_reports = await asyncio.wait(tasks, timeout=0.1)
            await ProcessAppsflyerReport(done_reports).process_reports()

            if pending_reports:
                await self._retry_pending_reports(session, pending_reports)


appsflyer = PullAppsFlyerReport()
pull_appsflyer_reports = appsflyer.pull_reports()
