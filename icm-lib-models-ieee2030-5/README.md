# icm-lib-models-ieee2030-5

IEEE 2030.5 (SEP2) models as pydantic classes: `icm.models.ieee2030_5`. The classes are generated from the IEEE 2030.5 XSD (`IEEE2030_5_SCHEMAS` names the schema directory) by the
package's own `generate_models.py`, so the standard's definitions stay the authority and the package can be regenerated
when the standard moves. Each profile or model class knows its fields, their types and units, and the builders in
`profile_builders` assemble valid instances from plain values.

Part of the `icm-utils` repository; depends on pydantic only.
