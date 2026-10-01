import streamlit as st
import requests
import pandas as pd

# --------------------------------
# 基本設定
# --------------------------------

st.set_page_config(
    page_title="昆虫の分布を調べよう",
    layout="wide"
)

st.title("🔎 GBIFで昆虫の分布を調べよう")

st.write(
    "昆虫を選んで、GBIFに登録されている日本国内の報告地点を見てみよう！"
)

# --------------------------------
# 調べる昆虫
# --------------------------------

species = {
    "アカボシゴマダラ": {
        "scientific_name": "Hestina assimilis",
        "image": "akaboshigomadara.jpg"
    },
    "キマダラカメムシ": {
        "scientific_name": "Erthesina fullo",
        "image": "kimadarakamemushi.jpg"
    }
}

selected_species = st.selectbox(
    "調べる昆虫を選んでください",
    list(species.keys())
)

info = species[selected_species]

# --------------------------------
# 写真と学名
# --------------------------------

col1, col2 = st.columns([1, 2])

with col1:

    st.image(
        info["image"],
        caption=selected_species
    )

with col2:

    st.subheader(selected_species)

    st.write(
        f"学名：*{info['scientific_name']}*"
    )

    st.write(
        "GBIFに登録された日本国内の位置情報を表示します。"
    )


# --------------------------------
# 年代の選択肢
# --------------------------------

years = list(range(2000, 2026, 5))

periods = []

for start in years:

    end = min(start + 4, 2026)

    periods.append(
        f"{start}–{end}"
    )

selected_period = st.selectbox(
    "調べる年代",
    periods
)

# 選択された年代を数値に変換
start_year = int(selected_period[:4])
end_year = int(selected_period[-4:])


# --------------------------------
# GBIFからデータを取得
# --------------------------------

if st.button("🗺️ 分布を表示"):

    url = "https://api.gbif.org/v1/occurrence/search"

    MAX_RECORDS = 3000
    PAGE_SIZE = 300

    params = {
        "scientificName": info["scientific_name"],
        "country": "JP",
        "hasCoordinate": "true",

        # 5年間のデータ
        "year": f"{start_year},{end_year}",

        "limit": PAGE_SIZE,
        "offset": 0
    }

    records = []

    with st.spinner("GBIFから報告例を探しています……"):

        while len(records) < MAX_RECORDS:

            response = requests.get(
                url,
                params=params,
                timeout=30
            )

            if response.status_code != 200:

                st.error(
                    "GBIFからデータを取得できませんでした。"
                )

                break

            data = response.json()

            results = data.get("results", [])

            if not results:
                break

            records.extend(results)

            # 次のページへ
            params["offset"] += PAGE_SIZE

            # GBIFに残りのデータがない
            if params["offset"] >= data.get("count", 0):
                break


    # --------------------------------
    # 結果を整理
    # --------------------------------

    points = []

    for record in records:

        lat = record.get("decimalLatitude")
        lon = record.get("decimalLongitude")

        if lat is not None and lon is not None:

            points.append({
                "latitude": lat,
                "longitude": lon
            })


    df = pd.DataFrame(points)


    # --------------------------------
    # 地図表示
    # --------------------------------

    if len(df) == 0:

        st.warning(
            f"{selected_species}について、"
            f"{selected_period}の位置情報付き報告例は見つかりませんでした。"
        )

    else:

        if len(df) >= MAX_RECORDS:

            st.info(
                f"報告例が非常に多いため、"
                f"最大{MAX_RECORDS}件まで表示しています。"
            )

        st.success(
            f"{selected_species}："
            f"{selected_period}に"
            f"{len(df)}件の報告例が見つかりました。"
        )

        st.map(df)

        st.caption(
            "※ 地図上の点はGBIFに登録された位置情報付きの報告例です。"
        )