from flask import request, jsonify, g
import datetime
from ..auth_tools import login_required
from data.model import *
from .record_tools import damage_to_score, subtract_damage_from_group, make_new_team_record
from data.alchemy_encoder import AlchemyEncoder
import json as js
from . import record_blueprint
from config import Config
from server_app.push_notification_tools import push_ios
from server_app.qq_tools import send_message_to_qq


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
    @apiParam {String}  origin       (可选)    请求来源。例如「iOS 客户端」「Web 端」等
    @apiParam {String}  user_id      (可选)    出刀用户ID，如果不提供则默认为当前用户自己出刀
    @apiParam {String}  boss_gen     (可选)    boss周目（如果没有则为当前boss）
    @apiParam {String}  boss_order   (可选)    第几个boss（如果没有则为当前boss）

    @apiSuccess (回参) {String}     msg        为"Successful!"
    @apiSuccess (回参) {Dictionary} record     添加的Record，具体内容参照Records表
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
    origin = json.get('origin', None)

    if not type_:
        return jsonify({"msg": "Parameter is missing"}), 400
    if type_ != 'last' and not damage:
        return jsonify({"msg": "Parameter is missing"}), 400
    if user.group_id is None:
        return jsonify({"msg": "User is not in any group."}), 403
    if boss_gen:
        boss_gen = int(boss_gen)
    if boss_order:
        boss_order = int(boss_order)

    group: Group = user.group
    if not group:
        return jsonify({"msg": "User's group not found."}), 417
    team_record: TeamRecord = group.team_record \
        .order_by(TeamRecord.last_modified.desc()).first()
    if not team_record:
        team_record = make_new_team_record(group_id=group.id)
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

    if not damage:
        damage = team_record.boss_remaining_health

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

    user_name_list = []
    for user_obj in group.users:
        user_name_list.append(user_obj.username)
    content = user.nickname
    content += '对' + str(added_record.boss_order) + '王'
    content += '造成了' + str(added_record.damage) + '点伤害'
    if team_record.boss_remaining_health == Config.BOSS_HEALTH[team_record.current_boss_order - 1]:
        content += '并击破。'
    else:
        content += str(team_record.current_boss_order) + \
                   '王血量还剩' + str(team_record.boss_remaining_health) + '。'
    push_ios(user_name_list, '添加了新纪录', '', content)

    origin = origin if origin else '客户端'
    msg = '通过' + origin + '添加了新的记录喵！'
    msg += '\n' + content
    msg += '\n' + '当前为' + str(team_record.current_boss_gen) + '周目'

    if origin == "QQ":
        return_data = dict(message=msg, id=group.group_chat_id, type='group')
        return jsonify(return_data), 200
    else:
        headers = dict(auth=request.headers.get('auth'))
        send_message_to_qq(message=msg, id_=group.group_chat_id, type_='group', header=headers)
        return js.dumps(return_data, cls=AlchemyEncoder), 200


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

    @apiErrorExample {json} 没有修改任何信息
        HTTP/1.1 406 Not Acceptable
        {'msg': 'Must submit one optional option'}

    @apiErrorExample {json} 用户没有权限修改
        HTTP/1.1 417 Expectation Failed
        {"msg": "Permission Denied"}

    @apiErrorExample {json} 没有找到这一条记录
        HTTP/1.1 406 Gone
        {'msg': 'Record not found'}

    """
    user: User = g.user
    # 1.获取接收的json
    json = request.get_json(force=True)  # force参数作用是忽视请求类型，并强制解析为json
    id_ = json.get('id', None)
    damage = json.get('damage', None)
    type_ = json.get('type', None)
    boss_gen = json.get('boss_gen', None)
    boss_order = json.get('boss_order', None)
    # 2.参数处理
    if not user.group_id:
        return jsonify({"msg": "User is not in any group."}), 403
    if not id_:
        return jsonify({"msg": "Parameter is missing"}), 400
    if not (damage or type_ or boss_gen or boss_order):
        return jsonify({'msg': 'Must submit one optional option'}), 406
    # 3.判断是否有权限操作
    try:
        r = PersonalRecord.query.filter_by(id=id_, group_id=user.group_id).first()
        if not r:
            return jsonify({'msg': 'Record not found'}), 410
        # 3.1 判断是否是本人操作
        if r.user.id == user.id or user.role != 0:
            if damage:
                r.damage = damage
            if type_:
                r.type = type_
            if boss_order:
                r.boss_order = boss_order
            if boss_gen:
                r.boss_gen = boss_gen
            db.session.commit()
            return js.dumps({
                "team_record": r
            }, cls=AlchemyEncoder), 200
        else:
            return jsonify({"msg": "Permission Denied"}), 417
    except Exception as e:
        db.session.rollback()
        print(e)
