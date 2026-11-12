# HTTP registrar documentation

This project accepts AllStarLink-compatible HTTP registration requests, verifies
node credentials, and publishes successful registrations to Kafka.

```text
Repeater --HTTPS--> trusted reverse proxy --> HTTP registrar
                                            |-- file or Central Auth credential lookup
                                            |-- verify password
                                            +-- publish accepted update --> Kafka
```

The reverse proxy terminates public TLS and forwards requests to the HTTP service.
Forwarded client addresses are trusted only when explicitly configured. The
registrar can read a local CSV or retrieve the password from Central Auth over
verified gRPC; it verifies the request itself. Kafka publication must succeed
before the client receives the success response. The HTTP status and body follow
the AllStarLink client contract, including a compatible response for ordinary
credential rejection.

Start with the repository [README](../README.md) for a local container example and
configuration summary. See [authentication](authentication.md) for credential
providers and request limits, [HTTP compatibility](http-compatibility.md) for the
client contract, and [glossary](glossary.md) for domain terms.
