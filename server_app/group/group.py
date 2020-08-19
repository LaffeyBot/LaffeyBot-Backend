from flask import request, jsonify, g
from typing import List
from server_app.auth_tools import login_required
from data.model import *
from server_app.group_tools import get_group_of_user
from data.alchemy_encoder import AlchemyEncoder
from . import group_blueprint


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
        HTTP/1.1 412 Precondition Failed
        {"msg": "User is already in a group."}

    @apiErrorExample {json} 未提供必要参数
        HTTP/1.1 400 Bad Request
        {"msg": "Missing parameter"}

    """
    user: User = g.user
    if user.group_id:
        return jsonify({"msg": "User is already in a group."}), 412

    try:
        json: dict = request.get_json(force=True)
        group_name = json['group_name']
        group_chat_id = json.get('group_chat_id', '')
        description = json.get('description', '')
        must_request: bool = json['must_request']
    except KeyError:
        return jsonify({"msg": "Missing parameter", "code": 101}), 400

    new_group = Group(group_chat_id=group_chat_id,
                      name=group_name,
                      description=description,
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
        {"msg": "User is not in any group."}

    @apiErrorExample {json} 用户的公会不存在
        HTTP/1.1 417 Expectation Failed
        {"msg": "User's group not found."}

    """
    user: User = g.user
    if user.group_id is None:
        return jsonify({"msg": "User is not in any group."}), 403

    group: Group = user.group
    if not group:
        return jsonify({"msg": "User's group not found."}), 417

    members: List[User] = group.users
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
        {"msg": "ID is missing."}

    @apiErrorExample {json} 用户没有加入公会
        HTTP/1.1 406 Not Acceptable
        {"msg": "User is not in any group."}

    @apiErrorExample {json} 用户的公会不存在
        HTTP/1.1 417 Expectation Failed
        {"msg": "User's group not found."}

    @apiErrorExample {json} 用户不是会长
        HTTP/1.1 403 Forbidden
        {"msg": "Permission Denied"}

    @apiErrorExample {json} 被踢出的成员不存在
        HTTP/1.1 204 No Content
        {"msg": "Invalid ID"}

    """
    id_: int = request.get_json().get('id', None)
    if not id_:
        return jsonify({"msg": "ID is missing.", "code": 201}), 400

    user: User = g.user
    if user.group_id == -1:
        return jsonify({"msg": "User is not in any group."}), 403

    group = get_group_of_user()
    if not group:
        return jsonify({"msg": "User's group not found."}), 417

    if user.role < 2:
        return jsonify({"msg": "Permission Denied"}), 403

    user_to_be_kicked: User = User.query.filter_by(group_id=group.id, id=id_).first()
    if not user_to_be_kicked:
        return jsonify({"msg": "Invalid ID"}), 204
    user_to_be_kicked.group_id = None
    user_to_be_kicked.role = 0
    db.session.commit()

    return jsonify({
        "msg": "Successful!"
    }), 200
