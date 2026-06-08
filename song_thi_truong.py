import streamlit as st
import pandas as pd
import numpy as np
import requests

st.set_page_config(
    page_title="Sóng thị trường & ngành dẫn dắt",
    layout="wide"
)

st.title("📈 Sóng thị trường - Ngành đẹp - Cổ phiếu tăng mạnh sau đáy")


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
# SIDEBAR
# =========================

st.sidebar.header("⚙️ Cài đặt")

start_date = st.sidebar.date_input(
    "Ngày bắt đầu",
    pd.to_datetime("2023-06-08")
)

holding_period = st.sidebar.selectbox(
    "Tính mức tăng sau bao nhiêu phiên?",
    [5, 10, 20],
    index=2
)

top_n = st.sidebar.slider(
    "Top cổ phiếu hiển thị",
    5, 50, 10
)


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

bottom_dates = market_df.loc[
    market_df["xac_nhan_tao_day"],
    "date"
].drop_duplicates().tolist()


# =========================
# 6. GIÁ TOÀN BỘ CỔ PHIẾU
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
price_detail["close"] = pd.to_numeric(
    price_detail["close"],
    errors="coerce"
)

price_detail = price_detail[
    ["date", "ticker", "close"]
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
# HIỂN THỊ
# =========================

st.subheader("📌 Ngày thị trường xác nhận tạo đáy")

bottom_show = market_df[
    market_df["xac_nhan_tao_day"]
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

st.dataframe(bottom_show, use_container_width=True)


st.subheader("🏆 Top cổ phiếu tăng mạnh sau mỗi đáy")

show_cols = [
    "bottom_date",
    "nganh",
    "ticker",
    "close_bottom",
    "smdt_bottom",
    "flow_num_bottom",
    "cashflow_bottom",
    "flow_vua_tich_cuc",
    "smdt_vua_vuot_70",
    "nganh_vua_dep",
    return_col
]

best_stock_each_bottom = (
    stock_after_bottom_df
    .sort_values(["bottom_date", return_col], ascending=[True, False])
    .groupby("bottom_date")
    .head(top_n)
    .reset_index(drop=True)
)

st.dataframe(
    best_stock_each_bottom[show_cols],
    use_container_width=True
)


st.subheader("📊 Ngành nào tăng tốt nhất sau đáy")

sector_summary = (
    stock_after_bottom_df
    .groupby(["bottom_date", "nganh"])
    .agg(
        so_ma=("ticker", "nunique"),
        return_tb=(return_col, "mean"),
        return_max=(return_col, "max")
    )
    .reset_index()
    .sort_values(["bottom_date", "return_tb"], ascending=[True, False])
)

st.dataframe(sector_summary, use_container_width=True)


st.subheader("🔥 Top cổ phiếu mạnh nhất toàn bộ các đáy")

top_all = stock_after_bottom_df.sort_values(
    return_col,
    ascending=False
).head(top_n)

st.dataframe(
    top_all[show_cols],
    use_container_width=True
)
