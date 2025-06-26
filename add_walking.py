import json

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
    ("川崎", "京急川崎"),
    ("鶴見", "京急鶴見"),
    ("東神奈川", "京急東神奈川"),
    ("新子安", "京急新子安"),
    ("南越谷", "新越谷"),
    ("杉田", "新杉田"),
    ("綱島", "新綱島"),
    ("妙音通", "呼続"),
    ("桜", "桜本町"),
    ("栄", "栄町"),
    ("名古屋", "名鉄名古屋"),
    ("近鉄名古屋", "名鉄名古屋"),
    ("名古屋", "近鉄名古屋"),
    ("八田", "近鉄八田"),
]


def add_walking_connections(graph_path: str, output_path: str):
    with open(graph_path, "r", encoding="utf-8") as f:
        graph = json.load(f)

    def ensure_entry(station_name):
        if station_name not in graph:
            graph[station_name] = []

    def connection_exists(from_station, to_station):
        print(from_station, to_station)
        return any(
            conn["station"] == to_station and conn["line"] == "徒歩"
            for conn in graph[from_station].get("edges", [])
        )

    def add_connection(from_station, to_station):
        ensure_entry(from_station)
        ensure_entry(to_station)

        if not connection_exists(from_station, to_station):
            graph[from_station]["edges"].append(
                {"station": to_station, "line": "徒歩", "station_cd": "", "line_cd": ""}
            )

    for s1, s2 in walking_pairs:
        add_connection(s1, s2)
        add_connection(s2, s1)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    print(f"徒歩接続を追加して {output_path} に保存しました。")


if __name__ == "__main__":
    add_walking_connections("graph_with_pos.json", "graph_with_pos_walking.json")
