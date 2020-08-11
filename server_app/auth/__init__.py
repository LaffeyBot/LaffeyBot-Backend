from flask import Blueprint

auth_blueprint = Blueprint(
    "auth_v1",
    __name__,
    url_prefix='/v1/auth'
)

from .auth import *
