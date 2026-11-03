"""Weather entity for Meteo Alto Adige."""

from __future__ import annotations

from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import (
    CONF_STATION_NAME,
    DOMAIN,
    FORECAST_ENTITY_ID,
)
from .coordinator import MeteoAltoAdigeCoordinator


VALID_CONDITIONS = {
    "clear-night",
    "cloudy",
    "exceptional",
    "fog",
    "hail",
    "lightning",
    "lightning-rainy",
    "partlycloudy",
    "pouring",
    "rainy",
    "snowy",
    "snowy-rainy",
    "sunny",
    "windy",
    "windy-variant",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the weather entity."""

    async_add_entities(
        [
            MeteoAltoAdigeWeather(
                hass=hass,
                entry=entry,
                coordinator=entry.runtime_data,
            )
        ]
    )


class MeteoAltoAdigeWeather(
    CoordinatorEntity[MeteoAltoAdigeCoordinator],
    WeatherEntity,
):
    """Combined station measurements and MeteoEuregio forecast."""

    _attr_has_entity_name = True
    _attr_name = None

    _attr_native_temperature_unit = (
        UnitOfTemperature.CELSIUS
    )
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = (
        UnitOfSpeed.KILOMETERS_PER_HOUR
    )
    _attr_native_precipitation_unit = "mm"

    _attr_attribution = (
        "IT: Dati delle stazioni meteorologiche: "
        "Agenzia per la Protezione civile, "
        "Provincia autonoma di Bolzano - Alto Adige. "
        "Condizioni e previsioni: MeteoEuregio. | "
        "DE: Wetterstationsdaten: Agentur für Bevölkerungsschutz, "
        "Autonome Provinz Bozen - Südtirol. "
        "Wetterlage und Vorhersagen: MeteoEuregio. | "
        "EN: Weather-station data: Civil Protection Agency, "
        "Autonomous Province of Bolzano - South Tyrol. "
        "Conditions and forecasts: MeteoEuregio."
    )

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: MeteoAltoAdigeCoordinator,
    ) -> None:
        """Initialize the weather entity."""

        super().__init__(coordinator)

        self.hass = hass
        self.entry = entry

        self._attr_unique_id = (
            f"{entry.entry_id}_weather"
        )

        self._attr_device_info = {
            "identifiers": {
                (
                    DOMAIN,
                    entry.data["station_id"],
                )
            },
            "name": entry.data[CONF_STATION_NAME],
            "manufacturer": (
                "Provincia autonoma di Bolzano"
            ),
        }

    @property
    def condition(self) -> str | None:
        """Return the condition supplied by MeteoEuregio."""

        source = self.hass.states.get(
            FORECAST_ENTITY_ID
        )

        if source is None:
            return None

        if source.state in VALID_CONDITIONS:
            return source.state

        return None

    @property
    def supported_features(
        self,
    ) -> WeatherEntityFeature:
        """Return forecast features supported by MeteoEuregio."""

        source = self.hass.states.get(
            FORECAST_ENTITY_ID
        )

        if source is None:
            return WeatherEntityFeature(0)

        raw_features = source.attributes.get(
            "supported_features",
            0,
        )

        try:
            return WeatherEntityFeature(
                int(raw_features)
            )
        except (TypeError, ValueError):
            return WeatherEntityFeature(0)

    async def _async_get_forecast(
        self,
        forecast_type: str,
    ) -> list[Forecast] | None:
        """Retrieve a forecast from MeteoEuregio."""

        source = self.hass.states.get(
            FORECAST_ENTITY_ID
        )

        if source is None:
            return None

        response = await self.hass.services.async_call(
            domain="weather",
            service="get_forecasts",
            service_data={
                ATTR_ENTITY_ID: FORECAST_ENTITY_ID,
                "type": forecast_type,
            },
            blocking=True,
            return_response=True,
        )

        if not isinstance(response, dict):
            return None

        source_response = response.get(
            FORECAST_ENTITY_ID
        )

        if not isinstance(source_response, dict):
            return None

        forecast = source_response.get("forecast")

        if not isinstance(forecast, list):
            return None

        return forecast

    async def async_forecast_daily(
        self,
    ) -> list[Forecast] | None:
        """Return the daily MeteoEuregio forecast."""

        return await self._async_get_forecast(
            "daily"
        )

    async def async_forecast_hourly(
        self,
    ) -> list[Forecast] | None:
        """Return the hourly MeteoEuregio forecast."""

        return await self._async_get_forecast(
            "hourly"
        )

    async def async_forecast_twice_daily(
        self,
    ) -> list[Forecast] | None:
        """Return the twice-daily forecast."""

        return await self._async_get_forecast(
            "twice_daily"
        )

    @property
    def native_temperature(
        self,
    ) -> float | None:
        """Return measured temperature."""

        return self.coordinator.data.get(
            "temperature"
        )

    @property
    def humidity(
        self,
    ) -> float | None:
        """Return measured humidity."""

        return self.coordinator.data.get(
            "humidity"
        )

    @property
    def native_pressure(
        self,
    ) -> float | None:
        """Return measured pressure."""

        return self.coordinator.data.get(
            "pressure"
        )

    @property
    def native_wind_speed(
        self,
    ) -> float | None:
        """Return measured mean wind speed."""

        return self.coordinator.data.get(
            "wind_speed"
        )

    @property
    def native_wind_gust_speed(
        self,
    ) -> float | None:
        """Return measured wind gust speed."""

        return self.coordinator.data.get(
            "wind_gust"
        )

    @property
    def wind_bearing(
        self,
    ) -> str | float | None:
        """Return measured wind direction."""

        return self.coordinator.data.get(
            "wind_bearing"
        )

    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, Any]:
        """Return station-specific attributes."""

        data = self.coordinator.data

        attributes = {
            key: data.get(key)
            for key in (
                "station_code",
                "altitude",
                "latitude",
                "longitude",
                "updated",
                "precipitation",
                "solar_radiation",
            )
            if data.get(key) is not None
        }

        attributes["condition_source"] = (
            FORECAST_ENTITY_ID
        )
        attributes["forecast_source"] = (
            FORECAST_ENTITY_ID
        )

        return attributes