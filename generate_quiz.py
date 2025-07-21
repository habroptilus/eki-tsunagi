#!/usr/bin/env python3
"""
area.jsonのstartから3駅をランダムにピックし、
これらを含む最小連結成分を計算して正解の駅を出力するスクリプト
"""

import json
import random
from collections import deque


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
        "yokohama": "output/graph_tokyo_walking.json",  # 横浜も東京グラフを使用
        "osaka": "output/graph_osaka_walking.json",
        "nagoya": "output/graph_nagoya_walking.json"
    }
    
    graph_file = graph_file_map.get(area_key, "output/graph_tokyo_walking.json")
    
    try:
        with open(graph_file, "r", encoding="utf-8") as f:
            graph_data = json.load(f)
    except FileNotFoundError:
        print(f"警告: グラフファイル {graph_file} が見つかりません。東京グラフを使用します。")
        with open("output/graph_tokyo_walking.json", "r", encoding="utf-8") as f:
            graph_data = json.load(f)

    return area_data, graph_data


def find_shortest_path_between_stations(graph, start, end):
    """
    2駅間の最短パスを見つける

    Args:
        graph: グラフデータ
        start: 開始駅
        end: 終了駅

    Returns:
        最短パスの駅リスト（startからendまで）
    """
    if start == end:
        return [start]

    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        current, path = queue.popleft()

        for edge in graph.get(current, {}).get("edges", []):
            neighbor = edge["station"]
            if neighbor == end:
                return path + [neighbor]

            if neighbor not in visited and neighbor in graph:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return []  # パスが見つからない場合


def find_minimal_connected_component(graph, target_stations):
    """
    シュタイナー木の2-近似アルゴリズムを使用して最小連結成分を計算

    アルゴリズム：
    1. 全ペア間の最短距離を計算
    2. 距離重み付き完全グラフを作成
    3. 最小全域木(MST)を計算
    4. MSTの各辺に対応する元グラフの最短パスを結合

    Args:
        graph: グラフデータ（駅名をキーとする辞書）
        target_stations: 含める必要がある駅のリスト

    Returns:
        最小連結成分に含まれる駅のセット
    """
    # target_stationsがグラフに存在するかチェック
    for station in target_stations:
        if station not in graph:
            print(f"警告: 駅 '{station}' がグラフに存在しません")
            return set()

    if len(target_stations) < 2:
        return set(target_stations)

    if len(target_stations) == 2:
        path = find_shortest_path_between_stations(
            graph, target_stations[0], target_stations[1]
        )
        return set(path) if path else set()

    # ステップ1: 全ペア間の最短距離とパスを計算
    distances = {}
    paths = {}

    for i, station1 in enumerate(target_stations):
        for j, station2 in enumerate(target_stations):
            if i < j:  # 対称なので片方向のみ計算
                path = find_shortest_path_between_stations(graph, station1, station2)
                if not path:
                    print(f"エラー: {station1} と {station2} が接続されていません")
                    return set()

                distance = len(path) - 1  # エッジ数
                distances[(station1, station2)] = distance
                paths[(station1, station2)] = path

    # ステップ2&3: 最小全域木(MST)を計算（Kruskalアルゴリズム）
    edges = [(dist, s1, s2) for (s1, s2), dist in distances.items()]
    edges.sort()  # 距離でソート

    # Union-Find データ構造
    parent = {station: station for station in target_stations}

    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
            return True
        return False

    mst_edges = []
    for dist, s1, s2 in edges:
        if union(s1, s2):
            mst_edges.append((s1, s2))
            if len(mst_edges) == len(target_stations) - 1:
                break

    # ステップ4: MSTの各辺に対応する最短パスを結合
    result_stations = set()

    for s1, s2 in mst_edges:
        # 正規化されたキーを使ってパスを取得
        if (s1, s2) in paths:
            path = paths[(s1, s2)]
        else:
            path = paths[(s2, s1)]

        result_stations.update(path)

    print(f"🔗 MST エッジ数: {len(mst_edges)}")
    print(f"📊 結果ノード数: {len(result_stations)} 駅")

    return result_stations


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


def select_disconnected_stations(graph, candidates, count):
    """
    候補駅からお互いに接続していない駅を指定数選択

    Args:
        graph: グラフデータ
        candidates: 候補駅のリスト
        count: 選択する駅数

    Returns:
        お互いに接続していない駅のリスト（失敗時はNone）
    """
    import itertools

    # 最大試行回数
    max_attempts = 1000

    for attempt in range(max_attempts):
        # ランダムに候補を選択
        if len(candidates) < count:
            return None

        selected = random.sample(candidates, count)

        # 選択された駅がお互いに接続していないかチェック
        all_disconnected = True

        for i, j in itertools.combinations(range(len(selected)), 2):
            station1, station2 = selected[i], selected[j]

            # station1がstation2に隣接しているかチェック
            if station1 in graph and station2 in graph:
                station1_neighbors = {
                    edge["station"] for edge in graph[station1].get("edges", [])
                }
                if station2 in station1_neighbors:
                    all_disconnected = False
                    break

        if all_disconnected:
            print(f"✅ 非接続な{count}駅を{attempt+1}回目で発見")
            return selected

    print(f"❌ {max_attempts}回試行しても非接続な{count}駅を見つけられませんでした")
    return None


def is_connected_to_current_stations(graph, target_station, current_stations):
    """
    指定された駅が現在の駅集合に接続されているかチェック

    Args:
        graph: グラフデータ
        target_station: チェック対象の駅
        current_stations: 現在の駅集合

    Returns:
        bool: 接続されている場合True
    """
    if target_station not in graph:
        return False

    current_set = set(current_stations)

    # target_stationの隣接駅をチェック
    for edge in graph[target_station].get("edges", []):
        neighbor = edge["station"]
        if neighbor in current_set:
            return True

    return False


def sort_answer_stations_by_connectivity(graph, start_stations, answer_stations):
    """
    スタート駅+これまで追加した駅に接続されていない駅を優先して前に並べるように正解駅をソート

    Args:
        graph: グラフデータ
        start_stations: スタート駅のリスト
        answer_stations: 正解駅のリスト

    Returns:
        ソートされた正解駅のリスト
    """
    remaining_answers = answer_stations.copy()
    current_stations = start_stations.copy()
    sorted_answers = []

    while remaining_answers:
        # 現在の駅集合（スタート駅+これまで追加した駅）に接続されていない駅を探す
        unconnected = []
        connected = []

        for station in remaining_answers:
            if is_connected_to_current_stations(graph, station, current_stations):
                connected.append(station)
            else:
                unconnected.append(station)

        # 接続されていない駅が存在する場合、それを優先
        if unconnected:
            # 接続されていない駅からランダムに1つ選択
            next_station = random.choice(unconnected)
        else:
            # 全て接続されている場合、ランダムに選択
            next_station = random.choice(connected)

        # 選択された駅を追加
        sorted_answers.append(next_station)
        current_stations.append(next_station)
        remaining_answers.remove(next_station)

    return sorted_answers


def analyze_connectivity_progression(graph, start_stations, sorted_answer_stations):
    """
    ソート済み正解駅を順次追加し、最大連結成分数を分析

    Args:
        graph: グラフデータ
        start_stations: スタート駅のリスト
        sorted_answer_stations: ソート済み正解駅のリスト

    Returns:
        最大連結成分数、連結成分数の推移リスト
    """
    # 既にソート済みの正解駅を使用

    # スタート駅から開始
    current_stations = start_stations.copy()

    # 初期連結成分数
    initial_components = count_connected_components(graph, current_stations)
    max_components = initial_components
    component_counts = [initial_components]

    # 正解駅を順次追加して連結成分数を記録
    for answer_station in sorted_answer_stations:
        current_stations.append(answer_station)
        components = count_connected_components(graph, current_stations)
        component_counts.append(components)
        max_components = max(max_components, components)

    return max_components, component_counts


def calculate_distances_from_stations(graph, start_stations):
    """
    複数のスタート駅からの各駅への最短距離を計算

    Args:
        graph: グラフデータ
        start_stations: スタート駅のリスト

    Returns:
        各駅への最短距離の辞書
    """
    distances = {}

    # 複数点BFS
    queue = deque()
    visited = set()

    # 全てのスタート駅を初期化
    for station in start_stations:
        if station in graph:
            queue.append((station, 0))
            distances[station] = 0
            visited.add(station)

    while queue:
        current, dist = queue.popleft()

        # 隣接駅を探索
        for edge in graph.get(current, {}).get("edges", []):
            neighbor = edge["station"]
            if neighbor not in visited and neighbor in graph:
                visited.add(neighbor)
                distances[neighbor] = dist + 1
                queue.append((neighbor, dist + 1))

    return distances


def generate_dummy_stations(
    graph_data, start_stations, answer_stations, area_goal_stations, num_dummies=5
):
    """
    ダミー駅を生成する（同じエリアのgoal駅から、スタート駅・正解駅以外で、それらと隣接していない駅を選択）

    Args:
        graph_data: グラフデータ
        start_stations: スタート駅のリスト
        answer_stations: 正解駅のリスト
        area_goal_stations: 同じエリアのgoal駅のリスト
        num_dummies: 生成するダミー駅数

    Returns:
        ダミー駅のリスト
    """
    excluded_stations = set(start_stations + answer_stations)

    # スタート駅と正解駅の隣接駅を取得
    adjacent_stations = set()
    for station in start_stations + answer_stations:
        if station in graph_data:
            for edge in graph_data[station].get("edges", []):
                adjacent_stations.add(edge["station"])

    # ダミー候補を同じエリアのgoal駅から生成（除外駅でも隣接駅でもない駅）
    dummy_candidates = []
    for station in area_goal_stations:
        if station not in excluded_stations and station not in adjacent_stations:
            dummy_candidates.append(station)

    # 十分な候補がない場合は隣接制限を緩和
    if len(dummy_candidates) < num_dummies:
        print(f"⚠️ 非隣接ダミー候補が不足（{len(dummy_candidates)}駅）、隣接制限を緩和")
        for station in area_goal_stations:
            if station not in excluded_stations:
                dummy_candidates.append(station)
        # 重複除去
        dummy_candidates = list(set(dummy_candidates))

    # ランダムに選択
    if len(dummy_candidates) >= num_dummies:
        selected_dummies = random.sample(dummy_candidates, num_dummies)
    else:
        selected_dummies = dummy_candidates  # 全て使用

    print(f"🎭 ダミー駅数: {len(selected_dummies)} 駅（エリアgoal駅から選択）")
    return selected_dummies


def create_question_list(sorted_answer_stations, dummy_stations):
    """
    正解駅とダミー駅をランダムに混ぜてから、正解駅のみを指定順序に並び替えてquestionリストを作成

    Args:
        sorted_answer_stations: ソート済み正解駅のリスト
        dummy_stations: ダミー駅のリスト

    Returns:
        questionのリスト（dictのリスト）
    """
    questions = []

    # 正解駅とダミー駅を全て混ぜる
    all_stations = []
    
    # 正解駅を追加
    for answer_station in sorted_answer_stations:
        all_stations.append({"station": answer_station, "is_correct": True})
    
    # ダミー駅を追加
    for dummy_station in dummy_stations:
        all_stations.append({"station": dummy_station, "is_correct": False})
    
    # 全てをランダムにシャッフル
    random.shuffle(all_stations)
    
    # 正解駅のみを元の順序に並び替える
    # 1. 正解駅の位置を記録
    correct_positions = []
    for i, question in enumerate(all_stations):
        if question["is_correct"]:
            correct_positions.append(i)
    
    # 2. 正解駅を元の順序で正解駅の位置に配置
    for i, position in enumerate(correct_positions):
        if i < len(sorted_answer_stations):
            all_stations[position] = {"station": sorted_answer_stations[i], "is_correct": True}
    
    return all_stations


def generate_quiz(area_key="central"):
    """
    クイズを生成する

    Args:
        area_key: area.jsonのキー（デフォルト: "central"）

    Returns:
        スタート駅のリスト、正解駅のリスト
    """
    area_data, graph_data = load_data(area_key)

    if area_key not in area_data:
        print(f"エラー: エリア '{area_key}' が見つかりません")
        return None, None

    goal_candidates = area_data[area_key]["goal"]

    # 重複を除去
    unique_goal_candidates = list(set(goal_candidates))

    if len(unique_goal_candidates) < 3:
        print(f"エラー: エリア '{area_key}' のユニークなgoal駅が3駅未満です")
        print(f"  元のgoal駅数: {len(goal_candidates)}")
        print(f"  ユニークなgoal駅数: {len(unique_goal_candidates)}")
        return None, None

    # 3駅を非接続になるようにピック
    start_stations = select_disconnected_stations(graph_data, unique_goal_candidates, 3)

    if not start_stations:
        print("エラー: 非接続な3駅を見つけることができませんでした")
        return None, None

    # 重複チェック（デバッグ用）
    if len(start_stations) != len(set(start_stations)):
        print(f"⚠️ 警告: スタート駅に重複があります: {start_stations}")
        return None, None

    print(f"🚉 スタート駅: {start_stations}")

    # 最小連結成分を計算
    component = find_minimal_connected_component(graph_data, start_stations)

    if not component:
        return None, None

    print(f"📊 連結成分のサイズ: {len(component)} 駅")

    # スタート駅を除いた正解の駅
    answer_stations = list(component - set(start_stations))

    print(f"✅ 正解駅数: {len(answer_stations)} 駅")

    # 正解駅を正しい順序（未接続優先）で並び替え
    sorted_answer_stations = sort_answer_stations_by_connectivity(
        graph_data, start_stations, answer_stations
    )

    # 連結成分数の推移を分析（ソート済み順序を使用）
    max_components, component_progression = analyze_connectivity_progression(
        graph_data, start_stations, sorted_answer_stations
    )

    print(f"🔗 最大連結成分数: {max_components}")

    # ダミー駅を生成（同じエリアのgoal駅から）
    dummy_stations = generate_dummy_stations(
        graph_data, start_stations, answer_stations, unique_goal_candidates
    )

    # questionリストを作成
    questions = create_question_list(sorted_answer_stations, dummy_stations)

    return start_stations, questions, max_components


def generate_multiple_quizzes(area_key="central", iterations=10):
    """
    複数のクイズを生成してJSON形式で出力

    Args:
        area_key: area.jsonのキー
        iterations: 生成するクイズの数

    Returns:
        クイズのリスト（辞書のリスト）
    """
    quizzes = []

    print(f"🎯 {area_key}エリアで{iterations}個のクイズを生成中...")
    print("=" * 50)

    for i in range(iterations):
        print(f"\n📝 クイズ {i+1}/{iterations}")
        result = generate_quiz(area_key)

        if result and len(result) == 3:
            start_stations, questions, max_components = result
            quiz = {
                "start_stations": start_stations,
                "questions": questions,
                "max_connected_components": max_components,
            }
            quizzes.append(quiz)
            print(f"✅ クイズ {i+1} 生成完了")
        else:
            print(f"❌ クイズ {i+1} 生成失敗")

    print(f"\n🎉 {len(quizzes)}/{iterations} 個のクイズを生成しました")
    return quizzes


def main():
    """メイン関数"""
    print("🎯 駅つなぎクイズ生成スクリプト")
    print("=" * 40)

    # エリアを選択（デフォルトは central）
    area_key = input(
        "エリアを選択してください (central/east/west/north/south/yokohama/nagoya/osaka) [central]: "
    ).strip()
    if not area_key:
        area_key = "central"

    # 生成回数を選択
    iterations_input = input("生成するクイズ数を入力してください [10]: ").strip()
    try:
        iterations = int(iterations_input) if iterations_input else 10
    except ValueError:
        iterations = 10

    # 複数クイズを生成
    quizzes = generate_multiple_quizzes(area_key, iterations)

    if quizzes:
        # JSON形式で出力
        output_filename = f"quizzes_{area_key}_{len(quizzes)}.json"

        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(quizzes, f, ensure_ascii=False, indent=2)

        print(f"\n💾 {output_filename} に保存しました")
        print(f"📊 生成されたクイズ数: {len(quizzes)}")

        # サンプル表示
        if quizzes:
            print("\n📝 サンプル（クイズ1）:")
            sample = quizzes[0]
            print(f"  スタート駅: {sample['start_stations']}")

            # 正解駅とダミー駅の数を計算
            correct_questions = [q for q in sample["questions"] if q["is_correct"]]
            dummy_questions = [q for q in sample["questions"] if not q["is_correct"]]

            print(f"  正解駅数: {len(correct_questions)} 駅")
            print(f"  ダミー駅数: {len(dummy_questions)} 駅")
            print(f"  最大連結成分数: {sample['max_connected_components']}")

            show_sample = (
                input("\nサンプルの詳細を表示しますか? (y/N): ").strip().lower()
            )
            if show_sample == "y":
                print("  クエスチョン一覧:")
                for i, q in enumerate(
                    sample["questions"][:15], 1
                ):  # 最初の15駅のみ表示
                    status = "✅正解" if q["is_correct"] else "🎭ダミー"
                    print(f"    {i:2d}. {q['station']} ({status})")
                if len(sample["questions"]) > 15:
                    print(f"    ... 他{len(sample['questions'])-15}駅")
    else:
        print("❌ クイズの生成に失敗しました")


if __name__ == "__main__":
    main()
