import streamlit as st
import pandas as pd
import requests
from streamlit_lightweight_charts import renderLightweightCharts


st.set_page_config(
    page_title="Sóng thị trường",
    layout="wide"
)

st.title("📈 Giao dịch theo sóng thị trường")

start_date = "2023-06-08"


@st.cache_data(ttl=3600)
def post_api(url, payload):
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=3600)
def load_all_data():
    account = "uyen.png"

    wave_data = post_api(
        "https://stocktraders.vn/service/data/getStockWave",
        {"StockWaveRequest": {"account": account}}
    )

    smdt_data = post_api(
        "https://stocktraders.vn/service/data/getSMDTBranch",
        {"SMDTBranchRequest": {"account": account}}
    )

    flow_data = post_api(
        "https://stocktraders.vn/service/data/getCashFlowBranch",
        {"CashFlowBranchRequest": {"account": account}}
    )

    price_data = post_api(
        "https://stocktraders.vn/service/data/getTotalTrade",
        {"TotalTradeRequest": {"account": account}}
    )

    return wave_data, smdt_data, flow_data, price_data


with st.spinner("Đang tải dữ liệu..."):
    wave_data, smdt_data, flow_data, price_data = load_all_data()


# =========================
# 1. STOCK WAVE
# =========================

if "StockWaveReply" in wave_data:
    stock_waves = wave_data["StockWaveReply"]["stockWaves"]
else:
    stock_waves = wave_data["StockWaveRequest"]["stockWaves"]

waves_df = pd.DataFrame(stock_waves)

waves_data_df = pd.DataFrame(
    waves_df["waveDatas"].tolist()
)

waves_data_df["date"] = pd.to_datetime(waves_data_df["date"])

waves_data_df = waves_data_df[
    ["date", "waitbuy", "buy", "waitsell", "sell", "reliability"]
].copy()

waves_data_df = waves_data_df[
    waves_data_df["date"] >= pd.to_datetime(start_date)
].copy()

waves_data_df = waves_data_df.sort_values("date").reset_index(drop=True)


# =========================
# 2. SMDT TOÀN BỘ NGÀNH
# =========================

smdt_branch_df = pd.DataFrame(
    smdt_data["SMDTBranchReply"]["SMDTDatas"]
)

smdt_expand = smdt_branch_df.explode("smdts").copy()

smdt_detail = pd.DataFrame(
    smdt_expand["smdts"].tolist()
)

smdt_detail["nganh"] = smdt_expand["keyName"].values
smdt_detail["date"] = pd.to_datetime(smdt_detail["date"])
smdt_detail["smdt"] = pd.to_numeric(
    smdt_detail["smdt"],
    errors="coerce"
)

smdt_detail = smdt_detail[
    smdt_detail["date"] >= pd.to_datetime(start_date)
].copy()

smdt_detail = smdt_detail[
    ["date", "nganh", "smdt"]
].sort_values(["nganh", "date"]).reset_index(drop=True)


# =========================
# 3. FLOW TOÀN BỘ NGÀNH
# =========================

flow_branch_df = pd.DataFrame(
    flow_data["CashFlowBranchReply"]["cashFlowBranchs"]
)

flow_expand = flow_branch_df.explode("cashFlowBranchDatas").copy()

flow_detail = pd.DataFrame(
    flow_expand["cashFlowBranchDatas"].tolist()
)

flow_detail["date"] = flow_expand["date"].values
flow_detail["date"] = pd.to_datetime(flow_detail["date"])

flow_detail = flow_detail.rename(columns={
    "name": "nganh",
    "content": "cashflow"
})

flow_map = {
    "Nhen nhóm đổ vào": 1,
    "Tiếp tục đổ vào": 1,
    "Đang thoát ra": -1,
    "Tiếp tục thoát ra": -1
}

flow_detail["flow_num"] = flow_detail["cashflow"].map(flow_map)

flow_detail = flow_detail[
    ["date", "nganh", "cashflow", "flow_num"]
]


# =========================
# 4. GỘP SMDT + FLOW NGÀNH
# =========================

sector_all_df = smdt_detail.merge(
    flow_detail,
    on=["date", "nganh"],
    how="left"
)

sector_all_df = sector_all_df.sort_values(
    ["nganh", "date"]
).reset_index(drop=True)

sector_all_df["flow_num"] = (
    sector_all_df
    .groupby("nganh")["flow_num"]
    .ffill()
)

sector_all_df["flow_vua_tich_cuc"] = (
    (sector_all_df["flow_num"] == 1)
    & (sector_all_df.groupby("nganh")["flow_num"].shift(1) == -1)
)

sector_all_df["smdt_vua_vuot_70"] = (
    (sector_all_df["smdt"] > 70)
    & (sector_all_df.groupby("nganh")["smdt"].shift(1) <= 70)
)

sector_all_df["nganh_vua_dep"] = (
    sector_all_df["flow_vua_tich_cuc"]
    | sector_all_df["smdt_vua_vuot_70"]
)


# =========================
# 5. XÁC ĐỊNH ĐÁY GIỐNG NOTEBOOK
# =========================

nganh_signal_by_date = (
    sector_all_df
    .groupby("date")
    .agg(
        nganh_vua_dep=("nganh_vua_dep", "any"),
        so_nganh_flow_vua_tich_cuc=("flow_vua_tich_cuc", "sum"),
        so_nganh_smdt_vua_vuot_70=("smdt_vua_vuot_70", "sum")
    )
    .reset_index()
)

market_df = waves_data_df.merge(
    nganh_signal_by_date,
    on="date",
    how="left"
)

market_df["nganh_vua_dep"] = market_df["nganh_vua_dep"].fillna(False)
market_df["so_nganh_flow_vua_tich_cuc"] = market_df["so_nganh_flow_vua_tich_cuc"].fillna(0)
market_df["so_nganh_smdt_vua_vuot_70"] = market_df["so_nganh_smdt_vua_vuot_70"].fillna(0)

market_df = market_df.sort_values("date").reset_index(drop=True)

is_nganh_dep = False

nganh_dang_dep_list = []
chuan_bi_list = []
xac_nhan_list = []

for _, row in market_df.iterrows():

    if row["nganh_vua_dep"]:
        is_nganh_dep = True

    xac_nhan_signal = (
        is_nganh_dep
        and (row["buy"] > 25)
        and (row["waitbuy"] > row["waitsell"])
    )

    chuan_bi_signal = (
        is_nganh_dep
        and (row["waitbuy"] > 60)
        and (row["waitbuy"] > row["waitsell"])
        and not xac_nhan_signal
    )

    nganh_dang_dep_list.append(is_nganh_dep)
    chuan_bi_list.append(chuan_bi_signal)
    xac_nhan_list.append(xac_nhan_signal)

    if xac_nhan_signal:
        is_nganh_dep = False

market_df["nganh_dang_dep"] = nganh_dang_dep_list
market_df["chuan_bi_tao_day"] = chuan_bi_list
market_df["xac_nhan_tao_day"] = xac_nhan_list

market_df["bottom_phase"] = "Bình thường"

market_df.loc[
    market_df["chuan_bi_tao_day"],
    "bottom_phase"
] = "Chuẩn bị tạo đáy"

market_df.loc[
    market_df["xac_nhan_tao_day"],
    "bottom_phase"
] = "Xác nhận tạo đáy"

bottom_dates = market_df.loc[
    market_df["xac_nhan_tao_day"],
    "date"
].tolist()


# =========================
# 6. BUNG GIÁ
# =========================

price_df = pd.DataFrame(
    price_data["TotalTradeReply"]["stockTotals"]
)

price_expand = price_df.explode("totalDatas").copy()

price_detail = pd.DataFrame(
    price_expand["totalDatas"].tolist()
)

price_detail["ticker"] = price_expand["ticker"].values
price_detail["date"] = pd.to_datetime(price_detail["date"])

for col in ["open", "high", "low", "close"]:
    price_detail[col] = pd.to_numeric(
        price_detail[col],
        errors="coerce"
    )

price_detail = price_detail[
    ["date", "ticker", "open", "high", "low", "close"]
].sort_values(["ticker", "date"]).reset_index(drop=True)


# =========================
# 7. TÌM VNINDEX
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

vnindex_df = vnindex_df.sort_values("date").reset_index(drop=True)


# =========================
# 8. TẠO DỮ LIỆU NẾN
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
# 9. MARKER TRÊN BIỂU ĐỒ
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
        "text": "Xác nhận đáy"
    })


# =========================
# 10. VẼ BIỂU ĐỒ NẾN
# =========================

st.subheader(
    f"📉 {vnindex_ticker} - Biểu đồ nến và điểm xác nhận tạo đáy"
)

st.write(
    f"Số điểm xác nhận tạo đáy: {len(bottom_markers)}"
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
# 11. BẢNG GIỐNG NOTEBOOK
# =========================

st.subheader("📌 Bảng tín hiệu tạo đáy")

bottom_signal_df = market_df[
    [
        "date",
        "waitbuy",
        "buy",
        "waitsell",
        "sell",
        "reliability",
        "nganh_vua_dep",
        "nganh_dang_dep",
        "chuan_bi_tao_day",
        "xac_nhan_tao_day",
        "bottom_phase"
    ]
].copy()

bottom_signal_df["date"] = bottom_signal_df["date"].dt.strftime("%Y-%m-%d")

st.dataframe(
    bottom_signal_df,
    hide_index=True,
    use_container_width=True,
    height=500
)
