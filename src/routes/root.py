"""HTTP registration endpoint blueprint.

The blueprint exposes a single `POST /` endpoint which accepts a
registration payload (validated by marshmallow schemas), authenticates
the node, builds a protobuf `update` message and publishes it to Kafka.
"""

from datetime import datetime
from flask.views import MethodView
from flask import request, current_app
from flask_smorest import Blueprint
from schema.request import RequestRegistration
from schema.result import ReturnRegistration
from dns_pb2 import update
from verifier import verify


bp = Blueprint("root", __name__)


@bp.route("/", methods=['POST'])
class Register(MethodView):
    @bp.arguments(RequestRegistration)
    @bp.response(200, schema=ReturnRegistration())
    def post(self, postBody):
        """Handle a registration POST.

        `postBody` is already validated and deserialized by `flask-smorest`.
        We extract the first node entry, authenticate it, create a protobuf
        `update` message and publish it using the application's Kafka
        producer helper attached to `current_app.bus`.
        """
        # Extract the single node object from the nested dict structure
        nodeInfo = list(postBody['data']['nodes'].values())[0]

        password = nodeInfo['passwd']
        Entry = update()
        Entry.timestamp.FromDatetime(datetime.now())
        Entry.node = int(nodeInfo['node'])
        # Use the request's remote address as the node IP
        Entry.ipaddress = request.remote_addr
        Entry.port = postBody['port']
        Entry.ttl = 60
        Entry.server = "XXXXX"

        # Authenticate the node using the verifier helper
        valid = verify(Entry.node, password)

        if valid:
            # Publish the serialized protobuf to Kafka topic "test"
            publisher = current_app.bus.get_producer()
            publisher.produce("test", key=nodeInfo['node'], value=Entry.SerializeToString())
            data = f"{Entry.node} successfully registered."
        else:
            data = f"{Entry.node} failed authentication. Please check your password and node number."

        result = {
            'ipaddr': Entry.ipaddress,  # IP we detected for the client
            'port': Entry.port,         # Port the client reported
            'refresh': Entry.ttl,       # TTL for the cached registration
            'data': [data],             # Human readable status messages
        }
        return result
