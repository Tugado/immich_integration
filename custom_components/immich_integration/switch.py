"""Platform for Switch integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
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
    """Set up Immich Switch platform."""

    hub = hass.data[DOMAIN][config_entry.entry_id]

    # Create entity for random favorite image
    # async_add_entities([ImmichJobs(hass, hub)])

    # Create entities for random image from each watched
    jobs = await hub.get_jobs(False)
    async_add_entities(
        [ImmichSwitch(hass, hub, job=jobs[key], job_name=key) for key in jobs]
    )
    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))


async def update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options updates."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class ImmichSwitch(SwitchEntity):
    """Represent a switch ."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(
        self, hass: HomeAssistant, hub: ImmichHub, job: dict, job_name: str
    ) -> None:
        """Initialize the binary sensor entity."""
        super().__init__()
        self.hub = hub
        self.hass = hass
        self.entity_description = f"Switch {job_name}"
        self.job_name=job_name
        self._attr_device_class = SwitchDeviceClass.SWITCH
        self.paused=job["queueStatus"]["isPaused"]
        self._attr_extra_state_attributes = {}

        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, "immich_integration")},
            manufacturer="Immich",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        return self.paused

    @property
    def name(self) -> str:
        """Return the display name of this light."""
        return self._name

    def turn_on(self) -> None:
        """Instruct the light to turn on.

        You can skip the brightness part if your light does not support
        brightness control.
        """
        bool ok = await self.hub.start(job_id=self.job_name)
        self.paused=False if ok else True


    def turn_off(self) -> None:
        """Instruct the light to turn off."""
        bool ok = await self.hub.pause(job_id=self.job_name)
        self.paused=True if ok else False

