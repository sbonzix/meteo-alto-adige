"""Client for the South Tyrol Open Data weather services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import (
    SENSORS_URL,
    STATIONS_URL,
)


class MeteoAltoAdigeError(Exception):
    """Base API error."""


@dataclass(slots=True)
class Station:
    """Weather station metadata."""

    station_id: str
    name: str
    altitude: float | None = None
    latitude: float | None = None
    longitude: float | None = None


def _as_float(
    value: Any,
) -> float | None:
    """Convert an API value to float."""

    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_station_list(
    payload: dict[str, Any],
) -> list[Station]:
    """Parse the station GeoJSON response."""

    features = payload.get("features")

    if not isinstance(features, list):
        raise MeteoAltoAdigeError(
            "Invalid stations response"
        )

    stations: list[Station] = []

    for feature in features:
        if not isinstance(feature, dict):
            continue

        properties = feature.get("properties")

        if not isinstance(properties, dict):
            continue

        station_code = properties.get("SCODE")

        if not station_code:
            continue

        station_code = str(station_code)

        # Only meteorological stations.
        if not station_code.upper().endswith("MS"):
            continue

        name = (
            properties.get("NAME_I")
            or properties.get("NAME_D")
            or properties.get("NAME_E")
            or station_code
        )

        stations.append(
            Station(
                station_id=station_code,
                name=str(name).strip(),
                altitude=_as_float(
                    properties.get("ALT")
                ),
                latitude=_as_float(
                    properties.get("LAT")
                ),
                longitude=_as_float(
                    properties.get("LONG")
                ),
            )
        )

    if not stations:
        raise MeteoAltoAdigeError(
            "No meteorological stations found"
        )

    return sorted(
        stations,
        key=lambda station: station.name.casefold(),
    )


def parse_sensor_data(
    payload: list[dict[str, Any]],
    station: Station,
) -> dict[str, Any]:
    """Convert Open Data sensor values to HA weather data."""

    sensors: dict[str, dict[str, Any]] = {}

    for item in payload:
        sensor_type = item.get("TYPE")

        if sensor_type:
            sensors[str(sensor_type)] = item

    def value(
        sensor_type: str,
    ) -> float | None:
        sensor = sensors.get(sensor_type)

        if sensor is None:
            return None

        return _as_float(sensor.get("VALUE"))

    # API wind measurements are m/s.
    # The integration exposes km/h.
    wind_speed_ms = value("WG")
    wind_gust_ms = value("WG.BOE")

    wind_speed = (
        wind_speed_ms * 3.6
        if wind_speed_ms is not None
        else None
    )

    wind_gust = (
        wind_gust_ms * 3.6
        if wind_gust_ms is not None
        else None
    )

    # Use the newest timestamp present in the response.
    dates = [
        item.get("DATE")
        for item in payload
        if item.get("DATE")
    ]

    updated = max(dates) if dates else None

    return {
        "name": station.name,
        "station_code": station.station_id,
        "altitude": station.altitude,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "updated": updated,

        "temperature": value("LT"),
        "humidity": value("LF"),
        "pressure": value("LD.RED"),

        "precipitation": value("N"),

        "wind_speed": wind_speed,
        "wind_gust": wind_gust,

        # Home Assistant accepts degrees for wind bearing.
        "wind_bearing": value("WR"),

        "solar_radiation": value("GS"),
        "sunshine_duration": value("SD"),
    }


class MeteoAltoAdigeClient:
    """Client for the South Tyrol weather Open Data API."""

    def __init__(
        self,
        session: ClientSession,
    ) -> None:
        self._session = session

        self._headers = {
            "Accept": "application/json",
            "User-Agent": (
                "HomeAssistant MeteoAltoAdige"
            ),
        }

        self._stations_cache: dict[str, Station] = {}

    async def _get_json(
        self,
        url: str,
        params: dict[str, str] | None = None,
    ) -> Any:
        """Retrieve JSON from the API."""

        try:
            async with self._session.get(
                url,
                params=params,
                headers=self._headers,
                timeout=20,
            ) as response:
                response.raise_for_status()

                return await response.json(
                    content_type=None
                )

        except (
            ClientError,
            TimeoutError,
            ValueError,
        ) as error:
            raise MeteoAltoAdigeError(
                str(error)
            ) from error

    async def stations(
        self,
    ) -> list[Station]:
        """Retrieve weather stations."""

        payload = await self._get_json(
            STATIONS_URL,
            params={
                "output_format": "JSON",
            },
        )

        if not isinstance(payload, dict):
            raise MeteoAltoAdigeError(
                "Invalid stations API response"
            )

        stations = parse_station_list(payload)

        self._stations_cache = {
            station.station_id: station
            for station in stations
        }

        return stations

    async def station(
        self,
        station_id: str,
    ) -> dict[str, Any]:
        """Retrieve the latest measurements for a station."""

        if station_id not in self._stations_cache:
            await self.stations()

        station = self._stations_cache.get(
            station_id
        )

        if station is None:
            raise MeteoAltoAdigeError(
                f"Unknown station: {station_id}"
            )

        payload = await self._get_json(
            SENSORS_URL,
            params={
                "station_code": station_id,
                "output_format": "JSON",
            },
        )

        if not isinstance(payload, list):
            raise MeteoAltoAdigeError(
                "Invalid sensors API response"
            )

        if not payload:
            raise MeteoAltoAdigeError(
                f"No measurements for station {station_id}"
            )

        return parse_sensor_data(
            payload,
            station,
        )
