import streamlit as st
import pandas as pd
import requests
from streamlit_lightweight_charts import renderLightweightCharts


st.set_page_config(
    page_title="Bảng tạo đáy thị trường",
    layout="wide"
)

st.title("📌 Bảng tín hiệu tạo đáy thị trường")

start_date = "2023-06-08"


@st.cache_data(ttl=86400)
def post_api(url, payload):
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=86400)
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
    [
        "date",
        "waitbuy",
        "buy",
        "waitsell",
        "sell",
        "reliability"
    ]
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
# 5. GỘP TÍN HIỆU NGÀNH THEO NGÀY
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


# =========================
# 6. TẠO BẢNG TẠO ĐÁY GIỐNG NOTEBOOK
# =========================

is_nganh_dep = False
da_xac_nhan_trong_chu_ky = False

nganh_dang_dep_list = []
chuan_bi_list = []
xac_nhan_list = []

for _, row in market_df.iterrows():

    if row["nganh_vua_dep"]:
        is_nganh_dep = True
        da_xac_nhan_trong_chu_ky = False

    xac_nhan_signal = (
        is_nganh_dep
        and not da_xac_nhan_trong_chu_ky
        and (row["buy"] > 25)
        and (row["waitbuy"] > row["waitsell"])
    )

    chuan_bi_signal = (
        is_nganh_dep
        and not da_xac_nhan_trong_chu_ky
        and (row["waitbuy"] > 60)
        and (row["waitbuy"] > row["waitsell"])
        and not xac_nhan_signal
    )

    nganh_dang_dep_list.append(is_nganh_dep)
    chuan_bi_list.append(chuan_bi_signal)
    xac_nhan_list.append(xac_nhan_signal)

    if xac_nhan_signal:
        da_xac_nhan_trong_chu_ky = True


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


# =========================
# 7. TẠO BẢNG TÍN HIỆU
# =========================

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
        "so_nganh_flow_vua_tich_cuc",
        "so_nganh_smdt_vua_vuot_70",
        "chuan_bi_tao_day",
        "xac_nhan_tao_day",
        "bottom_phase"
    ]
].copy()

# =========================
# 8. LẤY MARKER TỪ BẢNG
# Không thay đổi bảng gốc
# Chỉ hiện marker Xác nhận tạo đáy
# Mỗi cụm xác nhận chỉ lấy ngày đầu tiên
# =========================

marker_df = bottom_signal_df.copy()
marker_df = marker_df.sort_values("date").reset_index(drop=True)

# Nếu nhiều ngày xác nhận liên tiếp:
# 10/04 True, 11/04 True, 12/04 True
# thì chỉ lấy 10/04 làm marker trên biểu đồ
marker_df["xac_nhan_marker"] = (
    marker_df["xac_nhan_tao_day"]
    & ~marker_df["xac_nhan_tao_day"].shift(1).fillna(False)
)

xac_nhan_marker_df = marker_df[
    marker_df["xac_nhan_marker"]
].copy()

# tạo sẵn danh sách marker cho biểu đồ
markers = []

for _, row in xac_nhan_marker_df.iterrows():

    markers.append({
        "time": row["date"].strftime("%Y-%m-%d"),
        "position": "belowBar",
        "color": "#00C853",
        "shape": "arrowUp",
        "text": "Đáy"
    })


# =========================
# 9. LẤY DỮ LIỆU VNINDEX
# =========================

price_df = pd.DataFrame(
    price_data["TotalTradeReply"]["stockTotals"]
)

vnindex_row = price_df[
    price_df["ticker"].isin(
        ["VNINDEX", "VN-INDEX", "VN_INDEX", "VNI", "INDEX"]
    )
].copy()

if vnindex_row.empty:

    st.warning("Không tìm thấy VNINDEX trong dữ liệu giá.")
    st.write(price_df["ticker"].drop_duplicates().head(100).tolist())

else:

    vnindex_ticker = vnindex_row["ticker"].iloc[0]

    vnindex_df = pd.DataFrame(
        vnindex_row["totalDatas"].iloc[0]
    )

    vnindex_df["date"] = pd.to_datetime(vnindex_df["date"])

    for col in ["open", "high", "low", "close"]:
        vnindex_df[col] = pd.to_numeric(
            vnindex_df[col],
            errors="coerce"
        )

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

    markers = []

    for _, row in chuan_bi_marker_df.iterrows():

        markers.append({
            "time": row["date"].strftime("%Y-%m-%d"),
            "position": "belowBar",
            "color": "#F9A825",
            "shape": "circle",
            "text": "Chuẩn bị"
        })

    for _, row in xac_nhan_marker_df.iterrows():

        markers.append({
            "time": row["date"].strftime("%Y-%m-%d"),
            "position": "belowBar",
            "color": "#00C853",
            "shape": "arrowUp",
            "text": "Xác nhận"
        })

    st.subheader(f"📉 {vnindex_ticker} - Tín hiệu tạo đáy")

    chart = [
        {
            "chart": {
                "height": 600,
                "layout": {
                    "background": {
                        "type": "solid",
                        "color": "transparent"
                    },
                    "textColor": "#999999"
                },
                "grid": {
                    "vertLines": {"color": "rgba(150,150,150,0.12)"},
                    "horzLines": {"color": "rgba(150,150,150,0.12)"}
                },
                "timeScale": {
                    "visible": True,
                    "timeVisible": True,
                    "secondsVisible": False,
                    "barSpacing": 6,
                    "rightOffset": 5
                },
                "handleScroll": {
                    "mouseWheel": True,
                    "pressedMouseMove": True
                },
                "handleScale": {
                    "axisPressedMouseMove": True,
                    "mouseWheel": True,
                    "pinch": True
                }
            },
            "series": [
                {
                    "type": "Candlestick",
                    "data": candle_data,
                    "markers": markers,
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
        }
    ]

    renderLightweightCharts(
        chart,
        key="vnindex_bottom_chart"
    )


# =========================
# 10. HIỂN THỊ BẢNG
# =========================

st.subheader("📌 Bảng tín hiệu tạo đáy")

bottom_signal_df_show = bottom_signal_df.copy()

bottom_signal_df_show["date"] = (
    bottom_signal_df_show["date"]
    .dt.strftime("%Y-%m-%d")
)

st.dataframe(
    bottom_signal_df_show,
    hide_index=True,
    use_container_width=True,
    height=600
)
