import streamlit as st
import pandas as pd 
import plotly.graph_objects as go
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(layout="wide")

st.title("Giao dịch theo sóng thị trường")

# =========================
# LOAD DATA ĐÃ TÍNH SẴN
# =========================

@st.cache_data
def load_price_data():
    df = pd.read_csv("all_price_data.csv")

    df["ticker"] = df["ticker"].astype(str).str.upper()
    df["date"] = pd.to_datetime(df["date"])

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


@st.cache_data
def load_zigzag_data():
    df = pd.read_csv("all_zigzag_points.csv")

    df["ticker"] = df["ticker"].astype(str).str.upper()
    df["date"] = pd.to_datetime(df["date"])
    df["type"] = pd.to_numeric(df["type"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["percent"] = pd.to_numeric(df["percent"], errors="coerce")

    return df

price_all = load_price_data()
zigzag_all = load_zigzag_data()

# =========================
# LẤY DATA VNINDEX
# =========================

df_vnindex_price = (
    price_all[price_all["ticker"] == "VNINDEX"]
    .sort_values("date")
    .reset_index(drop=True)
)

# VNINDEX chỉ lấy ZigZag percent = 5
df_vnindex_zigzag = (
    zigzag_all[
        (zigzag_all["ticker"] == "VNINDEX") &
        (zigzag_all["percent"] == 5)
    ]
    .sort_values("date")
    .reset_index(drop=True)
)

if df_vnindex_price.empty:
    st.error("Không tìm thấy dữ liệu giá VNINDEX trong all_price_data.csv.")
    st.stop()

if df_vnindex_zigzag.empty:
    st.error("Không tìm thấy ZigZag VNINDEX percent = 5 trong all_zigzag_points.csv. Em cần chạy lại file prepare với VNINDEX percent = 5.")
    st.stop()

# =========================
# CHUẨN BỊ NẾN VNINDEX
# =========================

candles = []

for _, row in df_vnindex_price.iterrows():
    candles.append({
        "time": row["date"].strftime("%Y-%m-%d"),
        "open": float(row["open"]),
        "high": float(row["high"]),
        "low": float(row["low"]),
        "close": float(row["close"])
    })

# =========================
# CHUẨN BỊ ZIGZAG VNINDEX
# =========================

zigzag_line = []
markers = []

for _, row in df_vnindex_zigzag.iterrows():
    time_str = row["date"].strftime("%Y-%m-%d")

    zigzag_line.append({
        "time": time_str,
        "value": float(row["price"])
    })

    price_text = f"{row['price']:.2f}"
    
    if row["type"] == 1:
        markers.append({
            "time": time_str,
            "position": "aboveBar",
            "shape": "arrowDown",
            "color": "red",
            "text": f"Đỉnh {price_text}"
        })
    
    elif row["type"] == 2:
        markers.append({
            "time": time_str,
            "position": "belowBar",
            "shape": "arrowUp",
            "color": "green",
            "text": f"Đáy {price_text}"
        })
# =========================
# VẼ CHART NẾN + ZIGZAG
# =========================

chart = {
    "chart": {
        "height": 500,
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
    key="vnindex_candle_zigzag_chart"
)

# =========================
# DROPDOWN CHỌN ĐÁY VNINDEX
# =========================

st.subheader("Cổ phiếu tạo đáy quanh đáy VNINDEX")

start_date = pd.to_datetime("2023-06-01")
window_days = 2

vnindex_bottoms = df_vnindex_zigzag[
    (df_vnindex_zigzag["type"] == 2) &
    (df_vnindex_zigzag["date"] >= start_date)
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
    zigzag_percent = bottom_row["percent"]

    ticker_zigzag = (
        zigzag_all[zigzag_all["ticker"] == ticker]
        .sort_values("date")
        .reset_index(drop=True)
    )

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

    days_to_peak = (peak_date - bottom_date).days

    result_rows.append({
        "Ticker": ticker,
        "Percent ZigZag": int(zigzag_percent),
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

    result_df = result_df[
        [
            "Ticker",
            "Percent ZigZag",
            "Đáy VNINDEX",
            "Ngày đáy CP",
            "Giá đáy CP",
            "Lệch ngày",
            "Ngày đỉnh tiếp theo",
            "Giá đỉnh tiếp theo",
            "Số ngày đáy → đỉnh",
            "Hiệu suất đáy → đỉnh (%)"
        ]
    ]

    st.dataframe(
        result_df,
        use_container_width=True
    )

# =========================
# BOX TÌM MÃ VÀ VẼ ZIGZAG CỔ PHIẾU
# =========================

st.subheader("Tra cứu biểu đồ ZigZag theo mã cổ phiếu")

ticker_input = st.text_input(
    "Nhập mã cổ phiếu",
    value="VIX"
).upper()

if ticker_input:

    df_stock_price = (
        price_all[
            price_all["ticker"] == ticker_input
        ]
        .sort_values("date")
        .reset_index(drop=True)
    )

    df_stock_zigzag = (
        zigzag_all[
            zigzag_all["ticker"] == ticker_input
        ]
        .sort_values("date")
        .reset_index(drop=True)
    )

    if df_stock_price.empty:
        st.warning(f"Không tìm thấy dữ liệu giá của mã {ticker_input}.")
    elif df_stock_zigzag.empty:
        st.warning(f"Không tìm thấy dữ liệu ZigZag của mã {ticker_input}.")
    else:

        candles_stock = []

        for _, row in df_stock_price.iterrows():
            candles_stock.append({
                "time": row["date"].strftime("%Y-%m-%d"),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"])
            })

        zigzag_line_stock = []
        markers_stock = []

        for _, row in df_stock_zigzag.iterrows():
            time_str = row["date"].strftime("%Y-%m-%d")
            price_text = f"{row['price']:.2f}"

            zigzag_line_stock.append({
                "time": time_str,
                "value": float(row["price"])
            })

            if row["type"] == 1:
                markers_stock.append({
                    "time": time_str,
                    "position": "aboveBar",
                    "shape": "arrowDown",
                    "color": "red",
                    "text": f"Đỉnh {price_text}"
                })

            elif row["type"] == 2:
                markers_stock.append({
                    "time": time_str,
                    "position": "belowBar",
                    "shape": "arrowUp",
                    "color": "green",
                    "text": f"Đáy {price_text}"
                })

        chart_stock = {
            "chart": {
                "height": 500,
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
                    "data": candles_stock,
                    "markers": markers_stock
                },
                {
                    "type": "Line",
                    "data": zigzag_line_stock,
                    "options": {
                        "color": "#2962FF",
                        "lineWidth": 2,
                        "priceLineVisible": False
                    }
                }
            ]
        }

        renderLightweightCharts(
            [chart_stock],
            key=f"stock_zigzag_chart_{ticker_input}"
        )

# =========================
# HIỂN THỊ CHUẨN BỊ / XÁC NHẬN ĐÁY
# =========================

@st.cache_data
def load_bottom_signal():
    df = pd.read_parquet("bottom_signal_df.parquet")
    df["date"] = pd.to_datetime(df["date"])
    return df


bottom_signal_df = load_bottom_signal()

selected_confirm_date = pd.to_datetime(selected_bottom_date)

prepare_df = bottom_signal_df[
    (bottom_signal_df["chuan_bi_tao_day"] == True)
    &
    (bottom_signal_df["date"] < selected_confirm_date)
].copy()

confirm_df = bottom_signal_df[
    bottom_signal_df["date"] == selected_confirm_date
].copy()

if prepare_df.empty or confirm_df.empty:

    st.info("Không tìm thấy đủ dữ liệu chuẩn bị / xác nhận đáy cho ngày này.")

else:

    prepare_row = (
        prepare_df
        .sort_values("date")
        .tail(1)
        .iloc[0]
    )

    confirm_row = confirm_df.iloc[0]

    prepare_date_str = prepare_row["date"].strftime("%Y-%m-%d")
    confirm_date_str = confirm_row["date"].strftime("%Y-%m-%d")

    st.markdown(
        f"""
        <div style="
            background:#F7F8FC;
            padding:14px 18px;
            border-radius:16px;
            margin-bottom:12px;
            border:1px solid #ECEEF5;
        ">
            <div style="font-size:18px; font-weight:700;">
                Đáy được chọn: {confirm_date_str}
            </div>
            <div style="font-size:14px; color:#666; margin-top:4px;">
                Ngày chuẩn bị tạo đáy: {prepare_date_str}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    labels = ["Chờ mua", "Mua", "Chờ bán", "Bán"]

    colors = [
        "#11D99A",
        "#00A86B",
        "#FFA114",
        "#F23670"
    ]

    legend_html = """
    <div style="
        display:flex;
        justify-content:center;
        gap:14px;
        margin-top:-18px;
        margin-bottom:4px;
        font-size:13px;
        color:#444;
        flex-wrap:wrap;
    ">
        <div><span style="color:#11D99A; font-size:18px;">●</span> Chờ mua</div>
        <div><span style="color:#00A86B; font-size:18px;">●</span> Mua</div>
        <div><span style="color:#FFA114; font-size:18px;">●</span> Chờ bán</div>
        <div><span style="color:#F23670; font-size:18px;">●</span> Bán</div>
    </div>
    """

    def make_pie(row, title):

        values = [
            row["waitbuy"],
            row["buy"],
            row["waitsell"],
            row["sell"]
        ]

        total = sum(values)

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.70,
                    marker=dict(
                        colors=colors,
                        line=dict(
                            color="white",
                            width=1
                        )
                    ),
                    textinfo="value",
                    textfont=dict(
                        size=12,
                        color="white"
                    ),
                    sort=False,
                    direction="clockwise",
                    showlegend=False
                )
            ]
        )

        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                xanchor="center",
                font=dict(
                    size=14,
                    color="#333"
                )
            ),
            height=250,
            margin=dict(
                t=35,
                b=5,
                l=5,
                r=5
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            annotations=[
                dict(
                    text=f"<b>{total}</b>",
                    x=0.5,
                    y=0.5,
                    font=dict(
                        size=22,
                        color="#111111"
                    ),
                    showarrow=False
                )
            ]
        )

        return fig

    col1, col2 = st.columns(2)

    with col1:

        fig_prepare = make_pie(
            prepare_row,
            f"Chuẩn bị tạo đáy - {prepare_date_str}"
        )

        st.plotly_chart(
            fig_prepare,
            use_container_width=True,
            config={"displayModeBar": False}
        )

        st.markdown(legend_html, unsafe_allow_html=True)

    with col2:

        fig_confirm = make_pie(
            confirm_row,
            f"Xác nhận đáy - {confirm_date_str}"
        )

        st.plotly_chart(
            fig_confirm,
            use_container_width=True,
            config={"displayModeBar": False}
        )

        st.markdown(legend_html, unsafe_allow_html=True)
