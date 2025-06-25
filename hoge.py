import pandas as pd

# CSV読み込み
stations = pd.read_csv("data/v2/station.csv")

# グループごとに異なるstation_nameがあるものを抽出
grouped = stations.groupby("station_g_cd")["station_name"].nunique()

# 異なる駅名が2つ以上あるグループコードだけフィルタ
conflicting_groups = grouped[grouped > 1].index

# 対象のレコードを抽出
conflicts = stations[stations["station_g_cd"].isin(conflicting_groups)]

# 表示
for group_cd, group_df in conflicts.groupby("station_g_cd"):
    print(f"station_g_cd: {group_cd}")
    for _, row in group_df.iterrows():
        print(f" - {row['station_cd']} : {row['station_name']}")
    print()
