from . import record_blueprint
from server_app.auth_tools import login_required
from data.model import *
from flask import jsonify, request, g
import datetime


@record_blueprint.route('/delete_record', methods=['DELETE'])
@login_required
def delete_record():
    """
    @api {post} /v1/record/delete_record 删除一条记录
    @apiVersion 1.0.0
    @apiName delete_record
    @apiGroup Records
    @apiParam {String}  type              (必要)    personal：个人出刀记录/team：公会状态记录
    @apiParam {int}     id                (必要)    出刀ID
    @apiDescription 删除一条记录。操作者必须是本人或管理员。


    @apiSuccess (回参) {String}           msg   为"Successful!"

    @apiErrorExample {json} 未提供参数
        HTTP/1.1 400 Bad Request
        {"msg": "Parameter is missing"}

    @apiErrorExample {json} 用户没有加入公会
        HTTP/1.1 403 Forbidden
        {"msg": "User is not in any group."}

    @apiErrorExample {json} 用户没有权限修改
        HTTP/1.1 417 Expectation Failed
        {"msg": "Permission Denied"}

    """
    user: User = g.user
    json = request.get_json(force=True)
    id_ = json.get('id', None)

    if not id_:
        return jsonify({"msg": "Parameter is missing"}), 400
    if not user.group_id:
        return jsonify({"msg": "User is not in any group."}), 403

    r = PersonalRecord.query.filter_by(id=id_, group_id=user.group_id).first()

    if r.user.id == user.id or user.role > 0:  # 有权限删除
        db.session.delete(r)
        deletion_history = DeletionHistory(deleted_date=datetime.datetime.now(),
                                           from_table='PersonalRecord',
                                           deleted_id=id_,
                                           group_id=user.group_id)
        db.session.add(deletion_history)
        db.session.commit()
    else:
        return jsonify({"msg": "Permission Denied"}), 417