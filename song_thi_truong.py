import streamlit as st
import pandas as pd
import requests
from streamlit_lightweight_charts import renderLightweightCharts


# =========================
# CẤU HÌNH TRANG
# =========================

st.set_page_config(
    page_title="Sóng thị trường",
    layout="wide"
)

st.title("📈 Giao dịch theo sóng thị trường")


# =========================
# THAM SỐ CỐ ĐỊNH
# =========================

start_date = "2023-06-08"
min_gap_days = 30


# =========================
# HÀM GỌI API
# =========================

@st.cache_data(ttl=3600)
def post_api(url, payload):
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=3600)
def load_stock_wave():
    url = "https://stocktraders.vn/service/data/getStockWave"

    payload = {
        "StockWaveRequest": {
            "account": "uyen.png"
        }
    }

    data = post_api(url, payload)

    if "StockWaveReply" in data:
        stock_waves = data["StockWaveReply"]["stockWaves"]
    else:
        stock_waves = data["StockWaveRequest"]["stockWaves"]

    waves_df = pd.DataFrame(stock_waves)

    waves_data_df = pd.DataFrame(
        waves_df["waveDatas"].tolist()
    )

    waves_data_df["date"] = pd.to_datetime(
        waves_data_df["date"]
    )

    waves_data_df = waves_data_df[
        [
            "date",
            "waitbuy",
            "buy",
            "waitsell",
            "sell",
            "reliability"
        ]
    ].copy()

    waves_data_df = waves_data_df.sort_values(
        "date"
    ).reset_index(drop=True)

    return waves_data_df


@st.cache_data(ttl=3600)
def load_total_trade():
    url = "https://stocktraders.vn/service/data/getTotalTrade"

    payload = {
        "TotalTradeRequest": {
            "account": "uyen.png"
        }
    }

    data = post_api(url, payload)

    stock_data = data["TotalTradeReply"]["stockTotals"]

    price_df = pd.DataFrame(stock_data)

    return price_df


# =========================
# LOAD DATA
# =========================

with st.spinner("Đang tải dữ liệu..."):

    waves_data_df = load_stock_wave()
    price_df = load_total_trade()


# =========================
# 1. XỬ LÝ STOCK WAVE
# =========================

waves_data_df = waves_data_df[
    waves_data_df["date"] >= pd.to_datetime(start_date)
].copy()

waves_data_df = waves_data_df.sort_values(
    "date"
).reset_index(drop=True)


# =========================
# 2. XÁC ĐỊNH NGÀY XÁC NHẬN TẠO ĐÁY
# =========================

waves_data_df["xac_nhan_tao_day_raw"] = (
    (waves_data_df["buy"] > 25)
    & (waves_data_df["waitbuy"] > waves_data_df["waitsell"])
)

bottom_dates = []
last_bottom_date = None

for _, row in waves_data_df.iterrows():

    if row["xac_nhan_tao_day_raw"]:

        if (
            last_bottom_date is None
            or (row["date"] - last_bottom_date).days > min_gap_days
        ):

            bottom_dates.append(row["date"])
            last_bottom_date = row["date"]

waves_data_df["xac_nhan_tao_day"] = (
    waves_data_df["date"].isin(bottom_dates)
)


# =========================
# 3. BUNG DỮ LIỆU GIÁ
# =========================

price_expand = price_df.explode(
    "totalDatas"
).copy()

price_detail = pd.DataFrame(
    price_expand["totalDatas"].tolist()
)

price_detail["ticker"] = price_expand["ticker"].values

price_detail["date"] = pd.to_datetime(
    price_detail["date"]
)

for col in ["open", "high", "low", "close"]:
    price_detail[col] = pd.to_numeric(
        price_detail[col],
        errors="coerce"
    )

price_detail = price_detail[
    [
        "date",
        "ticker",
        "open",
        "high",
        "low",
        "close"
    ]
].sort_values(["ticker", "date"]).reset_index(drop=True)


# =========================
# 4. TÌM VNINDEX
# =========================

all_tickers = (
    price_detail["ticker"]
    .drop_duplicates()
    .astype(str)
    .sort_values()
    .tolist()
)

possible_vnindex_names = [
    "VNINDEX",
    "VN-INDEX",
    "VN_INDEX",
    "INDEX",
    "VNI"
]

vnindex_ticker = None

for name in possible_vnindex_names:

    if name in all_tickers:
        vnindex_ticker = name
        break


if vnindex_ticker is None:

    st.error("Không tìm thấy mã VNINDEX trong API getTotalTrade.")

    st.write("Một số ticker có trong dữ liệu:")

    st.write(all_tickers[:100])

    st.stop()


vnindex_df = price_detail[
    price_detail["ticker"] == vnindex_ticker
].copy()

vnindex_df = vnindex_df.sort_values(
    "date"
).reset_index(drop=True)


# =========================
# 5. TẠO CANDLE DATA
# =========================

candle_data = []

for _, row in vnindex_df.iterrows():

    candle_data.append({
        "time": row["date"].strftime("%Y-%m-%d"),
        "open": float(row["open"]),
        "high": float(row["high"]),
        "low": float(row["low"]),
        "close": float(row["close"])
    })


# =========================
# 6. TẠO MARKER ĐÁY
# =========================

bottom_points = vnindex_df[
    vnindex_df["date"].isin(bottom_dates)
].copy()

bottom_markers = []

for _, row in bottom_points.iterrows():

    bottom_markers.append({
        "time": row["date"].strftime("%Y-%m-%d"),
        "position": "belowBar",
        "color": "#00C853",
        "shape": "arrowUp",
        "text": "Đáy"
    })


# =========================
# 7. VẼ BIỂU ĐỒ NẾN
# =========================

st.subheader(
    f"📉 {vnindex_ticker} - Biểu đồ nến và điểm xác nhận tạo đáy"
)

st.write(
    f"Số điểm tạo đáy hiển thị: {len(bottom_markers)}"
)

vnindex_series = [
    {
        "type": "Candlestick",
        "data": candle_data,
        "markers": bottom_markers,
        "options": {
            "upColor": "#26A69A",
            "downColor": "#EF5350",
            "borderUpColor": "#26A69A",
            "borderDownColor": "#EF5350",
            "wickUpColor": "#26A69A",
            "wickDownColor": "#EF5350",
            "priceLineVisible": False
        }
    }
]

vnindex_options = {
    "height": 600,
    "layout": {
        "background": {
            "type": "solid",
            "color": "transparent"
        },
        "textColor": "#999999"
    },
    "grid": {
        "vertLines": {
            "color": "rgba(150,150,150,0.12)"
        },
        "horzLines": {
            "color": "rgba(150,150,150,0.12)"
        }
    },
    "timeScale": {
        "visible": True,
        "timeVisible": True,
        "secondsVisible": False,
        "barSpacing": 6,
        "rightOffset": 5,
        "fixLeftEdge": False,
        "fixRightEdge": False
    },
    "rightPriceScale": {
        "visible": True,
        "borderVisible": False
    },
    "crosshair": {
        "mode": 1
    },
    "handleScroll": {
        "mouseWheel": True,
        "pressedMouseMove": True,
        "horzTouchDrag": True,
        "vertTouchDrag": False
    },
    "handleScale": {
        "axisPressedMouseMove": True,
        "mouseWheel": True,
        "pinch": True
    }
}

renderLightweightCharts(
    [
        {
            "chart": vnindex_options,
            "series": vnindex_series
        }
    ],
    key="vnindex_bottom_chart"
)


# =========================
# 8. BẢNG NGÀY TẠO ĐÁY
# =========================

st.subheader("📌 Danh sách ngày xác nhận tạo đáy")

bottom_show = waves_data_df[
    waves_data_df["xac_nhan_tao_day"]
][
    [
        "date",
        "waitbuy",
        "buy",
        "waitsell",
        "sell",
        "reliability"
    ]
].copy()

bottom_show["date"] = bottom_show["date"].dt.strftime(
    "%Y-%m-%d"
)

st.dataframe(
    bottom_show,
    hide_index=True,
    use_container_width=True
)
