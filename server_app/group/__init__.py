from flask import Blueprint

group_blueprint = Blueprint(
    "group_v1",
    __name__,
    url_prefix='/v1/group'
)