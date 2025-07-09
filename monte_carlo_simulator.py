import random
from types import SimpleNamespace
import pandas as pd
from tabulate import tabulate

def roll_dice(num_dice, num_sides, modifier=0):
    """模拟掷骰子并返回总和。"""
    return sum(random.randint(1, num_sides) for _ in range(num_dice)) + modifier

# --- Action Functions: 每个函数代表一种武器或攻击模式的完整回合逻辑 ---

def simple_attack_action(state, attacker, defender, current_round=0):
    """动作: 基础单体攻击，无任何特性。"""
    attack_roll = roll_dice(2, 12, attacker.attack_modifier)
    if attack_roll >= defender.defense:
        return attacker.base_damage_roll(), 1
    return 0, 0

def long_sword_token_action(state, attacker, defender, current_round=0):
    """动作: 太刀 - 见切。通过Token系统获得伤害加成。"""
    tokens = state.get('tokens', 0)
    attack_roll = roll_dice(2, 12, attacker.attack_modifier)
    
    if attack_roll >= defender.defense:
        # 命中: 获得一个Token，上限为3
        tokens = min(tokens + 1, 3)
        state['tokens'] = tokens
        bonus_damage = tokens * 4
        damage = attacker.base_damage_roll() + bonus_damage
        return damage, 1
    else:
        # 未命中: 失去一个Token，下限为0
        tokens = max(tokens - 1, 0)
        state['tokens'] = tokens
        return 0, 0

def form_switching_action(state, attacker, defender, current_round=0):
    """动作: 成功攻击N次后切换形态，在形态内获得命中和伤害加成。"""
    # 检查并更新激活的形态
    if state.get('form_active', False):
        state['form_attacks_remaining'] -= 1
        if state['form_attacks_remaining'] <= 0:
            state['form_active'] = False
            state.pop('form_attacks_remaining', None)

    # 计算动态攻击调整值
    current_attack_modifier = attacker.attack_modifier
    if state.get('form_active', False):
        current_attack_modifier += attacker.form_attack_bonus

    # 执行攻击
    attack_roll = roll_dice(2, 12, current_attack_modifier)
    if attack_roll >= defender.defense:
        bonus_damage = attacker.form_damage_bonus if state.get('form_active', False) else 0
        damage = attacker.base_damage_roll() + bonus_damage
        
        # 如果形态未激活，则累积命中次数以触发
        if not state.get('form_active', False):
            state['successful_attacks_total'] = state.get('successful_attacks_total', 0) + 1
            if state['successful_attacks_total'] >= attacker.form_switch_threshold:
                state['form_active'] = True
                state['form_attacks_remaining'] = attacker.form_duration
                state['successful_attacks_total'] = 0
        return damage, 1
    else:
        return 0, 0

def charge_blade_action(state, attacker, defender, current_round=0):
    """动作: 盾斧。积攒Token，然后通过“超解”释放巨大伤害。"""
    tokens = state.get('tokens', 0)

    # 如果Token达到阈值，或在第10回合且有Token，则执行“超解”
    if (tokens >= attacker.discharge_threshold) or (current_round == 10 and tokens > 0):
        state['tokens'] = 0 # 消耗所有Token
        attack_roll = roll_dice(2, 12, attacker.attack_modifier)
        if attack_roll >= defender.defense:
            # 超解命中
            bonus_damage = ((2*tokens) ** 2) 
            single_target_damage = attacker.base_damage_roll() 
            total_damage = (single_target_damage + bonus_damage) * attacker.num_aoe_targets
            return total_damage, attacker.num_aoe_targets
        else:
            # 超解未命中
            return 0, 0
    
    # --- 如果未达到阈值，则执行普通攻击以积攒Token ---
    attack_roll = roll_dice(2, 12, attacker.attack_modifier)
    if attack_roll >= defender.defense:
        # 命中，获得Token
        state['tokens'] = tokens + 1
        return attacker.base_damage_roll(), 1
    else:
        # 未命中
        return 0, 0

def multi_attack_action(state, attacker, defender, current_round=0):
    """动作: 每回合进行多次独立的攻击。"""
    total_damage_this_turn = 0
    total_hits_this_turn = 0
    # 在一回合内循环执行多次攻击
    for _ in range(attacker.num_attacks):
        attack_roll = roll_dice(2, 12, attacker.attack_modifier)
        if attack_roll >= defender.defense:
            total_hits_this_turn += 1
            total_damage_this_turn += attacker.base_damage_roll()
    return total_damage_this_turn, total_hits_this_turn

def wyvernstake_action(state, attacker, defender, current_round=0):
    """动作: 起爆龙杭。插入动作是一次攻击，成功后开始倒计时。"""
    
    # 如果龙杭未激活，则本回合的动作是“尝试插入”
    if not state.get('stake_active', False):
        attack_roll = roll_dice(2, 12, attacker.attack_modifier)
        if attack_roll >= defender.defense:
            # 插入成功: 造成伤害并激活状态
            state['stake_active'] = True
            state['countdown'] = 3
            state['damage_accumulated'] = 0
            return attacker.base_damage_roll(), 1
        else:
            # 插入失败
            return 0, 0

    # --- 如果龙杭已激活，则执行常规攻击并更新状态 ---
    damage_this_turn, hits_this_turn = 0, 0
    
    # 1. 执行本回合的常规攻击
    attack_roll = roll_dice(2, 12, attacker.attack_modifier)
    if attack_roll >= defender.defense:
        hits_this_turn = 1
        damage = attacker.base_damage_roll()
        damage_this_turn += damage
        # 累积伤害用于最终引爆
        state['damage_accumulated'] += damage
    
    # 2. 更新倒计时
    state['countdown'] -= 1

    # 3. 检查是否在本回合结束后引爆
    if state['countdown'] <= 0:
        explosion_damage = (state.get('damage_accumulated', 0))
        damage_this_turn += explosion_damage
        # 重置状态，以便下回合可以重新插入
        state['stake_active'] = False
        state.pop('damage_accumulated', None)
        state.pop('countdown', None)
    
    return damage_this_turn, hits_this_turn
def insect_glaive_action(state, attacker, defender, current_round=0):
    """动作: 虫棍。基于Token数量获得不同增益。"""
    tokens = state.get('tokens', 0)
    
    # 根据Token数量计算动态加成
    current_attack_modifier = attacker.attack_modifier
    bonus_damage = 0
    if tokens >= 1:
        current_attack_modifier += 2
    if tokens >= 2:
        bonus_damage += 4
    # if tokens >= 3:
        # bonus_damage += 2 # 在2-token的基础上再+2，总共+4

    # 执行攻击
    attack_roll = roll_dice(2, 12, current_attack_modifier)
    
    if attack_roll >= defender.defense:
        # --- 命中 ---
        # 增加Token，上限为3
        state['tokens'] = min(tokens + 1, 3)
        damage = attacker.base_damage_roll() + bonus_damage
        return damage, 1
    else:
        # --- 未命中 ---
        # 减少Token，下限为0
        state['tokens'] = max(tokens - 1, 0)
        return 0, 0


def simple_aoe_action(state, attacker, defender, current_round=0):
    """动作: 简单的AoE攻击，一次判定，伤害应用到所有目标。"""
    attack_roll = roll_dice(2, 12, attacker.attack_modifier)
    if attack_roll >= defender.defense:
        damage = attacker.base_damage_roll() * attacker.num_aoe_targets
        hits = attacker.num_aoe_targets
        return damage, hits
    return 0, 0

def great_hammer_action(state, attacker, defender, current_round=0):
    """动作: 大锤。攻击3次后，敌人脆弱2回合（攻击命中+1d6）。"""
    
    # 检查并更新脆弱状态
    if state.get('vulnerable_active', False):
        state['vulnerable_duration'] -= 1
        if state['vulnerable_duration'] <= 0:
            state['vulnerable_active'] = False
            state.pop('vulnerable_duration', None)
            state['attack_count'] = 0 # 脆弱结束后重置攻击计数

    # 计算本次攻击的命中加成
    hit_roll_modifier = attacker.attack_modifier
    if state.get('vulnerable_active', False):
        hit_roll_modifier += roll_dice(1, 6)

    # 执行攻击
    attack_roll = roll_dice(2, 12, hit_roll_modifier)
    
    # 如果脆弱未激活，则累积攻击次数
    if not state.get('vulnerable_active', False):
        attack_count = state.get('attack_count', 0) + 1
        state['attack_count'] = attack_count
        # 检查是否触发脆弱
        if attack_count >= 3:
            state['vulnerable_active'] = True
            state['vulnerable_duration'] = 2
            state['attack_count'] = 0 # 触发后立即重置

    if attack_roll >= defender.defense:
        bonus_damage = 0
        if state.get('vulnerable_active',False):
            bonus_damage = roll_dice(1,12,-1)
        return attacker.base_damage_roll() + bonus_damage, 1
    
    return 0, 0

def lance_action(state, attacker, defender, current_round=0):
    """动作: 长枪。有40%的概率进行一次追击。"""
    total_damage_this_turn = 0
    total_hits_this_turn = 0

    # 第一次攻击
    attack_roll_1 = roll_dice(2, 12, attacker.attack_modifier)
    if attack_roll_1 > defender.defense:
        total_hits_this_turn += 1
        total_damage_this_turn += attacker.base_damage_roll()

    # 40%概率追击
    if random.random() < 0.5:
        attack_roll_2 = roll_dice(2, 12, attacker.attack_modifier)
        if attack_roll_2 > defender.defense:
            total_hits_this_turn += 1
            total_damage_this_turn += attacker.base_damage_roll()
            
    return total_damage_this_turn, total_hits_this_turn

def light_bowgun_action(state, attacker, defender, current_round=0):
    """动作: 轻弩。攻击失败时可以重骰一次。"""
    # 第一次攻击检定
    attack_roll = roll_dice(2, 12, attacker.attack_modifier)
    
    # 如果第一次失败，则重骰
    if attack_roll <= defender.defense:
        attack_roll = roll_dice(2, 12, attacker.attack_modifier)

    # 以最终结果判断命中
    if attack_roll >= defender.defense:
        return attacker.base_damage_roll(), 1
    
    return 0, 0

def heavy_bowgun_action(state, attacker, defender, current_round=0):
    """动作: 重弩。根据固定的buff层数获得攻击和伤害加成。"""
    # Buff层数由attacker对象提供，是固定的
    buff_stacks = attacker.buff_stacks
    
    # 根据buff层数计算动态加成
    current_attack_modifier = attacker.attack_modifier + buff_stacks * 1
    bonus_damage = buff_stacks * 1
    
    # 执行攻击
    attack_roll = roll_dice(2, 12, current_attack_modifier)
    
    if attack_roll >= defender.defense:
        damage = attacker.base_damage_roll() + bonus_damage
        return damage, 1
    else:
        return 0, 0

# --- 模拟器核心 ---
class Simulator:
    def __init__(self, action_function, attacker_stats, defender_stats):
        self.action_function = action_function
        self.attacker_stats = attacker_stats
        self.defender_stats = defender_stats

    def _convert_damage_to_hp_loss(self, damage, pro_level):
        """根据伤害阈值将伤害转换为HP损失。"""
        if damage <= 0:
            return 0
        
        # 根据Pro等级选择正确的阈值
        threshold1, threshold2 = self.defender_stats.thresholds[pro_level - 1]
        if damage < threshold1:
            return 1
        elif damage < threshold2:
            return 2
        else:
            return 3

    def run(self, num_simulations=10000, num_rounds=10, pro_level=1):
        grand_total_hp_loss = 0
        grand_total_hits = 0

        for _ in range(num_simulations):
            state = {}
            battle_total_hp_loss = 0
            
            for current_round in range(1, num_rounds + 1):
                damage_this_round, hits_this_round = self.action_function(state, self.attacker_stats, self.defender_stats, current_round)
                hp_loss_this_round = self._convert_damage_to_hp_loss(damage_this_round, pro_level)
                battle_total_hp_loss += hp_loss_this_round
                grand_total_hits += hits_this_round
            
            grand_total_hp_loss += battle_total_hp_loss

        # 计算每场战斗的平均值
        avg_hp_loss_per_battle = grand_total_hp_loss / num_simulations
        avg_hits_per_battle = grand_total_hits / num_simulations
        
        # 返回每场战斗的平均扣血和平均命中
        return avg_hits_per_battle, avg_hp_loss_per_battle

if __name__ == "__main__":
    # --- 通用配置 ---
    NUM_SIMULATIONS = 10000
    NUM_ROUNDS = 10
    DEFENDER = SimpleNamespace(
        defense=13,
        thresholds=[[8, 16], [13, 26], [13, 26], [20, 35], [20, 35], [36, 66]]
    )
    ATTACKER_MOD = 0

    # --- 武器配置中心 ---
    WEAPON_CONFIG = {
        "原版长剑":   {"dice": 10, "bonus": [6,9,9,12,12,15],   "action": simple_attack_action}, # 相当于高一位阶的武器
        "大剑":       {"dice": 12, "bonus": [3,6,6,9,9,12],   "action": simple_attack_action, "params": {"damage_multiplier": 2}},
        "片手":       {"dice": 6,  "bonus": [2,6,6,10,10,14], "action": simple_attack_action, "params": {"extra_roll_dice": 8}},
        "双刀":       {"dice": 8,  "bonus": [0,3,3,6,6,9],    "action": multi_attack_action,  "params": {"num_attacks": 2}},
        "太刀":       {"dice": 8, "bonus": [0,3,3,6,6,9],   "action": long_sword_token_action},
        "大锤":       {"dice": 12, "bonus": [1,4,4,7,7,10],   "action": great_hammer_action},
        "狩猎笛":     {"dice": 8,  "bonus": [0,3,3,6,6,9],   "action": simple_attack_action, "params": {"attack_modifier_bonus": 1, "damage_bonus": 2}},
        "长枪":       {"dice": 10,  "bonus": [1,4,4,7,7,10],   "action": lance_action},
        "铳枪":       {"dice": 10, "bonus": [3,6,6,9,9,12],   "action": wyvernstake_action},
        "斩斧 (N=1)": {"dice": 10, "bonus": [3,6,6,9,9,12],   "action": form_switching_action,"params": {"form_switch_threshold": 1, "form_duration": 1, "form_damage_bonus": 2, "form_attack_bonus": 1}},
        "斩斧 (N=2)": {"dice": 10, "bonus": [3,6,6,9,9,12],   "action": form_switching_action,"params": {"form_switch_threshold": 2, "form_duration": 2, "form_damage_bonus": 4, "form_attack_bonus": 2}},
        "斩斧 (N=3)": {"dice": 10, "bonus": [3,6,6,9,9,12],   "action": form_switching_action,"params": {"form_switch_threshold": 3, "form_duration": 3, "form_damage_bonus": 6, "form_attack_bonus": 3}},
        "斩斧 (N=4)": {"dice": 10, "bonus": [3,6,6,9,9,12],   "action": form_switching_action,"params": {"form_switch_threshold": 4, "form_duration": 4, "form_damage_bonus": 8, "form_attack_bonus": 4}},
        "斩斧 (N=5)": {"dice": 10, "bonus": [3,6,6,9,9,12],   "action": form_switching_action,"params": {"form_switch_threshold": 5, "form_duration": 5, "form_damage_bonus": 10, "form_attack_bonus": 5}},
        "盾斧 (N=1)": {"dice": 12, "bonus": [3,6,6,9,9,12],   "action": charge_blade_action,  "params": {"discharge_threshold": 1, "num_aoe_targets": 1}},
        "盾斧 (N=2)": {"dice": 12, "bonus": [3,6,6,9,9,12],   "action": charge_blade_action,  "params": {"discharge_threshold": 2, "num_aoe_targets": 2}},
        "盾斧 (N=3)": {"dice": 12, "bonus": [3,6,6,9,9,12],   "action": charge_blade_action,  "params": {"discharge_threshold": 3, "num_aoe_targets": 3}},
        "盾斧 (N=4)": {"dice": 12, "bonus": [3,6,6,9,9,12],   "action": charge_blade_action,  "params": {"discharge_threshold": 4, "num_aoe_targets": 3}},
        "盾斧 (N=5)": {"dice": 12, "bonus": [3,6,6,9,9,12],   "action": charge_blade_action,  "params": {"discharge_threshold": 5, "num_aoe_targets": 3}},
        "虫棍":       {"dice": 8,  "bonus": [1,4,4,7,7,10],   "action": insect_glaive_action},
        "龙矢":       {"dice": 8,  "bonus": [3,6,6,9,9,12],   "action": simple_aoe_action,    "params": {"num_aoe_targets": 3}},
        "轻弩":       {"dice": 6,  "bonus": [1,4,4,7,7,10],    "action": light_bowgun_action},
        "重弩 (N=1)": {"dice": 8,  "bonus": [0,3,3,6,6,9],    "action": heavy_bowgun_action,  "params": {"buff_stacks": 1}},
        "重弩 (N=2)": {"dice": 8,  "bonus": [0,3,3,6,6,9],    "action": heavy_bowgun_action,  "params": {"buff_stacks": 2}},
        "重弩 (N=3)": {"dice": 8,  "bonus": [0,3,3,6,6,9],    "action": heavy_bowgun_action,  "params": {"buff_stacks": 3}},
        "重弩 (N=4)": {"dice": 8,  "bonus": [0,3,3,6,6,9],    "action": heavy_bowgun_action,  "params": {"buff_stacks": 4}},
    }

    # --- 数据存储 ---
    results_data = []
    weapon_order = list(WEAPON_CONFIG.keys())

    # --- 模拟循环 ---
    for pro_val in range(1, 7):
        Pro = pro_val
        for name, config in WEAPON_CONFIG.items():
            params = config.get("params", {})
            
            # 构建base_damage_roll函数
            def create_damage_roll(p, c):
                bonus_val = c['bonus'][p-1]
                damage_multiplier = c.get("params", {}).get("damage_multiplier", 1)
                extra_roll_dice = c.get("params", {}).get("extra_roll_dice")
                damage_bonus = c.get("params", {}).get("damage_bonus", 0)

                def roll_func():
                    main_damage = roll_dice(p, c['dice'], bonus_val)
                    if extra_roll_dice:
                        main_damage += roll_dice(p, extra_roll_dice, 0)
                    return (main_damage + damage_bonus) * damage_multiplier
                return roll_func

            attacker_stats = SimpleNamespace(
                attack_modifier=ATTACKER_MOD + params.get("attack_modifier_bonus", 0),
                base_damage_roll=create_damage_roll(Pro, config),
                **params
            )

            sim = Simulator(config["action"], attacker_stats, DEFENDER)
            _, avg_dmg = sim.run(NUM_SIMULATIONS, NUM_ROUNDS, pro_val)
            results_data.append({'Weapon': name, 'Pro': Pro, 'HP Loss': avg_dmg})

    # --- 结果展示 ---
    df = pd.DataFrame(results_data)
    df['Weapon'] = pd.Categorical(df['Weapon'], categories=weapon_order, ordered=True)
    df.sort_values('Weapon', inplace=True)
    
    pivot_df = df.pivot(index='Weapon', columns='Pro', values='HP Loss')
    
    pd.set_option('display.float_format', '{:.2f}'.format)
    print(f"模拟环境: 敌人防御={DEFENDER.defense}, 伤害阈值随Pro等级变化, 每场战斗 {NUM_ROUNDS} 回合, 共模拟 {NUM_SIMULATIONS} 次")
    try:
        from tabulate import tabulate
        print(tabulate(pivot_df, headers='keys', tablefmt='psql'))
    except ImportError:
        print("\n[提示] 'tabulate' 库未安装，建议运行 'pip install tabulate' 以获得更美观的表格输出。")
        print(pivot_df)
