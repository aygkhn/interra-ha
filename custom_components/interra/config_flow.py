"""Interra yapılandırma akışı (host/port/kullanıcı/şifre)."""
from __future__ import annotations

import socket

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import (
    CONF_HOST,
    CONF_LOCAL_HOST,
    CONF_LOCAL_PORT,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    DEFAULT_PORT,
    DOMAIN,
)


def _test(candidates):
    """Adaylardan en az biri bağlanabiliyor mu."""
    last = None
    for host, port in candidates:
        try:
            s = socket.create_connection((host, int(port)), timeout=8)
            s.close()
            return
        except OSError as err:
            last = err
    raise last or OSError("no host")


class InterraConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        errors = {}
        if user_input is not None:
            cands = []
            if user_input.get(CONF_LOCAL_HOST):
                cands.append(
                    (user_input[CONF_LOCAL_HOST],
                     user_input.get(CONF_LOCAL_PORT) or user_input[CONF_PORT])
                )
            cands.append((user_input[CONF_HOST], user_input[CONF_PORT]))
            try:
                await self.hass.async_add_executor_job(_test, cands)
            except OSError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Interra", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_LOCAL_HOST): str,
                vol.Optional(CONF_LOCAL_PORT): int,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
