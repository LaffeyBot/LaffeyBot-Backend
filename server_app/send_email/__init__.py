from flask import Blueprint

email_blueprint = Blueprint(
    "email_v1",
    __name__,
    url_prefix='/v1/email'
)

from .send_email import *