import json
from collections import defaultdict

import pandas as pd

# CSVの読み込み
stations = pd.read_csv("data/v2/station.csv")
joins = pd.read_csv("data/v2/join.csv")
lines = pd.read_csv("data/v2/line.csv")

# 東京近郊（埼玉・千葉・東京・神奈川）に該当するpref_cd
valid_pref_cds = {11, 12, 13, 14}

major_lines = {
    "11301": "JR東海道本線(東京～熱海)",
    "11302": "JR山手線",
    "11303": "JR南武線",
    "11304": "JR鶴見線",
    "11305": "JR武蔵野線",
    "11306": "JR横浜線",
    "11307": "JR根岸線",
    "11308": "JR横須賀線",
    # "11311": "JR中央本線(東京～塩尻)",
    "11312": "JR中央線(快速)",
    "11313": "JR中央・総武線",
    "11314": "JR総武本線",
    "11315": "JR青梅線",
    "11316": "JR五日市線",
    "11319": "宇都宮線",
    "11320": "JR常磐線(上野～取手)",
    "11321": "JR埼京線",
    "11322": "JR川越線",
    "11323": "JR高崎線",
    "11324": "JR外房線",
    "11325": "JR内房線",
    "11326": "JR京葉線",
    "11327": "JR成田線",
    # "11328": "JR成田エクスプレス",
    "11332": "JR京浜東北線",
    "11333": "JR湘南新宿ライン",
    "28001": "東京メトロ銀座線",
    "28002": "東京メトロ丸ノ内線",
    "28003": "東京メトロ日比谷線",
    "28004": "東京メトロ東西線",
    "28005": "東京メトロ千代田線",
    "28006": "東京メトロ有楽町線",
    "28008": "東京メトロ半蔵門線",
    "28009": "東京メトロ南北線",
    "28010": "東京メトロ副都心線",
    "99302": "都営浅草線",
    "99303": "都営三田線",
    "99304": "都営新宿線",
    "99301": "都営大江戸線",
    "24001": "京王線",
    "24007": "京王新線",
    "24002": "京王相模原線",
    "24006": "京王井の頭線",
    "25001": "小田急線",
    "25002": "小田急江ノ島線",
    "26001": "東急東横線",
    "26002": "東急目黒線",
    "26003": "東急田園都市線",
    "26004": "東急大井町線",
    "26005": "東急池上線",
    "26006": "東急多摩川線",
    "26007": "東急世田谷線",
    "26008": "東急こどもの国線",
    "26009": "東急新横浜線",
    # "21001": "東武東上線", 霞ケ関問題
    "21002": "東武伊勢崎線",
    "21004": "東武野田線",
    "22001": "西武池袋線",
    "22007": "西武新宿線",
    "29001": "相鉄本線",
    "29002": "相鉄いずみ野線",
    "29003": "相鉄・JR直通線",
    "29004": "相鉄新横浜線",
    "99337": "りんかい線",
    "99309": "つくばエクスプレス",
    "99311": "ゆりかもめ",
    "99334": "多摩モノレール",
}

# フィルタされた駅
filtered_stations = stations[stations["pref_cd"].isin(valid_pref_cds)]
cd_to_name = filtered_stations.set_index("station_cd")["station_name"].to_dict()
valid_station_cds = set(cd_to_name.keys())

# 路線コード → 路線名
line_cd_to_name = lines.set_index("line_cd")["line_name"].to_dict()

# 駅名 → 隣接駅と路線名のリスト（例: { "新宿": [ {"station": "代々木", "line": "山手線"}, ... ] } ）
graph = defaultdict(list)

for _, row in joins.iterrows():
    cd1, cd2, line_cd = row["station_cd1"], row["station_cd2"], row["line_cd"]

    if cd1 in valid_station_cds and cd2 in valid_station_cds:
        name1, name2 = cd_to_name[cd1], cd_to_name[cd2]

        if name1 == "市ヶ谷":
            name1 = "市ケ谷"

        if name2 == "市ヶ谷":
            name2 = "市ケ谷"

        if name1 == "明治神宮前〈原宿〉":
            name1 = "明治神宮前"

        if name2 == "明治神宮前〈原宿〉":
            name2 = "明治神宮前"

        if name1 == "押上（スカイツリー前）":
            name1 = "押上"

        if name2 == "押上（スカイツリー前）":
            name2 = "押上"

        if str(line_cd) not in major_lines:
            continue

        line_name = major_lines[str(line_cd)]

        graph[name1].append(
            {
                "station": name2,
                "line": line_name,
                "station_cd": str(cd2),
                "line_cd": str(line_cd),
            }
        )
        graph[name2].append(
            {
                "station": name1,
                "line": line_name,
                "station_cd": str(cd1),
                "line_cd": str(line_cd),
            }
        )

line_set = set()
# 最初の5駅分を表示
for station, edges in list(graph.items()):
    print(f"{station}:")
    for edge in edges:
        print(f"  └─ {edge['station']} ({edge['line']})")
        line_set.add((edge["line_cd"], edge["line"]))

for item in line_set:
    print(item)

print(len(line_set))
print(len(graph))

# 出力
with open("graph.json", "w", encoding="utf-8") as f:
    json.dump(graph, f, ensure_ascii=False, indent=2)
