from flask import Blueprint, request, jsonify, g

from typing import List

from server_app.auth_tools import login_required
from data.model import *
from server_app.group_tools import get_group_of_user
from data.alchemy_encoder import AlchemyEncoder

group_blueprint = Blueprint(
    "group_v1",
    __name__,
    url_prefix='/v1/group'
)


@group_blueprint.route('/create_group', methods=['POST'])
@login_required
def create_group():
    """
    @api {post} /v1/group/create_group 成立新公会

    @apiVersion 1.0.0
    @apiName create_group
    @apiGroup Groups

    @apiParam {String}  group_name       (必须)    公会名
    @apiParam {String}  description      (必须)    公会介绍
    @apiParam {String}  must_request       (必须)    是否强制出刀
    @apiParam {String}  group_chat_id    (可选)    公会群号

    @apiSuccess (回参) {String}                 msg     为"Successful!"
    @apiSuccess (回参) {List[Dictionary]}       data    成立的公会信息，具体内容参照Groups表

    @apiSuccessExample {json} 成功样例
        HTTP/1.1 200 OK
        {
            "msg": "Successful!",
            "data": [
                {
                    "group_name": "美食殿",
                    "group_chat_id": 123123123,
                    "description": "みんなで楽しく食事をするギルド。その名も、美食殿！",
                    "must_request": False
                },
                ...
            ]
        }

    @apiErrorExample {json} 用户已经在一个公会里了
        HTTP/1.1 403 Forbidden
        {"msg": "User is already in a group.", "code": 410}

    @apiErrorExample {json} 未提供必要参数
        HTTP/1.1 400 Bad Request
        {"msg": "Missing parameter", "code": 101}

    """
    user: Users = g.user
    if g.user.group_id != -1:
        return jsonify({"msg": "User is already in a group.", "code": 410}), 403

    try:
        json: dict = request.get_json(force=True)
        group_name = json['group_name']
        group_chat_id = json.get('group_chat_id', '')
        description = json.get('description', '')
        must_request: bool = json['must_request']
    except KeyError:
        return jsonify({"msg": "Missing parameter", "code": 101}), 400

    new_group = Groups(group_chat_id=group_chat_id,
                       name=group_name,
                       description=description,
                       owner_id=user.id,
                       current_boss_gen=1,
                       current_boss_order=1,
                       boss_remaining_health=Config.BOSS_HEALTH[0],
                       must_request=must_request)
    db.session.add(new_group)
    db.session.commit()
    db.session.refresh(new_group)
    user.group_id = new_group.id
    user.role = 2  # 玩家成爲會長
    db.session.commit()

    return jsonify({
        "msg": "Successful!",
        "data": AlchemyEncoder().default(new_group)
    }), 200


@group_blueprint.route('/get_members', methods=['GET'])
@login_required
def get_members():
    """
    @api {get} /v1/group/get_members 获取公会成员信息
    @apiVersion 1.0.0
    @apiName get_members
    @apiGroup Groups

    @apiSuccess (回参) {String}                 msg     为"Successful!"
    @apiSuccess (回参) {List[Dictionary]}       data    公会成员列表，包含Users表中的id, group_id, nickname, role, username.

        @apiSuccessExample {json} 成功样例
        HTTP/1.1 200 OK
        {
            "msg": "Successful!",
            "data": [
                {
                    "id": 123,
                    "group_id": 12345,
                    "nickname": "キョウカ",
                    "role": 1,
                    "username": "kyouka"
                },
                ...
            ]
        }

    @apiErrorExample {json} 用户没有加入公会
        HTTP/1.1 403 Forbidden
        {"msg": "User is not in any group.", "code": 402}

    @apiErrorExample {json} 用户的公会不存在
        HTTP/1.1 404 Not Found
        {"msg": "User's group not found.", "code": 403}

    """
    if g.user.group_id == -1:
        return jsonify({"msg": "User is not in any group.", "code": 402}), 403

    group = get_group_of_user()
    if not group:
        return jsonify({"msg": "User's group not found.", "code": 403}), 404

    members: List[Users] = Users.query.filter_by(group_id=group.id).all()
    data_list: List[dict] = list()
    for member in members:
        data_dict = dict(id=member.id,
                         group_id=member.group_id,
                         nickname=member.nickname,
                         role=member.role,
                         username=member.username)
        data_list.append(data_dict)

    return jsonify({
        "msg": "Successful!",
        "data": data_list
    }), 200


@group_blueprint.route('/kick_member', methods=['DELETE'])
@login_required
def kick_member():
    """
    @api {delete} /v1/group/kick_member 踢出成员
    @apiVersion 1.0.0
    @apiName kick_member
    @apiGroup Groups

    @apiParam {String}  id       (必须)    成员ID
    @apiSuccess (回参) {String}   msg     为"Successful!"

        @apiSuccessExample {json} 成功样例
        HTTP/1.1 200 OK
        {
            "msg": "Successful!"
        }

    @apiErrorExample {json} 未提供ID
        HTTP/1.1 400 Bad Request
        {"msg": "ID is missing.", "code": 201}

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

    user: Users = g.user
    if user.group_id == -1:
        return jsonify({"msg": "User is not in any group.", "code": 402}), 403

    group = get_group_of_user()
    if not group:
        return jsonify({"msg": "User's group not found.", "code": 403}), 403

    if user.role < 2 or group.owner_id != user.id:
        return jsonify({"msg": "Permission Denied", "code": 404}), 403

    user_to_be_kicked: Users = Users.query.filter_by(group_id=group.id, id=user.id).first()
    if not user_to_be_kicked:
        return jsonify({"msg": "Invalid ID", "code": 405}), 204
    user_to_be_kicked.group_id = -1
    db.session.commit()

    return jsonify({
        "msg": "Successful!"
    }), 200
