#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
goal駅からstart駅への最短距離を分析し、適切な距離範囲の3駅を選択するスクリプト

Usage:
    python generate_guess_problems.py --area central --output distances_central.json
    python generate_guess_problems.py --area osaka --min-distance 3 --max-distance 15
"""

import argparse
import json
import random
from collections import deque
from datetime import datetime
from pathlib import Path


def load_data(area_key="central"):
    """
    エリアに応じたデータを読み込む

    Args:
        area_key: エリア名

    Returns:
        area_data, graph_data
    """
    with open("area.json", "r", encoding="utf-8") as f:
        area_data = json.load(f)

    # エリアに応じたグラフファイルを選択
    graph_file_map = {
        "central": "output/graph_tokyo_walking.json",
        "south": "output/graph_tokyo_walking.json",
        "west": "output/graph_tokyo_walking.json",
        "north": "output/graph_tokyo_walking.json",
        "east": "output/graph_tokyo_walking.json",
        "yokohama": "output/graph_tokyo_walking.json",
        "osaka": "output/graph_osaka_walking.json",
        "nagoya": "output/graph_nagoya_walking.json",
    }

    graph_file = graph_file_map.get(area_key, "output/graph_tokyo_walking.json")

    try:
        with open(graph_file, "r", encoding="utf-8") as f:
            graph_data = json.load(f)
    except FileNotFoundError:
        print(
            f"警告: グラフファイル {graph_file} が見つかりません。東京グラフを使用します。"
        )
        with open("output/graph_tokyo_walking.json", "r", encoding="utf-8") as f:
            graph_data = json.load(f)

    return area_data, graph_data


def find_shortest_distance(graph, start, end):
    """
    2駅間の最短距離（駅数）を計算

    Args:
        graph: グラフデータ
        start: 開始駅
        end: 終了駅

    Returns:
        最短距離（駅数）、見つからない場合は None
    """
    if start == end:
        return 0

    if start not in graph or end not in graph:
        return None

    queue = deque([(start, 0)])
    visited = {start}

    while queue:
        current, distance = queue.popleft()

        # 隣接駅を探索
        for edge in graph.get(current, {}).get("edges", []):
            next_station = edge["station"]

            if next_station == end:
                return distance + 1

            if next_station not in visited:
                visited.add(next_station)
                queue.append((next_station, distance + 1))

    return None


def calculate_distances_from_goal(graph, goal_station, start_candidates):
    """
    goal駅から各start候補駅への最短距離を計算

    Args:
        graph: グラフデータ
        goal_station: goal駅名
        start_candidates: start駅の候補リスト

    Returns:
        {start_station: distance} の辞書
    """
    distances = {}

    for start_station in start_candidates:
        distance = find_shortest_distance(graph, goal_station, start_station)
        if distance is not None:
            distances[start_station] = distance

    return distances


def select_three_stations_in_range(distances, min_distance=4, max_distance=12):
    """
    指定された距離範囲内にある駅から重複のない3駅を選択

    Args:
        distances: {station: distance} の辞書
        min_distance: 最小距離
        max_distance: 最大距離

    Returns:
        選択された3駅のリスト、条件を満たす駅が不足の場合は None
    """
    # 範囲内の駅を抽出
    valid_stations = [
        station
        for station, distance in distances.items()
        if min_distance <= distance <= max_distance
    ]

    if len(valid_stations) < 3:
        return None

    # 重複のない3駅を選択
    selected = random.sample(valid_stations, 3)
    return selected


def analyze_area_distances(area_key="central", min_distance=4, max_distance=12):
    """
    指定エリアのgoal駅からstart駅への距離を分析

    Args:
        area_key: エリア名
        min_distance: 最小距離
        max_distance: 最大距離

    Returns:
        分析結果のリスト
    """
    area_data, graph_data = load_data(area_key)

    if area_key not in area_data:
        print(f"エラー: エリア '{area_key}' が見つかりません")
        return []

    goal_candidates = area_data[area_key]["goal"]
    start_candidates = area_data[area_key]["start"]

    # goal駅の重複を除去
    unique_goals = list(set(goal_candidates))

    print(f"🎯 {area_key}エリアの距離分析開始")
    print(f"📊 goal駅数: {len(unique_goals)}")
    print(f"📊 start駅数: {len(start_candidates)}")
    print(f"📏 距離範囲: {min_distance}~{max_distance}駅")
    print("=" * 50)

    results = []
    processed = 0
    skipped = 0

    for i, goal_station in enumerate(unique_goals, 1):
        print(f"\n🚉 {i}/{len(unique_goals)}: {goal_station}")

        # goal駅がグラフに存在するかチェック
        if goal_station not in graph_data:
            print(f"⚠️ goal駅 '{goal_station}' がグラフに存在しません - スキップ")
            skipped += 1
            continue

        # goal駅から各start駅への距離を計算
        distances = calculate_distances_from_goal(
            graph_data, goal_station, start_candidates
        )

        if not distances:
            print("⚠️ 距離計算結果が空です - スキップ")
            skipped += 1
            continue

        # 距離範囲内の3駅を選択
        selected_starts = select_three_stations_in_range(
            distances, min_distance, max_distance
        )

        if selected_starts is None:
            valid_count = len(
                [d for d in distances.values() if min_distance <= d <= max_distance]
            )
            print(f"⚠️ 範囲内の駅が不足: {valid_count}駅 - スキップ")
            skipped += 1
            continue

        # 選択された駅の距離を取得
        selected_distances = [distances[station] for station in selected_starts]

        result = {
            "goal_station": goal_station,
            "start_stations": selected_starts,
            "distances": selected_distances,
        }

        results.append(result)
        processed += 1

        print(f"✅ 選択: {selected_starts}")
        print(f"📏 距離: {selected_distances}")

    print("\n📈 分析完了!")
    print(f"✅ 処理成功: {processed}個")
    print(f"⚠️ スキップ: {skipped}個")
    print(f"📦 総結果: {len(results)}個")

    return results


def get_available_areas():
    """
    area.jsonから利用可能なエリアのリストを取得

    Returns:
        エリア名のリスト
    """
    try:
        with open("area.json", "r", encoding="utf-8") as f:
            area_data = json.load(f)
        return list(area_data.keys())
    except FileNotFoundError:
        print("❌ area.json が見つかりません")
        return []
    except json.JSONDecodeError:
        print("❌ area.json の形式が無効です")
        return []


def generate_all_guess_problems(min_distance=4, max_distance=12, seed=None):
    """
    全エリアのguess問題を生成してoutput/guess/に保存

    Args:
        min_distance: 最小距離
        max_distance: 最大距離
        seed: ランダムシード

    Returns:
        生成結果の辞書
    """
    # ランダムシード設定
    if seed is not None:
        random.seed(seed)
        print(f"🎲 ランダムシード: {seed}")

    # 利用可能なエリアを取得
    areas = get_available_areas()
    if not areas:
        return {}

    # 出力ディレクトリを作成
    output_dir = Path("output/guess")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"🎯 全{len(areas)}エリアのguess問題生成開始")
    print(f"📏 距離範囲: {min_distance}~{max_distance}駅")
    print(f"📁 出力先: {output_dir}")
    print("=" * 60)

    results = {}
    total_problems = 0

    for i, area in enumerate(areas, 1):
        print(f"\n📍 エリア {i}/{len(areas)}: {area}")
        print("-" * 40)

        try:
            # guess問題生成
            area_results = analyze_area_distances(
                area_key=area, min_distance=min_distance, max_distance=max_distance
            )

            if area_results:
                # ファイル保存
                filename = f"guess_problems_{area}.json"
                filepath = output_dir / filename

                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(area_results, f, ensure_ascii=False, indent=2)

                results[area] = {
                    "success": True,
                    "count": len(area_results),
                    "filename": str(filepath),
                }

                total_problems += len(area_results)
                print(f"✅ {area}: {len(area_results)}問題を生成 → {filepath}")
            else:
                results[area] = {
                    "success": False,
                    "count": 0,
                    "filename": None,
                    "error": "問題生成失敗",
                }
                print(f"❌ {area}: 問題生成失敗")

        except Exception as e:
            results[area] = {
                "success": False,
                "count": 0,
                "filename": None,
                "error": str(e),
            }
            print(f"❌ {area}: エラー - {e}")

    # 生成結果のサマリー
    print("\n" + "=" * 60)
    print("🎉 全エリア生成完了!")
    print("-" * 30)

    successful_areas = [area for area, result in results.items() if result["success"]]
    failed_areas = [area for area, result in results.items() if not result["success"]]

    print(f"✅ 成功: {len(successful_areas)}エリア")
    print(f"❌ 失敗: {len(failed_areas)}エリア")
    print(f"📊 総問題数: {total_problems}問題")

    if successful_areas:
        print("\n📝 生成されたファイル:")
        for area in successful_areas:
            result = results[area]
            print(f"  {area}: {result['filename']} ({result['count']}問題)")

    if failed_areas:
        print(f"\n⚠️ 失敗したエリア: {failed_areas}")

    # サマリーファイルを生成
    summary_data = {
        "generated_at": datetime.now().isoformat(),
        "settings": {
            "min_distance": min_distance,
            "max_distance": max_distance,
            "seed": seed,
        },
        "summary": {
            "total_areas": len(areas),
            "successful_areas": len(successful_areas),
            "failed_areas": len(failed_areas),
            "total_problems": total_problems,
        },
        "areas": results,
    }

    summary_file = output_dir / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)

    print(f"\n📋 サマリーファイル: {summary_file}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="goal駅からstart駅への最短距離を分析してguess問題を生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  %(prog)s                                         # 全エリア生成（デフォルト設定）
  %(prog)s --min-distance 3 --max-distance 15     # 距離範囲をカスタマイズ
  %(prog)s --seed 42                               # 再現性のためのシード指定
  %(prog)s --area central                          # 単一エリアのみ生成
        """,
    )

    parser.add_argument(
        "--area", type=str, help="特定エリアのみ生成（未指定の場合は全エリア）"
    )

    parser.add_argument(
        "--min-distance", type=int, default=4, help="最小距離（駅数） (デフォルト: 4)"
    )

    parser.add_argument(
        "--max-distance", type=int, default=12, help="最大距離（駅数） (デフォルト: 12)"
    )

    parser.add_argument("--seed", type=int, help="ランダムシード（再現性のため）")

    parser.add_argument(
        "--list-areas", action="store_true", help="利用可能なエリアを表示して終了"
    )

    args = parser.parse_args()

    # エリア一覧表示
    if args.list_areas:
        areas = get_available_areas()
        print("利用可能なエリア:")
        for area in areas:
            print(f"  {area}")
        return

    if args.area:
        # 単一エリアの処理
        if args.seed is not None:
            random.seed(args.seed)
            print(f"🎲 ランダムシード: {args.seed}")

        results = analyze_area_distances(
            area_key=args.area,
            min_distance=args.min_distance,
            max_distance=args.max_distance,
        )

        if not results:
            print("❌ 分析結果がありません")
            return

        # 出力ディレクトリを作成
        output_dir = Path("output/guess")
        output_dir.mkdir(parents=True, exist_ok=True)

        # ファイル保存
        filename = f"guess_problems_{args.area}.json"
        filepath = output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n💾 結果を保存: {filepath}")
        print("📋 出力形式: リスト[辞書{goal_station, start_stations, distances}]")

        # 単一エリア用のサマリーファイルを生成
        summary_data = {
            "generated_at": datetime.now().isoformat(),
            "settings": {
                "min_distance": args.min_distance,
                "max_distance": args.max_distance,
                "seed": args.seed,
                "single_area": args.area,
            },
            "summary": {
                "total_areas": 1,
                "successful_areas": 1,
                "failed_areas": 0,
                "total_problems": len(results),
            },
            "areas": {
                args.area: {
                    "success": True,
                    "count": len(results),
                    "filename": str(filepath),
                }
            },
        }

        summary_file = output_dir / "summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)

        print(f"📋 サマリーファイル: {summary_file}")
    else:
        # 全エリアの処理
        generate_all_guess_problems(
            min_distance=args.min_distance,
            max_distance=args.max_distance,
            seed=args.seed,
        )


if __name__ == "__main__":
    main()
