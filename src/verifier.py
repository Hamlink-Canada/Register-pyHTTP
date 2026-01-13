"""Minimal verifier for authenticating nodes against an ASL-style table.

The module provides a tiny SQLAlchemy model for the legacy `user_Nodes`
table and a `verify()` helper that returns True when a (node, password)
pair matches a database row.

This is intentionally small — adapt or replace `verify()` to integrate
with your real user store or authentication service.
"""

from db import db
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column


# Minimal SQLAlchemy model representing the legacy ASL `user_Nodes` table.
class Node(db.Model):
    __tablename__ = "user_Nodes"

    # Primary key column in the legacy schema
    Node_ID: Mapped[int] = mapped_column(primary_key=True)
    # The node name (used as username in this project)
    name: Mapped[int]
    # The shared secret/password for the node
    secret: Mapped[str]


def verify(node, password):
    """Return True when `node`/`password` match a DB row, False otherwise."""
    # Simple query returning all matching rows; existence implies valid
    data = db.session.query(Node).filter_by(name=node, secret=password).all()
    return len(data) > 0
