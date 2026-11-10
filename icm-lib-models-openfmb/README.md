# icm-lib-models-openfmb

OpenFMB profile models as pydantic classes: `icm.models.openfmb`. The classes are generated from the OpenFMB `psm-protobuf-python` bindings (`OPENFMB_PSM_PROTOBUF_PYTHON` names a clone) by the
package's own `generate_models.py`, so the standard's definitions stay the authority and the package can be regenerated
when the standard moves. Each profile or model class knows its fields, their types and units, and the builders in
`profile_builders` assemble valid instances from plain values.

Part of the `icm-utils` repository; depends on pydantic only.
