"""Platform for sensor integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .hub import ImmichHub

SCAN_INTERVAL = timedelta(minutes=5)
_ID_LIST_REFRESH_INTERVAL = timedelta(hours=12)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Immich Sensor platform."""

    hub = ImmichHub(
        host=config_entry.data[CONF_HOST], api_key=config_entry.data[CONF_API_KEY]
    )

    # Create entity for random favorite image
    # async_add_entities([ImmichJobs(hass, hub)])

    # Create entities for random image from each watched album
    async_add_entities(
        [
            ImmichJob(hass, hub, job_id=value, job_name=key)
            for key, value in await hub.list_jobs()
        ]
    )

    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options updates."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class BaseImmichJob(ImageEntity):
    """Base image entity for Immich. Subclasses will define where the random image comes from (e.g. favorite images, by album ID,..)."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(self, hass: HomeAssistant, hub: ImmichHub) -> None:
        """Initialize the Immich image entity."""
        super().__init__(hass=hass, verify_ssl=True)
        self.hub = hub
        self.hass = hass

        self._attr_extra_state_attributes = {}

    async def async_update(self) -> None:
        raise NotImplementedError


class ImmichJob(BaseImmichJob):
    """Image entity for Immich that displays a random image from the user's favorites."""

    def __init__(
        self, hass: HomeAssistant, hub: ImmichHub, job: dict, job_name: str
    ) -> None:
        super().__init__(hass, hub)
        self._job_name = job_name
        self._attr_unique_id = job_name
        self._attr_name = f"Immich Job: {job_name}"
        self._queue_active = job["queueStatus"].isActive
        self._queue_paused = job["queueStatus"].isPaused
        self._active = job["jobCounts"].active

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._active
