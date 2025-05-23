import random
import urllib
from collections import deque
from typing import Dict, List, Set

from pydantic import BaseModel


def choose_goal(visited: list[str], candidates: set[str]) -> str:
    return random.choice(list(candidates.difference(set(visited))))


class Edge(BaseModel):
    from_station: str
    to_station: str
    line: str


def add_candidates(
    candidates: list[Edge],
    visited_station: str,
    graph_data: dict[str, list[dict[str, str]]],
    visited_stations: list[str],
) -> list[Edge]:
    edges_to_be_added = list(
        [
            Edge(
                from_station=visited_station,
                to_station=item["station"],
                line=item["line"],
            )
            for item in graph_data[visited_station]
        ]
    )
    combined = candidates + edges_to_be_added

    filtered = [edge for edge in combined if edge.to_station not in visited_stations]

    return filtered


def find_shortest_path(
    graph: Dict[str, List[Dict]], goal: str, visited: List[str]
) -> list[tuple[str, str | None]] | None:
    queue = deque()
    visited_set: Set[str] = set()
    prev: dict[str, tuple[str | None, str | None]] = {}

    queue.append(goal)
    visited_set.add(goal)
    prev[goal] = (None, None)

    while queue:
        current = queue.popleft()

        if current in visited:
            path: list[tuple[str, str | None]] = []
            while current is not None:
                prev_station, line = prev[current]
                path.append((current, line))
                current = prev_station
            return path

        for edge in graph.get(current, []):
            neighbor = edge["station"]
            line = edge["line"]

            if neighbor not in visited_set:
                visited_set.add(neighbor)
                queue.append(neighbor)
                prev[neighbor] = (current, line)

    return None


def _find_shortest_paths_to_visited_stations(
    graph: Dict[str, List[Dict]], goal: str, visited: List[str], top_n=int
) -> List[List[tuple[str, str | None]]]:
    queue = deque()
    visited_set: Set[str] = set()
    prev: dict[str, tuple[str | None, str | None]] = {}

    queue.append(goal)
    visited_set.add(goal)
    prev[goal] = (None, None)

    found_paths: List[List[tuple[str, str | None]]] = []
    visited_targets = set(visited)
    found_stations: Set[str] = set()  # 記録する出発駅

    while queue and len(found_stations) < top_n:
        current = queue.popleft()

        if current in visited_targets and current not in found_stations:
            # reconstruct path
            path: List[tuple[str, str | None]] = []
            temp = current
            while temp is not None:
                prev_station, line = prev[temp]
                path.append((temp, line))
                temp = prev_station
            found_paths.append(path)
            found_stations.add(current)

        for edge in graph.get(current, []):
            neighbor = edge["station"]
            line = edge["line"]

            if neighbor not in visited_set:
                visited_set.add(neighbor)
                queue.append(neighbor)
                prev[neighbor] = (current, line)

    # sort paths by length (shortest first)
    found_paths.sort(key=len)

    return found_paths


def calculate_hints(graph, goal, candidates, choices_num):
    shortest_path_list = _find_shortest_paths_to_visited_stations(
        graph=graph, goal=goal, visited=candidates, top_n=choices_num
    )
    hints = [shortest_path[0][0] for shortest_path in shortest_path_list]
    # random.shuffle(hints) shuffleするとおかしくなる
    return hints


def calculate_score(
    shortest_steps: int,
    lost_life: int | None = None,
    used_hints: int | None = None,
    actual_steps: int | None = None,
    penalty_per_step: int = 3,
    penalty_per_hint: int = 2,
    min_score: int = 10,
    max_score: int = 20,
    fail_score: int = 0,
) -> tuple[int, str]:
    if actual_steps is None:
        return fail_score

    excess = actual_steps - shortest_steps
    penalty = (
        (actual_steps - shortest_steps) * penalty_per_step
        + lost_life
        + used_hints * penalty_per_hint
    )
    raw_score = max_score - penalty
    header = f"{max_score}点 − (🚃 {excess} × {penalty_per_step} + 🩷 {lost_life} + 💡 {used_hints} × {penalty_per_hint})"
    result = (
        f"= **{raw_score} / 20 点**"
        if min_score <= raw_score
        else f"= {raw_score} -> **{min_score} / {max_score} 点** (クリアで10点に切り上げ) "
    )
    step_info = f"訪問駅数 {actual_steps}駅 ／ 最短 {shortest_steps}駅（+ {excess} 🚃）"
    explanation = f"""{step_info}  \n{header}  \n{result}"""
    return max(raw_score, min_score), explanation


def calculate_score_on_failure(graph_data, goal, visited, shortest_path):
    shortest_path_of_end_state = find_shortest_path(
        graph=graph_data,
        goal=goal,
        visited=visited,
    )
    progress_steps = len(shortest_path) - len(shortest_path_of_end_state)

    score = min(progress_steps, 10)
    return score, progress_steps


def get_result_title(area: str, score: int, max_score: int):
    if score == max_score:
        return f"{area}の特急ライダー"

    ratio = score / max_score
    if ratio >= 0.9:
        return f"{area}の急行ナビゲーター"
    elif ratio >= 0.75:
        return f"{area}の快速トラベラー"
    elif ratio >= 0.5:
        return f"{area}の各駅停車ルーキー"
    else:
        return f"{area}の乗り換え初心者"


def get_result_comment(score: int, max_score: int):
    if score == max_score:
        return "駅つなぎの神降臨🧝‍♀️"
    ratio = score / max_score
    if ratio >= 0.9:
        return "もうプロじゃん！次は駅長狙う？👨‍✈️"
    elif ratio >= 0.75:
        return "惜しい！プロまでもうちょい！👩‍💻"
    elif ratio >= 0.5:
        return "迷子でも楽しむ気持ちが大事😉"
    else:
        return "もう一回トライ！出発進行〜🚃"


def create_text_for_x(score: int, title: str, max_score: int) -> str:
    lines = []

    ratio = score / max_score
    if score == max_score:
        content = "駅つなぎで満点出してしまった💯"
    elif ratio >= 0.9:
        content = f"駅つなぎで{score}点とった！特技だ！🚃"
    elif ratio >= 0.75:
        content = f"駅つなぎで{score}点とった！マスターになれそう🫡"
    elif ratio >= 0.5:
        content = f"駅つなぎで{score}点とった！惜しい〜😬"
    else:
        content = f"駅つなぎで{score}点とった！目指せ高得点！🫣"

    lines.append(content)

    # ハッシュタグ（例）
    hashtags = f"#{title} #駅つなぎ"
    lines.append(f"\n{hashtags}")

    url = "https://eki-tsunagi.smartbowwow.com"
    lines.append(f"\n{url}")

    # 最終テキストを結合
    result = "\n".join(lines)
    return urllib.parse.quote(result)
