from data.model import PersonalRecord, TeamRecord
from config import Config


def damage_to_score(record: PersonalRecord) -> int:
    # 伤害转换分数计算，修正数值错误问题
    if record.boss_gen == 1:
        multiplier = [1.0, 1.0, 1.1, 1.1, 1.2]
    else:
        multiplier = [1.2, 1.2, 1.5, 1.7, 2.0]
    return int(int(record.damage) * multiplier[record.boss_gen-1])


def subtract_damage_from_group(record: PersonalRecord, team_record: TeamRecord):
    #  计算boss剩余血量
    damage = int(record.damage)
    if damage < team_record.boss_remaining_health:
        team_record.boss_remaining_health -= damage
    else:
        if team_record.current_boss_order < 5:
            team_record.current_boss_order += 1
        else:
            team_record.current_boss_order = 1
            team_record.current_boss_gen += 1
        team_record.boss_remaining_health = Config.BOSS_HEALTH[team_record.current_boss_order-1]
