from flask import Blueprint

record_blueprint = Blueprint(
    "record_v1",
    __name__,
    url_prefix='/v1/record'
)