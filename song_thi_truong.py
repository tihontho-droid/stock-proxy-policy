import streamlit as st
import pandas as pd
import numpy as np
import requests
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(
    page_title="Sóng thị trường & ngành dẫn dắt",
    layout="wide"
)

st.title("📈 Giao dịch theo sóng thị trường")


# =========================
# HÀM GỌI API
# =========================

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

    branch_data = post_api(
        "https://stocktraders.vn/service/data/getBranchPath",
        {"BranchPathRequest": {"account": account}}
    )

    price_data = post_api(
        "https://stocktraders.vn/service/data/getTotalTrade",
        {"TotalTradeRequest": {"account": account}}
    )

    return wave_data, smdt_data, flow_data, branch_data, price_data


# =========================
# LOAD DATA
# =========================

with st.spinner("Đang tải dữ liệu API..."):
    wave_data, smdt_data, flow_data, branch_data, price_data = load_all_data()


# =========================
# 1. STOCK WAVE
# =========================

waves_df = pd.DataFrame(
    wave_data["StockWaveRequest"]["stockWaves"]
)

waves_data_df = pd.DataFrame(
    waves_df["waveDatas"].tolist()
)

waves_data_df["date"] = pd.to_datetime(waves_data_df["date"])

waves_data_df = pd.DataFrame(
    waves_data_df,
    columns=[
        "date",
        "waitbuy",
        "buy",
        "waitsell",
        "sell",
        "reliability"
    ]
)

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
# 3. CASHFLOW TOÀN BỘ NGÀNH
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

sector_all_df["nganh_dep"] = (
    (sector_all_df["flow_num"] == 1)
    | (sector_all_df["smdt"] > 70)
)

sector_all_df["nganh_vua_dep"] = (
    sector_all_df["flow_vua_tich_cuc"]
    | sector_all_df["smdt_vua_vuot_70"]
)


# =========================
# 5. XÁC ĐỊNH NGÀY THỊ TRƯỜNG TẠO ĐÁY
# =========================

market_df = waves_data_df.copy()

market_df["xac_nhan_tao_day"] = (
    (market_df["buy"] > 25)
    & (market_df["waitbuy"] > market_df["waitsell"])
)

market_df["xac_nhan_tao_day_first"] = (
    market_df["xac_nhan_tao_day"]
    & ~market_df["xac_nhan_tao_day"].shift(1).fillna(False)
)

bottom_dates = market_df.loc[
    market_df["xac_nhan_tao_day_first"],
    "date"
].drop_duplicates().tolist()


# =========================
# 6. GIÁ TOÀN BỘ CỔ PHIẾU
# =========================
price_df = pd.DataFrame(
    price_data["TotalTradeReply"]["stockTotals"]
)

price_expand = price_df.explode(
    "totalDatas"
).copy()

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

for n in [5, 10, 20]:
    price_detail[f"close_after_{n}d"] = (
        price_detail.groupby("ticker")["close"].shift(-n)
    )

    price_detail[f"return_{n}d_pct"] = (
        price_detail[f"close_after_{n}d"] / price_detail["close"] - 1
    ) * 100


# =========================
# 7. MAP TICKER VỚI NGÀNH
# =========================

tickers_of_branch_df = pd.DataFrame(
    branch_data["BranchPathReply"]["branchs"]
)

ticker_branch_df = tickers_of_branch_df[
    ["name", "tickers"]
].copy()

ticker_branch_df = ticker_branch_df.rename(columns={
    "name": "nganh"
})

ticker_branch_df = ticker_branch_df.explode("tickers")

ticker_branch_df = ticker_branch_df.rename(columns={
    "tickers": "ticker"
})

ticker_branch_df = ticker_branch_df[
    ["ticker", "nganh"]
].dropna().drop_duplicates()

ticker_branch_df["ticker"] = ticker_branch_df["ticker"].astype(str)


# =========================
# 8. GỘP GIÁ VỚI NGÀNH
# =========================

price_sector_df = price_detail.merge(
    ticker_branch_df,
    on="ticker",
    how="inner"
)


# =========================
# 9. LỌC NGÀNH ĐẸP TẠI NGÀY TẠO ĐÁY
# =========================

bottom_sector_df = sector_all_df[
    (sector_all_df["date"].isin(bottom_dates))
    & (sector_all_df["nganh_dep"])
].copy()

bottom_sector_df = bottom_sector_df.rename(columns={
    "date": "bottom_date"
})


# =========================
# 10. GỘP CỔ PHIẾU THUỘC NGÀNH ĐẸP
# =========================

price_sector_bottom = price_sector_df.rename(columns={
    "date": "bottom_date",
    "close": "close_bottom"
})

stock_after_bottom_df = bottom_sector_df.merge(
    price_sector_bottom,
    on=["bottom_date", "nganh"],
    how="inner"
)


# =========================
# 11. FORMAT KẾT QUẢ
# =========================

return_col = f"return_{holding_period}d_pct"

stock_after_bottom_df = stock_after_bottom_df.rename(columns={
    "smdt": "smdt_bottom",
    "flow_num": "flow_num_bottom",
    "cashflow": "cashflow_bottom"
})

stock_after_bottom_df = stock_after_bottom_df.sort_values(
    ["bottom_date", return_col],
    ascending=[True, False]
).reset_index(drop=True)

# =========================
# 11. BIỂU ĐỒ VNINDEX
# =========================

vnindex_df = price_detail[
    price_detail["ticker"] == "VNINDEX"
].copy()

if vnindex_df.empty:

    st.warning("Không tìm thấy dữ liệu VNINDEX trong API getTotalTrade.")

else:

    vnindex_df = vnindex_df.sort_values("date").reset_index(drop=True)

    candle_data = []

    for _, row in vnindex_df.iterrows():

        candle_data.append({
            "time": row["date"].strftime("%Y-%m-%d"),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"])
        })

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
        "height": 500,
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
