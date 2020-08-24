from flask import request, jsonify, g
import datetime
from ..auth_tools import login_required
from data.model import *
from data.alchemy_encoder import AlchemyEncoder
import json as js
from . import record_blueprint
from .record_tools import make_new_team_record


@record_blueprint.route('/get_records', methods=['GET'])
@login_required
def get_records():
    """
    @api {post} /v1/record/get_records 获取XX记录列表
    @apiVersion 1.0.0
    @apiName get_records
    @apiGroup Records
    @apiParam {String}  type              (必要)    personal：个人出刀记录/team：公会状态记录/team_rank: 公会排名记录
    @apiParam {int}     limit             (可选)    多少条数据
    @apiParam {String}  page              (可选)    第几页(如果提供page则必须提供limit）(0为第一页）
    @apiParam {int}     start_date        (可选)    开始日期时间戳（秒）
    @apiParam {int}     end_date          (可选)    结束日期时间戳（秒）
    @apiParam {int}     last_updated      (可选)    在此时间之后更新的记录会被返回，deleted 项会记录在此时间之后删除的项。
    @apiDescription 返回公会中的出刀/状态/排名历史。


    @apiSuccess (回参) {String}           msg   为"Successful!"
    @apiSuccess (回参) {List[Dictionary]} data  相应的Records，具体内容参照PersonalRecord/TeamRecord表

    @apiSuccessExample {json} 没有更新
        HTTP/1.1 304 Not Modified
        # 注：只有在指定了last_updated 之后才会返回这一选项

    @apiErrorExample {json} 没有提供正确type
        HTTP/1.1 416 Whatever
        {"msg": "Illegal type parameter."}

    @apiErrorExample {json} 用户没有加入公会
        HTTP/1.1 403 Forbidden
        {"msg": "User is not in any group."}

    @apiErrorExample {json} 用户的公会不存在
        HTTP/1.1 417 Expectation Failed
        {"msg": "User's group not found."}

    """
    user: User = g.user
    limit: str = request.args.get('limit', '')
    page: str = request.args.get('page', '')
    start_date: str = request.args.get('start_date', '')
    end_date: str = request.args.get('end_date', '')
    type_: str = request.args.get('type', 'personal')
    last_updated = request.args.get('last_updated', '')

    current_time = int(datetime.datetime.timestamp(datetime.datetime.now()))

    if user.group_id == -1:
        return jsonify({"msg": "User is not in any group."}), 403

    group: Group = user.group
    if not group:
        return jsonify({"msg": "User's group not found."}), 417

    deleted = DeletionHistory.query.filter_by(group_id=group.id)

    if type_ == 'team':
        records = group.team_record.order_by(TeamRecord.last_modified.desc()).first()
        if not records:
            make_new_team_record(group_id=group.id)
            records = group.team_record.order_by(TeamRecord.last_modified.desc()).first()
        return js.dumps({
            "data": records
        }, cls=AlchemyEncoder), 200
    elif type_ == 'personal':
        records = group.personal_records
        date_type = PersonalRecord.detail_date
        last_modified = PersonalRecord.last_modified
        deleted = deleted.filter(DeletionHistory.from_table == 'PersonalRecord')
    elif type_ == 'team_rank':
        records = group.team_ranks
        date_type = TeamRank.record_date
        last_modified = TeamRank.record_date
        deleted = deleted.filter(DeletionHistory.from_table == 'TeamRank')
    else:
        return jsonify({'msg': 'Illegal type parameter'}), 416
    if start_date.isdigit() and start_date != -1:
        start = datetime.datetime.fromtimestamp(int(start_date))
        records = records.filter(date_type >= start)
    if end_date.isdigit() and end_date != -1:
        end = datetime.datetime.fromtimestamp(int(end_date))
        records = records.filter(date_type <= end)
    if limit.isdigit() and limit != 0:
        records = records.limit(int(limit))
        if page.isdigit() and page != 0:
            records = records.offset(int(limit) * int(page))
    if last_updated.isdigit():
        last_updated_date = datetime.datetime.fromtimestamp(int(last_updated))
        records = records.filter(last_modified >= last_updated_date)
        deleted = deleted.filter(DeletionHistory.deleted_date >= last_updated_date)

    records_list: dict = records.order_by(date_type.desc()).all()
    deleted = deleted.all()

    # db.session.commit()

    if last_updated.isdigit() and not records_list and not deleted:
        return '', 304  # 如果没有更新
    if not deleted:
        deleted = dict()
    if not records_list:
        records_list = dict()

    return js.dumps({
        "time": current_time,
        "data": records_list,
        "deleted": deleted
    }, cls=AlchemyEncoder), 200


@record_blueprint.route('/get_current_team_record', methods=['GET'])
@login_required
def get_current_team_record():
    """
    @api {post} /v1/record/get_current_team_record 获取公会boss状态
    @apiVersion 1.0.0
    @apiName get_current_team_record
    @apiGroup Records
    @apiDescription 获取公会boss状态


    @apiSuccess (回参) {String}           msg   为"Successful!"
    @apiSuccess (回参) {Dictionary}       data  相应的TeamRecord，具体内容参照TeamRecord表

    @apiErrorExample {json} 用户没有加入公会
        HTTP/1.1 403 Forbidden
        {"msg": "User is not in any group."}

    @apiErrorExample {json} 用户的公会不存在
        HTTP/1.1 417 Expectation Failed
        {"msg": "User's group not found.", "code": 403}

    """
    user: User = g.user

    if user.group_id == -1:
        return jsonify({"msg": "User is not in any group."}), 403

    group: Group = user.group
    if not group:
        return jsonify({"msg": "User's group not found."}), 417

    current_record = TeamRecord.query.filter(TeamRecord.group_id == user.group_id)\
        .order_by(TeamRecord.last_modified.desc()).first()
    if not current_record:
        current_record = make_new_team_record(group_id=group.id)

    return js.dumps({
        "data": current_record
    }, cls=AlchemyEncoder), 200

