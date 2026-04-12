# hhc-n818op-plugins

Python plugin package for IoT devices used by **HHC-N818OP Standalone**.

This repository contains device adapters that extend the standalone daemon through Python entry points. At the moment, the project provides plugins for:

- **Athom Smart Home** devices over HTTP
- **Meross** devices over MQTT (via `meross-iot`)

## Project Status

- Python package metadata is defined in `pyproject.toml`.
- Plugin discovery is configured through the `daemon_hhc_n818op.plugins` entry-point group.
- The `tests/` folder currently contains only package scaffolding.

## Requirements

- Python `>=3.10,<3.14`
- `uv` (recommended for dependency and virtualenv management)
- Access to the companion project `hhc-n818op-standalone` (declared as a direct dependency)

## Installation

### 1) Clone the repository

```bash
git clone <your-fork-or-origin-url>
cd hhc-n818op-plugins
```

### 2) Install dependencies

```bash
uv sync
```

If you prefer editable installation with pip:

```bash
python -m pip install -e .
```

## Quick Start

### Install from PyPI (when available)

```bash
pip install hhc-n818op-plugins
```

### Install from source (development mode)

```bash
git clone <your-fork-or-origin-url>
cd hhc-n818op-plugins
pip install -e .
```

### Verify installation

```bash
python -c "from daemon_hhc_n818op.plugins.athom import PluginAthomSmartHome; print('✓ Athom plugin loaded')"
python -c "from daemon_hhc_n818op.plugins.meross import PluginMeross; print('✓ Meross plugin loaded')"
```

## Development Workflow

Common targets are available in `Makefile`:

- `make dev` - install and validate toolchain versions
- `make style` - run formatting (`isort`, `black`)
- `make checks` - run static analysis (`ruff`, `flake8`, `pylint`, `mypy`, `bandit`)
- `make tests` - run unit-test selection (`not integration_tests`)

You can also run commands directly with `uv`:

```bash
uv run pytest -v
uv run ruff check daemon_hhc_n818op tests
uv run black --check daemon_hhc_n818op tests
```

## Plugin Layout

```text
daemon_hhc_n818op/
  plugins/
    athom/
      athom_smart_client_home_http.py
    meross/
      meross_client_cloud_mqtt.py
```

### Athom plugin

- Main implementation: `daemon_hhc_n818op/plugins/athom/athom_smart_client_home_http.py`
- Class: `PluginAthomSmartHome`
- Behavior:
  - Checks relay status over HTTP
  - Toggles relay state
  - Disables itself when host/network or payload errors are detected

### Meross plugin

- Main implementation: `daemon_hhc_n818op/plugins/meross/meross_client_cloud_mqtt.py`
- Class: `PluginMeross`
- Behavior:
  - Authenticates through Meross cloud credentials/profile
  - Initializes `MerossManager`
  - Discovers devices and controls switch state
  - Persists profile/registry credential artifacts in the plugin folder

## Configuration Notes

Meross plugin uses JSON files located under `daemon_hhc_n818op/plugins/meross/`, including:

- `meross_profile.json`
- `meross_registry.json`
- `meross_cloud_credentials.json`

Keep these files sanitized and avoid committing real secrets.

## Packaging

- Build backend: `setuptools.build_meta`
- License: `GPL-3.0-only`
- Source package target includes `daemon_hhc_n818op` and excludes test files

## Contributing

1. Create a feature branch.
2. Run formatting and checks.
3. Run tests.
4. Open a pull request with a clear change description.

## License

This project is distributed under the terms of the **GPL-3.0-only** license. See `LICENSE`.

