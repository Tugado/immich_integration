"""The Immich Integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import _LOGGER, HomeAssistant,callback,ServiceCall
from homeassistant.helpers.typing import ConfigType
from .immich_client import AuthenticatedClient
from .const import DOMAIN
# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]

# TODO Create ConfigEntry type alias with API object
# TODO Rename type alias and update all entry annotations


# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Immich Integration from a config entry."""

    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # entry.runtime_data = MyAPI(...)
    token="xW65lDDPLbCgZBCqlJIBhXcVU8wKOBj3HQhJH87k"

    entry.runtime_data =  AuthenticatedClient(base_url="http://immich.lumiere/api", token=token, headers={"Content-Type": "application/json",'Accept': 'application/json',"Cookie":"immich_access_token={}".format(token)})

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the an async service example component."""
    @callback
    def refresh(call: ServiceCall) -> None:
        """My first service."""
        _LOGGER.info('Received data', call.data)

    # Register our service with Home Assistant.
    hass.services.async_register(DOMAIN, 'refresh', refresh)
    await hass.config_entries.async_forward_entry_setups(config, PLATFORMS)

    # Return boolean to indicate that initialization was successfully.
    return True
def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the sync service example component."""
    def pause_job(call: ServiceCall) -> None:
        """My first service."""
        _LOGGER.info('Received data', call.data)

    # Register our service with Home Assistant.
    hass.services.register(DOMAIN, 'pause_job', pause_job)
    hass.config_entries.async_forward_entry_setup(config,PLATFORMS)


    # Return boolean to indicate that initialization was successfully.
    return True
