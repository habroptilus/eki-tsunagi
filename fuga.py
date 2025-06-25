import json
import re
from collections import defaultdict

# JSON読み込み
with open("graph_with_ids.json", encoding="utf-8") as f:
    graph = json.load(f)

# base_id → [station_idリスト]
groups = defaultdict(list)

for station_id in graph:
    # 末尾の -数字 を取り除いた base_id を取得
    match = re.match(r"(.+)-\d+$", station_id)
    if match:
        base_id = match.group(1)
        groups[base_id].append(station_id)

# sub-branchを持つ駅のみ出力
for base_id, ids in groups.items():
    if len(ids) > 1:
        print(f"{base_id}:")
        for sid in ids:
            name = graph[sid]["name"]
            print(f"  - {sid}: {name}")
