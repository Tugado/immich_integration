"""The Immich Integration."""

from __future__ import annotations
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import _LOGGER, HomeAssistant,callback,ServiceCall
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
#from . import hub
from .immich_client import AuthenticatedClient
from .const import DOMAIN,MANAGER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from immich_client.api.authentication import validate_access_token
from immich_client.models.validate_access_token_response_dto import ValidateAccessTokenResponseDto

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
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    host =  entry.data[CONF_HOST]
    client = AuthenticatedClient(base_url=host, token=password, headers={"Content-Type": "application/json",'Accept': 'application/json',"Cookie":"immich_access_token={}".format(password)})
    validate: ValidateAccessTokenResponseDto = await hass.async_add_executor_job(validate_access_token.asyncio(client=client))
    if not validate:
        _LOGGER.error("Unable to login to Immich")
        return False
    forward_setup = hass.config_entries.async_forward_entry_setup
    hass.data[DOMAIN] = {entry.entry_id: {}}
    hass.data[DOMAIN][entry.entry_id][MANAGER] = client
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Create a DataUpdateCoordinator for the manager
    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            await hass.async_add_executor_job(client.update)
        except Exception as err:
            raise UpdateFailed(f"Update failed: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="immich_integration",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    # Store the coordinator instance in hass.data
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
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
    def pause_job(call: ServiceCall) -> None:
        """My first service."""
        _LOGGER.info('Received data', call.data)

    # Register our service with Home Assistant.
    hass.services.async_register(DOMAIN, 'pause_job', pause_job)
    hass.services.async_register(DOMAIN, 'refresh', refresh)

    # Return boolean to indicate that initialization was successfully.
    return True