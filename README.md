# pyHTTP-Register

Lightweight HTTP endpoint to accept APP RPT node registrations and forward
them to Kafka as protobuf `update` messages.

Overview
- Receives node registration POST requests, authenticates against an
	existing ASL-style database, and publishes a protobuf `update` message
	to a Kafka topic for consumption by DNS services.

Prerequisites
- Python 3.8+
- Kafka cluster available (bootstrap servers)
- MySQL (or compatible) database with an ASL `user_Nodes` table for
	authentication, or modify `verifier.verify()` to match your user store
- `protoc` (Protocol Buffers compiler) if you need to generate `dns_pb2.py`

Install

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# If using MySQL with the URL in `src/app.py` install a driver such as:
pip install pymysql
```

2. Ensure protobuf bindings for `dns.proto` are available to the app.

The service imports `dns_pb2` from the application import path. The
`dns.proto` definition lives in a separate project (DNS server). Obtain
`dns.proto` from the external `dnsserver` GitHub repository and generate
`dns_pb2.py`. Two common ways to do this:

- Clone the official `dnsserver` repository and build locally:

```bash
git clone https://github.com/Apprpt-Central/dnsserver.git
cd dnsserver
./build_proto.sh
# Copy generated bindings into this project's import path
cp apprptdns/dns_pb2.py ../pyHTTP-Register/src/
```

- Or download the proto file and generate directly into this project:

```bash
curl -O https://raw.githubusercontent.com/Apprpt-Central/dnsserver/main/dns.proto
protoc --python_out=pyHTTP-Register/src dns.proto
# move generated file into the expected package location if necessary
mv pyHTTP-Register/src/apprptdns/dns_pb2.py pyHTTP-Register/src/
```

Note: `dnsserver` is a separate GitHub project: https://github.com/Apprpt-Central/dnsserver

Configuration

- Edit `src/app.py` to configure `KAFKA_CONFIG` and `SQLALCHEMY_DATABASE_URI`.
	Example Kafka config uses `bootstrap.servers` as expected by the
	confluent client wrapper.

Running the service

Run the Flask app (from the repository root):

```bash
export FLASK_APP=src.app
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

API

- POST / : Accepts a JSON body conforming to `src/schema/request.py` and
	responds with `src/schema/result.py` format. Example request body:

```json
{
	"port": 4567,
	"data": {
		"nodes": {
			"2509": { "node": "2500", "passwd": "1234567890", "remote": 0 }
		}
	}
}
```

On success the endpoint publishes a protobuf `update` message to Kafka
and returns a small JSON summary including the detected client IP and
TTL.

Testing

- A basic test loop is provided in `test.py` which POSTs a registration
	periodically to `http://localhost:5000/`.

Notes and troubleshooting
- `src/verifier.py` contains a minimal SQLAlchemy model for the old ASL
	`user_Nodes` table and a simple `verify()` function. Adjust as needed
	for your authentication backend.
- Ensure `dns_pb2.py` is importable from the application path (see
	protobuf generation above).
- The app uses `flask-kafka` to expose `app.bus.get_producer()`; the
	underlying Kafka client configuration is set in `app.config["KAFKA_CONFIG"]`.

License

See the `LICENSE` file for license information.
