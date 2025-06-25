import json
from collections import defaultdict

import pandas as pd

# 駅名の正規化マッピング
normalize_name_map = {
    "市ヶ谷": "市ケ谷",
    "明治神宮前〈原宿〉": "明治神宮前",
    "押上（スカイツリー前）": "押上",
    "押上〈スカイツリー前〉": "押上",
    "新線新宿": "新宿",
    "モノレール浜松町": "浜松町",
}

# ファイル読み込み
stations_df = pd.read_csv("data/v2/station.csv")
joins_df = pd.read_csv("data/v2/join.csv")
lines_df = pd.read_csv("data/v2/line.csv")

# 東京近郊のみ
valid_pref_cds = {11, 12, 13, 14}
stations_df = stations_df[stations_df["pref_cd"].isin(valid_pref_cds)]

# 駅名正規化
stations_df["station_name"] = stations_df["station_name"].replace(normalize_name_map)

# station_g_cdごとに駅名をグループ
grouped = stations_df.groupby("station_g_cd")

# 駅IDのマッピング（station_cd → station_id, および name）
station_id_map = {}
station_name_map = {}
station_pos_map = {}

for g_cd, group in grouped:
    # 駅名と対応する station_cd のペアを保持
    name_to_rows = defaultdict(list)
    for _, row in group.iterrows():
        normalized_name = row["station_name"]
        name_to_rows[normalized_name].append(row)

    if len(name_to_rows) == 1:
        # 駅名が1つしかない → 通常のID
        station_id = str(g_cd)
        for row in group.itertuples():
            station_id_map[row.station_cd] = station_id
            station_name_map[station_id] = row.station_name
            station_pos_map[station_id] = {"lat": row.lat, "lon": row.lon}
    else:
        # 駅名が複数 → 名前ごとにインデックス付きIDを付ける
        for idx, (name, rows) in enumerate(name_to_rows.items()):
            station_id = f"{g_cd}-{idx}"
            station_name_map[station_id] = name
            for row in rows:
                station_id_map[row.station_cd] = station_id
                station_pos_map[station_id] = {"lat": row.lat, "lon": row.lon}


# 有効なstation_cdセット
valid_station_cds = set(station_id_map.keys())

# line_cd → line_name
line_cd_to_name = lines_df.set_index("line_cd")["line_name"].to_dict()

# グラフ構造を構築
graph = {}

for _, row in joins_df.iterrows():
    cd1, cd2, line_cd = row["station_cd1"], row["station_cd2"], row["line_cd"]
    if cd1 not in valid_station_cds or cd2 not in valid_station_cds:
        continue

    id1 = station_id_map[cd1]
    id2 = station_id_map[cd2]
    name1 = station_name_map[id1]
    name2 = station_name_map[id2]
    line_name = line_cd_to_name.get(line_cd, "不明路線")

    for sid, name in [(id1, name1), (id2, name2)]:
        if sid not in graph:
            graph[sid] = {
                "name": name,
                "lat": station_pos_map[sid]["lat"],
                "lon": station_pos_map[sid]["lon"],
                "edges": [],
            }

    graph[id1]["edges"].append({"station": name2, "line": line_name, "station_id": id2})
    graph[id2]["edges"].append({"station": name1, "line": line_name, "station_id": id1})

# JSON保存
with open("graph_with_ids.json", "w", encoding="utf-8") as f:
    json.dump(graph, f, ensure_ascii=False, indent=2)
