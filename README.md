![maintained](https://img.shields.io/maintenance/yes/2025.svg)
[![hacs_badge](https://img.shields.io/badge/hacs-custom-orange.svg)](https://github.com/custom-components/hacs)
[![ha_version](https://img.shields.io/badge/home%20assistant-2024.10%2B-green.svg)](https://www.home-assistant.io)
![version](https://img.shields.io/badge/version-1.5.0-green.svg)
![stability](https://img.shields.io/badge/stability-beta-yellow.svg)
[![CI](https://github.com/DSorlov/smartthingsce/workflows/CI/badge.svg)](https://github.com/DSorlov/smartthingsce/actions/workflows/ci.yaml)
[![hassfest](https://github.com/DSorlov/smartthingsce/workflows/Validate%20with%20hassfest/badge.svg)](https://github.com/DSorlov/smartthingsce/actions/workflows/hassfest.yaml)
[![HACS](https://github.com/DSorlov/smartthingsce/workflows/HACS%20Validation/badge.svg)](https://github.com/DSorlov/smartthingsce/actions/workflows/hacs.yaml)
[![maintainer](https://img.shields.io/badge/maintainer-dsorlov-blue.svg)](https://github.com/DSorlov)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

SmartThings Community Edition (STCE)
====================================

A Home Assistant integration for SmartThings that provides full support for all device types, capabilities, events, and automations offered by the SmartThings platform. This integration connects to SmartThings as a hub-style integration using a Personal Access Token (PAT) and supports real-time event subscriptions via secure tunneling.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the "⋮" menu and select "Custom repositories"
4. Add `https://github.com/DSorlov/smartthingsce` as an "Integration"
5. Click the "+" button and search for "SmartThings Community Edition"
6. Install the integration
7. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/dsorlov/smartthingsce/releases)
2. Extract the `custom_components/smartthingsce` folder to your Home Assistant's `custom_components` directory
3. Restart Home Assistant

## Configuration

### Prerequisites

You need a SmartThings Personal Access Token (PAT) with the following scopes:
- `r:devices:*` - Read devices
- `x:devices:*` - Execute device commands
- `r:locations:*` - Read locations
- `r:scenes:*` - Read scenes
- `x:scenes:*` - Execute scenes
- `r:schedules` - Read schedules (optional)

### Creating a Personal Access Token

1. Go to [SmartThings Personal Access Tokens](https://account.smartthings.com/tokens)
2. Click "Generate new token"
3. Give it a name (e.g., "Home Assistant")
4. Select the required scopes listed above
5. Click "Generate token"
6. **Copy the token immediately** - you won't be able to see it again!

### Via UI (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "SmartThings Community Edition"
4. Enter your Personal Access Token
5. Select the location you want to connect
6. Configure webhook settings (optional but recommended for real-time updates)
7. Follow the configuration steps

## Supported Devices

The integration supports all SmartThings device types including:

### Climate & Comfort
- Air Conditioners
- Thermostats
- Fans
- Air Purifiers
- Humidifiers/Dehumidifiers

### Lighting
- Lights (Dimmable, Color, Temperature)
- Light Strips
- Bulbs

### Security & Safety
- Door/Window Sensors
- Motion Sensors
- Smoke Detectors
- CO Detectors
- Water Leak Sensors
- Security Systems

### Locks & Access
- Smart Locks
- Garage Door Openers

### Appliances & Home Care
- Refrigerators - Temperature monitoring, status, alerts
- Washing Machines - Cycle status, modes, completion time
- Dryers - Operating state, modes, completion time
- Ovens & Ranges - Temperature control, cooking modes, safety features
- Dishwasher - Cycle status, modes, completion time
- Robot Vacuum Cleaners - Movement, cleaning modes, battery status
- Air Conditioners - Temperature control, operating modes

### Entertainment
- TVs
- Speakers
- Media Players

### Energy & Power
- Smart Plugs
- Power Meters
- Energy Monitors

## Services & Actions

The integration provides services for controlling your devices:

### Device Commands
```yaml
# Turn on a device
service: smartthingsce.send_command
data:
  device_id: device123
  capability: switch
  command: "on"

# Set thermostat temperature
service: smartthingsce.send_command
data:
  device_id: thermostat123
  capability: thermostatCoolingSetpoint
  command: setCoolingSetpoint
  arguments: [22]

# Set light color
service: smartthingsce.send_command
data:
  device_id: light123
  capability: colorControl
  command: setColor
  arguments:
    hue: 50
    saturation: 75
```

### Scene Execution
```yaml
# Execute a SmartThings scene
service: smartthingsce.execute_scene
data:
  scene_id: scene123
```

### Refresh Devices
```yaml
# Refresh all devices
service: smartthingsce.refresh_devices
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 🐛 [Report a Bug](https://github.com/dsorlov/smartthingsce/issues)
- 💡 [Request a Feature](https://github.com/dsorlov/smartthingsce/issues)
- 📖 [Documentation](https://github.com/dsorlov/smartthingsce)
- 💬 [Community Discussion](https://github.com/dsorlov/smartthingsce/discussions)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Credits

Developed by [Daniel Sörlöv](https://github.com/DSorlov)

Built with ❤️ for the Home Assistant community.
