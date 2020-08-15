from flask import request, jsonify, g
from typing import List
from server_app.auth_tools import login_required
from data.model import *
from data.alchemy_encoder import AlchemyEncoder
from . import group_blueprint


@group_blueprint.route('/invite_member', methods=['POST'])
@login_required
def invite_member():
    """
    @api {post} /v1/group/invite_member 邀请新成员

    @apiVersion 1.0.0
    @apiName invite_member
    @apiGroup Groups

    @apiParam {String}  username       (必须)    玩家用户名
    @apiDescription 注：只有管理员或会长可以邀请玩家。

    @apiSuccess (回参) {String}                msg     为"Successful!"

    @apiSuccessExample {json} 成功样例
        HTTP/1.1 200 OK
        {
            "msg": "Successful!"
        }


    @apiErrorExample {json} 未提供username
        HTTP/1.1 400 Bad Request
        {"msg": "", "code": 201}

    @apiErrorExample {json} 用户没有加入公会
        HTTP/1.1 403 Forbidden
        {"msg": "User is not in any group.", "code": 402}

    @apiErrorExample {json} 用户的公会不存在
        HTTP/1.1 403 Forbidden
        {"msg": "User's group not found.", "code": 403}

    @apiErrorExample {json} 用户不是会长
        HTTP/1.1 403 Forbidden
        {"msg": "Permission Denied", "code": 404}

    @apiErrorExample {json} 被踢出的成员不存在
        HTTP/1.1 204 No Content
        {"msg": "Invalid ID", "code": 405}

    """
    id_: int = request.get_json().get('id', None)
    if not id_:
        return jsonify({"msg": "ID is missing.", "code": 201}), 400

    user: User = g.user
    if user.group_id == -1:
        return jsonify({"msg": "User is not in any group.", "code": 402}), 403

    group = user.group
    if not group:
        return jsonify({"msg": "User's group not found.", "code": 403}), 403

    if user.role < 2 or group.owner_id != user.id:
        return jsonify({"msg": "Permission Denied", "code": 404}), 403

    user_to_be_kicked: User = User.query.filter_by(group_id=group.id, id=user.id).first()
    if not user_to_be_kicked:
        return jsonify({"msg": "Invalid ID", "code": 405}), 204
    user_to_be_kicked.group_id = -1
    db.session.commit()

    return jsonify({
        "msg": "Successful!"
    }), 200