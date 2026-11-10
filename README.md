# icm-utils

Libraries shared by the interoperability control modules. Each directory is its own Poetry project and its own
distribution on PyPI:

| Directory           | Distribution        | Import package  | What it holds                                                   |
|---------------------|---------------------|-----------------|-----------------------------------------------------------------|
| `icm-lib-transform` | `icm-lib-transform` | `icm_transform` | transform functions, the pattern grammar, compiled pipelines     |
| `icm-lib-resource`  | `icm-lib-resource`  | `icm_resource`  | resource models, resource clients, wire codecs, OpenFMB headers |

`icm-lib-resource` depends on `icm-lib-transform`. Nothing here depends on VOLTTRON except the resource clients, which
are an extra: `pip install icm-lib-resource[volttron]`.

## Working on both at once

Each project is built, tested and published on its own:

```sh
cd icm-lib-transform && poetry install && poetry run pytest
cd icm-lib-resource && poetry install --all-extras && poetry run pytest
```

To develop against the sibling instead of the released version, install it editable into the same environment first:

```sh
pip install -e icm-lib-transform -e "icm-lib-resource[openfmb,volttron]"
```

## Publishing

Tag releases per project: `icm-lib-transform-v0.1.0`, `icm-lib-resource-v0.1.0`. Build and publish from the
project's directory with `poetry build` and `poetry publish`.
