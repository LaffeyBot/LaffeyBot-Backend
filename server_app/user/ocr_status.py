from flask import request, jsonify, g
import datetime
from ..auth_tools import login_required
from data.model import *
from data.alchemy_encoder import AlchemyEncoder
from . import user_blueprint
from server_app.qq_tools import send_message_to_qq


@user_blueprint.route('/get_ocr_status', methods=['GET'])
@login_required
def get_ocr_status():
    """
    @api {post} /v1/user/get_ocr_status 获取ocr状态
    @apiVersion 1.0.0
    @apiName get_ocr_status
    @apiGroup User

    @apiSuccess (回参) {String}           True/False

    @apiErrorExample {json} 用户没有加入公会
        HTTP/1.1 403 Forbidden
        {"msg": "User is not in any group."}

    @apiErrorExample {json} 用户的公会不存在
        HTTP/1.1 417 Expectation Failed
        {"msg": "User's group not found."}

    """
    user: User = g.user
    return str(user.is_fetching)


@user_blueprint.route('/set_ocr_status', methods=['POST'])
@login_required
def set_ocr_status():
    """
    @api {post} /v1/user/set_ocr_status 设置ocr状态
    @apiVersion 1.0.0
    @apiName set_ocr_status
    @apiGroup User
    @apiParam {Boolean}  status     (必要)   想要设置的状态

    @apiSuccess (回参) {String}           Success!

    @apiErrorExample {json} 参数错误
        HTTP/1.1 412
        {"msg": "Invalid Argument"}

    """
    user: User = g.user
    json = request.get_json(force=True)
    is_fetching = json.get('status', None)
    origin = json.get('origin', None)
    if isinstance(is_fetching, bool):
        user.is_fetching = is_fetching
        status_text = '开始抓取了。如需停止请发送【停止抓取】' if is_fetching else '停止抓取了。如需开始请发送【开始抓取】。'
        if origin and origin == 'QQ':
            return jsonify({'msg': status_text})
        elif not is_fetching:
            headers = dict(auth=request.headers.get('auth'))
            send_message_to_qq(status_text, id_=user.qq, type_='private', header=headers)
    else:
        return jsonify({'msg': 'Invalid argument'}), 412
