from flask import Blueprint

account_blueprint = Blueprint(
    "account_v1",
    __name__,
    url_prefix='/v1/account'
)

from .link_temporary_account import *
