from data.model import Records, Groups
from config import Config


def damage_to_score(record: Records) -> int:
    if record.boss_gen == 1:
        multiplier = [1.0, 1.0, 1.1, 1.2, 1.3]
    else:
        multiplier = [1.2, 1.3, 1.5, 1.7, 2.0]
    return int(int(record.damage) * multiplier[record.boss_gen-1])


def subtract_damage_from_group(record: Records, group: Groups):
    damage = int(record.damage)
    if damage < group.boss_remaining_health:
        group.boss_remaining_health -= damage
    else:
        if group.current_boss_order < 5:
            group.current_boss_order += 1
        else:
            group.current_boss_order = 1
            group.current_boss_gen += 1
        group.boss_remaining_health = Config.BOSS_HEALTH[group.current_boss_order-1]