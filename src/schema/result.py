from marshmallow import Schema, fields, ValidationError

 

class NodeData(Schema):
    node = fields.String()
    passwd = fields.String()
    remote = fields.Int()

class NodeRegistration(Schema):
    nodes = fields.Dict(keys = fields.Str(), values=fields.Nested(NodeData()), many=True)

class ReturnRegistration(Schema):
    ipaddr = fields.Str()
    port = fields.Int()
    refresh = fields.Int()
    data = fields.List(fields.String())

if __name__ == "__main__":
    import json
    from pprint import pprint

    data = {
        'ipaddr': '127.0.0.1',  # The IP we think the request came from
        'port': 3456,           # THe port from the registration
        'refresh': 60,          # Our TTL
        'data': [f"1234 successfully registered."],    # Successgful
    }
    schema = ReturnRegistration()
    result = schema.dump(data)
    pprint(result)
