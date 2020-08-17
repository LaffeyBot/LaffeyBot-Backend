from flask import Blueprint

pn_blueprint = Blueprint(
    "email_v1",
    __name__,
    url_prefix='/v1/email'
)


from .push_notification import *