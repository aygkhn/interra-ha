"""Interra entegrasyonu — HA içinde panelle kalıcı bağlantı."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .client import InterraClient
from .const import (
    CONF_HOST,
    CONF_LOCAL_HOST,
    CONF_LOCAL_PORT,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    DOMAIN,
    SIGNAL_CONN,
    SIGNAL_UPDATE,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SWITCH, Platform.COVER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = entry.data
    client = InterraClient(
        data[CONF_HOST], data.get(CONF_PORT, 2083),
        data[CONF_USERNAME], data[CONF_PASSWORD],
        local_host=data.get(CONF_LOCAL_HOST) or None,
        local_port=data.get(CONF_LOCAL_PORT) or None,
    )

    @callback
    def _state(dev_id, is_active, raw):
        hass.loop.call_soon_threadsafe(
            async_dispatcher_send, hass, SIGNAL_UPDATE.format(dev_id), is_active, raw
        )

    @callback
    def _conn(ok):
        hass.loop.call_soon_threadsafe(async_dispatcher_send, hass, SIGNAL_CONN, ok)

    client.on_state = _state
    client.on_connection = _conn

    client.start()
    # cihaz listesi gelsin diye (bloklamadan) bekle
    await hass.async_add_executor_job(client.wait_ready, 25)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # Entity'ler kurulduktan sonra anlık durumu tazele (başlangıç yarışına karşı)
    await hass.async_add_executor_job(client.request_status)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    client: InterraClient = hass.data[DOMAIN].pop(entry.entry_id)
    await hass.async_add_executor_job(client.stop)
    return unload_ok
