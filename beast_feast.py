import random
import numpy as np
from collections import Counter

def roll_dice(dice_pool):
    """根据给定的骰子池掷骰。"""
    return {i: random.randint(1, side) for i, side in enumerate(dice_pool)}

def find_and_process_matches(roll_results):
    """
    从掷骰结果中寻找匹配项。
    返回: (匹配组合的分数, 奖励骰数量, 剩余的骰子索引)
    """
    value_counts = Counter(roll_results.values())
    matched_score = 0
    bonus_dice = 0
    remaining_indices = list(roll_results.keys())
    
    for value, count in value_counts.items():
        if count > 1:
            matched_score += value
            if count > 2:
                bonus_dice += (count - 2)
            # 移除所有掷出该点数的骰子
            indices_to_remove = [idx for idx, val in roll_results.items() if val == value]
            for idx in indices_to_remove:
                if idx in remaining_indices:
                    remaining_indices.remove(idx)
                    
    return matched_score, bonus_dice, remaining_indices

def simulate_cooking_session(initial_dice_pool, removal_strategy):
    """
    模拟一次完整的烹饪过程。
    removal_strategy: 'largest', 'smallest', 'random'
    返回: (总分, 总奖励骰)
    """
    if not initial_dice_pool:
        return 0, 0

    current_dice_pool = list(initial_dice_pool)
    total_score = 0
    total_bonus_dice = 0
    
    while len(current_dice_pool) > 1:
        # 将骰子池与其原始索引配对，以便在移除后仍能追踪
        indexed_pool = {i: side for i, side in enumerate(current_dice_pool)}
        roll_results = {i: random.randint(1, side) for i, side in indexed_pool.items()}
        
        score_from_matches, bonus_from_matches, remaining_indices = find_and_process_matches(roll_results)
        
        if score_from_matches > 0:
            total_score += score_from_matches
            total_bonus_dice += bonus_from_matches
            # 更新骰子池为剩余的骰子
            current_dice_pool = [indexed_pool[i] for i in remaining_indices]
        else: # 没有匹配项
            if not current_dice_pool:
                break
            
            if removal_strategy == 'random':
                dice_to_remove = random.choice(current_dice_pool)
            else:
                # 保留随机作为默认，移除其他策略
                dice_to_remove = random.choice(current_dice_pool)

            current_dice_pool.remove(dice_to_remove)

    return total_score, total_bonus_dice

def run_simulation(dice_counts, num_simulations):
    """运行蒙特卡洛仿真。"""
    initial_dice_pool = []
    initial_dice_pool.extend([4] * dice_counts.get('d4', 0))
    initial_dice_pool.extend([6] * dice_counts.get('d6', 0))
    initial_dice_pool.extend([8] * dice_counts.get('d8', 0))
    initial_dice_pool.extend([10] * dice_counts.get('d10', 0))
    initial_dice_pool.extend([12] * dice_counts.get('d12', 0))
    initial_dice_pool.extend([20] * dice_counts.get('d20', 0))
    
    scores = []
    bonus_dices = []
    for _ in range(num_simulations):
        score, bonus = simulate_cooking_session(initial_dice_pool, 'random')
        scores.append(score)
        bonus_dices.append(bonus)
        
    return scores, bonus_dices

if __name__ == "__main__":
    # 示例配置列表
    dice_configurations = [
        { 'd4': 8, 'd6': 0, 'd8': 0, 'd10': 0, 'd12': 0, 'd20': 0 },
        { 'd4': 0, 'd6': 8, 'd8': 0, 'd10': 0, 'd12': 0, 'd20': 0 },
        { 'd4': 0, 'd6': 0, 'd8': 8, 'd10': 0, 'd12': 0, 'd20': 0 },
        { 'd4': 0, 'd6': 0, 'd8': 0, 'd10': 8, 'd12': 0, 'd20': 0 },
        { 'd4': 0, 'd6': 0, 'd8': 0, 'd10': 0, 'd12': 8, 'd20': 0 },
        { 'd4': 0, 'd6': 0, 'd8': 0, 'd10': 0, 'd12': 0, 'd20': 8 },
        { 'd4': 16, 'd6': 0, 'd8': 0, 'd10': 0, 'd12': 0, 'd20': 0 },
        { 'd4': 0, 'd6': 16, 'd8': 0, 'd10': 0, 'd12': 0, 'd20': 0 },
        { 'd4': 0, 'd6': 0, 'd8': 16, 'd10': 0, 'd12': 0, 'd20': 0 },
        { 'd4': 0, 'd6': 0, 'd8': 0, 'd10': 16, 'd12': 0, 'd20': 0 },
        { 'd4': 0, 'd6': 0, 'd8': 0, 'd10': 0, 'd12': 16, 'd20': 0 },
        { 'd4': 0, 'd6': 0, 'd8': 0, 'd10': 0, 'd12': 0, 'd20': 16 },
    ]

    simulations = 10000
    print(f"仿真次数: {simulations}\n")

    for dice_configuration in dice_configurations:
        print(f"配置: {dice_configuration}")
        
        scores, bonus_dices = run_simulation(dice_configuration, simulations)
        
        mean_score = np.mean(scores)
        variance_score = np.var(scores)
        mean_bonus_dice = np.mean(bonus_dices)
        
        print(f"  {mean_score:.2f} \ {mean_bonus_dice:.2f}")