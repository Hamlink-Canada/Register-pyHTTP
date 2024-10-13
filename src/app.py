from flask import Flask, request
from flask_smorest import Api
from flask_kafka import FlaskKafka
from routes.root import bp as rootBP
from db import db
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
app.config["API_TITLE"] = "app_rpt HTTP Registration"
app.config["API_VERSION"] = "v1.0.0"
app.config["OPENAPI_VERSION"] = "3.0.2"
app.config["KAFKA_CONFIG"] = {'bootstrap.servers': 'localhost:9092',
                              'group.id': "foo",
                             }
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://allstar:change_me@localhost/allstar"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {'pool_recycle': 60 * 5, 'pool_pre_ping': True}

db.init_app(app)

app.bus = FlaskKafka()
app.bus.init_app(app)

api = Api(app)
api.register_blueprint(rootBP)
