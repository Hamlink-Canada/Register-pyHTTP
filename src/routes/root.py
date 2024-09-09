#from flask import Flask, request
from datetime import datetime
from flask.views import MethodView
from flask import request, current_app
from flask_smorest import Api, Blueprint, abort
from schema.request import RequestRegistration
from schema.result import ReturnRegistration
from dns_pb2 import update
from verifier import verify

bp = Blueprint("root", __name__)

@bp.route("/", methods = ['POST'])
class Register(MethodView):
    @bp.arguments(RequestRegistration)
    @bp.response(200, schema=ReturnRegistration())
    def post(self, postBody):
        nodeInfo = list(postBody['data']['nodes'].values())[0]

        password = nodeInfo['passwd']
        Entry = update()
        Entry.timestamp.FromDatetime(datetime.now())
        Entry.node = int(nodeInfo['node'])
        Entry.ipaddress = request.remote_addr
        Entry.port = postBody['port']
        Entry.ttl = 60
        Entry.server = "XXXXX"

        valid = verify(Entry.node, password)

        if valid:
            publisher = current_app.bus.get_producer()
            publisher.produce("test", key=nodeInfo['node'], value=Entry.SerializeToString())
            data = f"{Entry.node} successfully registered."
        else:
            data = f"{Entry.node} failed authentication. Please check your password and node number."

        result = {
            'ipaddr': Entry.ipaddress,  # The IP we think the request came from
            'port': Entry.port,           # THe port from the registration
            'refresh': Entry.ttl,          # Our TTL
            'data': [data],    # Successgful 
        }
        return result

