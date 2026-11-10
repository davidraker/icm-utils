# icm-lib-models-ieee1815-2

IEEE 1815.2 (DNP3) point models as pydantic classes: `icm.models.ieee1815_2`. The classes are generated from the IEEE 1815.2 point tables carried in the package by the
package's own `generate_models.py`, so the standard's definitions stay the authority and the package can be regenerated
when the standard moves. Each profile or model class knows its fields, their types and units, and the builders in
`profile_builders` assemble valid instances from plain values.

Part of the `icm-utils` repository; depends on pydantic only.
