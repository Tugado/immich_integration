"""Hub for Immich integration."""

from __future__ import annotations

import logging
from urllib.parse import urljoin
from datetime import datetime
import aiohttp

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntry

_HEADER_API_KEY = "x-api-key"
_LOGGER = logging.getLogger(__name__)

_ALLOWED_MIME_TYPES = ["image/png", "image/jpeg"]


class ImmichHub:
    """Immich API hub."""

    def __init__(self, host: str, api_key: str) -> None:
        """Initialize."""
        self.host = host
        self.api_key = api_key
        self.jobs = {}

    async def authenticate(self) -> bool:
        """Test if we can authenticate with the host."""
        try:
            async with aiohttp.ClientSession() as session:
                url = urljoin(self.host, "/api/auth/validateToken")
                headers = {"Accept": "application/json", _HEADER_API_KEY: self.api_key}

                async with session.post(url=url, headers=headers) as response:
                    if response.status != 200:
                        raw_result = await response.text()
                        _LOGGER.error("Error from API: body=%s", raw_result)
                        return False

                    auth_result = await response.json()

                    if not auth_result.get("authStatus"):
                        raw_result = await response.text()
                        _LOGGER.error("Error from API: body=%s", raw_result)
                        return False

                    return True
        except aiohttp.ClientError as exception:
            _LOGGER.error("Error connecting to the API: %s", exception)
            raise CannotConnect from exception

    async def get_my_user_info(self) -> dict:
        """Get user info."""
        try:
            async with aiohttp.ClientSession() as session:
                url = urljoin(self.host, "/api/users/me")
                headers = {"Accept": "application/json", _HEADER_API_KEY: self.api_key}

                async with session.get(url=url, headers=headers) as response:
                    if response.status != 200:
                        raw_result = await response.text()
                        _LOGGER.error("Error from API: body=%s", raw_result)
                        raise ApiError

                    user_info: dict = await response.json()

                    return user_info
        except aiohttp.ClientError as exception:
            _LOGGER.error("Error connecting to the API: %s", exception)
            raise CannotConnect from exception

    async def refresh_jobs(self, now: datetime | None = None):
        """List Jobs."""
        try:
            async with aiohttp.ClientSession() as session:
                url = urljoin(self.host, "/api/jobs")
                headers = {
                    "Accept": "application/json",
                    _HEADER_API_KEY: self.api_key,
                }
                data = {}

                async with session.get(url=url, headers=headers, data=data) as response:
                    if response.status != 200:
                        raw_result = await response.text()
                        _LOGGER.error("Error from API: body=%s", raw_result)
                        raise ApiError

                    self.jobs: dict = await response.json()

        except aiohttp.ClientError as exception:
            _LOGGER.error("Error connecting to the API: %s", exception)
            raise CannotConnect from exception

    async def job_command(self, command: str, job_id: str) -> bool:
        """Pause Job"""
        try:
            async with aiohttp.ClientSession() as session:
                url = urljoin(self.host, f"/api/jobs/{job_id}")
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    _HEADER_API_KEY: self.api_key,
                }
                data = {"command": "pause", "force": True}

                async with session.put(url=url, headers=headers, data=data) as response:
                    return response.status == 200
        except aiohttp.ClientError as exception:
            _LOGGER.error("Error connecting to the API: %s", exception)
            raise CannotConnect from exception

    async def get_jobs(self, cache: bool) -> dict:
        if not self.jobs or not cache:
            await self.refresh_jobs()
        return self.jobs

    async def pause(self, job_id: str) -> bool:
        return self.job_command("pause", job_id)

    async def start(self, job_id: str) -> bool:
        return self.job_command("start", job_id)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class ApiError(HomeAssistantError):
    """Error to indicate that the API returned an error."""
