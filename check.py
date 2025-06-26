import json

# area.json の読み込み
with open("area.json", encoding="utf-8") as f:
    area_data = json.load(f)

# グラフデータの読み込み（東京・名古屋）
with open("output/graph_tokyo.json", encoding="utf-8") as f:
    graph_tokyo = json.load(f)

with open("output/graph_nagoya.json", encoding="utf-8") as f:
    graph_nagoya = json.load(f)

# グラフ未定義の駅検出用
missing_stations_total = {}

# 結果出力: ユニーク数 + グラフ未定義チェック
for area_key, area_info in area_data.items():
    # 対象グラフを選択
    graph = graph_nagoya if area_key == "nagoya" else graph_tokyo

    # start/goalのユニーク数を計算
    start_set = set(area_info.get("start", []))
    goal_set = set(area_info.get("goal", []))

    print(f"{area_key}")
    print(f"  start: {len(start_set)} 駅")
    print(f"  goal : {len(goal_set)} 駅")

    # graph に含まれない駅のチェック
    used_stations = start_set | goal_set | set(area_info.get("expansion", []))
    missing_stations = [station for station in used_stations if station not in graph]

    if missing_stations:
        missing_stations_total[area_key] = missing_stations
        print(f"  ⚠️ missing: {len(missing_stations)} 駅")
    else:
        print("  ✅ all stations exist in graph")

    print()

# 不足駅リストの詳細出力
if missing_stations_total:
    print("⚠️ 以下の駅がグラフに存在しません:\n")
    for area_key, stations in missing_stations_total.items():
        print(f"[{area_key}]")
        for station in stations:
            print(f" - {station}")
        print()
else:
    print("✅ すべての駅が該当のグラフに存在しています。")
