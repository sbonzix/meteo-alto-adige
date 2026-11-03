from __future__ import annotations
from datetime import timedelta
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import MeteoAltoAdigeClient, MeteoAltoAdigeError
from .const import CONF_STATION_ID, DEFAULT_SCAN_INTERVAL, DOMAIN
_LOGGER = logging.getLogger(__name__)

class MeteoAltoAdigeCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL))
        self.client = MeteoAltoAdigeClient(async_get_clientsession(hass))
        self.station_id = entry.data[CONF_STATION_ID]
    async def _async_update_data(self) -> dict:
        try:
            return await self.client.station(self.station_id)
        except MeteoAltoAdigeError as err:
            raise UpdateFailed(str(err)) from err
