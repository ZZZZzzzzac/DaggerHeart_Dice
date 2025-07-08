import random

def roll_dice(num_dice, num_sides, modifier=0):
    """
    模拟掷骰子。
    :param num_dice: 骰子数量
    :param num_sides: 骰子面数
    :param modifier: 调整值
    :return: 掷骰结果
    """
    return sum(random.randint(1, num_sides) for _ in range(num_dice)) + modifier

def simulate_attack(attack_modifier, enemy_defense, damage_roll_func, num_simulations=10000):
    """
    通过蒙特卡洛模拟计算命中概率和平均伤害。

    :param attack_modifier: 玩家的攻击调整值 (N)
    :param enemy_defense: 敌人的防御值
    :param damage_roll_func: 一个用于计算伤害的函数
    :param num_simulations: 模拟次数
    :return: (命中概率, 平均伤害)
    """
    hits = 0
    total_damage = 0

    for _ in range(num_simulations):
        # 1. 掷2d12 + N 来判断是否命中
        attack_roll = roll_dice(2, 12, attack_modifier)

        # 2. 如果攻击掷骰大于敌人防御，则命中
        if attack_roll > enemy_defense:
            hits += 1
            # 3. 计算伤害
            damage = damage_roll_func()
            total_damage += damage

    hit_probability = hits / num_simulations
    average_damage = total_damage / num_simulations if num_simulations > 0 else 0
    
    # 如果考虑暴击等情况，平均伤害需要除以命中次数而非总模拟次数
    # 这里我们计算的是每次攻击的伤害期望，所以除以总次数
    # average_damage_on_hit = total_damage / hits if hits > 0 else 0

    return hit_probability, average_damage

if __name__ == "__main__":
    # --- 参数配置 ---
    # 玩家攻击调整值 (N)
    PLAYER_ATTACK_MODIFIER = 5
    # 敌人防御值
    ENEMY_DEFENSE = 15
    # 模拟次数
    NUM_SIMULATIONS = 100000

    # 定义伤害掷骰函数，可以根据需要随意修改
    # 示例: 2d8 + 4
    def example_damage_roll():
        return roll_dice(2, 8, 4)

    # --- 执行模拟 ---
    hit_prob, avg_dmg = simulate_attack(
        PLAYER_ATTACK_MODIFIER,
        ENEMY_DEFENSE,
        example_damage_roll,
        NUM_SIMULATIONS
    )

    # --- 输出结果 ---
    print(f"模拟次数: {NUM_SIMULATIONS}")
    print(f"玩家攻击调整值: {PLAYER_ATTACK_MODIFIER}")
    print(f"敌人防御: {ENEMY_DEFENSE}")
    print(f"伤害骰: 2d8+4")
    print("-" * 30)
    print(f"命中概率: {hit_prob:.2%}")
    print(f"伤害期望 (每次攻击): {avg_dmg:.2f}")
