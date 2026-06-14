import streamlit as st
import requests
import pandas as pd
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(layout="wide")

st.title("Biểu đồ VNINDEX + ZigZag")

# =========================
# INPUT
# =========================

vnindex_ticker = "VNINDEX"

percent_input = st.number_input(
    "Percent ZigZag VNINDEX",
    min_value=5,
    max_value=50,
    value=10,
    step=5
)

# =========================
# LẤY TOÀN BỘ GIÁ
# =========================

@st.cache_data
def get_total_trade():
    url = "https://stocktraders.vn/service/data/getTotalTrade"

    payload = {
        "TotalTradeRequest": {
            "account": "uyen.png"
        }
    }

    r = requests.post(url, json=payload)
    data = r.json()

    stock_totals = data["TotalTradeReply"]["stockTotals"]

    return pd.DataFrame(stock_totals)


# =========================
# LẤY GIÁ THEO MÃ
# =========================

def get_price_by_ticker(df_all, ticker):
    row = df_all[df_all["ticker"] == ticker]

    if row.empty:
        return pd.DataFrame()

    df_price = pd.DataFrame(row.iloc[0]["totalDatas"])

    df_price["date"] = pd.to_datetime(df_price["date"])

    df_price = df_price.sort_values("date").reset_index(drop=True)

    for col in ["open", "high", "low", "close"]:
        df_price[col] = pd.to_numeric(df_price[col])

    return df_price


# =========================
# TỰ TÍNH ZIGZAG CUSTOM
# =========================

def zigzag_custom(df_price, deviation):
    df = df_price.copy()
    df = df.sort_values("date").reset_index(drop=True)

    dev = deviation / 100

    points = []

    trend = None

    low_idx = 0
    low_price = df.loc[0, "low"]

    high_idx = 0
    high_price = df.loc[0, "high"]

    for i in range(1, len(df)):
        high = df.loc[i, "high"]
        low = df.loc[i, "low"]

        if trend is None:

            if high >= low_price * (1 + dev):
                trend = "up"

                points.append({
                    "type": 2,
                    "price": low_price,
                    "date": df.loc[low_idx, "date"]
                })

                high_idx = i
                high_price = high

            elif low <= high_price * (1 - dev):
                trend = "down"

                points.append({
                    "type": 1,
                    "price": high_price,
                    "date": df.loc[high_idx, "date"]
                })

                low_idx = i
                low_price = low

        elif trend == "up":

            if high >= high_price:
                high_price = high
                high_idx = i

            elif low <= high_price * (1 - dev):
                points.append({
                    "type": 1,
                    "price": high_price,
                    "date": df.loc[high_idx, "date"]
                })

                trend = "down"

                low_idx = i
                low_price = low

        elif trend == "down":

            if low <= low_price:
                low_price = low
                low_idx = i

            elif high >= low_price * (1 + dev):
                points.append({
                    "type": 2,
                    "price": low_price,
                    "date": df.loc[low_idx, "date"]
                })

                trend = "up"

                high_idx = i
                high_price = high

    if trend == "up":
        points.append({
            "type": 1,
            "price": high_price,
            "date": df.loc[high_idx, "date"]
        })

    elif trend == "down":
        points.append({
            "type": 2,
            "price": low_price,
            "date": df.loc[low_idx, "date"]
        })

    df_zigzag = pd.DataFrame(points)

    if df_zigzag.empty:
        return df_zigzag

    df_zigzag["date"] = pd.to_datetime(df_zigzag["date"])

    return df_zigzag


# =========================
# LOAD DATA
# =========================

df_all = get_total_trade()

if vnindex_ticker not in df_all["ticker"].values:
    st.error("Không tìm thấy VNINDEX trong dữ liệu.")
else:
    df_price = get_price_by_ticker(df_all, vnindex_ticker)

    df_zigzag = zigzag_custom(
        df_price,
        deviation=percent_input
    )

    st.info(f"VNINDEX đang dùng ZigZag {percent_input}%")

    # =========================
    # CHUẨN BỊ NẾN
    # =========================

    candles = []

    for _, row in df_price.iterrows():
        candles.append({
            "time": row["date"].strftime("%Y-%m-%d"),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"])
        })

    # =========================
    # CHUẨN BỊ ZIGZAG
    # =========================

    zigzag_line = []
    markers = []

    if not df_zigzag.empty:
        for _, row in df_zigzag.iterrows():
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
                    "text": f"Đỉnh {row['price']}"
                })

            elif row["type"] == 2:
                markers.append({
                    "time": time_str,
                    "position": "belowBar",
                    "shape": "arrowUp",
                    "color": "green",
                    "text": f"Đáy {row['price']}"
                })

    # =========================
    # VẼ CHART
    # =========================

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
                "type": "Candlestick",
                "data": candles,
                "markers": markers
            },
            {
                "type": "Line",
                "data": zigzag_line,
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
        key=f"chart_{vnindex_ticker}_{percent_input}"
    )

    # =========================
    # BẢNG ĐÁY VNINDEX
    # =========================

    st.subheader("Các đáy ZigZag của VNINDEX")

    if df_zigzag.empty:
        st.warning("Không có điểm ZigZag.")
    else:
        df_show = df_zigzag.copy()

        df_show["type_name"] = df_show["type"].map({
            1: "Đỉnh",
            2: "Đáy"
        })

        st.dataframe(
            df_show[["date", "type_name", "price"]],
            use_container_width=True
        )
