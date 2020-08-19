from flask import request, jsonify
import datetime
from server_app.auth_tools import is_username_exist, get_user_with, sign, verify_otp, is_email_exist, generate_user_dict
import bcrypt
from config import Config
from data.model import *
from server_app.email_tools import is_valid_email
from . import auth_blueprint


@auth_blueprint.route('/sign_up', methods=['POST'])
def sign_up():
    """
    @api {post} /v1/auth/sign_up 注册
    @apiVersion 1.0.0
    @apiName sign_up
    @apiGroup Users
    @apiParam {String}  username   (必须)    用户名（3字以上）
    @apiParam {String}  password   (必须)    密码（8字以上）
    @apiParam {String}  email      (必须)    邮箱
    @apiParam {String}  otp        (必须)    邮箱验证码(请通过/v1/email/request_otp请求发送OTP)
    @apiParam {String}  phone      (可选)    手机号
    @apiParamExample {json} Request-Example:
        {
            "username": "someuser",
            "password": "12345678",
            "email": "a@ddavid.net",
            "phone": "13312341234",
            "otp": "123123"
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
                "group_id": 233  // This is optional.
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
        username = json["username"]  # 要求3字以上
        password = json["password"]  # 要求8字以上
        otp = json['otp']
        email = json['email']
        phone = json.get('phone', '')
        nickname = json.get('nickname', username)
    except KeyError:
        return jsonify({"msg": "Missing parameter"}), 400
    if len(username) < 3 or len(password) < 8:
        return jsonify({"msg": "Username or password is too short"}), 422
    if is_username_exist(username):
        return jsonify({"msg": "User Exists"}), 409
    if is_email_exist(email):
        return jsonify({"msg": "Email Exists"}), 410
    if not verify_otp(email, otp):
        return jsonify({"msg": "OTP is invalid", "code": 104}), 400
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


@auth_blueprint.route('/login', methods=['POST'])
def login():
    """
    @api {post} /v1/auth/login 登录
    @apiVersion 1.0.0
    @apiName login
    @apiGroup Users
    @apiParam {String}  username   (可选)    用户名
    @apiParam {String}  email      (可选)    邮箱
    @apiParam {String}  phone      (可选)    手机号
    @apiParam {String}  password   (必须)    密码
    @apiParamExample {json} Request-Example:
        {
            "username": "someuser",
            "password": "12345678"
        }
    @apiDescription 可以通过用户名，邮箱或手机号登录。登陆时只需要提供一项。

    @apiSuccess (回参) {String} msg  为"Successful!"
    @apiSuccess (回参) {String} jwt  jwt token，应当放入auth header
    @apiSuccess (回参) {String} user  user信息，具体见样例
    @apiSuccessExample {json} 成功样例
        { "msg": "Successful!",
         "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
         "user": {
                "username": "foo",
                "nickname": "bar",
                "id": 233,
                "role": 2,
                "email": "example@example.com",
                "group_id": 233  // This is optional.
            }
         }

    @apiErrorExample {json} 未提供用户名或密码
        HTTP/1.1 400 Bad Request
        {"msg": "Username or Password is missing"}

    @apiErrorExample {json} 用户不存在
        HTTP/1.1 417 Expectation Failed
        {"msg": "User does not exist", "code": 202}

    @apiErrorExample {json} 密码或用户名错误
        HTTP/1.1 403 Forbidden
        {"msg": "Username or Password is incorrect", "code": 203}

    """
    try:
        json: dict = request.get_json(force=True)
        username = json.get('username', None)
        email = json.get('email', None)
        phone = json.get('phone', None)
        password: str = json["password"]
    except KeyError:
        return jsonify({"msg": "Username or Password is missing"}), 400
    user: User = get_user_with(username=username)
    if user is None:
        user = get_user_with(email=email)
    if user is None:
        user = get_user_with(phone=phone)
    if user is None:
        return jsonify({"msg": "User does not exist"}), 417
    hash_pwd: str = user.password
    if not bcrypt.checkpw(password.encode(), hash_pwd.encode()):
        return jsonify({"msg": "Username or Password is incorrect"}), 403
    user_id: int = user.id
    token = {
        "sub": user_id,
        "iss": Config.DOMAIN_NAME,
        "aud": Config.FRONTEND_DOMAIN_NAME,
        "iat": int(datetime.datetime.now().timestamp()),
        "remember": True,
        "type": "login_credential"
    }
    signed = sign(token)

    user_data = generate_user_dict(user, True)

    return jsonify({
        "msg": "successful",
        "jwt": signed,
        "user": user_data
    }), 200


@auth_blueprint.route('/forget_password')
def forget_password():
    """
        @api {post} /v1/auth/forget_password 忘记密码
        @apiVersion 1.0.0
        @apiName forget_password
        @apiGroup Users
        @apiParam {String}  email           (必须)    邮箱
        @apiParam {String}  otp             (必须)    邮箱验证码(请通过/v1/email/request_otp请求发送OTP)
        @apiParam {String}  password        (必须)    新密码

        @apiParamExample {json} Request-Example:
            {
                "email": "example@example.com",
                "otp": "123123",
                "password": "password"
            }

        @apiSuccess (回参) {String} msg  为"Successful!"
        @apiSuccess (回参) {String} id   用户id

        @apiErrorExample {json} 未提供必要参数
            HTTP/1.1 400 Bad Request
            {"msg": "Missing parameter"}

        @apiErrorExample {json} 邮箱验证码错误
            HTTP/1.1 401 Unauthorized
            {"msg": "OTP is invalid."}

        @apiErrorExample {json} email格式不正确
            HTTP/1.1 406 Not Acceptable
            {"msg": "Invalid email address."}

        @apiErrorExample {json} 此邮箱没有关联任何账号
            HTTP/1.1 417 Expectation Failed
            {"msg": "There is no account associated with this email.", "code": 103}

        """
    try:
        json: dict = request.get_json(force=True)
        otp = json['otp']
        email = json['email']
        password = json['password']
    except KeyError:
        return jsonify({"msg": "Missing parameter"}), 400
    if not is_valid_email(email):
        return jsonify({"msg": "Invalid email address."}), 406

    user = get_user_with(email=email)
    if not is_email_exist(email) or not user:
        return jsonify({"msg": "There is no account associated with this email."}), 417
    if not verify_otp(email, otp):
        return jsonify({"msg": "OTP is invalid"}), 401

    user.password = bcrypt.hashpw(password, bcrypt.gensalt())
    db.session.commit()
    return jsonify({
        "msg": "Successful!"
    }), 200
