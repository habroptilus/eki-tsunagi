#!/usr/bin/env python3
"""
生成されたクイズファイルを読み取って連結成分数をシミュレーションするスクリプト
"""
import json
from collections import deque


def load_graph_data():
    """グラフデータを読み込む"""
    with open("output/graph_tokyo_walking.json", "r", encoding="utf-8") as f:
        return json.load(f)


def count_connected_components(graph, stations):
    """
    指定された駅集合における連結成分の個数を計算
    
    Args:
        graph: グラフデータ
        stations: 調べる駅のリスト
    
    Returns:
        連結成分の個数
    """
    if not stations:
        return 0
    
    station_set = set(stations)
    visited = set()
    components = 0
    
    for station in stations:
        if station not in visited and station in graph:
            # 新しい連結成分を発見
            components += 1
            
            # BFSでこの連結成分の全ての駅を訪問
            queue = deque([station])
            visited.add(station)
            
            while queue:
                current = queue.popleft()
                
                for edge in graph.get(current, {}).get("edges", []):
                    neighbor = edge["station"]
                    if neighbor in station_set and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
    
    return components


def simulate_quiz_progression(graph, quiz_data):
    """
    クイズの進行をシミュレーションして連結成分数の推移を計算
    
    Args:
        graph: グラフデータ
        quiz_data: クイズデータ（start_stations, questions）
    
    Returns:
        dict: シミュレーション結果
    """
    start_stations = quiz_data["start_stations"]
    questions = quiz_data["questions"]
    
    # 正解駅のみを抽出（順序維持）
    correct_questions = [q for q in questions if q["is_correct"]]
    
    # スタート駅から開始
    current_stations = start_stations.copy()
    
    # 連結成分数の推移を記録
    progression = []
    
    # 初期状態
    initial_components = count_connected_components(graph, current_stations)
    progression.append({
        "step": 0,
        "added_station": None,
        "current_stations": current_stations.copy(),
        "connected_components": initial_components
    })
    
    max_components = initial_components
    
    # 正解駅を順次追加
    for i, question in enumerate(correct_questions, 1):
        station = question["station"]
        current_stations.append(station)
        components = count_connected_components(graph, current_stations)
        
        progression.append({
            "step": i,
            "added_station": station,
            "current_stations": current_stations.copy(),
            "connected_components": components
        })
        
        max_components = max(max_components, components)
    
    return {
        "start_stations": start_stations,
        "total_correct_stations": len(correct_questions),
        "max_connected_components": max_components,
        "actual_max_from_data": quiz_data.get("max_connected_components", "N/A"),
        "progression": progression
    }


def analyze_all_quizzes(quiz_file_path):
    """
    クイズファイル内の全クイズを分析
    
    Args:
        quiz_file_path: クイズファイルのパス
    
    Returns:
        分析結果のリスト
    """
    # クイズデータを読み込み
    with open(quiz_file_path, "r", encoding="utf-8") as f:
        quizzes = json.load(f)
    
    # グラフデータを読み込み
    graph = load_graph_data()
    
    results = []
    
    print(f"📊 {len(quizzes)}個のクイズを分析中...")
    print("=" * 60)
    
    for i, quiz in enumerate(quizzes, 1):
        print(f"\n🔍 クイズ {i} 分析中...")
        
        result = simulate_quiz_progression(graph, quiz)
        results.append(result)
        
        # 結果表示
        print(f"  スタート駅: {result['start_stations']}")
        print(f"  正解駅数: {result['total_correct_stations']} 駅")
        print(f"  シミュレーション最大連結成分数: {result['max_connected_components']}")
        print(f"  データ記録値: {result['actual_max_from_data']}")
        
        # 値が一致しているかチェック
        if result['max_connected_components'] == result['actual_max_from_data']:
            print("  ✅ 値が一致")
        else:
            print("  ⚠️ 値が不一致")
    
    return results


def show_detailed_progression(result, quiz_index):
    """
    詳細な連結成分数の推移を表示
    
    Args:
        result: シミュレーション結果
        quiz_index: クイズ番号
    """
    print(f"\n📈 クイズ {quiz_index} の詳細推移:")
    print("-" * 50)
    
    for step_data in result["progression"]:
        step = step_data["step"]
        station = step_data["added_station"]
        components = step_data["connected_components"]
        
        if step == 0:
            print(f"初期状態: 連結成分数 {components}")
        else:
            print(f"ステップ {step}: {station} 追加 → 連結成分数 {components}")
    
    print(f"\n最大連結成分数: {result['max_connected_components']}")


def export_results(results, output_file):
    """
    結果をJSONファイルに出力
    
    Args:
        results: 分析結果のリスト
        output_file: 出力ファイル名
    """
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 結果を {output_file} に保存しました")


def main():
    """メイン関数"""
    print("🎯 クイズシミュレーションスクリプト")
    print("=" * 40)
    
    # 入力ファイルを指定
    quiz_file = input("クイズファイル名を入力してください [quizzes_central_10.json]: ").strip()
    if not quiz_file:
        quiz_file = "quizzes_central_10.json"
    
    try:
        # 全クイズを分析
        results = analyze_all_quizzes(quiz_file)
        
        # 統計情報表示
        print(f"\n📈 統計情報:")
        print("-" * 30)
        
        max_components_list = [r["max_connected_components"] for r in results]
        actual_max_list = [r["actual_max_from_data"] for r in results if isinstance(r["actual_max_from_data"], int)]
        
        print(f"平均最大連結成分数: {sum(max_components_list) / len(max_components_list):.2f}")
        print(f"最大値: {max(max_components_list)}")
        print(f"最小値: {min(max_components_list)}")
        
        # 値の一致率
        if actual_max_list:
            matches = sum(1 for r in results if r["max_connected_components"] == r["actual_max_from_data"])
            match_rate = matches / len(results) * 100
            print(f"データとの一致率: {match_rate:.1f}% ({matches}/{len(results)})")
        
        # 詳細表示オプション
        show_detail = input("\n詳細な推移を表示しますか？ (クイズ番号を入力、Enterでスキップ): ").strip()
        if show_detail.isdigit():
            quiz_num = int(show_detail)
            if 1 <= quiz_num <= len(results):
                show_detailed_progression(results[quiz_num - 1], quiz_num)
        
        # 結果出力オプション
        export_option = input("\n結果をJSONファイルに出力しますか？ (y/N): ").strip().lower()
        if export_option == 'y':
            output_file = f"simulation_results_{quiz_file.replace('.json', '')}.json"
            export_results(results, output_file)
        
    except FileNotFoundError:
        print(f"❌ ファイル '{quiz_file}' が見つかりません")
    except json.JSONDecodeError:
        print(f"❌ ファイル '{quiz_file}' の形式が正しくありません")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    main()