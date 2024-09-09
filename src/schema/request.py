from marshmallow import Schema, fields, ValidationError

class NodeData(Schema):
    node = fields.String()
    passwd = fields.String()
    remote = fields.Int()

class NodeRegistration(Schema):
    nodes = fields.Dict(keys = fields.Str(), values=fields.Nested(NodeData()), many=True)

class RequestRegistration(Schema):
    port = fields.Int()
    data = fields.Nested(NodeRegistration())

if __name__ == "__main__":
    import json
    from pprint import pprint

    data = json.loads('{"port":4567,"data":{"nodes":{"2509":{"node":"2509","passwd":"435009","remote":0}}}}')
    schema = RequestRegistration()
    result = schema.dump(data)
    pprint(result['data']['nodes']['2509'])
    pprint(result)
