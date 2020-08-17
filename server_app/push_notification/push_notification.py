from flask import request, jsonify, g
from ..auth_tools import login_required
from data.model import *
from . import pn_blueprint

from server_app.push_notification_tools import link_account_with_token


@pn_blueprint.route('/link_token', methods=['POST'])
@login_required
def link_token():
    """
    @api {post} /v1/push/link_token 关联token至当前帐号
    @apiVersion 1.0.0
    @apiName link_token
    @apiGroup Push Notification
    @apiParam {String}  token       (必须)    推送通知的token
    @apiParam {String}  platform    (必须)    平台(android/ios)

    @apiSuccess (回参) {String}     msg        为"Successful!"

    @apiErrorExample {json} 参数不存在
        HTTP/1.1 400 Bad Request
        {"msg": "Parameter is missing"}

    """
    user: User = g.user

    json = request.get_json(force=True)
    token = json.get('token', None)
    platform = json.get('platform', None)

    if not token or not platform:
        return jsonify({"msg": "Parameter is missing"}), 400

    result = link_account_with_token(account=user.username, platform=platform, token=token)
    return result, 200