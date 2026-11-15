"""Protobuf encoding of OpenFMB profiles, for every edition the project knows.

``proto`` names are the fully qualified protobuf message, ``<module>.<Message>`` (``essmodule.ESSReadingProfile``),
as the format declaration's ``proto`` entry gives them; ``edition`` (``'2.1'``, ``'2.2'``; default the newest) is the
OpenFMB release the peer speaks, from the alias declaration. Each edition's descriptors live in their own pool (see
:mod:`icm.resources.openfmb.descriptors`), so a 2.1 participant and a 2.2 participant can be served from one
process; nothing on the wire names the edition, so the alias has to.

The dicts encoded here follow protobuf's JSON mapping, exactly what the transforms produce and the pydantic models
validate: proto field names, enumerations by name, wrapper types collapsed to scalars.

Requires the ``protobuf`` runtime (the service's ``openfmb`` extra).
"""
from __future__ import annotations

from typing import Any

from ..openfmb import descriptors

editions = descriptors.editions
latest_edition = descriptors.latest_edition


def message_class(proto: str, edition: str | None = None):
    """The generated protobuf class for ``proto`` in ``edition``; ``LookupError`` when either is unknown."""
    return descriptors.message_class(proto, edition)


_WRAPPERS = {'google.protobuf.BoolValue': 'bool', 'google.protobuf.Int32Value': 'int', 'google.protobuf.Int64Value': 'int',
             'google.protobuf.UInt32Value': 'int', 'google.protobuf.UInt64Value': 'int', 'google.protobuf.FloatValue': 'float',
             'google.protobuf.DoubleValue': 'float', 'google.protobuf.StringValue': 'str'}
_TRUE, _FALSE = {'true', '1', 'yes', 'on', 'enabled'}, {'false', '0', 'no', 'off', 'disabled'}


def _kind(field) -> str | None:
    """'bool', 'int', 'float', 'str', 'message' or None (enums, bytes, maps: left as they are)."""
    from google.protobuf.descriptor import FieldDescriptor as F
    if field.type == F.TYPE_MESSAGE:
        return _WRAPPERS.get(field.message_type.full_name, 'message')
    if field.type == F.TYPE_BOOL:
        return 'bool'
    if field.type in (F.TYPE_INT32, F.TYPE_INT64, F.TYPE_UINT32, F.TYPE_UINT64, F.TYPE_SINT32, F.TYPE_SINT64,
                      F.TYPE_FIXED32, F.TYPE_FIXED64, F.TYPE_SFIXED32, F.TYPE_SFIXED64):
        return 'int'
    if field.type in (F.TYPE_FLOAT, F.TYPE_DOUBLE):
        return 'float'
    if field.type == F.TYPE_STRING:
        return 'str'
    return None


def _scalar(value, kind: str):
    """A transform's scalar brought to the field's JSON type: a SunSpec enum 0/1 or a DNP3 'true' string into a bool
    field, a 1.0 into an integer field, a numeric string into a number. Anything else is left for ParseDict to judge."""
    if value is None or isinstance(value, (dict, list)):
        return value
    if kind == 'bool':
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)) and value in (0, 1):
            return bool(value)
        if isinstance(value, str) and value.strip().lower() in _TRUE | _FALSE:
            return value.strip().lower() in _TRUE
        return value
    if kind == 'int':
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, str):
            try:
                return int(value) if value.strip().lstrip('-').isdigit() else int(float(value)) if float(value).is_integer() else value
            except ValueError:
                return value
        return value
    if kind == 'float':
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return value
        return value
    if kind == 'str':
        return value if isinstance(value, str) else str(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else value
    return value


def coerce(payload, descriptor):
    """``payload`` with every scalar brought to the type of the field it lands in, recursively, by ``descriptor``
    (a message descriptor). Unknown field names are kept as they are, so ParseDict still reports them."""
    if not isinstance(payload, dict):
        return payload
    out = {}
    for name, value in payload.items():
        field = descriptor.fields_by_name.get(name) or descriptor.fields_by_camelcase_name.get(name)
        if field is None:
            out[name] = value
            continue
        kind = _kind(field)
        repeated = _repeated(field)
        is_map = kind == 'message' and bool(getattr(field.message_type.GetOptions(), 'map_entry', False))
        if is_map or kind is None:
            out[name] = value
        elif repeated and isinstance(value, list):
            out[name] = [coerce(item, field.message_type) if kind == 'message' else _scalar(item, kind) for item in value]
        elif kind == 'message':
            out[name] = coerce(value, field.message_type)
        else:
            out[name] = _scalar(value, kind)
    return out


def _repeated(field) -> bool:
    is_repeated = getattr(field, 'is_repeated', None)       # protobuf >= 5 (upb) exposes it as a property
    if is_repeated is not None:
        return bool(is_repeated)
    from google.protobuf.descriptor import FieldDescriptor as F
    return field.label == F.LABEL_REPEATED


def encode(proto: str, payload: dict, edition: str | None = None) -> bytes:
    """Serialize a protobuf-JSON shaped dict as the ``proto`` message of ``edition``. Scalars are brought to their
    fields' types first (see :func:`coerce`); unknown fields are an error."""
    from google.protobuf import json_format
    cls = message_class(proto, edition)
    return json_format.ParseDict(coerce(payload, cls.DESCRIPTOR), cls()).SerializeToString()


def decode(proto: str, data: bytes, edition: str | None = None) -> dict:
    """Parse ``proto`` message bytes of ``edition`` into the protobuf-JSON shaped dict the transforms and models use."""
    from google.protobuf import json_format
    message = message_class(proto, edition).FromString(bytes(data))
    return json_format.MessageToDict(message, preserving_proto_field_name=True)


def validate(proto: str, payload: dict, edition: str | None = None) -> Any:
    """Validate a dict against the ``proto`` message of ``edition`` without serializing; returns the message."""
    from google.protobuf import json_format
    cls = message_class(proto, edition)
    return json_format.ParseDict(coerce(payload, cls.DESCRIPTOR), cls())
