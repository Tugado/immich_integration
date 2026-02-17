"""Coordinator for the Immich integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import logging
from urllib.parse import urljoin

import aiohttp
from aioimmich import Immich
from aioimmich.const import CONNECT_ERRORS
from aioimmich.exceptions import ImmichUnauthorizedError
from aioimmich.server.models import (
    ImmichServerAbout,
    ImmichServerStatistics,
    ImmichServerStorage,
    ImmichServerVersionCheck,
)
from awesomeversion import AwesomeVersion

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT, CONF_SSL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_HEADER_API_KEY = "x-api-key"


@dataclass
class ImmichData:
    """Data class for storing data from the API."""

    server_about: ImmichServerAbout
    server_storage: ImmichServerStorage
    server_usage: ImmichServerStatistics | None
    server_version_check: ImmichServerVersionCheck | None
    jobs: dict = field(default_factory=dict)


ImmichConfigEntry = ConfigEntry["ImmichDataUpdateCoordinator"]


class ImmichDataUpdateCoordinator(DataUpdateCoordinator[ImmichData]):
    """Class to manage fetching Immich API data."""

    config_entry: ImmichConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, api: Immich, is_admin: bool
    ) -> None:
        """Initialize the data update coordinator."""
        self.api = api
        self.is_admin = is_admin
        self.hass = hass
        self.entry = entry
        self._api_key = entry.data[CONF_API_KEY]
        self._host = entry.data[CONF_HOST]
        self._port = entry.data[CONF_PORT]
        self._ssl = entry.data[CONF_SSL]
        self.configuration_url = (
            f"{'https' if self._ssl else 'http'}://"
            f"{self._host}:{self._port}"
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )

    async def _async_update_data(self) -> ImmichData:
        """Update data via internal method."""
        try:
            server_about = await self.api.server.async_get_about_info()
            server_storage = await self.api.server.async_get_storage_info()
            server_usage = (
                await self.api.server.async_get_server_statistics()
                if self.is_admin
                else None
            )
            server_version_check = (
                await self.api.server.async_get_version_check()
                if AwesomeVersion(server_about.version) >= AwesomeVersion("v1.134.0")
                else None
            )
            jobs = await self._async_get_jobs()
        except ImmichUnauthorizedError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_error",
            ) from err
        except CONNECT_ERRORS as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_error",
                translation_placeholders={"error": repr(err)},
            ) from err

        return ImmichData(
            server_about, server_storage, server_usage, server_version_check, jobs
        )

    async def _async_get_jobs(self) -> dict:
        """Get jobs from Immich server."""
        try:
            async with aiohttp.ClientSession() as session:
                scheme = "https" if self._ssl else "http"
                url = f"{scheme}://{self._host}:{self._port}/api/jobs"
                headers = {
                    "Accept": "application/json",
                    _HEADER_API_KEY: self._api_key,
                }

                async with session.get(url=url, headers=headers) as response:
                    if response.status != 200:
                        _LOGGER.warning(
                            "Error getting jobs from Immich: status=%s", response.status
                        )
                        return {}

                    return await response.json()
        except aiohttp.ClientError as exception:
            _LOGGER.warning("Error connecting to Immich API for jobs: %s", exception)
            return {}

    async def async_pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        result = await self._async_job_command(job_id, "pause")
        if result:
            # Refresh data after successful command
            await self.async_refresh()
        return result

    async def async_resume_job(self, job_id: str) -> bool:
        """Resume a job."""
        result = await self._async_job_command(job_id, "start")
        if result:
            # Refresh data after successful command
            await self.async_refresh()
        return result

    async def _async_job_command(self, job_id: str, command: str) -> bool:
        """Send a command to a job."""
        try:
            async with aiohttp.ClientSession() as session:
                scheme = "https" if self._ssl else "http"
                url = f"{scheme}://{self._host}:{self._port}/api/jobs/{job_id}"
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    _HEADER_API_KEY: self._api_key,
                }
                data = '{"command": "' + command + '", "force": true}'

                async with session.put(url=url, headers=headers, data=data) as response:
                    return response.status == 200
        except aiohttp.ClientError as exception:
            _LOGGER.error("Error sending job command to Immich: %s", exception)
            return False
