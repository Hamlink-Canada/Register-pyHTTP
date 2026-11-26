# HTTP repeater registration

This service accepts HTTP registrations from AllStarLink-compatible nodes. It checks
each node's password and publishes accepted registrations to Kafka, where the DNS
directory can pick them up.

You need Docker, a reachable Kafka broker, node credentials, and an HTTPS reverse
proxy for public access. The container serves HTTP on port 5000. The AllStarLink
client connects over HTTPS, so TLS must terminate at your proxy.

See the [HTTP registrar documentation](docs/README.md) for protocol and authentication details.
The cross-project [operator guide](https://hamlink-canada.github.io/apt-rpt-docs/projects/http/)
explains how it fits with the other services.

## Prepare node credentials

The default authentication backend reads a CSV file when the service starts:

```csv
node_id,password
1234,YOUR_GENERATED_PASSWORD
```

Give each node its own generated password. Use printable ASCII without whitespace;
32-character base64url passwords fit the client configuration. The file requires the
`node_id,password` header and rejects duplicate IDs. Restart the service after editing
it. Never commit a real credential file.

The container runs as UID/GID 10001. That user must be able to read the mounted file;
restrict other access using the file ownership and permissions on your host.

## Run the service

Choose a versioned image from `ghcr.io/hamlink-canada/register-pyhttp` when a release
is available. Before an image is published, [build this checkout](#build-an-image)
and use `rpt-http-register:local`.

With `credentials.csv` in the current directory, replace the broker address below:

```sh
IMAGE=rpt-http-register:local

docker run -d --name rpt-http --restart unless-stopped \
  --publish 127.0.0.1:5000:5000 \
  --mount "type=bind,src=$(pwd)/credentials.csv,dst=/run/secrets/credentials.csv,readonly" \
  --env RPT_AUTH__BACKEND=file \
  --env RPT_AUTH__FILE=/run/secrets/credentials.csv \
  --env RPT_KAFKA__BOOTSTRAP=kafka.example.org:9092 \
  --env RPT_KAFKA__TOPIC=rpt.registrations \
  --env RPT_SERVER_ID=http-1 \
  "$IMAGE"
```

This example exposes HTTP only on the host's loopback address for a host-based
reverse proxy. Point the proxy's HTTPS endpoint at `127.0.0.1:5000`. If your proxy
runs in another container, use a shared Docker network and configure its upstream
address accordingly. Kafka's advertised broker addresses must be reachable from
the registration container.

The node address comes from the HTTP connection. If the proxy supplies that address
through `X-Forwarded-For`, explicitly configure `HTTP.TRUSTED_PROXIES` with the proxy
addresses as seen by the container and `HTTP.PROXY_HOPS` with the trusted hop count.
The proxy must overwrite client-supplied forwarding headers. Forwarded addresses are
ignored by default; incorrect proxy configuration can publish the proxy's address
as the node address. For example, in `settings.toml`:

```toml
[http]
trusted_proxies = ["192.0.2.10/32"]
proxy_hops = 1
```

Replace the example CIDR with your proxy's actual address. See
[HTTP compatibility](docs/http-compatibility.md) for the client contract.

## Configuration

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `RPT_KAFKA__BOOTSTRAP` | `localhost:9092` | Kafka bootstrap address. |
| `RPT_KAFKA__TOPIC` | `rpt.registrations` | Topic shared with the DNS directory. |
| `RPT_SERVER_ID` | `registrar-1` in the image settings | Identifier included in registrations. |
| `RPT_REFRESH` | `60` | Refresh value returned to clients, in seconds. |
| `RPT_LIFETIME` | `180` | Registration validity, in seconds. |
| `RPT_AUTH__BACKEND` | `file` | Credential source: `file` or `grpc`. |
| `RPT_AUTH__FILE` | `/run/secrets/credentials.csv` in the image settings | Local credential file. |
| `RPT_HTTP__MAX_BODY` | `16384` | Maximum request body size in bytes. |

Dynaconf reads `settings.toml` and optional `.secrets.toml` from the working directory,
then applies `RPT_` environment overrides. Nested settings use two underscores.
To mount your own files at `/config`, set `RPT_CONFIG_DIR=/config`. Use plain TOML
without environment sections, and absolute paths for mounted credential files.

The `grpc` backend retrieves passwords from a compatible central credential service;
HTTP password verification still happens here. The `Register-Central_Auth` repository
implements the production credential server. Clients require verified TLS and a
service token or client certificate. The cache holds up to 4096 successful lookups
for 60 seconds by default. During an outage, unexpired cached credentials still work;
expired entries and new lookups fail closed. Password rotation can take up to the
cache TTL to become visible. There is no automatic fallback to the CSV file.

See [authentication and limits](docs/authentication.md) for gRPC settings, certificate
configuration, cache controls, and rate limits. Limits are per process; use shared
ingress controls when running multiple instances. Allow for several nodes sharing
one source address when setting limits.

## Configure and check a node

In the node's `rpt_http_registrations.conf`, use its ID and generated password and
the hostname of your HTTPS endpoint:

```ini
[general]
register_interval = 60

[registrations]
register => 1234:YOUR_GENERATED_PASSWORD@register.example.org
```

See the [AllStarLink HTTP registration guide](https://allstarlink.github.io/adv-topics/httpreg/)
for client setup. Check its status with `rpt show registrations` in the Asterisk CLI. The
client uses its own configured interval to schedule renewals; returning a different
`refresh` value does not change that scheduler. Keep the server's registration
lifetime long enough to tolerate missed renewals.

```sh
docker logs --tail 100 rpt-http
docker restart rpt-http
docker stop rpt-http
```

An accepted registration returns HTTP 200 with `successfully registered` in its
response, after Kafka confirms publication. A rejected password also returns 200,
with a failure message, to match the client contract. Malformed requests return
400, oversized bodies 413, throttled requests 429, and backend failures 503.
The upstream client can retain an old displayed status after a non-2xx response;
check DNS and the current registration lifetime when diagnosing a stale status.

## Build an image

From this checkout, with Docker Buildx and Python 3.13+ installed:

```sh
PROTOBUF_REV=$(python3 scripts/dependency.py)
docker buildx build --load \
  --build-context "rpt_protobuf=https://github.com/Hamlink-Canada/rpt_protobuf.git#${PROTOBUF_REV}" \
  --tag rpt-http-register:local .
```

The build uses the public protobuf library from its `main` branch.
The image starts the production WSGI server through `rpt-http`.

## Development

Use Python 3.13+ and uv. Place this checkout next to `rpt_protobuf`, with the library
on an up-to-date `main` branch. uv installs that sibling in
editable mode.

```sh
uv sync --locked
make check test build
RPT_AUTH__FILE=examples/credentials.csv uv run --locked rpt-http
```

The example credential file is for local development only. For image builds with
local library changes, use `--build-context rpt_protobuf=../rpt_protobuf` instead of
the remote context. Standard Python installations use the `main` branch in
`pyproject.toml`. CI uses one resolved revision per run; separate builds can use newer
library code. Refresh lockfiles when dependency metadata changes.
The shared library owns the protobuf schemas and generated bindings.

CI checks Python 3.13 and 3.14 and is configured for Linux AMD64 and ARM64 image
builds and runtime imports. Published GitHub releases with `vMAJOR.MINOR.PATCH` tags publish versioned images
and commit-SHA
tags; only stable releases update `latest`. Pull requests never publish images.
There is no PyPI release.

Images are published only after the release workflow passes its tests and container
checks. Publishing a GitHub prerelease (for example, `v1.0.1-rc.1`) publishes its
version and commit-SHA image tags without updating `latest`. Pushing a tag alone
does not publish an image. Registry authentication uses the built-in `GITHUB_TOKEN`.

## License

[AGPL-3.0-or-later](LICENSE).
