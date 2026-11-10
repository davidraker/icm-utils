# icm-utils

Libraries shared by the interoperability control modules. Each directory is its own Poetry project and its own
distribution on PyPI; all of them install into the `icm` namespace package, the way VOLTTRON's packages share
`volttron`:

| Directory                   | Distribution                | Import package          | What it holds                                                  |
|-----------------------------|-----------------------------|-------------------------|----------------------------------------------------------------|
| `icm-lib-transforms`        | `icm-lib-transforms`        | `icm.transforms`        | transform functions, the pattern grammar, value transforms      |
| `icm-lib-resources`         | `icm-lib-resources`         | `icm.resources`         | resource models, resource clients, wire codecs, OpenFMB headers |
| `icm-lib-models-sunspec`    | `icm-lib-models-sunspec`    | `icm.models.sunspec`    | SunSpec information models as pydantic classes                 |
| `icm-lib-models-ieee1815-2` | `icm-lib-models-ieee1815-2` | `icm.models.ieee1815_2` | IEEE 1815.2 (DNP3) point models                                |
| `icm-lib-models-ieee2030-5` | `icm-lib-models-ieee2030-5` | `icm.models.ieee2030_5` | IEEE 2030.5 (SEP2) models                                      |
| `icm-lib-models-openfmb`    | `icm-lib-models-openfmb`    | `icm.models.openfmb`    | OpenFMB profile models                                         |

`icm-lib-resources` depends on `icm-lib-transforms`; the model packages depend on pydantic only and on nothing else
here. Nothing depends on VOLTTRON except the resource clients, which are an extra: `pip install icm-lib-resources[volttron]`.

`icm` and `icm.models` are namespace packages (PEP 420): no project ships an `icm/__init__.py` or an
`icm/models/__init__.py`, and none ever may, or every other member of the namespace stops importing.

## Working on several at once

Each project is built, tested and published on its own:

```sh
cd icm-lib-transforms && poetry install && poetry run pytest
cd icm-lib-resources && poetry install --all-extras && poetry run pytest
```

To develop against the siblings instead of released versions, install them editable into one environment first:

```sh
pip install -e icm-lib-transforms -e "icm-lib-resources[openfmb,volttron]" \
            -e icm-lib-models-sunspec -e icm-lib-models-ieee1815-2 -e icm-lib-models-ieee2030-5 -e icm-lib-models-openfmb
```

Editable installs of several members merge into one `icm` namespace at import time.

## Publishing

Tag releases per project: `icm-lib-transforms-v0.1.0`, `icm-lib-models-sunspec-v0.1.0`. Build and publish from the
project's directory with `poetry build` and `poetry publish`.
