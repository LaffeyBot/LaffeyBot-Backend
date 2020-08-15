from .auth_tools import login_required
from flask import g, jsonify
from data.model import *
from typing import Optional


@login_required
def get_group_of_user() -> Optional[Group]:
    """
    THIS METHOD IS DEPRECATED!
    :return: [Group of user]
    """
    user: User = g.user
    group: Group = Group.query.filter_by(id=user.group_id).first()
    return group
