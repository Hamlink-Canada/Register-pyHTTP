"""Marshmallow schemas for the registration response payload.

Defines the structure returned by the registration endpoint. The small
test harness at the bottom allows quick local verification.
"""

from marshmallow import Schema, fields, ValidationError


class NodeData(Schema):
    node = fields.String()
    passwd = fields.String()
    remote = fields.Int()


class NodeRegistration(Schema):
    nodes = fields.Dict(keys=fields.Str(), values=fields.Nested(NodeData()), many=True)


class ReturnRegistration(Schema):
    # IP address we believe the request came from
    ipaddr = fields.Str()
    # Port supplied by the registering client
    port = fields.Int()
    # TTL / refresh instruction for the client
    refresh = fields.Int()
    # One or more human readable messages describing the registration result
    data = fields.List(fields.String())


if __name__ == "__main__":
    # Quick example showing how the response schema serializes a result
    import json
    from pprint import pprint

    data = {
        'ipaddr': '127.0.0.1',  # The IP we think the request came from
        'port': 3456,           # The port from the registration
        'refresh': 60,          # Our TTL
        'data': [f"1234 successfully registered."],    # Successful
    }
    schema = ReturnRegistration()
    result = schema.dump(data)
    pprint(result)
