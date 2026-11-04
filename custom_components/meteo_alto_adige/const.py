DOMAIN = "meteo_alto_adige"

CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
CONF_FORECAST_ENTITY = "forecast_entity"

API_BASE_URL = (
"https://geoservices.buergernetz.bz.it/"
        "services/meteo/v1"
)

STATIONS_URL = f"{API_BASE_URL}/stations"

SENSORS_URL = f"{API_BASE_URL}/sensors"

DEFAULT_SCAN_INTERVAL = 600
