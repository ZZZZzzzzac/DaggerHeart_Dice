import random
from types import SimpleNamespace

def roll_dice(num_dice, num_sides, modifier=0):
    """模拟掷骰子并返回总和。"""
    return sum(random.randint(1, num_sides) for _ in range(num_dice)) + modifier

# --- Action Functions: 每个函数代表一种武器或攻击模式的完整回合逻辑 ---

def simple_attack_action(state, attacker, defender):
    """动作: 基础单体攻击，无任何特性。"""
    attack_roll = roll_dice(2, 12, attacker.attack_modifier)
    if attack_roll > defender.defense:
        return attacker.base_damage_roll(), 1
    return 0, 0

def stacking_bonus_action(state, attacker, defender):
    """动作: 连续命中可叠加伤害。"""
    attack_roll = roll_dice(2, 12, attacker.attack_modifier)
    if attack_roll > defender.defense:
        consecutive_hits = state.get('consecutive_hits', 0)
        bonus_damage = min(consecutive_hits, 3) * 4
        damage = attacker.base_damage_roll() + bonus_damage
        state['consecutive_hits'] = consecutive_hits + 1
        return damage, 1
    else:
        consecutive_hits = state.get('consecutive_hits', 0)
        state['consecutive_hits'] = max(consecutive_hits-1, 0)
        return 0, 0

def form_switching_action(state, attacker, defender):
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
    if attack_roll > defender.defense:
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

def charge_blade_action(state, attacker, defender):
    """动作: 盾斧。积攒Token，然后通过“超解”释放巨大伤害。"""
    tokens = state.get('tokens', 0)

    # 如果Token达到阈值，则执行“超解”
    if tokens >= attacker.discharge_threshold:
        state['tokens'] = 0 # 消耗所有Token
        attack_roll = roll_dice(2, 12, attacker.attack_modifier)
        if attack_roll > defender.defense:
            # 超解命中
            bonus_damage = (tokens ** 2) * attacker.num_aoe_targets
            single_target_damage = attacker.base_damage_roll() 
            total_damage = single_target_damage + bonus_damage
            return total_damage, attacker.num_aoe_targets
        else:
            # 超解未命中
            return 0, 0
    
    # --- 如果未达到阈值，则执行普通攻击以积攒Token ---
    attack_roll = roll_dice(2, 12, attacker.attack_modifier)
    if attack_roll > defender.defense:
        # 命中，获得Token
        state['tokens'] = tokens + 2
        return attacker.base_damage_roll(), 1
    else:
        # 未命中
        return 0, 0

def multi_attack_action(state, attacker, defender):
    """动作: 每回合进行多次独立的攻击。"""
    total_damage_this_turn = 0
    total_hits_this_turn = 0
    # 在一回合内循环执行多次攻击
    for _ in range(attacker.num_attacks):
        attack_roll = roll_dice(2, 12, attacker.attack_modifier)
        if attack_roll > defender.defense:
            total_hits_this_turn += 1
            total_damage_this_turn += attacker.base_damage_roll()
    return total_damage_this_turn, total_hits_this_turn

def wyvernstake_action(state, attacker, defender):
    """动作: 起爆龙杭。插入动作是一次攻击，成功后开始倒计时。"""
    
    # 如果龙杭未激活，则本回合的动作是“尝试插入”
    if not state.get('stake_active', False):
        attack_roll = roll_dice(2, 12, attacker.attack_modifier)
        if attack_roll > defender.defense:
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
    if attack_roll > defender.defense:
        hits_this_turn = 1
        damage = attacker.base_damage_roll()
        damage_this_turn += damage
        # 累积伤害用于最终引爆
        state['damage_accumulated'] += damage
    
    # 2. 更新倒计时
    state['countdown'] -= 1

    # 3. 检查是否在本回合结束后引爆
    if state['countdown'] <= 0:
        explosion_damage = (2 + state.get('damage_accumulated', 0))
        damage_this_turn += explosion_damage
        # 重置状态，以便下回合可以重新插入
        state['stake_active'] = False
        state.pop('damage_accumulated', None)
        state.pop('countdown', None)
    
    return damage_this_turn, hits_this_turn
def insect_glaive_action(state, attacker, defender):
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
    
    if attack_roll > defender.defense:
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


def simple_aoe_action(state, attacker, defender):
    """动作: 简单的AoE攻击，一次判定，伤害应用到所有目标。"""
    attack_roll = roll_dice(2, 12, attacker.attack_modifier)
    if attack_roll > defender.defense:
        damage = attacker.base_damage_roll() * attacker.num_aoe_targets
        hits = attacker.num_aoe_targets
        return damage, hits
    return 0, 0

def great_hammer_action(state, attacker, defender):
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

    if attack_roll > defender.defense:
        bonus_damage = 0
        if state.get('vulnerable_active',False):
            bonus_damage = roll_dice(1,12,-1)
        return attacker.base_damage_roll() + bonus_damage, 1
    
    return 0, 0

def lance_action(state, attacker, defender):
    """动作: 长枪。有40%的概率进行一次追击。"""
    total_damage_this_turn = 0
    total_hits_this_turn = 0

    # 第一次攻击
    attack_roll_1 = roll_dice(2, 12, attacker.attack_modifier)
    if attack_roll_1 > defender.defense:
        total_hits_this_turn += 1
        total_damage_this_turn += attacker.base_damage_roll()

    # 40%概率追击
    if random.random() < 0.40:
        attack_roll_2 = roll_dice(2, 12, attacker.attack_modifier)
        if attack_roll_2 > defender.defense:
            total_hits_this_turn += 1
            total_damage_this_turn += attacker.base_damage_roll()
            
    return total_damage_this_turn, total_hits_this_turn

def light_bowgun_action(state, attacker, defender):
    """动作: 轻弩。攻击失败时可以重骰一次。"""
    # 第一次攻击检定
    attack_roll = roll_dice(2, 12, attacker.attack_modifier)
    
    # 如果第一次失败，则重骰
    if attack_roll <= defender.defense:
        attack_roll = roll_dice(2, 12, attacker.attack_modifier)

    # 以最终结果判断命中
    if attack_roll > defender.defense:
        return attacker.base_damage_roll(), 1
    
    return 0, 0

# --- 模拟器核心 ---
class Simulator:
    def __init__(self, action_function, attacker_stats, defender_stats):
        self.action_function = action_function
        self.attacker_stats = attacker_stats
        self.defender_stats = defender_stats
        self.state = {}

    def run(self, num_simulations=10000):
        total_hits, total_damage = 0, 0
        self.state = {}
        for _ in range(num_simulations):
            damage_this_turn, hits_this_turn = self.action_function(self.state, self.attacker_stats, self.defender_stats)
            total_damage += damage_this_turn
            total_hits += hits_this_turn
        
        avg_hits = total_hits / num_simulations
        avg_damage = total_damage / num_simulations
        return avg_hits, avg_damage

if __name__ == "__main__":
    # --- 通用配置 ---
    NUM_SIMULATIONS = 100000
    DEFENDER = SimpleNamespace(defense=13)
    ATTACKER_MOD = 0
    Pro = 2

    print(f"模拟环境: 攻击调整值={ATTACKER_MOD}, 敌人防御={DEFENDER.defense}, 模拟次数={NUM_SIMULATIONS}\n")
    


    # --- 武器对比报告 ---

    #  基础武器 (1d10)
    print(f"--- 基础武器 ({Pro}d10+6) ---")
    attacker_s1 = SimpleNamespace(attack_modifier=ATTACKER_MOD, base_damage_roll=lambda: roll_dice(Pro, 10, 6))
    sim_s1 = Simulator(simple_attack_action, attacker_s1, DEFENDER)
    _, avg_dmg = sim_s1.run(NUM_SIMULATIONS)
    print(f"伤害期望: {avg_dmg:.2f}\n")


    #  大剑 ((1d12+3) * 2)
    print(f"--- 大剑 (({Pro}d12+3) * 2) ---")
    attacker_gs = SimpleNamespace(
        attack_modifier=ATTACKER_MOD, 
        base_damage_roll=lambda: roll_dice(Pro, 12, 3) * 2
    )
    sim_gs = Simulator(simple_attack_action, attacker_gs, DEFENDER)
    _, avg_dmg = sim_gs.run(NUM_SIMULATIONS)
    print(f"伤害期望: {avg_dmg:.2f}\n")

    # 片手 (1d6+2+1d8)
    print(f"--- 片手 ({Pro}d6+2+{Pro}d8) ---")
    attacker_new = SimpleNamespace(
        attack_modifier=ATTACKER_MOD, 
        base_damage_roll=lambda: roll_dice(Pro, 8, 2) + roll_dice(Pro, 8, 0)
    )
    sim_new = Simulator(simple_attack_action, attacker_new, DEFENDER)
    _, avg_dmg = sim_new.run(NUM_SIMULATIONS)
    print(f"伤害期望: {avg_dmg:.2f}\n")

    #  双刀 (1d6+1)
    print(f"--- 双刀 ({Pro}d6+1, 每回合攻击3次) ---")
    attacker_s5 = SimpleNamespace(
        attack_modifier=ATTACKER_MOD,
        base_damage_roll=lambda: roll_dice(Pro, 6, 1),
        num_attacks=3
    )
    sim_s5 = Simulator(multi_attack_action, attacker_s5, DEFENDER)
    _, avg_dmg = sim_s5.run(NUM_SIMULATIONS)
    print(f"伤害期望: {avg_dmg:.2f}\n")

    #  太刀
    print(f"--- 太刀 ({Pro}d10, 伤害+4, 上限3次) ---")
    attacker_s2 = SimpleNamespace(attack_modifier=ATTACKER_MOD, base_damage_roll=lambda: roll_dice(Pro, 10, 0))
    sim_s2 = Simulator(stacking_bonus_action, attacker_s2, DEFENDER)
    _, avg_dmg = sim_s2.run(NUM_SIMULATIONS)
    print(f"伤害期望: {avg_dmg:.2f}\n")


    #  大锤 (1d12+1)
    print(f"---  大锤 ({Pro}d12+1, 攻击3次后脆弱2回合[命中+1d6]) ---")
    attacker_gh = SimpleNamespace(
        attack_modifier=ATTACKER_MOD, 
        base_damage_roll=lambda: roll_dice(Pro, 12, 1)
    )
    sim_gh = Simulator(great_hammer_action, attacker_gh, DEFENDER)
    _, avg_dmg = sim_gh.run(NUM_SIMULATIONS)
    print(f"伤害期望: {avg_dmg:.2f}\n")


    #  狩猎笛 (1d8+3)
    print("---  狩猎笛 (1d8+3, 攻击命中+1, 伤害+2) ---")
    attacker_hh = SimpleNamespace(
        attack_modifier=ATTACKER_MOD + 1, 
        base_damage_roll=lambda: roll_dice(Pro, 8, 3) + 2
    )
    sim_hh = Simulator(simple_attack_action, attacker_hh, DEFENDER)
    _, avg_dmg = sim_hh.run(NUM_SIMULATIONS)
    print(f"伤害期望: {avg_dmg:.2f}\n")


    #  长枪 (1d8+1)
    print("---  长枪 (1d8+1, 40%概率追击) ---")
    attacker_lance = SimpleNamespace(
        attack_modifier=ATTACKER_MOD, 
        base_damage_roll=lambda: roll_dice(Pro, 8, 1)
    )
    sim_lance = Simulator(lance_action, attacker_lance, DEFENDER)
    _, avg_dmg = sim_lance.run(NUM_SIMULATIONS)
    print(f"伤害期望: {avg_dmg:.2f}\n")

    #  铳枪
    print(f"--- 铳枪 {Pro}d10+3 (3回合后引爆) ---")
    attacker_s6 = SimpleNamespace(
        attack_modifier=ATTACKER_MOD, 
        base_damage_roll=lambda: roll_dice(Pro, 10, 3)
    )
    sim_s6 = Simulator(wyvernstake_action, attacker_s6, DEFENDER)
    _, avg_dmg = sim_s6.run(NUM_SIMULATIONS)
    print(f"伤害期望: {avg_dmg:.2f}\n")



    #  斩斧
    print(f"--- 斩斧 ({Pro}d10+3, 命中N次后, 攻击+N, 伤害+2N, 持续N次) ---")
    for n in range(1, 6):
        attacker_s3 = SimpleNamespace(
            attack_modifier=ATTACKER_MOD,
            base_damage_roll=lambda: roll_dice(Pro, 10, 3),
            form_switch_threshold=n,
            form_duration=n,
            form_damage_bonus=3*n,
            form_attack_bonus=3*n
        )
        sim_s3 = Simulator(form_switching_action, attacker_s3, DEFENDER)
        _, avg_dmg = sim_s3.run(NUM_SIMULATIONS)
        print(f"  当 N={n}: 伤害期望: {avg_dmg:.2f}")
    print("")

    #  盾斧 (1d12)
    aoe = 3
    print(f"--- 盾斧 ({Pro}d12, 命中+2Token, 有N个Token时超解, AoE伤害+Token^2, 目标{aoe}人) ---")
    for N in range(1,6): # 假设需要6个Token（命中3次）才能超解
        attacker_s4 = SimpleNamespace(
            attack_modifier=ATTACKER_MOD,
            base_damage_roll=lambda: roll_dice(Pro, 12),
            discharge_threshold=N,
            num_aoe_targets=aoe
        )
        sim_s4 = Simulator(charge_blade_action, attacker_s4, DEFENDER)
        _, avg_dmg = sim_s4.run(NUM_SIMULATIONS)
        print(f"  当 N={N}时：伤害期望: {avg_dmg:.2f}")
    print("")

    # 虫棍
    print(f"--- 虫棍 ({Pro}d8+1, Token机制) ---")
    attacker_s7 = SimpleNamespace(
        attack_modifier=ATTACKER_MOD,
        base_damage_roll=lambda: roll_dice(Pro, 8, 1)
    )
    sim_s7 = Simulator(insect_glaive_action, attacker_s7, DEFENDER)
    _, avg_dmg = sim_s7.run(NUM_SIMULATIONS)
    print(f"伤害期望: {avg_dmg:.2f}\n")




    # 龙矢
    print(f"--- 龙矢 ({Pro}d8+1, 攻击3个目标) ---")
    attacker_s8 = SimpleNamespace(
        attack_modifier=ATTACKER_MOD,
        base_damage_roll=lambda: roll_dice(Pro, 8, 3),
        num_aoe_targets=3
    )
    sim_s8 = Simulator(simple_aoe_action, attacker_s8, DEFENDER)
    _, avg_dmg = sim_s8.run(NUM_SIMULATIONS)
    print(f"伤害期望: {avg_dmg:.2f}\n")





    # 轻弩 (1d6+3)
    print(f"--- 轻弩 ({Pro}d6+3, 失败可重骰) ---")
    attacker_lbg = SimpleNamespace(
        attack_modifier=ATTACKER_MOD, 
        base_damage_roll=lambda: roll_dice(Pro, 6, 3)
    )
    sim_lbg = Simulator(light_bowgun_action, attacker_lbg, DEFENDER)
    _, avg_dmg = sim_lbg.run(NUM_SIMULATIONS)
    print(f"伤害期望: {avg_dmg:.2f}\n")
