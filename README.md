# Meteo Alto Adige Stations

Custom integration for Home Assistant providing current measurements
from the official weather stations of the Autonomous Province of
Bolzano - South Tyrol.

## Features

- Configuration from the Home Assistant user interface
- Dynamic list of official weather stations
- Official station codes, coordinates and elevation
- Air temperature
- Relative humidity
- Atmospheric pressure
- Precipitation since midnight
- Mean wind speed
- Wind gust
- Wind direction
- Solar radiation, when available
- Current condition from MeteoEuregio
- Daily and hourly forecasts from MeteoEuregio

## Data sources

Observed measurements and station metadata are provided by the
Civil Protection Agency of the Autonomous Province of
Bolzano - South Tyrol.

Weather condition and forecast data are obtained from an existing
MeteoEuregio weather entity in Home Assistant.

The currently configured default source entity is:

    weather.esterno_meteoeuregio

Full attribution in Italian, German and English is available in
NOTICE.md.

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
