from flask import request, jsonify, g
import datetime
from ..auth_tools import login_required
from data.model import *
from data.alchemy_encoder import AlchemyEncoder
import json as js
from . import record_blueprint
from .record_tools import make_new_team_record


@record_blueprint.route('/get_ocr_status', methods=['GET'])
@login_required
def get_ocr_status():
    """
    @api {post} /v1/record/get_ocr_status 获取ocr状态
    @apiVersion 1.0.0
    @apiName get_records
    @apiGroup Records

    @apiSuccess (回参) {String}           True/False

    @apiErrorExample {json} 用户没有加入公会
        HTTP/1.1 403 Forbidden
        {"msg": "User is not in any group."}

    @apiErrorExample {json} 用户的公会不存在
        HTTP/1.1 417 Expectation Failed
        {"msg": "User's group not found."}

    """