import streamlit as st
import requests
import pandas as pd
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(layout="wide")

st.title("VNINDEX ZigZag")

# =========================
# CẤU HÌNH ẨN
# =========================

vnindex_ticker = "VNINDEX"

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

    return int(percent)


# =========================
# TỰ TÍNH ZIGZAG
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

    atr_pct = calculate_atr_percent(df_price)

    percent_input = suggest_percent_from_atr(atr_pct)

    df_zigzag = zigzag_custom(
        df_price,
        deviation=percent_input
    )

    # =========================
    # NẾN
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
    # ZIGZAG
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

    # =========================
    # CHART
    # =========================

    chart = {
        "chart": {
            "height": 750,
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
        key="vnindex_zigzag_chart"
    )

    # =========================
    # DROPDOWN CHỌN ĐÁY VNINDEX
    # =========================

    st.subheader("Cổ phiếu tạo đáy quanh đáy VNINDEX")

    vnindex_bottoms = df_zigzag[
        df_zigzag["type"] == 2
    ].copy()

    vnindex_bottoms["date_only"] = pd.to_datetime(
        vnindex_bottoms["date"]
    ).dt.date

    # =========================
    # TÍNH 1 LẦN DUY NHẤT
    # =========================

    if "all_bottom_result_df" not in st.session_state:
        st.session_state["all_bottom_result_df"] = pd.DataFrame()

    if st.button("Tính dữ liệu tất cả đáy VNINDEX"):

        result_rows = []

        window_days = 2

        for vn_bottom in vnindex_bottoms["date_only"]:

            selected_date = pd.to_datetime(
                vn_bottom
            )

            for _, stock_row in df_all.iterrows():

                ticker = stock_row["ticker"]

                if ticker == "VNINDEX":
                    continue

                df_stock_price = get_price_by_ticker(
                    df_all,
                    ticker
                )

                if df_stock_price.empty:
                    continue

                atr_pct_stock = calculate_atr_percent(
                    df_stock_price
                )

                if pd.isna(atr_pct_stock):
                    continue

                stock_percent = suggest_percent_from_atr(
                    atr_pct_stock
                )

                df_stock_zigzag = zigzag_custom(
                    df_stock_price,
                    deviation=stock_percent
                )

                if df_stock_zigzag.empty:
                    continue

                df_stock_zigzag = (
                    df_stock_zigzag
                    .sort_values("date")
                    .reset_index(drop=True)
                )

                stock_bottoms = df_stock_zigzag[
                    df_stock_zigzag["type"] == 2
                ].copy()

                stock_bottoms["date"] = pd.to_datetime(
                    stock_bottoms["date"]
                )

                matched_bottoms = stock_bottoms[
                    (
                        stock_bottoms["date"]
                        - selected_date
                    ).abs().dt.days <= window_days
                ]

                for _, bottom_row in matched_bottoms.iterrows():

                    bottom_date = pd.to_datetime(
                        bottom_row["date"]
                    )

                    bottom_price = bottom_row["price"]

                    zz_idx_list = df_stock_zigzag[
                        (
                            df_stock_zigzag["date"]
                            == bottom_date
                        )
                        &
                        (
                            df_stock_zigzag["type"]
                            == 2
                        )
                    ].index

                    if len(zz_idx_list) == 0:
                        continue

                    zz_idx = zz_idx_list[0]

                    next_idx = zz_idx + 1

                    if next_idx >= len(df_stock_zigzag):
                        continue

                    next_peak = df_stock_zigzag.iloc[
                        next_idx
                    ]

                    if next_peak["type"] != 1:
                        continue

                    peak_date = pd.to_datetime(
                        next_peak["date"]
                    )

                    peak_price = next_peak["price"]

                    return_pct = (
                        (
                            peak_price
                            - bottom_price
                        )
                        / bottom_price
                        * 100
                    )

                    days_to_peak = (
                        peak_date
                        - bottom_date
                    ).days

                    result_rows.append({
                        "Đáy VNINDEX": vn_bottom,
                        "Ticker": ticker,
                        "Ngày đáy CP": bottom_date.date(),
                        "Giá đáy CP": round(
                            bottom_price,
                            2
                        ),
                        "Lệch ngày": abs(
                            (
                                bottom_date
                                - selected_date
                            ).days
                        ),
                        "Ngày đỉnh tiếp theo": peak_date.date(),
                        "Giá đỉnh tiếp theo": round(
                            peak_price,
                            2
                        ),
                        "Số ngày đáy → đỉnh": days_to_peak,
                        "Hiệu suất (%)": round(
                            return_pct,
                            2
                        )
                    })

        st.session_state[
            "all_bottom_result_df"
        ] = pd.DataFrame(
            result_rows
        )

    # =========================
    # DROPDOWN CHỌN ĐÁY
    # =========================

    all_result_df = st.session_state[
        "all_bottom_result_df"
    ]

    if not all_result_df.empty:

        selected_bottom_date = st.selectbox(
            "Chọn đáy VNINDEX",
            options=sorted(
                all_result_df[
                    "Đáy VNINDEX"
                ].unique()
            )
        )

        show_df = all_result_df[
            all_result_df["Đáy VNINDEX"]
            == selected_bottom_date
        ].copy()

        show_df = show_df.sort_values(
            "Hiệu suất (%)",
            ascending=False
        )

        st.dataframe(
            show_df,
            use_container_width=True
        )

    else:

        st.info(
            "Bấm 'Tính dữ liệu tất cả đáy VNINDEX' để bắt đầu."
        )
