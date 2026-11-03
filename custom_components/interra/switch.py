"""Interra aç/kapat cihazları (ışık/genel/iklim-değersiz/alarm) -> switch."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import InterraClient
from .const import ACT_CLOSE, ACT_OPEN, DOMAIN
from .entity import InterraEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add: AddEntitiesCallback):
    client: InterraClient = hass.data[DOMAIN][entry.entry_id]
    add(
        InterraSwitch(client, did, info)
        for did, info in client.devices.items()
        if not info["is_cover"]
    )


class InterraSwitch(InterraEntity, SwitchEntity):
    def __init__(self, client, dev_id, info):
        super().__init__(client, dev_id, info)
        self._attr_is_on = False

    def _handle_update(self, is_active, raw) -> None:
        if is_active is not None:
            self._attr_is_on = bool(is_active)
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        self._attr_is_on = True
        self.async_write_ha_state()
        await self.hass.async_add_executor_job(self._client.action, self._id, ACT_OPEN, 100)

    async def async_turn_off(self, **kwargs):
        self._attr_is_on = False
        self.async_write_ha_state()
        await self.hass.async_add_executor_job(self._client.action, self._id, ACT_CLOSE, 0)
