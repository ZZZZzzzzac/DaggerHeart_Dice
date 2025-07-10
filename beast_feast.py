import random
import numpy as np
from collections import Counter

def roll_dice(dice_pool):
    """根据给定的骰子池掷骰。"""
    return {i: random.randint(1, side) for i, side in enumerate(dice_pool)}

def find_and_process_matches(roll_results):
    """
    从掷骰结果中寻找匹配项。
    返回: (匹配组合的分数, 剩余的骰子索引)
    """
    value_counts = Counter(roll_results.values())
    matched_score = 0
    remaining_indices = list(roll_results.keys())
    
    for value, count in value_counts.items():
        if count > 1:
            matched_score += value
            # 移除所有掷出该点数的骰子
            indices_to_remove = [idx for idx, val in roll_results.items() if val == value]
            for idx in indices_to_remove:
                if idx in remaining_indices:
                    remaining_indices.remove(idx)
                    
    return matched_score, remaining_indices

def simulate_cooking_session(initial_dice_pool, removal_strategy):
    """
    模拟一次完整的烹饪过程。
    removal_strategy: 'largest', 'smallest', 'random'
    """
    if not initial_dice_pool:
        return 0

    current_dice_pool = list(initial_dice_pool)
    total_score = 0
    
    while len(current_dice_pool) > 1:
        # 将骰子池与其原始索引配对，以便在移除后仍能追踪
        indexed_pool = {i: side for i, side in enumerate(current_dice_pool)}
        roll_results = {i: random.randint(1, side) for i, side in indexed_pool.items()}
        
        score_from_matches, remaining_indices = find_and_process_matches(roll_results)
        
        if score_from_matches > 0:
            total_score += score_from_matches
            # 更新骰子池为剩余的骰子
            current_dice_pool = [indexed_pool[i] for i in remaining_indices]
        else: # 没有匹配项
            if not current_dice_pool:
                break
            
            if removal_strategy == 'largest':
                dice_to_remove = max(current_dice_pool)
            elif removal_strategy == 'smallest':
                dice_to_remove = min(current_dice_pool)
            elif removal_strategy == 'random':
                dice_to_remove = random.choice(current_dice_pool)
            else:
                raise ValueError("Unknown removal strategy")
            
            current_dice_pool.remove(dice_to_remove)

    return total_score

def run_simulation(dice_counts, num_simulations, removal_strategy):
    """运行蒙特卡洛仿真。"""
    initial_dice_pool = []
    initial_dice_pool.extend([4] * dice_counts.get('d4', 0))
    initial_dice_pool.extend([6] * dice_counts.get('d6', 0))
    initial_dice_pool.extend([8] * dice_counts.get('d8', 0))
    initial_dice_pool.extend([10] * dice_counts.get('d10', 0))
    initial_dice_pool.extend([12] * dice_counts.get('d12', 0))
    initial_dice_pool.extend([20] * dice_counts.get('d20', 0))
    
    scores = []
    for _ in range(num_simulations):
        scores.append(simulate_cooking_session(initial_dice_pool, removal_strategy))
        
    return scores

if __name__ == "__main__":
    # 示例配置：5d12, 3d8, 1d4
    dice_configuration = {
        'd4': 0, # 7.6 / 3.5
        'd6': 0, # 11.7 / 10.8
        'd8': 0, # 15.4 / 22
        'd10': 0, # 18.8 / 36.5
        'd12': 0, # 22.1 / 54
        'd20': 10, # 32.5 / 156
    }
    
    # 用户可以修改这里的骰子数量
    # dice_configuration = {
    #     'd4': int(input("输入 d4 的数量 (A): ")),
    #     'd6': int(input("输入 d6 的数量 (B): ")),
    #     'd8': int(input("输入 d8 的数量 (C): ")),
    #     'd10': int(input("输入 d10 的数量 (D): ")),
    #     'd12': int(input("输入 d12 的数量 (E): ")),
    #     'd20': int(input("输入 d20 的数量 (F): ")),
    # }

    simulations = 10000
    
    print(f"使用以下配置进行仿真: {dice_configuration}")
    print(f"仿真次数: {simulations}\n")

    # 策略1: 移除最大的骰子
    scores_largest = run_simulation(dice_configuration, simulations, 'largest')
    mean_largest = np.mean(scores_largest)
    variance_largest = np.var(scores_largest)
    print(f"--- 移除最大骰子策略 ---")
    print(f"  期望评级点数 (平均值): {mean_largest:.2f}")
    print(f"  方差: {variance_largest:.2f}\n")

    # 策略2: 移除最小的骰子
    scores_smallest = run_simulation(dice_configuration, simulations, 'smallest')
    mean_smallest = np.mean(scores_smallest)
    variance_smallest = np.var(scores_smallest)
    print(f"--- 移除最小骰子策略 ---")
    print(f"  期望评级点数 (平均值): {mean_smallest:.2f}")
    print(f"  方差: {variance_smallest:.2f}\n")

    # 策略3: 随机移除骰子
    scores_random = run_simulation(dice_configuration, simulations, 'random')
    mean_random = np.mean(scores_random)
    variance_random = np.var(scores_random)
    print(f"--- 随机移除骰子策略 ---")
    print(f"  期望评级点数 (平均值): {mean_random:.2f}")
    print(f"  方差: {variance_random:.2f}")