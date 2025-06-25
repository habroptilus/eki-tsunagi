import json

# ファイル読み込み
with open("area.json", encoding="utf-8") as f:
    area_data = json.load(f)

with open("graph_with_pos_walking.json", encoding="utf-8") as f:
    graph_data = json.load(f)

# 駅名を収集
used_stations = set()

for item in area_data.values():
    for key in ["start", "goal", "expansion"]:
        if key in item:
            for station in item[key]:
                used_stations.add(station)

# 存在しない駅をチェック
missing_stations = [station for station in used_stations if station not in graph_data]

# 結果を表示
if missing_stations:
    print("⚠️ 以下の駅が graph.json に存在しません:")
    for station in missing_stations:
        print(f" - {station}")
else:
    print("✅ すべての駅が graph.json に存在しています。")
