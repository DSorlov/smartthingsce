"""Constants for the SmartThings Community Edition integration."""

# Component domain
__version__ = "1.5.0"
VERSION = __version__
DOMAIN = "smartthingsce"

# Device information
DEVICE_AUTHOR = "Daniel Sörlöv"
DEVICE_VERSION = __version__

# Configuration keys
CONF_ACCESS_TOKEN = "access_token"
CONF_LOCATION_ID = "location_id"
CONF_NAME = "name"
CONF_WEBHOOK_ENABLED = "webhook_enabled"
CONF_WEBHOOK_URL = "webhook_url"
CONF_TUNNEL_SUBDOMAIN = "tunnel_subdomain"

# API endpoints
API_BASE_URL = "https://api.smartthings.com/v1"
API_DEVICES = f"{API_BASE_URL}/devices"
API_LOCATIONS = f"{API_BASE_URL}/locations"
API_SCENES = f"{API_BASE_URL}/scenes"
API_ROOMS = f"{API_BASE_URL}/locations/{{location_id}}/rooms"

# Update intervals
UPDATE_INTERVAL_SECONDS = 30
WEBHOOK_TIMEOUT_SECONDS = 30

# Webhook configuration
WEBHOOK_PATH = "/api/smartthingsce"
DEFAULT_TUNNEL_PORT = 8123

# Platform support
PLATFORMS = [
    "binary_sensor",
    "climate",
    "cover",
    "fan",
    "light",
    "lock",
    "sensor",
    "switch",
    "vacuum",
]

# Attribute mapping
ATTR_DEVICE_ID = "device_id"
ATTR_CAPABILITY = "capability"
ATTR_COMMAND = "command"
ATTR_ARGUMENTS = "arguments"
ATTR_SCENE_ID = "scene_id"
ATTR_LOCATION_ID = "location_id"
ATTR_ROOM_ID = "room_id"

# Service names
SERVICE_SEND_COMMAND = "send_command"
SERVICE_EXECUTE_SCENE = "execute_scene"
SERVICE_REFRESH_DEVICES = "refresh_devices"

# Error messages
ERROR_AUTH_FAILED = "auth_failed"
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_INVALID_TOKEN = "invalid_token"
ERROR_NO_LOCATIONS = "no_locations"
ERROR_UNKNOWN = "unknown"

# Device attribution
ATTRIBUTION = "Data provided by SmartThings API"

# SmartThings capability to Home Assistant domain mapping
CAPABILITY_TO_DOMAIN = {
    "switch": "switch",
    "switchLevel": "light",
    "colorControl": "light",
    "colorTemperature": "light",
    "thermostat": "climate",
    "thermostatCoolingSetpoint": "climate",
    "thermostatHeatingSetpoint": "climate",
    "thermostatFanMode": "climate",
    "thermostatMode": "thermostat",
    "lock": "lock",
    "doorControl": "cover",
    "windowShade": "cover",
    "garageDoorControl": "cover",
    "fanSpeed": "fan",
    # Media Player capabilities
    "mediaPlayback": "media_player",
    "audioVolume": "media_player",
    "tvChannel": "media_player",
    "mediaInputSource": "media_player",
    "audioMute": "media_player",
    # Siren capabilities
    "alarm": "siren",
    "tone": "siren",
    "chime": "siren",
    # Button capabilities
    "button": "button",
    "holdableButton": "button",
    # Air Quality capabilities
    "airQualityDetector": "sensor",
    "dustSensor": "sensor",
    "tvocMeasurement": "sensor",
    "formaldehydeMeasurement": "sensor",
    "airQualityHealthConcern": "sensor",
    # Valve capabilities
    "valve": "valve",
    # Energy Monitor capabilities (enhanced)
    "voltageMeasurement": "sensor",
    "currentMeasurement": "sensor",
    # Camera capabilities
    "videoStream": "camera",
    "imageCapture": "camera",
    "videoCapture": "camera",
    "contactSensor": "binary_sensor",
    "motionSensor": "binary_sensor",
    "presenceSensor": "binary_sensor",
    "waterSensor": "binary_sensor",
    "smokeDetector": "binary_sensor",
    "carbonMonoxideDetector": "binary_sensor",
    "temperatureMeasurement": "sensor",
    "relativeHumidityMeasurement": "sensor",
    "illuminanceMeasurement": "sensor",
    "powerMeter": "sensor",
    "energyMeter": "sensor",
    "battery": "sensor",
    "voltage": "sensor",
    # Appliance capabilities
    "refrigeration": "sensor",
    "refrigerationSetpoint": "sensor",
    "washerMode": "sensor",
    "washerOperatingState": "sensor",
    "dryerMode": "sensor",
    "dryerOperatingState": "sensor",
    "ovenMode": "sensor",
    "ovenOperatingState": "sensor",
    "ovenSetpoint": "sensor",
    "dishwasherMode": "sensor",
    "dishwasherOperatingState": "sensor",
    "robotCleanerMovement": "vacuum",
    "robotCleanerCleaningMode": "vacuum",
    "robotCleanerTurboMode": "vacuum",
    "samsungce.robotCleanerCleaningArea": "vacuum",
    "custom.completionTime": "sensor",
    "custom.runningTime": "sensor",
    "custom.runningCourse": "sensor",
    "custom.error": "sensor",
    "samsungce.kidsLock": "binary_sensor",
    "samsungce.powerCool": "switch",
    "samsungce.powerFreeze": "switch",
    # Pet Care capabilities
    "petFeederOperatingState": "sensor",
    "petFeederFoodLevel": "sensor",
    "petFeederSchedule": "sensor",
    "petFeederFeed": "switch",
    # Plant Monitor capabilities
    "soilMoisture": "sensor",
    "plantMoisture": "sensor",
    "plantHealth": "sensor",
    "plantNutrient": "sensor",
    # Solar Energy capabilities
    "powerSource": "sensor",
    "solarPanel": "sensor",
    "solarPanelPower": "sensor",
    "solarPanelEnergy": "sensor",
    "inverter": "sensor",
    "inverterStatus": "sensor",
    "inverterEfficiency": "sensor",
    "solarBatteryLevel": "sensor",
    "solarEnergyProduction": "sensor",
    # Pool/Spa Controller capabilities
    "poolController": "sensor",
    "poolHeater": "climate",
    "poolPump": "switch",
    "poolChlorine": "sensor",
    "poolPH": "sensor",
}

# Icon mapping for capabilities
CAPABILITY_ICONS = {
    "switch": "mdi:toggle-switch",
    "switchLevel": "mdi:lightbulb",
    "colorControl": "mdi:palette",
    "colorTemperature": "mdi:thermometer",
    "thermostat": "mdi:thermostat",
    "lock": "mdi:lock",
    "doorControl": "mdi:door",
    "windowShade": "mdi:window-shutter",
    "garageDoorControl": "mdi:garage",
    "fanSpeed": "mdi:fan",
    "contactSensor": "mdi:door",
    "motionSensor": "mdi:motion-sensor",
    "presenceSensor": "mdi:account",
    "waterSensor": "mdi:water",
    "smokeDetector": "mdi:smoke-detector",
    "carbonMonoxideDetector": "mdi:smoke-detector-alert",
    "temperatureMeasurement": "mdi:thermometer",
    "relativeHumidityMeasurement": "mdi:water-percent",
    "illuminanceMeasurement": "mdi:brightness-5",
    "powerMeter": "mdi:flash",
    "energyMeter": "mdi:lightning-bolt",
    "battery": "mdi:battery",
    "voltage": "mdi:sine-wave",
    # Appliance icons
    "refrigeration": "mdi:fridge",
    "refrigerationSetpoint": "mdi:fridge-outline",
    "washerMode": "mdi:washing-machine",
    "washerOperatingState": "mdi:washing-machine",
    "dryerMode": "mdi:tumble-dryer",
    "dryerOperatingState": "mdi:tumble-dryer",
    "ovenMode": "mdi:stove",
    "ovenOperatingState": "mdi:stove",
    "ovenSetpoint": "mdi:thermometer",
    "dishwasherMode": "mdi:dishwasher",
    "dishwasherOperatingState": "mdi:dishwasher",
    "robotCleanerMovement": "mdi:robot-vacuum",
    "robotCleanerCleaningMode": "mdi:robot-vacuum",
    "robotCleanerTurboMode": "mdi:fast-forward",
    "custom.completionTime": "mdi:clock-end",
    "custom.runningTime": "mdi:timer",
    "custom.runningCourse": "mdi:playlist-check",
    "custom.error": "mdi:alert-circle",
    "samsungce.kidsLock": "mdi:lock-outline",
    # Pet Care icons
    "petFeederOperatingState": "mdi:dog",
    "petFeederFoodLevel": "mdi:bowl",
    "petFeederSchedule": "mdi:clock-outline",
    "petFeederFeed": "mdi:nutrition",
    # Plant Monitor icons
    "soilMoisture": "mdi:water-percent",
    "plantMoisture": "mdi:leaf",
    "plantHealth": "mdi:sprout",
    "plantNutrient": "mdi:flask",
    # Solar Energy icons
    "powerSource": "mdi:power-plug",
    "solarPanel": "mdi:solar-panel",
    "solarPanelPower": "mdi:solar-power",
    "solarPanelEnergy": "mdi:lightning-bolt",
    "inverter": "mdi:power-cycle",
    "inverterStatus": "mdi:check-circle",
    "inverterEfficiency": "mdi:gauge",
    "solarBatteryLevel": "mdi:battery-charging",
    "solarEnergyProduction": "mdi:chart-line",
    # Pool/Spa Controller icons
    "poolController": "mdi:pool",
    "poolHeater": "mdi:water-thermometer",
    "poolPump": "mdi:pump",
    "poolChlorine": "mdi:water",
    "poolPH": "mdi:ph",
}


def get_device_capabilities(device: dict, component_id: str = "main") -> list:
    """
    Extract capabilities from a SmartThings device.

    Args:
        device: The device dictionary from SmartThings API
        component_id: The component ID to get capabilities from (default: "main")

    Returns:
        List of capability IDs
    """
    components = device.get("components", [])
    component = next((c for c in components if c.get("id") == component_id), None)
    if component:
        capabilities = component.get("capabilities", [])
        return [cap.get("id") if isinstance(cap, dict) else cap for cap in capabilities]
    return []
