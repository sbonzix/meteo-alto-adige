from __future__ import annotations
from dataclasses import dataclass
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPrecipitationDepth, UnitOfPressure, UnitOfSpeed, UnitOfTemperature, UnitOfVolumetricFlux
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import CONF_STATION_NAME
from .coordinator import MeteoAltoAdigeCoordinator

@dataclass(frozen=True, kw_only=True)
class Desc(SensorEntityDescription): pass
DESCRIPTIONS = (
 Desc(key="temperature", translation_key="temperature", device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
 Desc(key="humidity", translation_key="humidity", device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
 Desc(key="pressure", translation_key="pressure", device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE, native_unit_of_measurement=UnitOfPressure.HPA, state_class=SensorStateClass.MEASUREMENT),
 Desc(
     key="precipitation", 
     translation_key="precipitation", 
     device_class=SensorDeviceClass.PRECIPITATION, 
     native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS, 
     state_class=SensorStateClass.MEASUREMENT),
 Desc(
     key="sunshine_duration",
     translation_key="sunshine_duration",
     native_unit_of_measurement="s",
     state_class=SensorStateClass.MEASUREMENT,
 ),
 Desc(key="wind_speed", translation_key="wind_speed", device_class=SensorDeviceClass.WIND_SPEED, native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR, state_class=SensorStateClass.MEASUREMENT),
 Desc(key="wind_gust", translation_key="wind_gust", device_class=SensorDeviceClass.WIND_SPEED, native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR, state_class=SensorStateClass.MEASUREMENT),
 Desc(key="solar_radiation", translation_key="solar_radiation", native_unit_of_measurement="W/m²", state_class=SensorStateClass.MEASUREMENT),
)
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities([StationSensor(entry, entry.runtime_data, d) for d in DESCRIPTIONS])
class StationSensor(
        CoordinatorEntity[MeteoAltoAdigeCoordinator],
        SensorEntity,
    ):
        """Representation of a station measurement."""
    
        _attr_has_entity_name = True
    
        _attr_attribution = (
            "IT: Dati: Agenzia per la Protezione civile, "
            "Provincia autonoma di Bolzano - Alto Adige. | "
            "DE: Daten: Agentur für Bevölkerungsschutz, "
            "Autonome Provinz Bozen - Südtirol. | "
            "EN: Data: Civil Protection Agency, "
            "Autonomous Province of Bolzano - South Tyrol."
        )
    
        def __init__(
            self,
            entry,
            coordinator,
            description,
        ):
            """Initialize the sensor."""
    
            super().__init__(coordinator)
    
            self.entity_description = description
            self._attr_unique_id = (
                f"{entry.entry_id}_{description.key}"
            )
    
            self._attr_device_info = {
                "identifiers": {
                    (
                        "meteo_alto_adige",
                        entry.data["station_id"],
                    )
                },
                "name": entry.data[CONF_STATION_NAME],
                "manufacturer": (
                    "Provincia autonoma di Bolzano"
                ),
            }
    
        @property
        def native_value(self):
            """Return the current sensor value."""
    
            return self.coordinator.data.get(
                self.entity_description.key
            )
