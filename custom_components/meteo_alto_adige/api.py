"""Client for official South Tyrol weather-station services."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError, ClientSession


STATIONS_URL = (
    "https://geoservices.buergernetz.bz.it/"
    "services/meteo/v1/stations"
)

CURRENT_DATA_URL = (
    "https://www.provincia.bz.it/"
    "weather/mobile/akt_w.asp"
)


class MeteoAltoAdigeError(Exception):
    """Base integration API error."""


@dataclass(slots=True)
class Station:
    """Weather station metadata."""

    station_id: str
    name: str
    altitude: float | None = None
    latitude: float | None = None
    longitude: float | None = None


_TAG_RE = re.compile(r"<[^>]+>")


def _html_to_text(raw: str) -> str:
    """Convert the legacy station page to normalized text."""

    raw = re.sub(
        r"<script\b[^>]*>.*?</script>",
        " ",
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    )

    raw = re.sub(
        r"<style\b[^>]*>.*?</style>",
        " ",
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    )

    raw = re.sub(
        r"<(?:br|p|div|li|tr|h[1-6])\b[^>]*>",
        "\n",
        raw,
        flags=re.IGNORECASE,
    )

    raw = _TAG_RE.sub(" ", raw)
    raw = html.unescape(raw)
    raw = raw.replace("\xa0", " ")

    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n\s*\n+", "\n", raw)

    return raw.strip()


def _number(
    text: str,
    label: str,
) -> float | None:
    """Extract a numeric measurement following a label."""

    match = re.search(
        label
        + r"\s*:?\s*(-?\d+(?:[.,]\d+)?|--)",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None

    raw_value = match.group(1)

    if raw_value == "--":
        return None

    return float(raw_value.replace(",", "."))


def parse_station_list(
    payload: dict[str, Any],
    ) -> list[Station]:
    """Parse the official stations GeoJSON response."""

    features = payload.get("features")

    if not isinstance(features, list):
        raise MeteoAltoAdigeError(
            "Invalid stations GeoJSON response"
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

        # Keep meteorological stations.
        # The API also contains hydrological and other stations.
        if not str(station_code).upper().endswith("MS"):
            continue

        name = (
            properties.get("NAME_I")
            or properties.get("NAME_D")
            or properties.get("NAME_E")
            or station_code
        )

        stations.append(
            Station(
                station_id=str(station_code),
                name=str(name).strip().title(),
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


def parse_current_station(
    raw: str,
    station: Station,
) -> dict[str, Any]:
    """Parse current observations from the station page."""

    text = _html_to_text(raw)

    code_match = re.search(
        r"Station code\s*:\s*([A-Z0-9]+)",
        text,
        re.IGNORECASE,
    )

    altitude_match = re.search(
        r"Station altitude\s*:\s*(\d+(?:[.,]\d+)?)",
        text,
        re.IGNORECASE,
    )

    coordinates_match = re.search(
        r"Latitude\s*/\s*Longitude\s*:\s*"
        r"([\d.]+)\s*°?\s*/\s*([\d.]+)",
        text,
        re.IGNORECASE,
    )

    updated_match = re.search(
        r"Measured data from\s*"
        r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})",
        text,
        re.IGNORECASE,
    )

    wind_direction_match = re.search(
        r"Wind direction\s*:\s*"
        r"([A-Z]{1,3}|--)",
        text,
        re.IGNORECASE,
    )

    temperature = _number(
        text,
        r"Air temperature(?:\s*\(°C\))?",
    )

    if temperature is None:
        raise MeteoAltoAdigeError(
            "Temperature not found in station response"
        )

    altitude = station.altitude

    if altitude_match:
        altitude = float(
            altitude_match.group(1).replace(",", ".")
        )

    latitude = station.latitude
    longitude = station.longitude

    if coordinates_match:
        latitude = float(coordinates_match.group(1))
        longitude = float(coordinates_match.group(2))

    wind_bearing: str | None = None

    if (
        wind_direction_match
        and wind_direction_match.group(1) != "--"
    ):
        wind_bearing = (
            wind_direction_match.group(1).upper()
        )

    return {
        "name": station.name,
        "station_code": (
            code_match.group(1)
            if code_match
            else station.station_id
        ),
        "altitude": altitude,
        "latitude": latitude,
        "longitude": longitude,
        "updated": (
            updated_match.group(1)
            if updated_match
            else None
        ),
        "temperature": temperature,
        "humidity": _number(
            text,
            r"Relative humidity(?:\s*\(%\))?",
        ),
        "pressure": _number(
            text,
            r"Air pressure(?:\s*\(hPa\))?",
        ),
        "precipitation": _number(
            text,
            r"Precipitation since midnight"
            r"(?:\s*\(mm\))?",
        ),
        "wind_speed": _number(
            text,
            r"(?:Medium|Average) wind speed"
            r"(?:\s*\(km/h\))?",
        ),
        "wind_gust": _number(
            text,
            r"(?:Gust speed|Wind gust)"
            r"(?:\s*\(km/h\))?",
        ),
        "wind_bearing": wind_bearing,
        "solar_radiation": _number(
            text,
            r"Global (?:Solar Irradiance|radiation)"
            r"(?:\s*\(W/m²\))?",
        ),
    }


class MeteoAltoAdigeClient:
    """Client for South Tyrol weather services."""

    def __init__(
        self,
        session: ClientSession,
    ) -> None:
        self._session = session

        self._headers = {
            "Accept-Language": "en",
            "User-Agent": (
                "HomeAssistant MeteoAltoAdige"
            ),
        }

        self._stations_cache: dict[str, Station] = {}

    async def _get_json(
        self,
        url: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Retrieve a JSON response."""

        try:
            async with self._session.get(
                url,
                params=params,
                headers=self._headers,
                timeout=20,
            ) as response:
                response.raise_for_status()

                payload = await response.json(
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

        if not isinstance(payload, dict):
            raise MeteoAltoAdigeError(
                "Unexpected JSON response"
            )

        return payload

    async def _get_text(
        self,
        url: str,
        params: dict[str, str] | None = None,
    ) -> str:
        """Retrieve a text response."""

        try:
            async with self._session.get(
                url,
                params=params,
                headers=self._headers,
                timeout=20,
            ) as response:
                response.raise_for_status()

                return await response.text(
                    errors="replace"
                )

        except (
            ClientError,
            TimeoutError,
        ) as error:
            raise MeteoAltoAdigeError(
                str(error)
            ) from error

    async def stations(
        self,
    ) -> list[Station]:
        """Retrieve official station metadata."""

        payload = await self._get_json(
            STATIONS_URL,
            params={
                "output_format": "JSON",
            },
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
        """Retrieve current observations for a station."""

        if station_id not in self._stations_cache:
            await self.stations()

        station = self._stations_cache.get(station_id)

        if station is None:
            raise MeteoAltoAdigeError(
                f"Unknown station: {station_id}"
            )

        # Temporary compatibility bridge:
        # current observations still come from the official
        # station page until the timeseries sensor mapping
        # has been fully validated.
        raw = await self._get_text(
            CURRENT_DATA_URL,
            params={
                "stations_stid": (
                    await self._legacy_station_id(
                        station.station_id
                    )
                )
            },
        )

        return parse_current_station(
            raw,
            station,
        )

    async def _legacy_station_id(
        self,
        station_code: str,
    ) -> str:
        """Resolve the old numeric station identifier.

        The legacy page is temporarily used only for current
        observations. Its overview maps station codes to the
        corresponding numeric IDs.
        """

        overview = await self._get_text(
            CURRENT_DATA_URL
        )

        pattern = re.compile(
            r"href=[\"'][^\"']*"
            r"stations_stid=(\d+)[^\"']*[\"']"
            r"[^>]*>(.*?)</a>",
            re.IGNORECASE | re.DOTALL,
        )

        for legacy_id, card in pattern.findall(overview):
            card_text = _html_to_text(card)

            if station_code in card_text:
                return legacy_id

        # The overview cards do not always include the
        # official station code. Match by official name.
        station = self._stations_cache.get(station_code)

        if station is not None:
            wanted_name = station.name.casefold()

            for legacy_id, card in pattern.findall(overview):
                card_text = _html_to_text(card).casefold()

                if wanted_name in card_text:
                    return legacy_id

        raise MeteoAltoAdigeError(
            "Unable to map the official station code "
            "to the current-observation endpoint"
        )