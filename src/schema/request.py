"""Marshmallow schemas for the registration request payload.

Defines the expected structure for incoming registration JSON so the API
can validate and deserialize requests cleanly.
"""

from marshmallow import Schema, fields, ValidationError


class NodeData(Schema):
    # Individual node fields included in a registration
    node = fields.String()
    passwd = fields.String()
    remote = fields.Int()


class NodeRegistration(Schema):
    # Mapping of node-id -> NodeData
    nodes = fields.Dict(keys=fields.Str(), values=fields.Nested(NodeData()), many=True)


class RequestRegistration(Schema):
    # Top-level registration object
    port = fields.Int()
    data = fields.Nested(NodeRegistration())


if __name__ == "__main__":
    # Quick manual test harness to exercise the schema
    import json
    from pprint import pprint

    data = json.loads('{"port":4567,"data":{"nodes":{"2509":{"node":"2509","passwd":"435009","remote":0}}}}')
    schema = RequestRegistration()
    result = schema.dump(data)
    pprint(result['data']['nodes']['2509'])
    pprint(result)
