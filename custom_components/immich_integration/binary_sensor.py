"""Platform for Binary sensor integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from collections.abc import Callable
from homeassistant.helpers import device_registry as dr
from .hub import ImmichHub
from .const import DOMAIN

SCAN_INTERVAL = timedelta(seconds=30)
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
    jobs = await hub.get_jobs(False)
    async_add_entities(
        [ImmichJob(hass, hub, job=jobs[key], job_name=key) for key in jobs]
    )
    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))
    async_track = async_track_time_interval(
        hass,
        hub.refresh_jobs,
        SCAN_INTERVAL,
        name="Immich Updater",
        cancel_on_shutdown=True,
    )


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options updates."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class BaseImmichJob(BinarySensorEntity):
    """Represent a binary sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(self, hass: HomeAssistant, hub: ImmichHub) -> None:
        """Initialize the binary sensor entity."""
        super().__init__()
        self.hub = hub
        self.hass = hass
        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_extra_state_attributes = {}

        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, "immich_integration")},
            manufacturer="Immich",
            entry_type=dr.DeviceEntryType.SERVICE,
        )


class ImmichJob(BaseImmichJob):
    """Job entity for Immich."""

    def __init__(
        self, hass: HomeAssistant, hub: ImmichHub, job: dict, job_name: str
    ) -> None:
        super().__init__(hass, hub)
        self._job_name = job_name
        self._attr_unique_id = f"status_{job_name}"
        self._attr_name = f"{job_name} Status"
        self.hub = hub
        self.update_entity(job)

    def update_entity(self, job):
        self._queue_active = job["queueStatus"]["isActive"]
        self._queue_paused = job["queueStatus"]["isPaused"]
        self._active = job["jobCounts"]["active"]
        self._attr_extra_state_attributes = {
            "failed": job["jobCounts"]["failed"],
            "waiting": job["jobCounts"]["waiting"],
        }
        if self._active == 0:
            self._attr_icon = "mdi:stop"
        else:
            self._attr_icon = "mdi:play"

    async def async_update(self) -> None:
        jobs = await self.hub.get_jobs(True)
        job = jobs[self._job_name]
        self.update_entity(job)

    @property
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return self._active == 1

    @property
    def queue_active(self):
        """Return the state of queue the sensor."""
        return self._queue_active
