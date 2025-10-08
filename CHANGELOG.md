# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] (2025-10-06)

#### New Pet Care Platform
- Pet feeder monitoring and control platform for automated pet care systems
- Support for SmartThings capabilities: `petFeederOperatingState`, `petFeederFoodLevel`, `petFeederSchedule`, `petFeederFeed`
- **Pet Feeder Operating State** sensor with enum device class (idle, feeding, scheduled, error, empty)
- **Food Level Monitor** sensor tracking remaining food as percentage with low-level alerts
- **Feeding Schedule** sensor displaying next scheduled feeding time and interval tracking
- **Manual Feed Control** switch for on-demand feeding with portion control
- Automatic device type detection for pet feeders and feeding systems
- Dynamic icons based on operational status and food levels
- Integration ready for smart pet care automation and notifications

#### New Plant Monitor Platform
- Plant health monitoring platform for smart gardening and agricultural systems
- Support for SmartThings capabilities: `soilMoisture`, `plantMoisture`, `plantHealth`, `plantNutrient`, `temperatureMeasurement`, `illuminanceMeasurement`
- **Soil Moisture** sensor with percentage measurements and dry/optimal/wet status
- **Plant Moisture** sensor for direct plant hydration monitoring
- **Plant Health Status** sensor with descriptive states (excellent, good, fair, poor, critical)
- **Plant Nutrient Level** sensor tracking fertilizer and nutrient requirements
- **Plant Temperature** monitoring with proper temperature device class integration
- **Light Level** sensor for photosynthesis and growth optimization

#### New Solar Energy Platform
- Solar panel and renewable energy monitoring platform for residential and commercial installations
- Support for SmartThings capabilities: `powerSource`, `solarPanel`, `inverter`, `batteryLevel`, `energyMeter`
- **Power Source Status** sensor tracking energy source (solar, battery, grid, generator)
- **Solar Panel Power** sensor monitoring real-time power generation in watts
- **Solar Panel Energy** sensor tracking cumulative energy generation in kWh
- **Inverter Status** sensor monitoring inverter operational state and health
- **Inverter Efficiency** sensor displaying conversion efficiency as percentage
- **Solar Battery Level** sensor with charge status and dynamic battery icons
- **Energy Production** sensor tracking total renewable energy production

#### New Pool/Spa Controller Platform
- Pool and spa management platform for residential and commercial aquatic systems
- Support for SmartThings capabilities: `poolController`, `poolHeater`, `poolPump`, `poolChlorine`, `poolPH`
- **Pool Controller Status** sensor tracking system status (normal, service, timeout, priming, freeze, error)
- **Pool Heater Thermostat** climate entity with heating control and temperature setpoints
- **Pool Pump Control** switch for pump operation with speed monitoring
- **Pool Temperature** sensor for water temperature monitoring with proper device class
- **Chlorine Level** sensor monitoring chemical balance in parts per million (ppm)
- **pH Level** sensor tracking water acidity/alkalinity for safety and comfort

## [1.4.0] (2025-10-04)

#### New Air Quality Monitoring Platform
- Air quality sensor platform for environmental monitoring devices
- Support for SmartThings capabilities: `airQualityDetector`, `dustSensor`, `tvocMeasurement`, `formaldehydeMeasurement`, `airQualityHealthConcern`
- **Air Quality Index (AQI)** sensor with descriptive state attributes (Good, Moderate, Unhealthy, etc.)
- **Particulate Matter (PM2.5/PM10)** sensors with proper device classes and units
- **TVOC (Total Volatile Organic Compounds)** measurement in μg/m³
- **Formaldehyde** detection in parts per million (ppm)
- **Health Concern** level reporting with dynamic icons based on air quality

#### New Valve Control Platform
- Valve platform for water management, irrigation, and gas control systems
- Support for SmartThings capability: `valve`
- Automatic valve type detection (water, gas) based on device naming and type
- Binary valve control (open/close) with transitional state tracking
- Position reporting and status attributes
- Proper device class assignment and icons for different valve types
- Integration ready for irrigation systems, water shutoff valves, and gas controls

#### Enhanced Energy Monitor Platform
- Dedicated energy monitoring platform separate from basic power sensors
- Support for SmartThings capabilities: `energyMeter`, `powerMeter`, `voltageMeasurement`, `currentMeasurement`
- **Energy Meter**: Cumulative energy consumption tracking in kWh with total-increasing state class
- **Power Meter**: Real-time power consumption monitoring in watts
- **Voltage Sensor**: Electrical voltage measurement and monitoring
- **Current Sensor**: Electrical current measurement in amperes

#### New Camera Integration Platform
- Camera platform for security cameras, doorbells, and surveillance devices
- Support for SmartThings capabilities: `videoStream`, `imageCapture`, `videoCapture`
- Still image capture with automatic refresh and caching
- Video streaming support for compatible cameras
- Motion detection integration with binary sensor capabilities
- Camera power control (on/off) through switch capability
- Motion detection enable/disable controls where supported
- Encrypted image URL handling for secure camera feeds
- Real-time status attributes for streaming and recording states

## [1.3.0] (2025-10-03)

### Added - High-Priority Platform Support

#### New Media Player Platform
- Complete media player platform for TVs, speakers, and audio/video devices
- Support for SmartThings capabilities: `mediaPlayback`, `audioVolume`, `tvChannel`, `mediaInputSource`
- Full playback control (play, pause, stop, next/previous track)
- Volume control with mute functionality and step adjustments
- Source selection for input switching on TVs and receivers
- Channel control for TV devices
- Power on/off control through switch capability
- Real-time state synchronization with media device status

#### New Siren Platform
- Siren platform for security alarms and notification devices
- Support for SmartThings capabilities: `alarm`, `tone`, `chime`
- **Alarm Siren**: Full security alarm with siren/strobe modes
- **Tone Siren**: Configurable tone devices with multiple sound options
- **Chime Siren**: Doorbell and notification chimes
- Tone selection support for devices with multiple available sounds
- Proper siren state tracking and control

#### New Traditional Thermostat Platform
- Dedicated thermostat platform for HVAC systems (separate from refrigerator climate control)
- Support for SmartThings capability: `thermostatMode` with full HVAC functionality
- Complete HVAC mode support (heat, cool, auto, off, fan-only, dry)
- Dual setpoint control for heating and cooling temperatures
- Fan mode control (auto, on, circulate, follow schedule)
- HVAC action reporting (heating, cooling, idle, fan-only)
- Temperature range validation and step control
- Real-time operating state monitoring

#### New Button/Scene Controller Platform  
- Button platform for physical switches and scene controllers
- Support for SmartThings capabilities: `button`, `holdableButton`
- Multi-button device support with automatic button count detection
- Individual button entities for complex scene controllers
- Button press event tracking and state attributes
- Support for both momentary buttons and holdable scene controllers
- Proper device identification and naming for single vs multi-button devices

## [1.2.0] (2025-10-02)

### Added - Cover and Fan Platform Support

#### New Cover Platform
- Complete cover platform for window shades, blinds, and door controls
- Support for SmartThings capabilities: `windowShade`, `doorControl`, `garageDoorControl`
- Full position control for devices with `windowShadeLevel` capability
- Open, close, stop, and set position functionality
- Proper device class mapping (shade, door, garage)
- Real-time state synchronization with SmartThings devices

#### New Fan Platform  
- Fan platform for ceiling fans and ventilation devices
- Support for SmartThings `fanSpeed` capability with multi-speed control
- Percentage-based speed control with automatic conversion from SmartThings speed levels
- Simple on/off control for basic fan devices using `switch` capability
- Intelligent device type detection for switch-based fans
- Speed range mapping for different SmartThings fan implementations

## [1.1.1] (2025-10-02)

### Changed
- Made `pyngrok` a required dependency to ensure real-time webhook functionality
- Improved user experience by automatically installing webhook dependencies

## [1.1.0] (2025-10-01)

#### New Vacuum Platform
- Complete vacuum platform for robot cleaners using Home Assistant's native vacuum entity
- Full vacuum controls (start, stop, pause, return to base)
- Battery level monitoring
- State tracking (cleaning, docked, returning, idle, paused, error)
- Cleaning mode and turbo mode support
- Integration with Home Assistant vacuum services and UI

#### Extended Sensor Platform
- Added appliance-specific sensors to existing sensor platform
- Temperature setpoints for refrigerators and ovens
- Operating state sensors for washers, dryers, ovens, dishwashers
- Mode sensors for all appliances
- Time-based sensors (running time, completion time)
- Program/course tracking
- Error reporting sensors

#### Refrigerators & Freezers
- Refrigeration status sensor
- Temperature setpoint monitoring
- Kids lock status
- Error detection

#### Washing Machines
- Operating state sensor (idle, running, paused, complete)
- Wash mode sensor
- Running time tracking
- Completion time estimation
- Running course/program display
- Binary sensor for running status
- Kids lock monitoring
- Error detection and alerts

#### Dryers (Tumble Dryers)
- Operating state sensor
- Dryer mode sensor
- Running time tracking
- Completion time estimation
- Running course/program display
- Binary sensor for running status
- Kids lock monitoring
- Error detection and alerts

#### Ovens & Ranges
- Operating state sensor
- Oven mode sensor (bake, broil, convection, etc.)
- Temperature setpoint monitoring
- Meat probe temperature tracking (if equipped)
- Lamp status
- Binary sensor for running status
- Kids lock monitoring
- Error detection and alerts

#### Dishwashers
- Operating state sensor
- Dishwasher mode sensor
- Running time tracking
- Completion time estimation
- Running course/program display
- Binary sensor for running status
- Kids lock monitoring
- Error detection and alerts

#### Robot Vacuum Cleaners
- Movement sensor (idle, cleaning, charging, homing)
- Cleaning mode sensor (auto, spot, edge, etc.)
- Turbo mode status
- Cleaning area tracking (if supported)

#### SmartThings Capabilities Added
- `refrigeration` - Refrigerator status
- `refrigerationSetpoint` - Fridge temperature control
- `washerMode` - Washing machine mode selection
- `washerOperatingState` - Washer state monitoring
- `dryerMode` - Dryer mode selection
- `dryerOperatingState` - Dryer state monitoring
- `ovenMode` - Oven mode selection
- `ovenOperatingState` - Oven state monitoring
- `ovenSetpoint` - Oven temperature control
- `dishwasherMode` - Dishwasher mode selection
- `dishwasherOperatingState` - Dishwasher state monitoring
- `robotCleanerMovement` - Robot vacuum movement
- `robotCleanerCleaningMode` - Robot vacuum cleaning mode
- `robotCleanerTurboMode` - Robot vacuum turbo mode
- `samsungce.robotCleanerCleaningArea` - Robot vacuum area
- `samsungce.kidsLock` - Child safety lock
- `samsungce.lamp` - Appliance light control
- `samsungce.meatProbe` - Oven meat probe
- `custom.completionTime` - Cycle completion time
- `custom.runningTime` - Current cycle running time
- `custom.runningCourse` - Active program/course
- `custom.error` - Error detection and reporting
- `custom.remoteControlStatus` - Remote control status

## [1.0.0] (2025-10-01)

### Initial Release

Welcome to SmartThings Community Edition! This is the first public release of a complete Home Assistant integration for SmartThings.

### Added
- Hub-style integration with Personal Access Token authentication
- Support for all major SmartThings device types and capabilities
- Real-time event subscriptions via pyngrok webhook
- GUI-based configuration flow
- Device discovery and automatic entity creation
- Location and room organization
- Scene execution support
- Automatic webhook tunnel generation with unique identifiers
- Full async/await implementation for non-blocking operations
- Proper Home Assistant device registry integration
- Support for device attributes and states
- Event handling for device state changes
- Configuration options flow for webhook settings
- System health integration

### Services
- `smartthingsce.send_command` - Send commands to devices
- `smartthingsce.execute_scene` - Execute SmartThings scenes
- `smartthingsce.refresh_devices` - Manually refresh device states

### Features
- Non-blocking async operations for all API calls
- Proper error handling and logging
- Rate limiting awareness
- Webhook subscription management
- Automatic reconnection on failures
- Device state caching
- Efficient update coordination
- Support for device-specific icons
- Translation key support for localization

[keep-a-changelog]: http://keepachangelog.com/en/1.0.0/
[1.0.0]: https://github.com/dsorlov/smartthingsce
