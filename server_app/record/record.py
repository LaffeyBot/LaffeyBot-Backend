from flask import request, jsonify, g
import datetime
from ..auth_tools import login_required
from data.model import *
from ..group_tools import get_group_of_user
from .record_tools import damage_to_score, subtract_damage_from_group
from data.alchemy_encoder import AlchemyEncoder
import json as js
from . import record_blueprint
from config import Config
import time


@record_blueprint.route('/add_record', methods=['POST'])
@login_required
def add_record():
    """
    @api {post} /v1/record/add_record 出刀
    @apiVersion 1.0.0
    @apiName add_record
    @apiGroup Records
    @apiParam {String}  damage       (必须)    伤害
    @apiParam {String}  type         (必须)    出刀类型(normal:普通刀/last:尾刀/compensation:补偿刀)
    @apiParam {String}  user_id      (可选)    出刀用户ID，如果不提供则默认为当前用户自己出刀
    @apiParam {String}  boss_gen     (可选)    boss周目（如果没有则为当前boss）
    @apiParam {String}  boss_order   (可选)    第几个boss（如果没有则为当前boss）

    @apiSuccess (回参) {String}     msg   为"Successful!"
    @apiSuccess (回参) {Dictionary} record  添加的Record，具体内容参照Records表
    @apiSuccess (回参) {Dictionary} team_record   更新后的当前公会信息，具体内容参照TeamRecord表

    @apiErrorExample {json} 参数不存在
        HTTP/1.1 400 Bad Request
        {"msg": "Parameter is missing"}

    @apiErrorExample {json} 用户没有加入公会
        HTTP/1.1 403 Forbidden
        {"msg": "User is not in any group."}

    @apiErrorExample {json} 用户的公会不存在
        HTTP/1.1 417 Expectation Failed
        {"msg": "User's group not found."}

    @apiErrorExample {json} 用户的公会没有相应用户
        HTTP/1.1 412 Precondition Failed
        {"msg": "Group doesn't have a user with this ID."}

    """
    user: User = g.user

    json = request.get_json(force=True)
    damage = json.get('damage', None)
    type_ = json.get('type', None)
    boss_gen = json.get('boss_gen', None)
    boss_order = json.get('boss_order', None)
    user_id = json.get('user_id', None)

    if not damage or not type_:
        return jsonify({"msg": "Parameter is missing"}), 400
    if user.group_id is None:
        return jsonify({"msg": "User is not in any group."}), 403

    group: Group = user.group
    if not group:
        return jsonify({"msg": "User's group not found."}), 417
    team_record: TeamRecord = group.team_records\
        .order_by(TeamRecord.detail_date.desc()).limit(1).first()
    if not team_record:
        current_epoch: TeamBattleEpoch = TeamBattleEpoch.query\
            .order_by(TeamBattleEpoch.end_date.desc()).limit(1).first()
        team_record = TeamRecord(detail_date=datetime.datetime.now(),
                                 epoch_id=current_epoch.id,
                                 group_id=group.id,
                                 current_boss_gen=1,
                                 current_boss_order=1,
                                 boss_remaining_health=Config.BOSS_HEALTH[0],
                                 last_modified=datetime.datetime.now())
        db.session.add(team_record)
        db.session.commit()
        db.session.refresh(team_record)
    else:
        team_record.last_modified = datetime.datetime.now()

    if user_id:
        user_of_attack = User.query.filter_by(id=user_id, group_id=user.group_id).first()
        if not user_of_attack:
            return jsonify({"msg": "Group doesn't have a user with this ID."}), 412
        user = user_of_attack
    if not boss_gen:
        boss_gen = team_record.current_boss_gen
    if not boss_order:
        boss_order = team_record.current_boss_order

    added_record: PersonalRecord = PersonalRecord(group_id=user.group_id,
                                                  boss_gen=boss_gen,
                                                  boss_order=boss_order,
                                                  damage=int(damage),
                                                  user_id=user.id,
                                                  nickname=user.nickname,
                                                  detail_date=datetime.datetime.now(),
                                                  type=type_,
                                                  last_modified=datetime.datetime.now(),
                                                  epoch_id=team_record.epoch_id)
    added_record.score = damage_to_score(record=added_record)
    subtract_damage_from_group(record=added_record, team_record=team_record)
    db.session.add(added_record)

    db.session.commit()
    db.session.refresh(added_record)
    db.session.refresh(team_record)
    return_data = {
        "msg": "Successful!",
        "record": added_record,
        "team_record": team_record
    }
    return js.dumps(return_data, cls=AlchemyEncoder), 200


@record_blueprint.route('/get_records', methods=['GET'])
@login_required
def get_records():
    """
    @api {post} /v1/record/get_records 获取出刀列表
    @apiVersion 1.0.0
    @apiName get_records
    @apiGroup Records
    @apiParam {String}  type              (必要)    personal：个人出刀记录/team：公会状态记录
    @apiParam {int}     limit             (可选)    多少条数据
    @apiParam {String}  page              (可选)    第几页(如果提供page则必须提供limit）(0为第一页）
    @apiParam {int}     start_date        (可选)    开始日期时间戳（秒）
    @apiParam {int}     end_date          (可选)    结束日期时间戳（秒）
    @apiDescription 返回公会中的出刀列表，如果无参数则返回所有出刀记录。


    @apiSuccess (回参) {String}           msg   为"Successful!"
    @apiSuccess (回参) {List[Dictionary]} data  相应的Records，具体内容参照PersonalRecord/TeamRecord表

    @apiErrorExample {json} 用户没有加入公会
        HTTP/1.1 403 Forbidden
        {"msg": "User is not in any group."}

    @apiErrorExample {json} 用户的公会不存在
        HTTP/1.1 417 Expectation Failed
        {"msg": "User's group not found.", "code": 403}

    """
    user: User = g.user
    limit: str = request.args.get('limit', '')
    page: str = request.args.get('page', '')
    start_date: str = request.args.get('start_date', '')
    end_date: str = request.args.get('end_date', '')
    type_: str = request.args.get('type', 'personal')
    last_updated = request.args.get('last_updated', '')

    current_time = datetime.datetime.timestamp(datetime.datetime.now())

    if user.group_id == -1:
        return jsonify({"msg": "User is not in any group."}), 403

    group: Group = user.group
    if not group:
        return jsonify({"msg": "User's group not found."}), 417

    if type_ == 'team':
        records = group.team_records
        date_type = TeamRecord.detail_date
        last_modified = TeamRecord.last_modified
    else:
        records = group.records
        date_type = PersonalRecord.detail_date
        last_modified = PersonalRecord.last_modified
    print(records)
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

    records_list: dict = records.order_by(date_type.desc()).all()

    db.session.commit()
    return js.dumps({
        "time": int(current_time),
        "data": records_list
    }, cls=AlchemyEncoder), 200


@record_blueprint.route('/modify_record', methods=['POST'])
@login_required
def modify_record():
    """
    @api {post} /v1/record/modify_record 改刀
    @apiVersion 1.0.0
    @apiName modify_record
    @apiGroup Records
    @apiParam {String}  id           (必须)    需要更改的出刀ID
    @apiParam {String}  damage       (可选)    新伤害（不提供则不修改）
    @apiParam {String}  type         (可选)    出刀类型(normal:普通刀/last:尾刀/compensation:补偿刀)（不提供则不修改）
    @apiParam {String}  boss_gen     (可选)    boss周目（不提供则不修改）
    @apiParam {String}  boss_order   (可选)    第几个boss（不提供则不修改）
    @apiDescription 只有出刀的人和管理员可以改刀。


    @apiSuccess (回参) {String}     msg   为"Successful!"
    @apiSuccess (回参) {Dictionary} record  更新后的Record
    @apiSuccess (回参) {Dictionary} group   更新后的当前公会信息，具体内容参照Groups表

    @apiErrorExample {json} 未提供参数
        HTTP/1.1 400 Bad Request
        {"msg": "Parameter is missing"}

    @apiErrorExample {json} 用户没有加入公会
        HTTP/1.1 403 Forbidden
        {"msg": "User is not in any group."}

    @apiErrorExample {json} 用户的公会不存在
        HTTP/1.1 403 Forbidden
        {"msg": "User's group not found."}

    @apiErrorExample {json} 用户的公会没有相应用户
        HTTP/1.1 403 Forbidden
        {"msg": "Group doesn't have a user with this ID.", "code": 404}

    @apiErrorExample {json} 用户没有权限修改
        HTTP/1.1 403 Forbidden
        {"msg": "Permission Denied", "code": 405}

    """
