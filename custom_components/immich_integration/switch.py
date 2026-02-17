"""Platform for switch integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .coordinator import ImmichConfigEntry, ImmichDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ImmichConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Immich switch platform."""
    coordinator = config_entry.runtime_data

    # Create switches for each job
    entities = []
    if coordinator.data.jobs:
        for job_id, job_data in coordinator.data.jobs.items():
            entities.append(ImmichJobSwitch(coordinator, job_id, job_data))

    async_add_entities(entities)


class ImmichJobSwitch(SwitchEntity):
    """Represent an Immich job control switch."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: ImmichDataUpdateCoordinator,
        job_id: str,
        job_data: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        self.coordinator = coordinator
        self._job_id = job_id
        self._job_data = job_data
        self._attr_unique_id = f"immich_job_{job_id}"
        self._attr_translation_key = "job_switch"
        self._attr_translation_placeholders = {"job_name": job_id.replace("_", " ").title()}

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, "immich_integration")},
            name="Immich Jobs",
            manufacturer="Immich",
            model="Jobs Manager",
        )

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._job_id.replace("_", " ").title()

    @property
    def is_on(self) -> bool:
        """Return True if job is paused (switch is ON = paused)."""
        if self._job_id in self.coordinator.data.jobs:
            job = self.coordinator.data.jobs[self._job_id]
            return job.get("queueStatus", {}).get("isPaused", False)
        return False

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Pause the job (turn on)."""
        await self.coordinator.async_pause_job(self._job_id)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Resume the job (turn off)."""
        await self.coordinator.async_resume_job(self._job_id)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

