from flask import Blueprint

user_blueprint = Blueprint(
    "user_v1",
    __name__,
    url_prefix='/v1/user'
)

from .ocr_status import *
