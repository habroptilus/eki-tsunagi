import json
import random
import textwrap
import urllib.parse

import streamlit as st
import streamlit.components.v1 as components

from utils import (
    Edge,
    add_candidates,
    calculate_hints,
    calculate_score,
    calculate_score_on_failure,
    choose_goal,
    create_text_for_x,
    find_shortest_path,
    get_result_comment,
    get_result_title,
)

st.set_page_config(
    page_title="駅つなぎ",
    page_icon="🚃",
)


def draw_header():
    components.html(
        """
        <div style="width: 100%; display: flex; justify-content: center;">
            <h1 style="
                background: linear-gradient(to right, #42a5f5, #1e88e5);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 2.4rem;
                font-weight: 900;
                font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
                letter-spacing: 0.05em;
                margin-top: 0.8rem;
                margin-bottom: 0.3rem;
                text-align: center;
            ">
                🚃 駅つなぎ 🚃
            </h1>
        </div>
        """,
        height=70,
    )


def share_to_x(text: str, url: str | None = None):
    tweet_text = urllib.parse.quote(text)
    share_url = f"https://twitter.com/intent/tweet?text={tweet_text}"
    if url is not None:
        share_url += f"&url={urllib.parse.quote(url)}"
    st.markdown(
        f'<a href="{share_url}" target="_blank" style="text-decoration:none;">'
        '<button style="background-color:#000000; color:white; border:none; padding:0.5rem 1rem; '
        'border-radius:5px; cursor:pointer;">'
        "Xでシェアする</button></a>",
        unsafe_allow_html=True,
    )


draw_header()


@st.cache_data
def load_graph():
    with open("graph.json", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_area():
    with open("area.json", encoding="utf-8") as f:
        return json.load(f)


graph_data = load_graph()
area_data = load_area()
MAX_ROUNDS = 5
CHOICE_NUM = 3
MAX_LIFE = 3
MAX_HINT = 2


def display_matched_edge(matched: list[Edge]) -> None:
    """入力した駅に到達する路線を表示する"""
    edges = "<br>".join(
        [
            f"{candidate.from_station} → {candidate.to_station} ({candidate.line})"
            for candidate in matched
        ]
    )

    st.markdown(
        f"""
<div style="background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px;">
{edges}
</div>
""",
        unsafe_allow_html=True,
    )


def display_path_with_lines(path: list[tuple[str, str | None]], title: str) -> None:
    """経路を路線名も合わせて表示する（折りたたみ付き）."""
    expanded = len(path) - 1 <= 5
    with st.expander(f"📍 {title}", expanded=expanded):
        style = """
        <style>
        .station {
            font-weight: bold;
            font-size: 18px;
            color: #2c3e50;
            margin-bottom: 4px;
        }
        .line-row {
            display: flex;
            align-items: center;
            font-size: 14px;
            color: #16a085;
            margin: 4px 0 8px 10px;
        }
        .arrow {
            margin-right: 4px;
            color: #7f8c8d;
            font-size: 16px;
        }
        </style>
        """
        html = [style, "<div>"]
        for i, (station, line) in enumerate(path):
            html.append(f'<div class="station">{station}</div>')
            if i < len(path) - 1 and line:
                html.append(f"""
                    <div class="line-row">
                        <div class="arrow">⬇</div>
                        <div class="line">{line}</div>
                    </div>
                """)
        html.append("</div>")
        st.markdown("".join(html), unsafe_allow_html=True)


def draw_round_result_success_page():
    with main:
        shortest_steps = len(st.session_state.shortest_path) - 1
        actual_steps = len(st.session_state.round_visited)

        score, explanation = calculate_score(
            shortest_steps=shortest_steps,
            lost_life=MAX_LIFE - st.session_state.life,
            actual_steps=actual_steps,
            used_hints=MAX_HINT - st.session_state.hint,
        )

        st.success(
            f"""🎉 **ラウンド{st.session_state.round} クリア！**  
        {explanation}"""
        )
        st.session_state.scores.append(score)

        display_path_with_lines(
            st.session_state.shortest_path,
            title=f"最短経路の例 ({len(st.session_state.shortest_path)-1}駅)",
        )
        # TODO:共通処理まとめる
        if st.session_state.round == MAX_ROUNDS:
            st.button("最終結果画面へ進む", on_click=handle_go_result)
        else:
            st.button("次のラウンドへ進む", on_click=handle_next_round)


def draw_round_result_fail_page():
    score, progress_steps = calculate_score_on_failure(
        graph_data=graph_data,
        goal=st.session_state.goal,
        visited=st.session_state.visited,
        shortest_path=st.session_state.shortest_path,
    )
    st.error(
        f"到達できませんでした...  \n{progress_steps}駅分だけ近づきました -> **{score}/20 点**"
    )
    st.session_state.scores.append(score)

    display_path_with_lines(
        st.session_state.shortest_path,
        title=f"最短経路の例 ({len(st.session_state.shortest_path)-1}駅)",
    )
    # TODO:共通処理まとめる
    if st.session_state.round == MAX_ROUNDS:
        st.button("最終結果画面へ進む", on_click=handle_go_result)
    else:
        st.button("次のラウンドへ進む", on_click=handle_next_round)


def handle_go_result():
    change_page("game_result")


def handle_next_round():
    start_round()
    change_page("round_play")


def handle_hint_click():
    st.session_state.next_station = st.session_state.hint_radio
    st.session_state.show_hint_modal = False
    handle_move()


def handle_move():
    next_station = st.session_state.next_station
    st.session_state.next_station = ""

    if next_station in st.session_state.visited:
        st.session_state.log_status = "visited"
        return
    elif next_station not in graph_data:
        st.session_state.log_status = "not_exist"
        return
    else:
        matched = [
            c for c in st.session_state.candidates if c.to_station == next_station
        ]
        if matched:
            st.session_state.log_status = "success"
            st.session_state.arrived_station = next_station
            st.session_state.matched_edges = matched

            st.session_state.visited.append(next_station)
            st.session_state.round_visited.append(next_station)
            st.session_state.candidates = add_candidates(
                st.session_state.candidates,
                next_station,
                graph_data,
                st.session_state.visited,
            )

        else:
            st.session_state.log_status = "fail"
            st.session_state.life -= 1

    if st.session_state.life <= 0:
        change_page("round_result_fail")

    elif st.session_state.goal in st.session_state.visited:
        change_page("round_result_success")


def draw_side_bar():
    if "log_status" not in st.session_state:
        return

    if st.session_state.log_status == "visited":
        st.warning("⚠️ その駅はすでに訪れています。")
    elif st.session_state.log_status == "not_exist":
        st.error("🚫 入力された駅はデータに存在しません。")
    elif st.session_state.log_status == "success":
        st.success(f"✅ {st.session_state.arrived_station} に到達！")
        display_matched_edge(st.session_state.matched_edges)
    elif st.session_state.log_status == "fail":
        st.error(f"❌ 隣接していません！ 残ライフ {st.session_state.life}")


def handle_surrender():
    change_page("round_result_fail")


def draw_area_select_page():
    area = st.selectbox(
        "東京都を中心とした一都三県が舞台のゲームです.",
        ["-- エリアを選んでください --", "中心部", "西部・南部", "北部・東部", "全域"],
    )

    if area != "-- エリアを選んでください --":
        if st.button("スタート"):
            st.session_state.area = area
            start_game()
            start_round()
            change_page("round_play")
            st.rerun()


def start_game():
    if st.session_state.area == "全域":
        start_candidates = []
        for area in area_data.values():
            start_candidates += area["start"]
        # 重複を取り除く. あとで綺麗に描き直す
        start_candidates = list(set(start_candidates))
    else:
        start_candidates = area_data[st.session_state.area]["start"]

    st.session_state.visited = random.sample(start_candidates, 3)
    st.session_state.candidates = []
    for start_station in st.session_state.visited:
        st.session_state.candidates = add_candidates(
            st.session_state.candidates,
            start_station,
            graph_data,
            st.session_state.visited,
        )
    st.session_state.scores = []
    st.session_state.goals = []
    st.session_state.round_visited = []
    st.session_state.round = 0
    st.session_state.life = 3


def start_round():
    st.session_state.round_visited = []
    st.session_state.round += 1
    st.session_state.life = MAX_LIFE
    st.session_state.hint = MAX_HINT
    st.session_state.log_status = ""

    if st.session_state.area == "全域":
        goal_candidates = []
        for area in area_data.values():
            goal_candidates += area["goal"]
    else:
        goal_candidates = area_data[st.session_state.area]["goal"]

    goal = choose_goal(st.session_state.visited, set(goal_candidates))
    st.session_state.goal = goal
    st.session_state.goals.append(goal)

    st.session_state.shortest_path = find_shortest_path(
        graph_data,
        goal,
        st.session_state.visited,
    )


def change_page(new_page: str):
    st.session_state.page = new_page


def display_visited_stations():
    if "visited" in st.session_state and st.session_state.visited:
        st.markdown("### 🛤️ 訪問済みの駅")

        tags_html = textwrap.dedent("""
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
        """)
        for station in st.session_state.visited:
            tags_html += textwrap.dedent(f"""
                <div style="
                    background-color: #e0f2f1;
                    color: #004d40;
                    padding: 0.4rem 0.8rem;
                    border-radius: 20px;
                    font-size: 0.9rem;
                    box-shadow: 1px 1px 4px rgba(0,0,0,0.1);
                ">{station}</div>
            """)
        tags_html += "</div>"

        st.markdown(tags_html, unsafe_allow_html=True)
        # 余白を追加
        st.markdown("<br>", unsafe_allow_html=True)  # 空白を追加


def draw_area_status():
    area = st.session_state["area"]
    # エリア表示
    st.markdown(
        f"""
        <div style="
            background-color: #fff3e0;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            font-size: 1.2rem;
            font-weight: bold;
            color: #e65100;
            margin-bottom: 1.5rem;
            box-shadow: 1px 1px 4px rgba(0,0,0,0.1);
        ">
            エリア：{area}
        </div>
    """,
        unsafe_allow_html=True,
    )


def draw_game_status():
    round_num = st.session_state["round"]
    goal = st.session_state.goal
    life = st.session_state.life
    hint = st.session_state.hint

    st.markdown(f"### 🏁 ラウンド {round_num}/{MAX_ROUNDS}")

    st.markdown(
        f"""
        <div style="
            background-color: #e3f2fd;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 1px 1px 6px rgba(0,0,0,0.08);
            display: flex;
            justify-content: space-between;
            flex-wrap: nowrap;
            text-align: center;
        ">
            <div style="flex: 1; min-width: 100px;">
                <div style="font-size: 0.8rem; color: #1565c0;">目的地</div>
                <div style="font-size: 1.2rem; font-weight: bold; margin-top: 0.3rem;">{goal}</div>
            </div>
            <div style="flex: 1; min-width: 100px;">
                <div style="font-size: 0.8rem; color: #1565c0;">残ライフ</div>
                <div style="font-size: 1.2rem; font-weight: bold; margin-top: 0.3rem;">{'🩷' * life}</div>
            </div>
            <div style="flex: 1; min-width: 100px;">
                <div style="font-size: 0.8rem; color: #1565c0;">残ヒント</div>
                <div style="font-size: 1.2rem; font-weight: bold; margin-top: 0.3rem;">{'💡' * hint}</div>
            </div>
        </div>
        <br>
        """,
        unsafe_allow_html=True,
    )


def draw_instruction():
    # ゲームの遊び方を折りたたみ式で表示
    with st.expander("🧭 ゲームの遊び方"):
        st.markdown(
            """
                1. **訪問済みの駅**に隣接する駅を入力して目的地を目指しましょう！
                2. 入力した駅数が少ないほど高得点を獲得できます。
                3. 駅を間違えるとライフを失います。ライフが **0** になるとラウンド失敗！
                4. 目的地に到達できなかった場合でも、目的地に近づいた分だけ **部分点** がもらえます。
                5. **ヒントをもらう** と隣接していて目的地に近づける駅がわかります！

                **さあ、スタート！**
            """,
            unsafe_allow_html=True,
        )


@st.dialog("💡ヒントから選ぶ")
def show_hint_modal():
    hints = calculate_hints(
        graph=graph_data,
        goal=st.session_state.goal,
        candidates=list(set([edge.to_station for edge in st.session_state.candidates])),
        choices_num=CHOICE_NUM,
    )

    with st.form("hint_form"):
        st.radio("", options=hints, horizontal=False, key="hint_radio")
        if st.form_submit_button(
            "回答する",
        ):
            handle_hint_click()
            st.rerun()

    if st.button("戻る"):
        st.session_state.show_hint_modal = False
        st.rerun()


# モーダル表示のための状態を初期化
if "show_hint_modal" not in st.session_state:
    st.session_state.show_hint_modal = False


def draw_round_play_page():
    # draw_area_status() いらないかも
    draw_instruction()
    draw_game_status()
    display_visited_stations()

    st.button(
        "🏳️ 降参する",
        disabled=len(st.session_state.scores) == MAX_ROUNDS,
        on_click=handle_surrender,
    )
    # ボタンを押すとモーダル表示
    if st.button("💡 ヒントを見る", disabled=st.session_state.hint <= 0):
        st.session_state.hint -= 1
        st.session_state.show_hint_modal = True

    if st.session_state.show_hint_modal:
        show_hint_modal()

    st.text_input(
        "訪問済みの駅に隣接した駅名を入力してください",
        key="next_station",
        on_change=handle_move,
        disabled=len(st.session_state.scores) == MAX_ROUNDS,
    )


def share_result_box(
    title: str, total: int, max_score: int, comment: str, url: str | None = None
):
    # スコアに応じた色を決定
    if total >= 80:  # 高得点
        score_color = "#388e3c"  # 緑色
    elif total >= 40:  # 中程度
        score_color = "#fbc02d"  # 黄色
    else:  # 低得点
        score_color = "#d32f2f"  # 赤色

    text_for_x = create_text_for_x(score=total, title=title, max_score=100)
    share_url = f"https://twitter.com/intent/tweet?text={text_for_x}"
    if url is not None:
        share_url += f"&url={urllib.parse.quote(url)}"

    st.markdown(
        f"""
        <div style="
            background-color: #e0f7fa;
            padding: 1.2rem 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
        ">
            <div style="font-size: 1.2rem; color: #00796b; margin-bottom: 0.5rem; font-weight: 600;">
                {title}
            </div>
            <div style="
                font-size: 2.5rem;
                font-weight: bold;
                color: {score_color};
                line-height: 1;
                white-space: nowrap;
                margin-bottom: 0.5rem;
            ">
                {total} <span style="font-size: 1rem; color: #555;">/ {max_score} 点</span>
            </div>
            <div style="font-size: 1rem; color: #444; margin-bottom: 1rem;">
                {comment}
            </div>
            <a href="{share_url}" target="_blank" style="text-decoration:none;">
                <button style="
                    background-color:#000000;
                    color:white;
                    border:none;
                    padding:0.5rem 1rem;
                    border-radius:5px;
                    cursor:pointer;
                ">
                    Xでシェアする
                </button>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def draw_game_result():
    total = sum(st.session_state.scores)

    # スコアに応じた色を決定
    if total >= 80:  # 高得点
        score_color = "#388e3c"  # 緑色
    elif total >= 40:  # 中程度
        score_color = "#fbc02d"  # 黄色
    else:  # 低得点
        score_color = "#d32f2f"  # 赤色

    components.html(
        """
    <div style="
        width: 100%;
        display: flex;
        justify-content: center;
        margin: 0.3rem 0 0.8rem 0;
    ">
        <h2 style="
            font-size: 1.6rem;
            font-weight: 700;
            font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
            color: #1e88e5;
            margin: 0;
        ">
            <span style="filter: brightness(0) saturate(100%) invert(30%) sepia(100%) saturate(2000%) hue-rotate(180deg);">🎉</span>
            結果発表
            <span style="filter: brightness(0) saturate(100%) invert(30%) sepia(100%) saturate(2000%) hue-rotate(180deg);">🎉</span>
        </h2>
    </div>
    """,
        height=60,
    )
    title = get_result_title(st.session_state.area, total, max_score=MAX_ROUNDS * 20)
    comment = get_result_comment(total, max_score=MAX_ROUNDS * 20)

    share_result_box(title=title, total=total, max_score=100, comment=comment)

    for i in range(MAX_ROUNDS):
        if i < len(st.session_state.scores):
            score = st.session_state.scores[i]
            goal = (
                st.session_state.goals[i]
                if "goals" in st.session_state and i < len(st.session_state.goals)
                else "？"
            )
            score_display = f"{score} / 20点"
            score_ratio = score / 20
        else:
            score = 0
            score_display = "－ / 20点"
            goal = (
                st.session_state.goals[i]
                if "goals" in st.session_state and i < len(st.session_state.goals)
                else "？"
            )
            score_ratio = 0

        st.markdown(
            textwrap.dedent(f"""
                    <div style="
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 0.5rem 0.75rem;
                        margin-bottom: 0.4rem;
                        background-color: #f9f9f9;
                        box-shadow: 1px 1px 4px rgba(0,0,0,0.03);
                        font-size: 0.9rem;
                        line-height: 1.3;
                    ">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <div style="font-weight: bold;">ラウンド {i + 1}</div>
                            <div style="color: #1565c0;">目的地: <b>{goal}</b></div>
                        </div>
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 0.4rem;">
                            <div>スコア: <b>{score_display}</b></div>
                            <div style="flex-grow: 1; margin-left: 1rem; background: #eee; border-radius: 4px; overflow: hidden;">
                                <div style="
                                    height: 8px;
                                    width: {score_ratio * 100}%;
                                    background-color: #4db6ac;
                                "></div>
                            </div>
                        </div>
                    </div>
                """),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    if st.button("🔙 エリア選択に戻る"):
        change_page("area_select")
        st.rerun()


if "page" not in st.session_state:
    st.session_state.page = "area_select"


# --- 画面分岐 ---
if st.session_state.page == "area_select":
    draw_area_select_page()
elif st.session_state.page == "round_play":
    main, side = st.columns([5, 4])
    with main:
        draw_round_play_page()
    with side:
        draw_side_bar()
elif st.session_state.page == "round_result_success":
    main, side = st.columns([5, 4])
    with main:
        draw_round_result_success_page()
    with side:
        draw_side_bar()
elif st.session_state.page == "round_result_fail":
    main, side = st.columns([5, 4])
    with main:
        draw_round_result_fail_page()
    with side:
        draw_side_bar()
elif st.session_state.page == "game_result":
    st.session_state.log_status = ""
    draw_game_result()
