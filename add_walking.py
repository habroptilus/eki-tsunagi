import json
from collections import defaultdict

# 徒歩接続ペア（駅名）
walking_pairs = [
    ("有楽町", "日比谷"),
    ("御茶ノ水", "新御茶ノ水"),
    ("新御茶ノ水", "小川町"),
    ("小川町", "淡路町"),
    ("馬喰町", "東日本橋"),
    ("馬喰町", "馬喰横山"),
    ("馬喰横山", "東日本橋"),
    ("人形町", "水天宮前"),
    ("日比谷", "有楽町"),
    ("銀座", "銀座一丁目"),
    ("国会議事堂前", "溜池山王"),
    ("永田町", "赤坂見附"),
    ("春日", "後楽園"),
    ("大門", "浜松町"),
    ("三田", "田町"),
    ("上野広小路", "上野御徒町"),
    ("上野御徒町", "御徒町"),
    ("御徒町", "仲御徒町"),
    ("原宿", "明治神宮前"),
    ("虎ノ門", "虎ノ門ヒルズ"),
    ("秋葉原", "岩本町"),
    ("新宿", "西武新宿"),
    ("有明", "国際展示場"),
    ("板橋", "新板橋"),
    ("溝の口", "武蔵溝ノ口"),
    ("鹿島田", "新川崎"),
    ("京急川崎", "川崎"),
    ("南越谷", "新越谷"),
    ("鶴見", "京急鶴見"),
    ("北朝霞", "朝霞台"),
    ("新松戸", "幸谷"),
    ("新八柱", "八柱"),
    ("本八幡", "京成八幡"),
    ("船橋", "京成船橋"),
    ("幕張", "京成幕張"),
]


def base_id(station_id: str) -> str:
    return station_id.split("-")[0]


def add_walking_connections(graph_path: str, output_path: str):
    with open(graph_path, "r", encoding="utf-8") as f:
        graph = json.load(f)

    # 駅名 → IDリスト の逆引き辞書作成
    name_to_ids = defaultdict(list)
    for station_id, station_data in graph.items():
        name = station_data.get("name")
        if name:
            name_to_ids[name].append(station_id)

    def connection_exists(from_id, to_id):
        return any(
            conn.get("station_id") == to_id and conn.get("line") == "徒歩"
            for conn in graph[from_id].get("edges", [])
        )

    def add_connection(from_id, to_id):
        # base_id が一致しなければ徒歩接続しない
        if base_id(from_id) != base_id(to_id):
            return

        to_name = graph[to_id]["name"]
        if not connection_exists(from_id, to_id):
            graph[from_id]["edges"].append(
                {
                    "station": to_name,
                    "station_id": to_id,
                    "line": "徒歩",
                }
            )

    for s1, s2 in walking_pairs:
        ids1 = name_to_ids.get(s1, [])
        ids2 = name_to_ids.get(s2, [])

        for id1 in ids1:
            for id2 in ids2:
                add_connection(id1, id2)
                add_connection(id2, id1)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    print(f"徒歩接続を追加して {output_path} に保存しました。")


if __name__ == "__main__":
    add_walking_connections("graph_with_ids.json", "graph_with_ids_walking.json")
