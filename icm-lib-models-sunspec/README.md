# icm-lib-models-sunspec

SunSpec information models as pydantic classes: `icm.models.sunspec`. The classes are generated from SunSpec model definitions (`SUNSPEC_MODELS` names the SunSpec `models` repository) by the
package's own `generate_models.py`, so the standard's definitions stay the authority and the package can be regenerated
when the standard moves. Each profile or model class knows its fields, their types and units, and the builders in
`profile_builders` assemble valid instances from plain values.

Part of the `icm-utils` repository; depends on pydantic only.
