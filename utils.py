import random
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

    filtered = [edge for edge in combined if edge.to_station != visited_station]

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
    return [shortest_path[0][0] for shortest_path in shortest_path_list]


def calculate_score(
    shortest_steps: int,
    lost_life: int | None = None,
    used_hints: int | None = None,
    actual_steps: int | None = None,
    penalty_per_step: int = 3,
    min_score: int = 10,
    max_score: int = 20,
    fail_score: int = 0,
) -> tuple[int, str]:
    if actual_steps is None:
        return fail_score

    excess = actual_steps - shortest_steps
    penalty = (
        (actual_steps - shortest_steps) * penalty_per_step + lost_life + used_hints
    )
    raw_score = max_score - penalty
    header = f"{max_score}点 − (超過駅数 {excess} × {penalty_per_step} + 失ったライフ {lost_life} + 使ったヒント {used_hints})"
    result = (
        f"= **{raw_score} / 20 点**"
        if min_score <= raw_score
        else f"= {raw_score} -> **{min_score} / {max_score} 点** (クリアで10点に切り上げ) "
    )
    step_info = f"訪問駅数 {actual_steps}駅 ／ 最短 {shortest_steps}駅（+{excess}）"
    explanation = f"""{step_info}  \n{header}  \n{result}"""
    return max(raw_score, min_score), explanation
