from __future__ import annotations
import logging
from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectOptionDict
from .api import MeteoAltoAdigeClient, MeteoAltoAdigeError
from .const import CONF_STATION_ID, CONF_STATION_NAME, DOMAIN
_LOGGER = logging.getLogger(__name__)

class MeteoAltoAdigeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors = {}
        client = MeteoAltoAdigeClient(async_get_clientsession(self.hass))
        try:
            stations = await client.stations()
        except MeteoAltoAdigeError:
            _LOGGER.exception("Unable to retrieve station list")
            return self.async_abort(reason="cannot_connect")
        station_map = {item.station_id: item.name for item in stations}
        if user_input is not None:
            station_id = user_input[CONF_STATION_ID]
            try:
                await client.station(station_id)
            except MeteoAltoAdigeError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"station_{station_id}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=station_map.get(station_id, station_id),
                    data={CONF_STATION_ID: station_id, CONF_STATION_NAME: station_map.get(station_id, station_id)},
                )
        options = [SelectOptionDict(value=s.station_id, label=s.name) for s in stations]
        schema = vol.Schema({vol.Required(CONF_STATION_ID): SelectSelector(SelectSelectorConfig(options=options, mode="dropdown"))})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
