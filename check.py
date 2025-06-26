import json

# area.json の読み込み
with open("area.json", encoding="utf-8") as f:
    area_data = json.load(f)

# グラフデータの読み込み（東京・名古屋）
with open("output/graph_tokyo.json", encoding="utf-8") as f:
    graph_tokyo = json.load(f)

with open("output/graph_nagoya.json", encoding="utf-8") as f:
    graph_nagoya = json.load(f)

# 結果格納用
missing_stations_total = {}

# 各エリアごとに確認
for area_key, area_info in area_data.items():
    # 該当エリアのグラフを選択
    graph = graph_nagoya if area_key == "nagoya" else graph_tokyo

    used_stations = set()

    for key in ["start", "goal", "expansion"]:
        if key in area_info:
            for station in area_info[key]:
                used_stations.add(station)

    # 存在チェック
    missing_stations = [station for station in used_stations if station not in graph]
    if missing_stations:
        missing_stations_total[area_key] = missing_stations

# 結果表示
if missing_stations_total:
    print("⚠️ 以下の駅がグラフに存在しません:\n")
    for area_key, stations in missing_stations_total.items():
        print(f"[{area_key}]")
        for station in stations:
            print(f" - {station}")
        print()
else:
    print("✅ すべての駅が該当のグラフに存在しています。")
