"""Interra panjur/perde -> cover (yukarı/dur/aşağı)."""
from __future__ import annotations

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import InterraClient
from .const import ACT_DOWN, ACT_STOP, ACT_UP, DOMAIN, OBJ_BLIND
from .entity import InterraEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add: AddEntitiesCallback):
    client: InterraClient = hass.data[DOMAIN][entry.entry_id]
    add(
        InterraCover(client, did, info)
        for did, info in client.devices.items()
        if info["is_cover"]
    )


class InterraCover(InterraEntity, CoverEntity):
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    def __init__(self, client, dev_id, info):
        super().__init__(client, dev_id, info)
        self._attr_device_class = (
            CoverDeviceClass.SHUTTER if info["type"] == OBJ_BLIND else CoverDeviceClass.CURTAIN
        )
        self._closed = True

    @property
    def is_closed(self) -> bool | None:
        return self._closed

    def _handle_update(self, is_active, raw) -> None:
        if is_active is not None:
            self._closed = not bool(is_active)
        self.async_write_ha_state()

    async def async_open_cover(self, **kwargs):
        self._closed = False
        self.async_write_ha_state()
        await self.hass.async_add_executor_job(self._client.action, self._id, ACT_UP, 0)

    async def async_close_cover(self, **kwargs):
        self._closed = True
        self.async_write_ha_state()
        await self.hass.async_add_executor_job(self._client.action, self._id, ACT_DOWN, 0)

    async def async_stop_cover(self, **kwargs):
        await self.hass.async_add_executor_job(self._client.action, self._id, ACT_STOP, 0)
