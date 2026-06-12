import streamlit as st
import requests
import pandas as pd
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(layout="wide")

st.title("Biểu đồ nến + ZigZag tự động theo ATR")

# =========================
# INPUT
# =========================

ticker_input = st.text_input(
    "Nhập mã cổ phiếu",
    value="GAS"
).upper()

# =========================
# API GIÁ
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
# LẤY GIÁ 1 MÃ
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
# TÍNH ATR%
# =========================

def calculate_atr_percent(df_price, period=20):
    df = df_price.copy()

    df["prev_close"] = df["close"].shift(1)

    df["tr1"] = df["high"] - df["low"]

    df["tr2"] = (
        df["high"] - df["prev_close"]
    ).abs()

    df["tr3"] = (
        df["low"] - df["prev_close"]
    ).abs()

    df["tr"] = df[["tr1", "tr2", "tr3"]].max(axis=1)

    df["atr"] = df["tr"].rolling(period).mean()

    df["atr_pct"] = df["atr"] / df["close"] * 100

    return df["atr_pct"].mean()


# =========================
# GỢI Ý PERCENT
# =========================

def suggest_percent_from_atr(atr_pct):
    raw_percent = atr_pct * 7.35

    percent = round(raw_percent / 5) * 5

    percent = max(5, percent)

    percent = min(50, percent)

    return int(percent), raw_percent


# =========================
# API ZIGZAG
# =========================

@st.cache_data
def get_zigzag(ticker, percent):
    url = "https://stocktradersai.vn/service/data/ZigZagPoint"

    payload = {
        "ticker": ticker,
        "percent": percent
    }

    r = requests.post(url, json=payload)
    data = r.json()

    points = data["points"]

    df = pd.DataFrame(points)

    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    return df


# =========================
# LOAD DATA
# =========================

df_all = get_total_trade()

if ticker_input not in df_all["ticker"].values:
    st.error("Không tìm thấy mã cổ phiếu này.")
else:
    df_price = get_price_by_ticker(df_all, ticker_input)

    atr_pct = calculate_atr_percent(df_price)

    percent_auto, percent_raw = suggest_percent_from_atr(atr_pct)

    df_zigzag = get_zigzag(ticker_input, percent_auto)

    st.info(
        f"Mã {ticker_input} | ATR% = {atr_pct:.2f}% | "
        f"Percent gợi ý = {percent_raw:.2f}% → làm tròn thành {percent_auto}%"
    )

    # =========================
    # CHUẨN BỊ DỮ LIỆU CHART
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
        key=f"chart_{ticker_input}_{percent_auto}"
    )

    st.subheader("Bảng điểm ZigZag")

    if df_zigzag.empty:
        st.warning("Không có dữ liệu ZigZag.")
    else:
        df_zigzag["type_name"] = df_zigzag["type"].map({
            1: "Đỉnh",
            2: "Đáy"
        })

        st.dataframe(
            df_zigzag[["date", "type_name", "price"]],
            use_container_width=True
        )
