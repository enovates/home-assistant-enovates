# Enovates Home Assistant Integration

This integration for Home Assistant enables communication between Enovates EVSEs, to allow monitoring and optionally control of the maximum charge current.

**Beware: The EVSE's Modbus communication must be enabled, this cannot be done via this integration.**
The relevant setting may be called "EMS mode", and should be switchable between "Off", "Monitoring Only" and "Full Control".
It must be enabled by the Installer or via OCPP. There is currently no switch for it in the end user app.

Supported devices are dictated by the underlying communication library [enovates-modbus](https://github.com/enovates/enovates-modbus):

- [ENO one](https://www.enovates.com/products/singlewallbox/), firmware version 2.13 or later.

## Integration Documentation

This section of the docs is geared towards end users of this integration, and is meant to serve as a pre-cursor to the required documentation to merge the integration into Home Assistant proper.

### Installation

Assuming you have [HACS](https://www.hacs.xyz/) installed:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=enovates&repository=home-assistant-enovates)

You may have to add the repository first manually via "Custom repositories".

Once you have installed the integration and restarted your Home Assistant, use the normal "Add Integration" flow (look for "Enovates"), or click this button:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=enovates)

### Removal

No special steps are needed. Just remove the device as any other. Optionally also uninstall the integration via HACS.

### Configuration

No automatic discovery is supported at the moment due to lack of support for this in the device firmware.

This means you need to have the IP address of your device (and Modbus TCP port, if it was changed from the default). Using a statically assigned IP address is recommended. You can do this in most routers, or ask your installer to configure your device with a static IP.

If you have a device with two charge ports (excluding a schuko socket), enable the "dual port" toggle.

You can only enable EMS Control mode if that mode is also enabled on the device, but you are not required to enable this configuration option in that case.
If disabled, the integration will only allow monitoring of the device. If enabled, you will be able to set an EMS power limit.

### Use-cases

The primary use-case for this integration is the monitoring of your EVSE, so you can keep an eye on the charging status of your car.

With the energy data, you can keep track of your car's consumption in the Energy dashboard.
The power data can be used to monitor instantaneous and thus peak electricity usage, which may be a cost factor in your area.

A more advanced use-case is (H)EMS ((Home) Energy Management) control via the "EMS Limit" number entity.
This will allow you to vary the charging current offered to your car to optimize the self-use of generated power, minimize peak grid load, priority home battery storage over car charging (or the inverse), and many more.

Note that the car determines how fast the charging actually proceeds. The EVSE can only communicate the maximum limit.

### Data Provided

This integration provides access to the following information from the device:

- Modbus API version (major.minor)
- State
  - nr of phases (int)
  - max amp per phase (A)
  - ocpp state (bool)
  - load shedding state (bool)
  - lock state (enum)
  - contactor state (bool)
  - led color (enum)
- Measurements
  - current on L1, L2, L3 (mA)
  - voltage on L1, L2, L3 (V)
  - charge active power total, L1, L2, L3 (W)
  - installation current L1, L2, L3 (mA)
  - active energy import total (Wh)
- Current Offered (mA)
- Mode 3 Details
  - state (enum and str)
  - pwm (in promille and mA)
  - pp (max cable current, if socketed)
  - cp + and - (volts)
- Diagnostics
  - manufacturer (str)
  - vendor id (str)
  - serial nr (str)
  - model id (str)
  - firmware version (str)

If EMS Control mode is disabled:

- EMS current limit (mA) Read only. Writes may be accepted but are ignored
- Transaction token (str) NOT available. Reading will error.

If EMS Control mode is enabled:

- EMS current limit (mA) Read / Write.
- Transaction token (str)

The recommended sensors for active power management are the "Current Offered", "EMS Current Limit" and the sensors under Measurements. For cars that support digital communication (ISO 15118), the values under Mode 3 Details could give a false impression of the EVSE/car behavior.

For dual-port devices, only the relevant sensors are duplicated per port.

Installation current measurements are only valid if the device was installed with an installation monitor (also called a load shedding device or load balancer).
It is currently not possible to provide this information from Home Assistant to the device.

A subset of these entities are show in the default dashboard. The rest is accessible via the device page and can be manually added to relevant dashboards.

### Data Updates

The integration polls the device via Modbus TCP (through the [enovates-modbus](https://github.com/enovates/enovates-modbus) library) asynchronously. To limit the load on the device, not all entities have the same polling rates. See the section above for the exact list:

+ API version: Daily
+ Diagnostics: Daily
+ Transaction Token: Every minute (assuming EMS Control mode is enabled)
+ Mode 3 related entities: Every 10 seconds
+ Others (State, Measurements, EMS Limit and Current Offered): Every second

## Troubleshooting

If you are having trouble adding your device:

1. Make sure the device is fully done booting. It can take a few minutes before the Modbus server is started.
2. Make sure the device has a valid network connection and its IP address is correct. Check your router status.
3. Make sure the device has its EMS/Modbus communication enabled. See at the top of this readme.

If the device goes unavailable and does not come back after a while:

1. Check if the device is powered (circuit breaker is not tripped).
2. Check if the device IP address changed (in your router).

If the device goes unavailable for brief periods:

1. Make sure the network connection from your Home Assistant to the device is stable.

## Integration Development

This repository is based on the [HACS Integration Blueprint](https://github.com/ludeeus/integration_blueprint).

Contributions may be accepted under the terms of the [Apache License, Version 2.0](./LICENSE.md).

[Make sure to read the HA developer documentation.](https://developers.home-assistant.io/docs/development_index/)

After cloning the repo, set up your working environment, and make sure to install [pre-commit](http://pre-commit.com/)'s hooks if your global git configuration lacks them:

```shell
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
pre-commit install
```

If you are also developing the `enovates-modbus` library, you can force the use of a local copy of that library with `uv pip install -e '../enovates-modbus'`, assuming they are cloned side by side.

Run `hass --config config --debug --skip-pip-packages enovates-modbus` in the repo root to run a test instance of Home Assistant for development.

All pre-commit checks should pass before you push your code.
Merge requests with violations are likely to be ignored until they are fully compliant.

### Testing

Run tests via `pytest`.

This repo uses [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) to enable easy testing custom components with HA related fixtures.

## Attribution

Thanks to Christof Mahieu (@maju101) for providing the initial implementation during his time at Enovates.

The library and this integration repo was created by Dries Kennes (@dries007) while working for @qteal.
