# Enovates Home Assistant Integration

This repo enables communication between Enovates EVSEs and Home Assistant, to allow monitoring and optionally control.

Beware: The EVSE's Modbus communication must be enabled, this cannot be done via this integration.
The relevant setting may be called "EMS mode", and should be switchable between "Off", "Monitoring Only" and "Full Control".
It must be enabled by the Installer or via OCPP. There is currently no switch for it in the end user app.

This repository is based on the [HACS Integration Blueprint](https://github.com/ludeeus/integration_blueprint).

Until this repo is added to the default list, you will have to add the repo to your HACS installation manually, or by using this button:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=enovates&repository=home-assistant-enovates)

Once you have installed the integration and restarted your Home Assistant, use the normal "Add Integration" flow (look for "Enovates"), or click this button:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=enovates)

Supported devices are dictated by the underlying communication library [enovates-modbus](https://github.com/enovates/enovates-modbus):

- [ENO one](https://www.enovates.com/products/singlewallbox/), firmware version 2.13 or later.

## Development

Contributions may be accepted under the terms of the [Apache License, Version 2.0](./LICENSE.md).

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

## Attribution

Thanks to Christof Mahieu (@maju101) for providing the initial implementation during his time at Enovates.

The library and this integration repo was created by Dries Kennes (@dries007) while working for @qteal.
