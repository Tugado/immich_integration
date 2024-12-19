"""The Immich Integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_API_KEY
from homeassistant.core import HomeAssistant, ServiceCall, callback
from .const import DOMAIN
from .hub import ImmichHub, InvalidAuth

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]

# TODO Create ConfigEntry type alias with API object
# TODO Rename type alias and update all entry annotations


# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up immich from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    hub = ImmichHub(host=entry.data[CONF_HOST], api_key=entry.data[CONF_API_KEY])

    if not await hub.authenticate():
        raise InvalidAuth

    hass.data[DOMAIN][entry.entry_id] = hub

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    async def refresh_service(call: ServiceCall) -> None:
        """My first service."""
        await hub.refresh_jobs()

    hass.services.async_register(DOMAIN, "refresh", refresh_service)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
