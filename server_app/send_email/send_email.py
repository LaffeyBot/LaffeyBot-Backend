from flask import Blueprint, request, jsonify
import datetime
from server_app.auth_tools import is_email_exist
import bcrypt
from server_app.email_tools import is_valid_email, send_email_to
from server_app.auth_tools import generate_otp, verify_otp

email_blueprint = Blueprint(
    "email_v1",
    __name__,
    url_prefix='/v1/email'
)


@email_blueprint.route('/request_otp', methods=['POST'])
def request_otp():
    """
    @api {post} /v1/email/request_otp 发一次性密码至邮箱
    @apiVersion 1.0.0
    @apiName request_email
    @apiGroup Emails
    @apiParam {String}  email   (必须)    邮箱
    @apiParam {String}  for             (可选)    用途（可选: sign-up/reset-password/others）
    @apiParamExample {json} Request-Example:
        {
            email_address: "example@example.com"
        }

    @apiSuccess (回参) {String} msg  为"Successful!"
    @apiDescription 每个OTP在五分钟内有效。

    @apiErrorExample {json} 未提供email或用途
        HTTP/1.1 400 Bad Request
        {"msg": "Missing parameter", "code": 101}

    @apiErrorExample {json} email格式不正确
        HTTP/1.1 400 Bad Request
        {"msg": "Invalid email address.", "code": 501}

    @apiErrorExample {json} 此邮箱没有关联任何账号
            HTTP/1.1 404 Not Found
            {"msg": "There is no account associated with this email.", "code": 103}

    """
    try:
        json: dict = request.get_json(force=True)
        email_address: str = json['email']
        print(email_address)
        for_: str = json.get('for', 'others')
    except KeyError:
        return jsonify({"msg": "Missing parameter", "code": 101}), 400
    if not is_valid_email(email_address):
        return jsonify({"msg": "Invalid email address.", "code": 501}), 400
    otp = generate_otp(email_address)
    email_title = '[Laffeybot] 您的验证码 / Your One-time Passcode'
    email_content = '指挥官，\n'
    if for_ == 'sign-up':
        email_content += '    欢迎注册LaffeyBot！\n'
    elif for_ == 'reset-password':
        if not is_email_exist(email_address):
            return jsonify({"msg": "There is no account associated with this email.", "code": 103}), 404
        email_content += '  您正在重设密码。\n'
    email_content += '您的验证码为: ' + otp + '\n'
    email_content += '验证码五分钟内有效。祝指挥官使用愉快喵！'
    send_email_to(email_address, email_title, email_content)

    return jsonify({
        "msg": "Successful!"
    }), 200


@email_blueprint.route('/validate_otp', methods=['POST'])
def validate_otp():
    """
    @api {post} /v1/email/validate_otp 验证一次性密码
    @apiVersion 1.0.0
    @apiName validate_otp
    @apiGroup Emails
    @apiParam {String}  email           (必须)    来源邮箱
    @apiParam {String}  otp             (必须)    一次性密码
    @apiParamExample {json} Request-Example:
        {
            email_address: "example@example.com",
            otp: "234324"
        }

    @apiSuccess (回参) {Boolean} result  验证码是否有效
    @apiDescription 每个OTP在五分钟内有效。

    @apiErrorExample {json} 未提供email或otp
        HTTP/1.1 400 Bad Request
        {"msg": "Missing parameter", "code": 101}

    @apiErrorExample {json} email格式不正确
        HTTP/1.1 400 Bad Request
        {"msg": "Invalid email address.", "code": 501}

    """
    try:
        json: dict = request.get_json(force=True)
        email_address: str = json['email']
        otp: str = json['otp']
    except KeyError:
        return jsonify({"msg": "Missing parameter", "code": 101}), 400
    if not is_valid_email(email_address):
        return jsonify({"msg": "Invalid email address.", "code": 501}), 400
    otp_is_valid: bool = verify_otp(email_address, otp)

    return jsonify({
        "result": otp_is_valid
    }), 200
