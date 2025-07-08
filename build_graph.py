import argparse
import json
from collections import defaultdict

import pandas as pd


def normalize_name(name: str, name_map: dict) -> str:
    return name_map.get(name, name)


def apply_replacement_rules(station_name: str, line_cds: set, replacement_rules: list, major_lines: dict) -> str:
    """
    駅名に対してreplacement_rulesを適用する
    
    Args:
        station_name: 対象の駅名
        line_cds: その駅が通っている路線コードのset
        replacement_rules: 置換ルールのリスト
        major_lines: 有効な路線コードのdict
        
    Returns:
        置換後の駅名
        
    Raises:
        ValueError: targetにマッチしたがどのruleにもマッチしなかった場合
    """
    for rule in replacement_rules:
        if station_name == rule["target"]:
            for line_rule in rule["rules"]:
                rule_line_cds = set(line_rule["lines"])
                # その駅が通っている路線コードを文字列に変換
                station_line_cds = {str(cd) for cd in line_cds}
                if rule_line_cds.intersection(station_line_cds):
                    return line_rule["dest"]
            # targetにマッチしたがどのruleにもマッチしなかった場合
            # デバッグ情報として文字列変換した路線コードも表示
            valid_line_cds_str = {str(cd) for cd in line_cds if str(cd) in major_lines}
            raise ValueError(f"Station '{station_name}' matched target but no replacement rule matched. Line codes: {line_cds}, Valid line codes: {valid_line_cds_str}")
    return station_name


def build_base_graph(config: dict, stations, joins, lines):
    major_lines = config["lines"]
    normalize_name_map = config["normalize_name_map"]
    replacement_rules = config.get("replacement_rules", [])
    valid_pref_cds = set(config["valid_pref_cds"])

    filtered_stations = stations[stations["pref_cd"].isin(valid_pref_cds)]
    cd_to_name = filtered_stations.set_index("station_cd")["station_name"].to_dict()
    valid_station_cds = set(cd_to_name.keys())

    station_pos = filtered_stations.set_index("station_cd")[["lon", "lat"]].to_dict(
        orient="index"
    )

    # 各駅が通っている路線コードを事前に計算
    station_lines = defaultdict(set)
    for _, row in joins.iterrows():
        cd1, cd2, line_cd = row["station_cd1"], row["station_cd2"], row["line_cd"]
        if cd1 in valid_station_cds and cd2 in valid_station_cds:
            station_lines[cd1].add(line_cd)
            station_lines[cd2].add(line_cd)

    graph = defaultdict(lambda: {"lat": None, "lon": None, "edges": []})

    for _, row in joins.iterrows():
        cd1, cd2, line_cd = row["station_cd1"], row["station_cd2"], row["line_cd"]

        if cd1 in valid_station_cds and cd2 in valid_station_cds:
            name1 = normalize_name(cd_to_name[cd1], normalize_name_map)
            name2 = normalize_name(cd_to_name[cd2], normalize_name_map)
            
            # replacement_rulesを適用
            name1 = apply_replacement_rules(name1, station_lines[cd1], replacement_rules, major_lines)
            name2 = apply_replacement_rules(name2, station_lines[cd2], replacement_rules, major_lines)

            if str(line_cd) not in major_lines:
                continue

            line_name = major_lines[str(line_cd)]

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

    return graph


def add_walking_connections(graph: dict, walking_pairs: list) -> dict:
    def ensure_entry(station_name):
        if station_name not in graph:
            graph[station_name] = {"lat": None, "lon": None, "edges": []}

    def connection_exists(from_station, to_station):
        return any(
            conn["station"] == to_station and conn["line"] == "徒歩"
            for conn in graph[from_station].get("edges", [])
        )

    for s1, s2 in walking_pairs:
        ensure_entry(s1)
        ensure_entry(s2)

        if not connection_exists(s1, s2):
            graph[s1]["edges"].append(
                {
                    "station": s2,
                    "line": "徒歩",
                    "station_cd": "",
                    "line_cd": "",
                }
            )

        if not connection_exists(s2, s1):
            graph[s2]["edges"].append(
                {
                    "station": s1,
                    "line": "徒歩",
                    "station_cd": "",
                    "line_cd": "",
                }
            )

    return graph


def main(config_path: str, base_output: str, walking_output: str):
    # 入力ファイル
    stations = pd.read_csv("data/v2/station.csv")
    joins = pd.read_csv("data/v2/join.csv")
    lines = pd.read_csv("data/v2/line.csv")

    # 設定ファイル読み込み
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    # ベースグラフ構築
    graph = build_base_graph(config, stations, joins, lines)

    with open(base_output, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    print(f"✅ ベースグラフを {base_output} に保存しました。")

    # 徒歩接続追加
    walking_pairs = config.get("walking_pairs", [])
    graph_with_walking = add_walking_connections(graph, walking_pairs)

    with open(walking_output, "w", encoding="utf-8") as f:
        json.dump(graph_with_walking, f, ensure_ascii=False, indent=2)
    print(f"🚶 徒歩接続グラフを {walking_output} に保存しました。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="駅グラフを生成（徒歩接続付き）")
    parser.add_argument("--config", required=True, help="設定ファイルのパス")
    parser.add_argument(
        "--base_output", default="graph_with_pos.json", help="ベースグラフ出力先"
    )
    parser.add_argument(
        "--walking_output",
        default="graph_with_pos_walking.json",
        help="徒歩接続グラフ出力先",
    )

    args = parser.parse_args()
    main(args.config, args.base_output, args.walking_output)
