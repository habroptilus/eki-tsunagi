#!/usr/bin/env python3
"""
line.csvから路線情報を読み込み、各路線の駅リストを繋がっている順番で出力するスクリプト
"""

import json
import pandas as pd
from collections import defaultdict
import sys
import argparse
from pathlib import Path

def load_lines_from_csv():
    """line.csvから路線情報を読み込む"""
    data_dir = Path('data/v2')
    lines_df = pd.read_csv(data_dir / 'line.csv')
    
    # 路線コードと路線名の辞書を作成
    lines_dict = {}
    for _, row in lines_df.iterrows():
        line_cd = str(row['line_cd'])
        line_name = row['line_name']
        lines_dict[line_cd] = line_name
    
    return lines_dict

def load_data():
    """CSVデータを読み込む"""
    data_dir = Path('data/v2')
    
    # 駅データ
    stations_df = pd.read_csv(data_dir / 'station.csv')
    
    # 路線接続データ
    join_df = pd.read_csv(data_dir / 'join.csv')
    
    # 路線データ
    lines_dict = load_lines_from_csv()
    
    return stations_df, join_df, lines_dict

def build_line_graph(join_df):
    """路線ごとの駅接続グラフを構築"""
    line_graphs = defaultdict(lambda: defaultdict(list))
    
    for _, row in join_df.iterrows():
        line_cd = str(row['line_cd'])
        station1 = str(row['station_cd1'])
        station2 = str(row['station_cd2'])
        
        # 双方向に接続を追加
        line_graphs[line_cd][station1].append(station2)
        line_graphs[line_cd][station2].append(station1)
    
    return line_graphs

def trace_line_path(line_graph):
    """路線の駅を接続順に並べる"""
    if not line_graph:
        return []
    
    # 端点（接続が1つの駅）を見つける
    endpoints = [station for station, connections in line_graph.items() if len(connections) == 1]
    
    if not endpoints:
        # 環状線の場合、適当な駅から開始
        start_station = list(line_graph.keys())[0]
    else:
        start_station = endpoints[0]
    
    # 駅を順番に辿る
    path = [start_station]
    visited = {start_station}
    current = start_station
    
    while True:
        next_stations = [s for s in line_graph[current] if s not in visited]
        
        if not next_stations:
            break
            
        next_station = next_stations[0]
        path.append(next_station)
        visited.add(next_station)
        current = next_station
    
    return path

def get_station_name(station_cd, stations_df):
    """駅コードから駅名を取得"""
    station_row = stations_df[stations_df['station_cd'] == int(station_cd)]
    if station_row.empty:
        return f"不明駅({station_cd})"
    
    station_name = station_row.iloc[0]['station_name']
    
    return station_name

def filter_stations_by_pref(stations_df, pref_cds=None):
    """指定した都道府県コードの駅のみをフィルタリング"""
    if pref_cds is None:
        # 全駅を対象とする
        filtered_stations = stations_df['station_cd'].astype(str).tolist()
    else:
        filtered_stations = stations_df[stations_df['pref_cd'].isin(pref_cds)]['station_cd'].astype(str).tolist()
    
    return set(filtered_stations)

def main():
    # コマンドライン引数を解析
    parser = argparse.ArgumentParser(description="路線ごとの駅リストを出力")
    parser.add_argument("--output", "-o", required=True, help="出力JSONファイルのパス")
    parser.add_argument("--pref-codes", nargs="*", type=int, help="対象の都道府県コード（指定しない場合は全駅対象）")
    
    args = parser.parse_args()
    
    # データを読み込み
    stations_df, join_df, lines_dict = load_data()
    
    # 指定された都道府県の駅をフィルタリング
    target_stations = filter_stations_by_pref(stations_df, args.pref_codes)
    
    # 路線グラフを構築
    line_graphs = build_line_graph(join_df)
    
    # 結果を格納するリスト
    result_lines = []
    
    # line.csvから読み込んだ全ての路線を処理
    for line_cd, line_name in lines_dict.items():
        if line_cd not in line_graphs:
            print(f"警告: 路線 {line_name} (コード: {line_cd}) のデータが見つかりません", file=sys.stderr)
            continue
        
        # 路線の駅パスを取得
        station_path = trace_line_path(line_graphs[line_cd])
        
        # 対象エリア内の駅のみをフィルタリング
        filtered_station_path = [s for s in station_path if s in target_stations]
        
        if not filtered_station_path:
            print(f"情報: 路線 {line_name} には対象エリア内の駅がありません", file=sys.stderr)
            continue
        
        # 駅名リストを作成
        stations_list = []
        for i, station_cd in enumerate(filtered_station_path):
            station_name = get_station_name(station_cd, stations_df)
            stations_list.append({
                "order": i + 1,
                "name": station_name
            })
        
        # 路線情報を追加
        line_info = {
            "name": line_name,
            "stations": stations_list
        }
        result_lines.append(line_info)
        
        print(f"処理完了: {line_name} ({len(stations_list)}駅)", file=sys.stderr)
    
    # 出力ディレクトリを作成
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # JSONファイルとして出力
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_lines, f, ensure_ascii=False, indent=2)
    
    print(f"出力完了: {output_path} ({len(result_lines)}路線)", file=sys.stderr)

if __name__ == "__main__":
    main()