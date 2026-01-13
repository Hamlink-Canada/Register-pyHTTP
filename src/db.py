"""Database helper module exposing a configured `SQLAlchemy` instance.

`db` is initialized with a custom declarative base so SQLAlchemy models in
this package use modern typing-friendly base classes.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# `db` is imported by application modules and initialized with `db.init_app(app)`
db = SQLAlchemy(model_class=Base)
