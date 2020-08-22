from flask import request, jsonify, g
import datetime
from server_app.auth_tools import is_username_exist, get_user_with, sign, verify_otp, is_email_exist, generate_user_dict
import bcrypt
from config import Config
from data.model import *
from server_app.email_tools import is_valid_email
from . import account_blueprint
from server_app.auth_tools import login_required


@account_blueprint.route('/link_account', methods=['POST'])
@login_required
def link_account():
    """
    @api {post} /v1/account/link_account  绑定QQ账号（仅供Bot使用）
    @apiVersion 1.0.0
    @apiName sign_up
    @apiGroup Users
    @apiParam {String}  username   (必须)    绑定的用户名

    @apiParamExample {json} Request-Example:
        {
            "username": "someuser"
        }

    @apiSuccess (回参) {String} msg   为"Successful!"
    @apiSuccess (回参) {String} jwt   token，应当在后续请求中被附在 auth 栏
    @apiSuccess (回参) {String} user  user信息，具体见样例
    @apiSuccessExample {json} 成功样例
        HTTP/1.1 200 OK
        {
            "msg": "Successful!",
            "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
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
    if qq_temp_user.role >= 0:
        return jsonify({"msg": "User has already linked to an account."}), 410
    account_to_link.
    new_user: User = User(username=username,
                          password=bcrypt.hashpw(password.encode(), bcrypt.gensalt()),
                          nickname=nickname,
                          created_at=datetime.datetime.now(),
                          role=0,
                          email=email,
                          email_verified=True,
                          phone=phone,
                          phone_verified=False,
                          valid_since=datetime.datetime.now()
                          )
    db.session.add(new_user)
    db.session.commit()
    db.session.refresh(new_user)

    token = {
        "sub": new_user.id,
        "iss": Config.DOMAIN_NAME,
        "aud": Config.FRONTEND_DOMAIN_NAME,
        "iat": int(datetime.datetime.now().timestamp()),
        "remember": True,
        "type": "login_credential"
    }

    signed = sign(token)

    user_data = generate_user_dict(user=new_user, for_oneself=True)

    return jsonify({
        "msg": "Successful!",
        "user": user_data,
        "jwt": signed
    }), 200