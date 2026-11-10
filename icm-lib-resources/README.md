# icm-lib-resources

Resources for interoperability agents: the models a resource is declared with, the clients that read and write one,
and the codecs that turn a transform's output into a wire payload.

- `icm.resources.resource`: `Resource`, `CanonicalResource` and `AliasedResource` (pydantic); `ResourceData`, which
  subscribes to a resource's publications and hands each one over transformed and encoded; `ResourceWriter`, which
  tracks what a target device is known to hold so a writer sends only what changed.
- `icm.resources.codecs`: `encoder_for` and `decoder_for` a codec declaration (`json`, or `protobuf` with an OpenFMB
  message name and edition).
- `icm.resources.openfmb.bus`: the headers OpenFMB messages travel with on the platform bus (content type, protobuf
  message name, origin, remote).
- `icm.resources.openfmb.descriptors`: the OpenFMB protobuf descriptors of each edition (1.0, 2.0, 2.1, 2.2), each in
  its own descriptor pool, so participants on different releases can be served from one process.

```python
from icm.resources import ResourceData

resource = ResourceData.lookup(agent, 'site/inverter/ess')     # resolved through the presentation service
resource.subscribe(lambda peer, sender, bus, topic, headers, message: ...)
```

## Extras

- `openfmb`: the protobuf runtime, for encoding and decoding OpenFMB profiles.
- `volttron`: `volttron-core`, for `ResourceData` and `ResourceWriter`, which speak VIP pubsub and RPC. The models,
  codecs and headers need no platform.

Depends on `icm-lib-transforms` and pydantic.
