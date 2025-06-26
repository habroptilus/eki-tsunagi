import json
from collections import defaultdict

import pandas as pd

# CSVの読み込み
stations = pd.read_csv("data/v2/station.csv")
joins = pd.read_csv("data/v2/join.csv")
lines = pd.read_csv("data/v2/line.csv")

config_path = "config/tokyo.json"

with open(config_path, encoding="utf-8") as f:
    config = json.load(f)

major_lines = config["lines"]
normalize_name_map = config["normalize_name_map"]
valid_pref_cds = set(config["valid_pref_cds"])


def normalize_name(name: str) -> str:
    return normalize_name_map.get(name, name)


# フィルタされた駅
filtered_stations = stations[stations["pref_cd"].isin(valid_pref_cds)]
cd_to_name = filtered_stations.set_index("station_cd")["station_name"].to_dict()
valid_station_cds = set(cd_to_name.keys())

# 路線コード → 路線名
line_cd_to_name = lines.set_index("line_cd")["line_name"].to_dict()
# 駅コード → 緯度経度辞書
station_pos = filtered_stations.set_index("station_cd")[["lon", "lat"]].to_dict(
    orient="index"
)

# cd_to_nameは既にあるので、graph作成時は駅コードも使う形にします。

graph = defaultdict(lambda: {"lat": None, "lon": None, "edges": []})

for _, row in joins.iterrows():
    cd1, cd2, line_cd = row["station_cd1"], row["station_cd2"], row["line_cd"]

    if cd1 in valid_station_cds and cd2 in valid_station_cds:
        # 使用箇所
        name1, name2 = cd_to_name[cd1], cd_to_name[cd2]
        name1 = normalize_name(name1)
        name2 = normalize_name(name2)

        if str(line_cd) not in major_lines:
            continue

        line_name = major_lines[str(line_cd)]

        # ここでstation_cdを使ってlat, lonを取得
        if graph[name1]["lat"] is None or graph[name1]["lon"] is None:
            pos1 = station_pos.get(cd1)
            if pos1:
                graph[name1]["lat"] = pos1["lat"]
                graph[name1]["lon"] = pos1["lon"]

        if graph[name2]["lat"] is None or graph[name2]["lon"] is None:
            pos2 = station_pos.get(cd2)
            if pos2:
                graph[name2]["lat"] = pos2["lat"]
                graph[name2]["lon"] = pos2["lon"]

        graph[name1]["edges"].append(
            {
                "station": name2,
                "line": line_name,
                "station_cd": str(cd2),
                "line_cd": str(line_cd),
            }
        )
        graph[name2]["edges"].append(
            {
                "station": name1,
                "line": line_name,
                "station_cd": str(cd1),
                "line_cd": str(line_cd),
            }
        )

# JSON出力
with open("graph_with_pos.json", "w", encoding="utf-8") as f:
    json.dump(graph, f, ensure_ascii=False, indent=2)
