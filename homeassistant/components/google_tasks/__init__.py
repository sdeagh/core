"""The Google Tasks integration."""

from __future__ import annotations

from aiohttp import ClientError, ClientResponseError

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_entry_oauth2_flow

from . import api
from .const import DOMAIN
from .exceptions import GoogleTasksApiError
from .types import GoogleTasksConfigEntry, GoogleTasksData

__all__ = [
    "DOMAIN",
]

PLATFORMS: list[Platform] = [Platform.TODO]


async def async_setup_entry(hass: HomeAssistant, entry: GoogleTasksConfigEntry) -> bool:
    """Set up Google Tasks from a config entry."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )
    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    auth = api.AsyncConfigEntryAuth(hass, session)
    try:
        await auth.async_get_access_token()
    except ClientResponseError as err:
        if 400 <= err.status < 500:
            raise ConfigEntryAuthFailed(
                "OAuth session is not valid, reauth required"
            ) from err
        raise ConfigEntryNotReady from err
    except ClientError as err:
        raise ConfigEntryNotReady from err

    try:
        task_lists = await auth.list_task_lists()
    except GoogleTasksApiError as err:
        raise ConfigEntryNotReady from err

    entry.runtime_data = GoogleTasksData(auth, task_lists)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: GoogleTasksConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
