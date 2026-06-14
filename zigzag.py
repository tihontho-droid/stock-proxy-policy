import streamlit as st
import pandas as pd
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(layout="wide")

st.title("VNINDEX ZigZag và cổ phiếu tạo đáy cùng ngày")

# =========================
# LOAD ZIGZAG ĐÃ TÍNH SẴN
# =========================

@st.cache_data
def load_zigzag_data():
    df = pd.read_csv("all_zigzag_points.csv")

    df["date"] = pd.to_datetime(df["date"])
    df["type"] = pd.to_numeric(df["type"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    return df


zigzag_all = load_zigzag_data()

# =========================
# LẤY ZIGZAG VNINDEX
# =========================

vnindex_zigzag = zigzag_all[
    zigzag_all["ticker"] == "VNINDEX"
].copy()

vnindex_zigzag = vnindex_zigzag.sort_values("date").reset_index(drop=True)

# =========================
# VẼ BIỂU ĐỒ ZIGZAG VNINDEX
# =========================

zigzag_line = []
markers = []

for _, row in vnindex_zigzag.iterrows():
    time_str = row["date"].strftime("%Y-%m-%d")

    zigzag_line.append({
        "time": time_str,
        "value": float(row["price"])
    })

    if row["type"] == 1:
        markers.append({
            "time": time_str,
            "position": "aboveBar",
            "shape": "arrowDown",
            "color": "red",
            "text": "Đỉnh"
        })

    elif row["type"] == 2:
        markers.append({
            "time": time_str,
            "position": "belowBar",
            "shape": "arrowUp",
            "color": "green",
            "text": "Đáy"
        })


chart = {
    "chart": {
        "height": 700,
        "layout": {
            "background": {
                "type": "solid",
                "color": "#ffffff"
            },
            "textColor": "#000000"
        },
        "grid": {
            "vertLines": {
                "color": "#eeeeee"
            },
            "horzLines": {
                "color": "#eeeeee"
            }
        },
        "rightPriceScale": {
            "borderColor": "#cccccc"
        },
        "timeScale": {
            "borderColor": "#cccccc",
            "timeVisible": True,
            "secondsVisible": False
        }
    },
    "series": [
        {
            "type": "Line",
            "data": zigzag_line,
            "markers": markers,
            "options": {
                "color": "#2962FF",
                "lineWidth": 2,
                "priceLineVisible": False
            }
        }
    ]
}

renderLightweightCharts(
    [chart],
    key="vnindex_zigzag_chart"
)

# =========================
# DROPDOWN CHỌN ĐÁY VNINDEX
# =========================

st.subheader("Cổ phiếu tạo đáy quanh đáy VNINDEX")

start_date = pd.to_datetime("2023-06-01")
window_days = 2

vnindex_bottoms = vnindex_zigzag[
    (vnindex_zigzag["type"] == 2) &
    (vnindex_zigzag["date"] >= start_date)
].copy()

vnindex_bottoms["date_only"] = vnindex_bottoms["date"].dt.date

selected_bottom_date = st.selectbox(
    "Chọn đáy VNINDEX",
    options=vnindex_bottoms["date_only"].tolist()
)

selected_date = pd.to_datetime(selected_bottom_date)

# =========================
# TÌM CỔ PHIẾU TẠO ĐÁY QUANH NGÀY ĐÓ
# =========================

stock_bottoms = zigzag_all[
    (zigzag_all["ticker"] != "VNINDEX") &
    (zigzag_all["type"] == 2)
].copy()

matched_bottoms = stock_bottoms[
    (
        stock_bottoms["date"] - selected_date
    ).abs().dt.days <= window_days
].copy()

result_rows = []

for _, bottom_row in matched_bottoms.iterrows():

    ticker = bottom_row["ticker"]
    bottom_date = bottom_row["date"]
    bottom_price = bottom_row["price"]

    ticker_zigzag = zigzag_all[
        zigzag_all["ticker"] == ticker
    ].copy()

    ticker_zigzag = ticker_zigzag.sort_values("date").reset_index(drop=True)

    matched_idx = ticker_zigzag[
        (ticker_zigzag["date"] == bottom_date) &
        (ticker_zigzag["type"] == 2) &
        (ticker_zigzag["price"] == bottom_price)
    ].index

    if len(matched_idx) == 0:
        continue

    zz_idx = matched_idx[0]
    next_idx = zz_idx + 1

    if next_idx >= len(ticker_zigzag):
        continue

    next_peak = ticker_zigzag.iloc[next_idx]

    if next_peak["type"] != 1:
        continue

    peak_date = next_peak["date"]
    peak_price = next_peak["price"]

    return_pct = (
        (peak_price - bottom_price)
        / bottom_price
        * 100
    )

    days_to_peak = (
        peak_date - bottom_date
    ).days

    result_rows.append({
        "Ticker": ticker,
        "Đáy VNINDEX": selected_bottom_date,
        "Ngày đáy CP": bottom_date.date(),
        "Giá đáy CP": round(bottom_price, 2),
        "Lệch ngày": abs((bottom_date - selected_date).days),
        "Ngày đỉnh tiếp theo": peak_date.date(),
        "Giá đỉnh tiếp theo": round(peak_price, 2),
        "Số ngày đáy → đỉnh": days_to_peak,
        "Hiệu suất đáy → đỉnh (%)": round(return_pct, 2)
    })

result_df = pd.DataFrame(result_rows)

if result_df.empty:
    st.warning("Không có cổ phiếu nào tạo đáy quanh đáy VNINDEX đã chọn.")
else:
    result_df = result_df.sort_values(
        "Hiệu suất đáy → đỉnh (%)",
        ascending=False
    )

    st.dataframe(
        result_df,
        use_container_width=True
    )
