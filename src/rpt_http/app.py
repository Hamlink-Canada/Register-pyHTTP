"""AllStarLink-compatible HTTP registration endpoint."""

from hmac import compare_digest
from ipaddress import IPv4Address, ip_address, ip_network

from flask import Flask, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix

from .auth import AuthUnavailable, credentials, node_id, valid_password
from .config import load_settings
from .publisher import Publisher, PublishUnavailable
from .security import AbuseGuard

try:
    from opentelemetry import trace
except ImportError:  # Telemetry is an optional extra.
    trace = None


def _trace_attributes(**attributes):
    if trace is None:
        return
    span = trace.get_current_span()
    if span.is_recording():
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)


class TrustedProxy:
    def __init__(self, app, networks, hops):
        self.app = app
        self.networks = [ip_network(n) for n in networks]
        self.fixed = ProxyFix(app, x_for=hops)

    def __call__(self, environ, start_response):
        try:
            trusted = any(ip_address(environ["REMOTE_ADDR"]) in n for n in self.networks)
        except (ValueError, KeyError):
            trusted = False
        return (self.fixed if trusted else self.app)(environ, start_response)


def create_app(settings=None, provider=None, publisher=None):
    settings = settings if settings is not None else load_settings()
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = int(settings.HTTP.MAX_BODY)
    if settings.HTTP.TRUSTED_PROXIES:
        if int(settings.HTTP.PROXY_HOPS) < 1:
            raise ValueError("proxy_hops must be positive")
        app.wsgi_app = TrustedProxy(
            app.wsgi_app, settings.HTTP.TRUSTED_PROXIES, int(settings.HTTP.PROXY_HOPS)
        )
    provider = provider if provider is not None else credentials(settings)
    publisher = publisher if publisher is not None else Publisher(settings)
    guard = AbuseGuard(settings)
    app.extensions.update(credentials=provider, publisher=publisher, abuse_guard=guard)

    def reply(message, port=4569, status=200):
        # Only successful registration may include the client's success substring.
        return jsonify(
            ipaddr=request.remote_addr, port=port, refresh=int(settings.REFRESH), data=[message]
        ), status

    @app.before_request
    def ingress():
        if not guard.ingress(request.remote_addr):
            response, status = reply("Registration rate limited.", status=429)
            response.headers["Retry-After"] = "60"
            return response, status

    @app.post("/")
    def register():
        _trace_attributes(
            **{"client.address": request.remote_addr, "service.operation": "registration"}
        )
        body = request.get_json(silent=True)
        try:
            if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
                raise ValueError
            nodes = body["data"]["nodes"]
            if not isinstance(nodes, dict) or len(nodes) != 1:
                raise ValueError
            key, entry = next(iter(nodes.items()))
            if not isinstance(entry, dict):
                raise ValueError
            submitted_node = entry.get("node")
            submitted_password = entry.get("passwd")
            _trace_attributes(
                **{
                    "auth.username": submitted_node[:128]
                    if isinstance(submitted_node, str)
                    else None,
                    "auth.password.present": "passwd" in entry,
                    "auth.password.length": len(submitted_password)
                    if isinstance(submitted_password, str)
                    else None,
                }
            )
            node = node_id(entry["node"])
            _trace_attributes(**{"repeater.node_id": node, "auth.username": node})
            if (
                not isinstance(entry["node"], str)
                or key != node
                or not valid_password(entry["passwd"])
            ):
                _trace_attributes(
                    **{
                        "auth.password.present": "passwd" in entry,
                        "auth.password.length": (
                            len(entry["passwd"]) if isinstance(entry["passwd"], str) else None
                        ),
                        "auth.failure.category": "invalid_credentials_format",
                    }
                )
                raise ValueError
            if type(entry.get("remote", 0)) is not int or entry.get("remote", 0) != 0:
                raise ValueError
            port = body.get("port", 4569)
            if type(port) is not int or not 1 <= port <= 65535:
                raise ValueError
            ip = str(IPv4Address(request.remote_addr))
        except (KeyError, TypeError, ValueError):
            return reply("Invalid registration request.", status=400)
        if not guard.auth_allowed(ip, node):
            response, status = reply("Registration rate limited.", port, 429)
            response.headers["Retry-After"] = "60"
            return response, status
        try:
            password = provider.get(node)
            if password is None or not compare_digest(password.encode(), entry["passwd"].encode()):
                _trace_attributes(
                    **{
                        "auth.password.present": True,
                        "auth.password.length": len(entry["passwd"]),
                        "auth.failure.category": "credential_mismatch",
                    }
                )
                guard.failure(ip, node)
                return reply("Registration authentication failed.", port)
            if not guard.success(ip, node):
                _trace_attributes(
                    **{"auth.result": "success", "registration.result": "rate_limited"}
                )
                return reply("Registration rate limited.", port, 429)
            publisher.publish(node, ip, port)
            _trace_attributes(**{"auth.result": "success", "registration.result": "published"})
        except AuthUnavailable:
            _trace_attributes(**{"auth.failure.category": "credential_service_unavailable"})
            return reply("Authentication service unavailable.", port, 503)
        except PublishUnavailable:
            _trace_attributes(**{"registration.failure.category": "publisher_unavailable"})
            return reply("Registration service unavailable.", port, 503)
        return reply(f"{node} successfully registered.", port)

    @app.errorhandler(413)
    def too_large(error):
        return reply("Registration request too large.", status=413)

    return app
