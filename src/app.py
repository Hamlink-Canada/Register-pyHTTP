"""Flask application factory-ish module for the pyHTTP-Register project.

This module creates a Flask `app`, configures OpenAPI metadata, wires up
the SQLAlchemy `db` instance and a Kafka helper (`FlaskKafka`) used by
the registration endpoint to publish protobuf messages.

Note: Configuration values (KAFKA_CONFIG, SQLALCHEMY_DATABASE_URI) are
set inline for convenience — in production prefer loading from environment
or a configuration file.
"""

from flask import Flask
from flask_smorest import Api
from flask_kafka import FlaskKafka
from routes.root import bp as rootBP
from db import db
from werkzeug.middleware.proxy_fix import ProxyFix


app = Flask(__name__)
# If the app is behind a proxy/load-balancer, ProxyFix helps get the
# correct client IP address from `request.remote_addr` or headers.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

# API (OpenAPI) metadata
app.config["API_TITLE"] = "app_rpt HTTP Registration"
app.config["API_VERSION"] = "v1.0.0"
app.config["OPENAPI_VERSION"] = "3.0.2"

# Kafka configuration used by `flask-kafka` (confluent style keys)
app.config["KAFKA_CONFIG"] = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': "foo",
}

# SQLAlchemy DB URL; example uses pymysql driver for MySQL
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://allstar:change_me@localhost/allstar"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {'pool_recycle': 60 * 5, 'pool_pre_ping': True}

# Initialize DB with the app context so models can use `db.session`
db.init_app(app)

# Kafka helper attached to `app.bus` — the routes use `current_app.bus`
app.bus = FlaskKafka()
app.bus.init_app(app)

# Register OpenAPI-enabled blueprint(s)
api = Api(app)
api.register_blueprint(rootBP)
