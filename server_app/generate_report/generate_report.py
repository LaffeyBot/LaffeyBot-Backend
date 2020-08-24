from . import generate_report_blueprint
from server_app.auth_tools import login_required, sign, get_user_with
from flask import g, jsonify, request, send_file
from .generate_report_tool import make_xlsx_for_group
from config import Config
import jwt
import datetime


@generate_report_blueprint.route('/generate', methods=['GET'])
@login_required
def generate():
    """
    @api {post} /v1/generate_report/generate 生成xlsx出刀报告
    @apiVersion 1.0.0
    @apiName generate
    @apiGroup GenerateReport

    @apiSuccess (回参) {String} msg   为"Successful!"
    @apiSuccess (回参) {String} url   获取报告的URL
    @apiSuccessExample {json} 成功样例
        HTTP/1.1 200 OK
        {
            "msg": "Successful!",
            "url": "https://dd.works:5555/v1/generate_report/download?auth=xxx",
        }
    """
    group = g.user.group
    if not group:
        return jsonify({'msg': 'User does not have a group'})
    auth_dict = {
        'user_id': g.user.id,
        "iss": Config.DOMAIN_NAME,
        "aud": Config.FRONTEND_DOMAIN_NAME,
        "iat": int(datetime.datetime.now().timestamp()),
    }
    signed = sign(auth_dict)
    print(signed)
    return jsonify({
        "msg": "Successful!",
        "url": Config.SELF_URL + '/v1/generate_report/download?auth=' + signed
    })


@generate_report_blueprint.route('/download', methods=['GET'])
def report_download():
    """
    @api {post} /v1/generate_report/download 下载通过generate生成的报告
    @apiVersion 1.0.0
    @apiName report_download
    @apiGroup GenerateReport

    @apiSuccess (回参) {File}   生成的xlsx文件
    """
    auth_header = request.args.get('auth', None)
    print(auth_header)
    if not auth_header:
        return jsonify({'msg': 'You must provide a auth header.'})
    try:
        decode_jwt = jwt.decode(auth_header,
                                Config.SECRET_KEY,
                                algorithms=['HS256'],
                                audience=Config.DOMAIN_NAME)
    except jwt.exceptions.InvalidTokenError:
        return jsonify({"msg": "Auth sign does not verify"}), 401
    user_id = decode_jwt.get('user_id', None)
    user = get_user_with(id_=user_id)
    if not user:
        return jsonify({"msg": "User not found."}), 402
    group = user.group
    if not group:
        return jsonify({'msg': 'User does not have a group'})
    make_xlsx_for_group(group_id=group.id)
    return send_file(f'temp\\group-{group.id}-report.xlsx', as_attachment=True)
