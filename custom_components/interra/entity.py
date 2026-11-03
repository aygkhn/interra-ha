"""Interra ortak entity temeli."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .client import InterraClient
from .const import DOMAIN, SIGNAL_CONN, SIGNAL_UPDATE


class InterraEntity(Entity):
    """Tüm Interra entity'leri için ortak taban (cihaz bilgisi, abonelik, durum)."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(self, client: InterraClient, dev_id: int, info: dict):
        self._client = client
        self._id = dev_id
        self._info = info
        self._attr_unique_id = f"interra_{dev_id}"
        self._attr_name = info["name"]
        self._attr_available = True

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"interra_{self._id}")},
            name=self._info["name"],
            manufacturer="Interra",
            model="Interra Pro",
            suggested_area=self._info["room"] or None,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_UPDATE.format(self._id), self._handle_update
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_CONN, self._handle_conn)
        )
        # Başlangıç durumu: kurulumdan önce gelmiş olabilir, saklanandan oku
        stored = self._client.states.get(self._id)
        if stored is not None:
            self._handle_update(stored[0], stored[1])

    def _handle_conn(self, ok: bool) -> None:
        self._attr_available = ok
        self.async_write_ha_state()

    def _handle_update(self, is_active, raw) -> None:
        """Alt sınıflar override eder."""
        self.async_write_ha_state()
