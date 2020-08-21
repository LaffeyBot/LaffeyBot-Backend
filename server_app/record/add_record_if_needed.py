from flask import request, jsonify, g
import datetime
from ..auth_tools import login_required
from data.model import *
from .record_tools import damage_to_score, subtract_damage_from_group
from . import record_blueprint
from config import Config
from server_app.push_notification_tools import push_ios
from datetime import timedelta
from server_app.qq_tools import send_message_to_qq


@record_blueprint.route('/add_record_if_needed', methods=['POST'])
@login_required
def add_record_if_needed():
    """
    @api {post} /v1/record/add_record_if_needed 出刀(仅供OCR使用）
    @apiVersion 1.0.0
    @apiName add_record_if_needed
    @apiGroup Records
    @apiParam {String}  damage       (必须)    伤害
    @apiParam {String}  nickname     (必须)    出刀用户游戏名/nickname
    @apiParam {String}  group_id     (必须)    公会ID

    @apiSuccess (回参) {String}     msg        为"Successful!"

    @apiErrorExample {json} 参数不存在
        HTTP/1.1 400 Bad Request
        {"msg": "Parameter is missing"}

    @apiErrorExample {json} 用户不在任何公会
        HTTP/1.1 403 Forbidden
        {"msg": "User is not in any group."}

    """
    user: User = g.user

    json = request.get_json(force=True)
    damage = json.get('damage', None)
    nickname = json.get('nickname', None)

    if not damage or not nickname:
        return jsonify({"msg": "Parameter is missing"}), 400
    if user.group_id is None:
        return jsonify({"msg": "User is not in any group."}), 403
    damage: int = int(damage)

    group: Group = user.group
    if not group:
        return jsonify({"msg": "User's group not found."}), 417
    team_record: TeamRecord = group.team_records \
        .order_by(TeamRecord.detail_date.desc()).limit(1).first()
    if not team_record:
        current_epoch: TeamBattleEpoch = TeamBattleEpoch.query \
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

    user_of_attack = User.query.filter_by(nickname=nickname, group_id=group.id).first()
    if not user_of_attack:
        return jsonify({"msg": "Group doesn't have a user with this name."}), 412
    start = datetime.datetime.now() - timedelta(days=1)
    existing_record = PersonalRecord.query.filter_by(real_damage=damage, group_id=group.id)\
        .filter(PersonalRecord.detail_date > start).first()
    if existing_record:
        return jsonify({"msg": "Already Recorded. "}), 200

    real_damage = damage
    if team_record.boss_remaining_health <= damage:
        type_ = 'last'
        damage = team_record.boss_remaining_health
    else:
        type_ = 'normal'  # OCR没有办法判断补偿刀

    added_record: PersonalRecord = PersonalRecord(group_id=user.group_id,
                                                  boss_gen=team_record.current_boss_gen,
                                                  boss_order=team_record.current_boss_order,
                                                  damage=damage,
                                                  real_damage=real_damage,
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

    user_name_list = []
    for user_obj in group.users:
        user_name_list.append(user_obj.username)
    damage_msg = user.nickname
    damage_msg += '对' + str(team_record.current_boss_order) + '王'
    damage_msg += '造成了' + str(added_record.damage) + '点伤害'
    if team_record.boss_remaining_health == Config.BOSS_HEALTH[team_record.current_boss_order - 1]:
        damage_msg += '并击破。'
    else:
        damage_msg += '。Boss 血量还剩' + str(team_record.boss_remaining_health) + '。'
    push_ios(user_name_list, '添加了新纪录', '', damage_msg)

    headers = dict(auth=request.headers.get('auth'))
    damage_msg = '通过OCR添加了新的记录喵！\n' + damage_msg
    send_message_to_qq(message=damage_msg, id_=group.group_chat_id, type_='group', header=headers)

    return jsonify({"msg": "Successful!"}), 200
