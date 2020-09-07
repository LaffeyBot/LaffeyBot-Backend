from flask import request, jsonify, g
import datetime
from server_app.auth_tools import get_user_with, generate_user_dict
from data.model import *
from . import account_blueprint
from server_app.auth_tools import login_required


@account_blueprint.route('/link_account', methods=['POST'])
@login_required
def link_account():
    """
    @api {post} /v1/account/link_account  绑定QQ账号（仅供Bot使用）
    @apiVersion 1.0.0
    @apiName link_account
    @apiGroup Users
    @apiParam {String}  username   (必须)    绑定的用户名

    @apiParamExample {json} Request-Example:
        {
            "username": "someuser"
        }

    @apiSuccess (回参) {String} msg   为"Successful!"
    @apiSuccess (回参) {String} user  user信息，具体见样例
    @apiSuccessExample {json} 成功样例
        HTTP/1.1 200 OK
        {
            "msg": "Successful!",
            "user": {
                "username": "foo",
                "nickname": "bar",
                "id": 233,
                "role": 2,
                "email": "example@example.com",
                "group_id": 233
            }
        }

    @apiErrorExample {json} 用户名或密码过短
        HTTP/1.1 422 Unprocessable Entity
        {
            "msg": "Username or password is too short",
            "code": 102
        }

    @apiErrorExample {json} 用户名已存在
        HTTP/1.1 409 Conflict
        {"msg": "User Exists."}

    @apiErrorExample {json} 邮箱验证码错误
        HTTP/1.1 403 Forbidden
        {"msg": "OTP is invalid."}

    @apiErrorExample {json} 邮箱已存在
        HTTP/1.1 410 Gone
        {"msg": "Email Exists"}
    """
    if not Config.REGISTER_ENABLED:
        return jsonify({"msg": "Register is not enabled."}), 400
    try:
        json: dict = request.get_json(force=True)
        username = json["username"]
    except KeyError:
        return jsonify({"msg": "Missing parameter"}), 400
    account_to_link: User = get_user_with(username=username)
    if not account_to_link:
        return jsonify({"msg": "User does not exist"}), 409

    qq_temp_user: User = g.user
    if not qq_temp_user.is_temp:
        return jsonify({"msg": "User has already linked to an account."}), 410

    account_to_link.qq = qq_temp_user.qq
    account_to_link.group_id = qq_temp_user.group_id
    account_to_link.nickname = qq_temp_user.nickname
    account_to_link.role = qq_temp_user.role

    qq_temp_user.personal_records.update({
        PersonalRecord.last_modified: datetime.datetime.now(),
        PersonalRecord.user_id: account_to_link.id
    })

    qq_temp_user.hang_on_trees.update({
        HangOnTree.user_id: account_to_link.id
    })

    db.session.delete(qq_temp_user)
    db.session.commit()

    user_data = generate_user_dict(user=account_to_link, for_oneself=True)

    return jsonify({
        "msg": "Successful!",
        "user": user_data
    }), 200
