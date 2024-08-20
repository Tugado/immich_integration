from __future__ import annotations

import logging
from typing import Any, Dict, List

from homeassistant.components.sensor import SCAN_INTERVAL
from homeassistant.const import CONF_API_KEY, CONF_PORT, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import (
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ImmichDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Grocy data update coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize Grocy data update coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

        url = self.config_entry.data[CONF_URL]
        api_key = self.config_entry.data[CONF_API_KEY]
        port = self.config_entry.data[CONF_PORT]

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data."""
        data: dict[str, Any] = {}

        for entity in self.entities:
            if not entity.enabled:
                _LOGGER.debug("Entity %s is disabled.", entity.entity_id)
                continue

            try:
                data[
                    entity.entity_description.key
                ] = await self.grocy_data.async_update_data(
                    entity.entity_description.key
                )
            except Exception as error:  # pylint: disable=broad-except
                raise UpdateFailed(f"Update failed: {error}") from error

        return data


