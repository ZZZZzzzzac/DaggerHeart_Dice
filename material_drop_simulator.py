import random
# --- 配置 ---
CONFIG = {
    "simulation_runs": 100000,
    "team_size": 4,
    "dice_per_person": 4,
    "dice_sides": 10,
    "materials": {
        "皮/鳞/壳": {"roll": range(1, 4), "value": 1},
        "翼/爪/骨": {"roll": range(4, 7), "value": 2},
        "器官/延髓": {"roll": range(7, 9), "value": 4},
        "宝玉": {"roll": [9], "value": 8},
        "逆鳞": {"roll": [10], "value": 8}
    },
    "rare_materials": ["宝玉", "逆鳞"]
}

def get_material_for_roll(roll, materials_config):
    """根据出目获取对应的素材"""
    for name, data in materials_config.items():
        # 兼容列表和范围
        if isinstance(data["roll"], list):
            if roll in data["roll"]:
                return name, data["value"]
        elif isinstance(data["roll"], range):
             if roll in data["roll"]:
                return name, data["value"]
    return None, 0

def simulate_hunt(config):
    """模拟一次狩猎"""
    total_dice_count = config["team_size"] * config["dice_per_person"]
    total_value = 0
    value_without_rares = 0
    rare_counts = {name: 0 for name in config["rare_materials"]}

    for _ in range(total_dice_count):
        roll = random.randint(1, config["dice_sides"])
        material_name, material_value = get_material_for_roll(roll, config["materials"])

        if material_name:
            total_value += material_value
            if material_name in config["rare_materials"]:
                rare_counts[material_name] += 1
            else:
                value_without_rares += material_value

    return total_value, value_without_rares, rare_counts

def main():
    """主函数，运行模拟并打印结果"""
    config = CONFIG

    total_value_sum = 0
    total_value_without_rares_sum = 0
    total_rare_counts = {name: 0 for name in config["rare_materials"]}
    
    runs = config["simulation_runs"]

    for _ in range(runs):
        hunt_value, hunt_value_without_rares, hunt_rare_counts = simulate_hunt(config)
        total_value_sum += hunt_value
        total_value_without_rares_sum += hunt_value_without_rares
        for name, count in hunt_rare_counts.items():
            total_rare_counts[name] += count

    # --- 计算并打印平均值 ---
    avg_total_value = total_value_sum / runs
    avg_value_without_rares = total_value_without_rares_sum / runs
    avg_rare_counts = {name: count / runs for name, count in total_rare_counts.items()}

    print(f"--- 模拟了 {runs} 次狩猎 ---")
    print(f"配置: {config['team_size']}人小队, 每人{config['dice_per_person']}个d{config['dice_sides']}")
    print(f"\n平均总分值: {avg_total_value:.4f}")
    print(f"除去宝玉和逆鳞的平均总分值: {avg_value_without_rares:.4f}")
    print("\n平均获得的稀有素材:")
    for name, avg_count in avg_rare_counts.items():
        print(f"  - {name}: {avg_count:.4f} 个")

if __name__ == "__main__":
    main()