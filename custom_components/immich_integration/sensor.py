"""Sensor platform for the Immich integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfInformation
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .coordinator import ImmichConfigEntry, ImmichData, ImmichDataUpdateCoordinator
from .entity import ImmichEntity

# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class ImmichSensorEntityDescription(SensorEntityDescription):
    """Immich sensor entity description."""

    value: Callable[[ImmichData], StateType]
    is_suitable: Callable[[ImmichData], bool] = lambda _: True


SENSOR_TYPES: tuple[ImmichSensorEntityDescription, ...] = (
    ImmichSensorEntityDescription(
        key="disk_size",
        translation_key="disk_size",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.server_storage.disk_size_raw,
    ),
    ImmichSensorEntityDescription(
        key="disk_available",
        translation_key="disk_available",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.server_storage.disk_available_raw,
    ),
    ImmichSensorEntityDescription(
        key="disk_use",
        translation_key="disk_use",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.server_storage.disk_use_raw,
        entity_registry_enabled_default=False,
    ),
    ImmichSensorEntityDescription(
        key="disk_usage",
        translation_key="disk_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.server_storage.disk_usage_percentage,
        entity_registry_enabled_default=False,
    ),
    ImmichSensorEntityDescription(
        key="photos_count",
        translation_key="photos_count",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.server_usage.photos if data.server_usage else None,
        is_suitable=lambda data: data.server_usage is not None,
    ),
    ImmichSensorEntityDescription(
        key="videos_count",
        translation_key="videos_count",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda data: data.server_usage.videos if data.server_usage else None,
        is_suitable=lambda data: data.server_usage is not None,
    ),
    ImmichSensorEntityDescription(
        key="usage_by_photos",
        translation_key="usage_by_photos",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda d: d.server_usage.usage_photos if d.server_usage else None,
        is_suitable=lambda data: data.server_usage is not None,
        entity_registry_enabled_default=False,
    ),
    ImmichSensorEntityDescription(
        key="usage_by_videos",
        translation_key="usage_by_videos",
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.GIBIBYTES,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda d: d.server_usage.usage_videos if d.server_usage else None,
        is_suitable=lambda data: data.server_usage is not None,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ImmichConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add immich server state sensors."""
    coordinator = entry.runtime_data
    entities = [
        ImmichSensorEntity(coordinator, description)
        for description in SENSOR_TYPES
        if description.is_suitable(coordinator.data)
    ]

    # Add job sensors
    if coordinator.data.jobs:
        for job_id, job_data in coordinator.data.jobs.items():
            # Sensor for queue status (processed/total)
            entities.append(
                ImmichJobQueueSensor(coordinator, job_id, "processed", job_data)
            )
            entities.append(ImmichJobQueueSensor(coordinator, job_id, "total", job_data))
            # Sensor for paused status as a string
            entities.append(ImmichJobStatusSensor(coordinator, job_id, job_data))
            # Sensor for active status
            entities.append(ImmichJobActiveSensor(coordinator, job_id, job_data))

    async_add_entities(entities)


class ImmichSensorEntity(ImmichEntity, SensorEntity):
    """Define Immich sensor entity."""

    entity_description: ImmichSensorEntityDescription

    def __init__(
        self,
        coordinator: ImmichDataUpdateCoordinator,
        description: ImmichSensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{description.key}"
        self.entity_description = description

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        return self.entity_description.value(self.coordinator.data)

class ImmichJobQueueSensor(SensorEntity):
    """Sensor for job queue status (processed/total items)."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: ImmichDataUpdateCoordinator,
        job_id: str,
        queue_type: str,
        job_data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._job_id = job_id
        self._queue_type = queue_type
        self._attr_unique_id = f"immich_job_{job_id}_queue_{queue_type}"
        self._attr_translation_key = "job_queue_count"
        self._attr_translation_placeholders = {
            "job_name": job_id.replace("_", " ").title(),
            "type": queue_type,
        }

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
        """Return the name of the sensor."""
        queue_name = "Processed" if self._queue_type == "processed" else "Total"
        return f"{self._job_id.replace('_', ' ').title()} {queue_name}"

    @property
    def native_value(self) -> int:
        """Return the value of the sensor."""
        if self._job_id in self.coordinator.data.jobs:
            job = self.coordinator.data.jobs[self._job_id]
            queue_status = job.get("queueStatus", {})
            if self._queue_type == "processed":
                return queue_status.get("itemsProcessed", 0)
            else:
                return queue_status.get("itemsToProcess", 0)
        return 0

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )


class ImmichJobStatusSensor(SensorEntity):
    """Sensor for job pause status."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: ImmichDataUpdateCoordinator,
        job_id: str,
        job_data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._job_id = job_id
        self._attr_unique_id = f"immich_job_{job_id}_status"
        self._attr_translation_key = "job_status"
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
        """Return the name of the sensor."""
        return f"{self._job_id.replace('_', ' ').title()} Status"

    @property
    def native_value(self) -> str:
        """Return the value of the sensor."""
        if self._job_id in self.coordinator.data.jobs:
            job = self.coordinator.data.jobs[self._job_id]
            is_paused = job.get("queueStatus", {}).get("isPaused", False)
            return "Paused" if is_paused else "Running"
        return "Unknown"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )


class ImmichJobActiveSensor(SensorEntity):
    """Sensor for job active status."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: ImmichDataUpdateCoordinator,
        job_id: str,
        job_data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._job_id = job_id
        self._attr_unique_id = f"immich_job_{job_id}_active"
        self._attr_translation_key = "job_active"
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
        """Return the name of the sensor."""
        return f"{self._job_id.replace('_', ' ').title()} Active"

    @property
    def native_value(self) -> str:
        """Return the value of the sensor."""
        if self._job_id in self.coordinator.data.jobs:
            job = self.coordinator.data.jobs[self._job_id]
            is_active = job.get("queueStatus", {}).get("isActive", False)
            return "Active" if is_active else "Inactive"
        return "Unknown"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )