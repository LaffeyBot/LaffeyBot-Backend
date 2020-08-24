from flask import Blueprint

generate_report_blueprint = Blueprint(
    "generate_report_blueprint",
    __name__,
    url_prefix='/v1/generate_report'
)

from .generate_report import *
