from db import db
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

# This is a basic model for the old ASL database. 
# It does not implement everything, just enough to authenticate a node
class Node(db.Model):
    __tablename__ = "user_Nodes"

    Node_ID: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[int]
    secret: Mapped[str]

def verify(node, password):
    data = db.session.query(Node).filter_by(name = node, secret = password).all()
    if len(data) > 0:
        return True
    return False
