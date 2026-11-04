"""Config flow for Meteo Alto Adige."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .api import MeteoAltoAdigeClient, MeteoAltoAdigeError
from .const import (
    CONF_FORECAST_ENTITY,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DOMAIN,
)


_LOGGER = logging.getLogger(__name__)


class MeteoAltoAdigeConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle the Meteo Alto Adige config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle initial setup."""

        errors: dict[str, str] = {}

        client = MeteoAltoAdigeClient(
            async_get_clientsession(self.hass)
        )

        try:
            stations = await client.stations()

        except MeteoAltoAdigeError:
            _LOGGER.exception(
                "Unable to retrieve weather stations"
            )

            return self.async_abort(
                reason="cannot_connect"
            )

        station_names = {
            station.station_id: station.name
            for station in stations
        }

        if user_input is not None:
            station_id = user_input[CONF_STATION_ID]

            try:
                await client.station(station_id)

            except MeteoAltoAdigeError:
                errors["base"] = "cannot_connect"

            else:
                await self.async_set_unique_id(
                    f"station_{station_id}"
                )

                self._abort_if_unique_id_configured()

                station_name = station_names.get(
                    station_id,
                    station_id,
                )

                return self.async_create_entry(
                    title=station_name,
                    data={
                        CONF_STATION_ID: station_id,
                        CONF_STATION_NAME: station_name,
                    },
                )

        station_options = [
            SelectOptionDict(
                value=station.station_id,
                label=station.name,
            )
            for station in stations
        ]

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_STATION_ID
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=station_options,
                        mode="dropdown",
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> MeteoAltoAdigeOptionsFlow:
        """Return the options flow."""

        return MeteoAltoAdigeOptionsFlow()


class MeteoAltoAdigeOptionsFlow(
    OptionsFlowWithReload
):
    """Handle Meteo Alto Adige options."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage integration options."""

        if user_input is not None:
            return self.async_create_entry(
                data=user_input
            )

        current_entity = (
            self.config_entry.options.get(
                CONF_FORECAST_ENTITY
            )
        )

        schema = vol.Schema(
            {
vol.Optional(
    CONF_FORECAST_ENTITY,
    description={
        "suggested_value": current_entity,
    },
): EntitySelector(
    EntitySelectorConfig(
        domain="weather",
    )
)
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
