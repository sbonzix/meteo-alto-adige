# Meteo Alto Adige Stations

Custom integration for Home Assistant providing current measurements
from the official weather stations of the Autonomous Province of
Bolzano - South Tyrol.

## Features
- Official South Tyrol Open Data weather service
- Dynamic selection of official weather stations
- Air temperature
- Relative humidity
- Atmospheric pressure
- Precipitation
- Wind speed
- Wind gust
- Wind direction in degrees
- Global solar radiation
- Sunshine duration
- Optional external Home Assistant weather entity for conditions
  and forecasts
- Daily, hourly and twice-daily forecasts when supported
- Italian, German and English translations
- UI-based configuration

## Data sources

Observed measurements and station metadata are provided by the
Civil Protection Agency of the Autonomous Province of
Bolzano - South Tyrol.

Weather condition and forecast data are obtained from an existing
MeteoEuregio weather entity in Home Assistant.

Full attribution in Italian, German and English is available in
NOTICE.md.

## Weather conditions and forecasts

Current measurements are obtained directly from the official
South Tyrol Open Data weather services.

Optionally, any Home Assistant `weather` entity can be selected
to provide the current weather condition and forecasts.

The forecast provider is optional. Without one, all current
measurements from the selected provincial weather station remain
available.

The forecast source can be configured or changed from:

Settings > Devices & services > Meteo Alto Adige Stations > Configure

## Manual installation

Copy:

    custom_components/meteo_alto_adige

into the `custom_components` directory of Home Assistant.

Restart Home Assistant, then open:

    Settings > Devices & services > Add integration

Search for:

    Meteo Alto Adige Stations

## HACS or Marketplace installation

Add this GitHub repository as a custom integration repository,
install the integration and restart Home Assistant.

## Disclaimer

This is an independent open-source project. It is not an official
integration of, endorsed by, or affiliated with the Autonomous
Province of Bolzano - South Tyrol, its Civil Protection Agency,
SIAG, Meteo Alto Adige, or MeteoEuregio.

## License

The integration source code is released under the MIT License.

See NOTICE.md for data sources, licensing and attribution.
