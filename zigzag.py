import streamlit as st
import requests
import pandas as pd
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(layout="wide")

st.title("Biểu đồ nến + ZigZag tự tính theo ATR")

# =========================
# INPUT
# =========================

ticker_input = st.text_input(
    "Nhập mã cổ phiếu",
    value="GAS"
).upper()

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
# GỢI Ý PERCENT TỪ ATR
# =========================

def suggest_percent_from_atr(atr_pct):
    raw_percent = atr_pct * 7.35

    percent = round(raw_percent / 5) * 5

    percent = max(5, percent)
    percent = min(50, percent)

    return int(percent), raw_percent


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

    # thêm pivot cuối đang hình thành
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

if ticker_input not in df_all["ticker"].values:
    st.error("Không tìm thấy mã cổ phiếu này.")
else:
    df_price = get_price_by_ticker(df_all, ticker_input)

    atr_pct = calculate_atr_percent(df_price)

    percent_auto, percent_raw = suggest_percent_from_atr(atr_pct)

    df_zigzag = zigzag_custom(
        df_price,
        deviation=percent_auto
    )

    st.info(
        f"Mã {ticker_input} | ATR% = {atr_pct:.2f}% | "
        f"Percent gợi ý = {percent_raw:.2f}% → làm tròn thành {percent_auto}%"
    )

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
        key=f"chart_{ticker_input}_{percent_auto}"
    )

    # =========================
    # SO SÁNH ĐÁY CỔ PHIẾU VỚI ĐÁY VNINDEX
    # =========================

    st.subheader("Đáy cổ phiếu trùng với đáy VNINDEX")

    window_days = 2
    holding_days_list = [20, 40, 60]

    st.caption(
        f"Điều kiện: đáy cổ phiếu lệch tối đa ±{window_days} ngày so với đáy VNINDEX"
    )

    vnindex_ticker = "VNINDEX"

    if vnindex_ticker not in df_all["ticker"].values:
        st.warning("Không tìm thấy VNINDEX trong dữ liệu.")
    else:
        df_vnindex = get_price_by_ticker(df_all, vnindex_ticker)

        # Với VNINDEX nên dùng percent cố định nhẹ hơn, tránh quá ít đáy
        vnindex_percent = 10

        df_vnindex_zigzag = zigzag_custom(
            df_vnindex,
            deviation=vnindex_percent
        )

        stock_bottoms = df_zigzag[
            df_zigzag["type"] == 2
        ].copy()

        market_bottoms = df_vnindex_zigzag[
            df_vnindex_zigzag["type"] == 2
        ].copy()

        result_rows = []

        for _, market_row in market_bottoms.iterrows():

            market_bottom_date = pd.to_datetime(market_row["date"])

            matched_stock_bottoms = stock_bottoms[
                (
                    stock_bottoms["date"] - market_bottom_date
                ).abs().dt.days <= window_days
            ]

            for _, stock_row in matched_stock_bottoms.iterrows():

                stock_bottom_date = pd.to_datetime(stock_row["date"])
                stock_bottom_price = stock_row["price"]

                row_result = {
                    "Đáy VNINDEX": market_bottom_date.date(),
                    "Giá đáy VNINDEX": round(market_row["price"], 2),
                    "Đáy cổ phiếu": stock_bottom_date.date(),
                    "Giá đáy cổ phiếu": round(stock_bottom_price, 2),
                    "Lệch ngày": abs(
                        (stock_bottom_date - market_bottom_date).days
                    )
                }

                matched_price_row = df_price[
                    df_price["date"] == stock_bottom_date
                ]

                if matched_price_row.empty:
                    continue

                bottom_idx = matched_price_row.index[0]

                for holding_days in holding_days_list:

                    future_idx = bottom_idx + holding_days

                    if future_idx >= len(df_price):
                        row_result[f"Return {holding_days} phiên (%)"] = None
                    else:
                        future_close = df_price.loc[future_idx, "close"]

                        return_pct = (
                            (future_close - stock_bottom_price)
                            / stock_bottom_price
                            * 100
                        )

                        row_result[f"Return {holding_days} phiên (%)"] = round(
                            return_pct,
                            2
                        )

                result_rows.append(row_result)

        result_df = pd.DataFrame(result_rows)

        st.info(
            f"VNINDEX dùng ZigZag {vnindex_percent}% | "
            f"Cổ phiếu {ticker_input} dùng ZigZag {percent_auto}%"
        )

        if result_df.empty:
            st.warning(
                f"{ticker_input} chưa có đáy ZigZag trùng hoặc lệch ±{window_days} ngày với đáy VNINDEX."
            )
        else:
            st.dataframe(
                result_df,
                use_container_width=True
            )
