from flask import Blueprint

pn_blueprint = Blueprint(
    "push",
    __name__,
    url_prefix='/v1/push'
)


from .push_notification import *