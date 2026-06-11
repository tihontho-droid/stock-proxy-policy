import streamlit as st
import pandas as pd
import requests 
from streamlit_lightweight_charts import renderLightweightCharts
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="Bảng tạo đáy thị trường",
    layout="wide"
)

st.title("📉 Giao dịch theo sóng thị trường")
if st.button("🔄 Tải lại dữ liệu API"):
    if os.path.exists("api_cache.pkl"):
        os.remove("api_cache.pkl")
    st.cache_data.clear()
    st.rerun()
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

    branch_data = post_api(
        "https://stocktraders.vn/service/data/getBranchPath",
        {"BranchPathRequest": {"account": account}}
    )    
    return wave_data, smdt_data, flow_data, price_data, branch_data


with st.spinner("Đang tải dữ liệu..."):
    wave_data, smdt_data, flow_data, price_data, branch_data = load_all_data()


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
# CHUẨN HÓA TÊN NGÀNH FLOW CHO KHỚP SMDT
# =========================

flow_name_map = {
    "Ngân hàng thương mại truyền thống": "Ngân hàng",
    "Môi giới chứng khoán": "Chứng khoán",
    "Bất động sản dân cư": "BĐS Dân cư",
    "Bất động sản dân cư": "BĐS Dân cư",
    "Thương mại (Bán buôn) sắt thép": "Thép"
}

flow_detail["nganh"] = (
    flow_detail["nganh"]
    .replace(flow_name_map)
)

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
# Nếu các điểm xác nhận gần nhau trong 5 phiên thì chỉ hiện 1 marker
# =========================

marker_df = bottom_signal_df.copy()
marker_df = marker_df.sort_values("date").reset_index(drop=True)

xac_nhan_df = marker_df[
    marker_df["xac_nhan_tao_day"] == True
].copy()

xac_nhan_df = xac_nhan_df.sort_values("date").reset_index(drop=True)

marker_rows = []

last_marker_idx = None

for idx, row in xac_nhan_df.iterrows():

    current_date = row["date"]

    if last_marker_idx is None:
        marker_rows.append(row)
        last_marker_idx = marker_df.index[
            marker_df["date"] == current_date
        ][0]

    else:
        current_idx = marker_df.index[
            marker_df["date"] == current_date
        ][0]

        # Nếu cách marker trước <= 5 phiên thì bỏ qua
        if current_idx - last_marker_idx > 5:
            marker_rows.append(row)
            last_marker_idx = current_idx

xac_nhan_marker_df = pd.DataFrame(marker_rows)

# =========================
# 9. LẤY DỮ LIỆU VNINDEX
# Khóa dữ liệu nến lại bằng file parquet
# =========================

vnindex_cache_path = "vnindex_df.parquet"

if os.path.exists(vnindex_cache_path):

    vnindex_ticker = "VNINDEX"

    vnindex_df = pd.read_parquet(vnindex_cache_path)

    vnindex_df["date"] = pd.to_datetime(vnindex_df["date"])

else:

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
        st.stop()

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

    vnindex_df.to_parquet(
        vnindex_cache_path,
        index=False
    )


# =========================
# TẠO CANDLE DATA TỪ FILE ĐÃ KHÓA
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
# MARKER XÁC NHẬN ĐÁY
# Marker vẫn tính lại vì phụ thuộc xac_nhan_marker_df
# =========================

markers = []

for _, row in xac_nhan_marker_df.iterrows():

    markers.append({
        "time": row["date"].strftime("%Y-%m-%d"),
        "position": "belowBar",
        "color": "#00C853",
        "shape": "arrowUp",
        "text": "Xác nhận đáy"
    })


# =========================
# VẼ BIỂU ĐỒ
# =========================

st.subheader(f"{vnindex_ticker} - Tín hiệu tạo đáy")

chart = [
    {
        "chart": {
            "height": 500,
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
# 10. TRA CỨU NGÀY XÁC NHẬN ĐÁY
# =========================

st.subheader("🔎 Tra cứu ngày xác nhận đáy")

confirm_df = xac_nhan_marker_df.copy()
confirm_df = confirm_df.sort_values("date").reset_index(drop=True)

confirm_dates = confirm_df["date"].dt.strftime("%Y-%m-%d").tolist()

if len(confirm_dates) == 0:

    st.warning("Chưa có ngày xác nhận tạo đáy.")
    st.stop()

selected_confirm_date_str = st.selectbox(
    "Chọn ngày xác nhận đáy",
    confirm_dates
)

selected_confirm_date = pd.to_datetime(selected_confirm_date_str)

prepare_df = bottom_signal_df[
    (bottom_signal_df["chuan_bi_tao_day"] == True)
    & (bottom_signal_df["date"] < selected_confirm_date)
].copy()

if prepare_df.empty:

    st.warning("Không tìm thấy ngày chuẩn bị tạo đáy trước ngày xác nhận này.")
    st.stop()


prepare_row = (
    prepare_df
    .sort_values("date")
    .tail(1)
    .iloc[0]
)

confirm_row = bottom_signal_df[
    bottom_signal_df["date"] == selected_confirm_date
].iloc[0]

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

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:13px;
            color:#555;
            margin-top:4px;
            background:#F8F9FD;
            padding:10px;
            border-radius:12px;
            border:1px solid #ECEEF5;
        ">
            Chờ mua: <b>{prepare_row["waitbuy"]}</b> |
            Mua: <b>{prepare_row["buy"]}</b> |
            Chờ bán: <b>{prepare_row["waitsell"]}</b> |
            Bán: <b>{prepare_row["sell"]}</b>
        </div>
        """,
        unsafe_allow_html=True
    )


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

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:13px;
            color:#555;
            margin-top:4px;
            background:#F8F9FD;
            padding:10px;
            border-radius:12px;
            border:1px solid #ECEEF5;
        ">
            Chờ mua: <b>{confirm_row["waitbuy"]}</b> |
            Mua: <b>{confirm_row["buy"]}</b> |
            Chờ bán: <b>{confirm_row["waitsell"]}</b> |
            Bán: <b>{confirm_row["sell"]}</b>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================
# ĐỌC FILE MAP TICKER - NGÀNH
# =========================

if "ticker_branch_df" not in globals():

    if os.path.exists("ticker_branch_df.parquet"):

        ticker_branch_df = pd.read_parquet(
            "ticker_branch_df.parquet"
        )

    elif os.path.exists("flow/ticker_branch_df.parquet"):

        ticker_branch_df = pd.read_parquet(
            "flow/ticker_branch_df.parquet"
        )

    else:

        st.error("Không tìm thấy file ticker_branch_df.parquet.")
        st.stop()

ticker_branch_df["ticker"] = (
    ticker_branch_df["ticker"]
    .astype(str)
)

# =========================
# LỘ TRÌNH DẪN SÓNG + ĐỘ LAN TỎA NỘI NGÀNH
# =========================

st.write("")
st.subheader("Lộ trình dẫn sóng và độ lan tỏa nội ngành")

nganh_chu_luc = [
    "Ngân hàng",
    "Chứng khoán",
    "BĐS Dân cư",
    "Xây dựng",
    "Thép",
    "Sóng ngành Vin"
]

# =========================
# ĐỌC FILE TÍN HIỆU MÃ
# =========================

if "stock_signal_df" not in globals():

    if os.path.exists("stock_signal_df.parquet"):

        stock_signal_df = pd.read_parquet(
            "stock_signal_df.parquet"
        )

    elif os.path.exists("flow/stock_signal_df.parquet"):

        stock_signal_df = pd.read_parquet(
            "flow/stock_signal_df.parquet"
        )

    else:

        stock_signal_df = pd.DataFrame()

if not stock_signal_df.empty:

    stock_signal_df["date"] = pd.to_datetime(
        stock_signal_df["date"]
    )

    stock_signal_df["ticker"] = (
        stock_signal_df["ticker"]
        .astype(str)
    )

# =========================
# LẤY VÙNG QUANH ĐÁY
# =========================

all_signal_dates = (
    bottom_signal_df["date"]
    .sort_values()
    .reset_index(drop=True)
)

confirm_idx = all_signal_dates[
    all_signal_dates == selected_confirm_date
].index[0]

start_idx = max(confirm_idx - 5, 0)
end_idx = min(confirm_idx + 5, len(all_signal_dates) - 1)

window_dates = all_signal_dates.iloc[
    start_idx:end_idx + 1
]

lead_sector_df = sector_all_df[
    (sector_all_df["date"].isin(window_dates))
    & (
        (sector_all_df["flow_vua_tich_cuc"] == True)
        | (sector_all_df["smdt_vua_vuot_70"] == True)
    )
].copy()

if lead_sector_df.empty:

    st.info("Không có ngành xuất hiện tín hiệu quanh đáy này.")

else:

    # =========================
    # PHÂN NHÓM NGÀNH
    # =========================

    lead_sector_df["nhom_nganh"] = lead_sector_df["nganh"].apply(
        lambda x: "Ngành chủ lực" if x in nganh_chu_luc else "Ngành phụ"
    )

    lead_sector_df["giai_doan"] = lead_sector_df["date"].apply(
        lambda x: "Trước đáy" if x < selected_confirm_date
        else ("Ngày xác nhận" if x == selected_confirm_date else "Sau đáy")
    )

    # =========================
    # TÍNH ĐỘ LAN TỎA NỘI NGÀNH
    # =========================

    breadth_records = []

    for _, row in lead_sector_df.iterrows():

        signal_date = row["date"]
        nganh = row["nganh"]

        sector_tickers = (
            ticker_branch_df[
                ticker_branch_df["nganh"] == nganh
            ]["ticker"]
            .astype(str)
            .drop_duplicates()
            .tolist()
        )

        tong_ma = len(sector_tickers)

        so_ma_flow_good = 0
        so_ma_smdt_good = 0
        so_ma_ca_hai_good = 0

        if (not stock_signal_df.empty) and tong_ma > 0:

            stock_tmp = stock_signal_df[
                (stock_signal_df["date"] == signal_date)
                & (stock_signal_df["ticker"].isin(sector_tickers))
            ].copy()

            if not stock_tmp.empty:

                so_ma_flow_good = (
                    stock_tmp["flow_ma_num"] == 1
                ).sum()

                so_ma_smdt_good = (
                    stock_tmp["smdt_ma"] > 70
                ).sum()

                so_ma_ca_hai_good = (
                    (stock_tmp["flow_ma_num"] == 1)
                    & (stock_tmp["smdt_ma"] > 70)
                ).sum()

        ty_le_flow_good = (
            so_ma_flow_good / tong_ma * 100
            if tong_ma > 0 else 0
        )

        ty_le_smdt_good = (
            so_ma_smdt_good / tong_ma * 100
            if tong_ma > 0 else 0
        )

        ty_le_ca_hai_good = (
            so_ma_ca_hai_good / tong_ma * 100
            if tong_ma > 0 else 0
        )

        breadth_records.append({
            "date": signal_date,
            "nganh": nganh,
            "Tổng mã ngành": tong_ma,
            "Số mã dòng tiền tích cực": so_ma_flow_good,
            "% mã dòng tiền tích cực": ty_le_flow_good,
            "Số mã SMDT > 70": so_ma_smdt_good,
            "% mã SMDT > 70": ty_le_smdt_good,
            "Số mã cả 2 tín hiệu tốt": so_ma_ca_hai_good,
            "% mã cả 2 tín hiệu tốt": ty_le_ca_hai_good
        })

    breadth_df = pd.DataFrame(breadth_records)

    lead_sector_df = lead_sector_df.merge(
        breadth_df,
        on=["date", "nganh"],
        how="left"
    )

    # =========================
    # BẢNG HIỂN THỊ
    # =========================

    lead_sector_show = lead_sector_df[
        [
            "date",
            "giai_doan",
            "nganh",
            "nhom_nganh",
            "cashflow",
            "smdt",
            "Tổng mã ngành",
            "Số mã dòng tiền tích cực",
            "% mã dòng tiền tích cực",
            "Số mã SMDT > 70",
            "% mã SMDT > 70",
            "Số mã cả 2 tín hiệu tốt",
            "% mã cả 2 tín hiệu tốt"
        ]
    ].copy()

    lead_sector_show["date"] = (
        lead_sector_show["date"]
        .dt.strftime("%Y-%m-%d")
    )

    lead_sector_show["smdt"] = (
        lead_sector_show["smdt"]
        .round(2)
    )

    for col in [
        "% mã dòng tiền tích cực",
        "% mã SMDT > 70",
        "% mã cả 2 tín hiệu tốt"
    ]:

        lead_sector_show[col] = (
            lead_sector_show[col]
            .round(1)
        )

    lead_sector_show = lead_sector_show.sort_values(
        [
            "date",
            "nhom_nganh",
            "% mã cả 2 tín hiệu tốt",
            "% mã SMDT > 70"
        ],
        ascending=[True, True, False, False]
    ).reset_index(drop=True)

    chu_luc_df = lead_sector_show[
        lead_sector_show["nhom_nganh"] == "Ngành chủ lực"
    ].copy()

    phu_df = lead_sector_show[
        lead_sector_show["nhom_nganh"] == "Ngành phụ"
    ].copy()

    chu_luc_df = chu_luc_df.rename(columns={
        "date": "Ngày",
        "giai_doan": "Giai đoạn",
        "nganh": "Ngành",
        "cashflow": "Dòng tiền",
        "smdt": "SMDT"
    })

    phu_df = phu_df.rename(columns={
        "date": "Ngày",
        "giai_doan": "Giai đoạn",
        "nganh": "Ngành",
        "cashflow": "Dòng tiền",
        "smdt": "SMDT"
    })

    show_cols = [
        "Ngày",
        "Giai đoạn",
        "Ngành",
        "Dòng tiền",
        "SMDT",
        "Tổng mã ngành",
        "Số mã dòng tiền tích cực",
        "% mã dòng tiền tích cực",
        "Số mã SMDT > 70",
        "% mã SMDT > 70",
        "Số mã cả 2 tín hiệu tốt",
        "% mã cả 2 tín hiệu tốt"
    ]

    col_left, col_right = st.columns(2)

    with col_left:

        st.markdown("##### Ngành chủ lực")

        if chu_luc_df.empty:

            st.info("Không có ngành chủ lực dẫn sóng quanh đáy này.")

        else:

            st.dataframe(
                chu_luc_df[show_cols],
                hide_index=True,
                use_container_width=True,
                height=320
            )

    with col_right:

        st.markdown("##### Ngành phụ")

        if phu_df.empty:

            st.info("Không có ngành phụ dẫn sóng quanh đáy này.")

        else:

            st.dataframe(
                phu_df[show_cols],
                hide_index=True,
                use_container_width=True,
                height=320
            )


# ==================
# TOP 10 MÃ MẠNH 
# ==================
top_stock_all_bottoms = pd.read_parquet(
    "top_stock_all_bottoms.parquet"
)

top_stock_all_bottoms["market_bottom_date"] = pd.to_datetime(
    top_stock_all_bottoms["market_bottom_date"]
)

top_stock_df = top_stock_all_bottoms[
    top_stock_all_bottoms["market_bottom_date"]
    == selected_confirm_date
].copy()

top_stock_df = top_stock_df.head(10)

st.subheader("Top 10 cổ phiếu tăng mạnh")

if top_stock_df.empty:

    st.info("Không có dữ liệu Top 10 cho ngày đáy này.")

else:

    top10_show = top_stock_df.copy()

    top10_show["Top"] = [
        f"TOP {i + 1}"
        for i in range(len(top10_show))
    ]

    top10_show["Mã"] = top10_show["ticker"]

    top10_show["Ngành"] = (
        top10_show["nganh"]
        + " ("
        + top10_show["nhom_nganh"]
        + ")"
    )

    top10_show["Ngày tạo đáy"] = (
        top10_show["stock_bottom_date"]
        .dt.strftime("%d/%m/%Y")
    )

    top10_show["Ngày tạo đỉnh"] = (
        top10_show["peak_date"]
        .dt.strftime("%d/%m/%Y")
    )

    top10_show["Hiệu suất"] = (
        "+"
        + top10_show["return_pct"]
        .round(1)
        .astype(str)
        + "%"
    )

    top10_show = top10_show[
        [
            "Top",
            "Mã",
            "Ngành",
            "Ngày tạo đáy",
            "Ngày tạo đỉnh",
            "Hiệu suất"
        ]
    ]

    st.dataframe(
        top10_show,
        hide_index=True,
        use_container_width=True,
        height=350
    )
# =========================
# MÃ CÓ FLOW + SMDT ĐẸP TRONG GIAI ĐOẠN CHUẨN BỊ TẠO ĐÁY
# =========================

st.subheader("Mã có Flow + SMDT đẹp trong giai đoạn chuẩn bị tạo đáy")

nganh_chu_luc = [
    "Ngân hàng",
    "Chứng khoán",
    "BĐS Dân cư",
    "Xây dựng",
    "Thép",
    "Sóng ngành Vin"
]

# đọc stock_signal_df
if "stock_signal_df" not in globals():

    if os.path.exists("stock_signal_df.parquet"):

        stock_signal_df = pd.read_parquet("stock_signal_df.parquet")

    elif os.path.exists("flow/stock_signal_df.parquet"):

        stock_signal_df = pd.read_parquet("flow/stock_signal_df.parquet")

    else:

        stock_signal_df = pd.DataFrame()

# đọc ticker_branch_df
if "ticker_branch_df" not in globals():

    if os.path.exists("ticker_branch_df.parquet"):

        ticker_branch_df = pd.read_parquet("ticker_branch_df.parquet")

    elif os.path.exists("flow/ticker_branch_df.parquet"):

        ticker_branch_df = pd.read_parquet("flow/ticker_branch_df.parquet")

    else:

        ticker_branch_df = pd.DataFrame()

if stock_signal_df.empty or ticker_branch_df.empty:

    st.info("Chưa có đủ dữ liệu stock_signal_df hoặc ticker_branch_df.")

else:

    stock_signal_df["date"] = pd.to_datetime(stock_signal_df["date"])
    stock_signal_df["ticker"] = stock_signal_df["ticker"].astype(str)

    ticker_branch_df["ticker"] = ticker_branch_df["ticker"].astype(str)

    # =========================
    # TÌM NGÀY CHUẨN BỊ TẠO ĐÁY TRƯỚC NGÀY XÁC NHẬN ĐANG CHỌN
    # =========================

    prepare_df = bottom_signal_df[
        (bottom_signal_df["chuan_bi_tao_day"] == True)
        & (bottom_signal_df["date"] < selected_confirm_date)
    ].copy()

    if prepare_df.empty:

        st.info("Không có ngày chuẩn bị tạo đáy trước đáy đang chọn.")

    else:

        prepare_row = (
            prepare_df
            .sort_values("date")
            .tail(1)
            .iloc[0]
        )

        prepare_date = prepare_row["date"]

        st.markdown(
            f"""
            **Ngày chuẩn bị tạo đáy:** `{prepare_date.strftime('%d/%m/%Y')}`  
            **Ngày xác nhận đáy:** `{selected_confirm_date.strftime('%d/%m/%Y')}`
            """
        )

        # =========================
        # LẤY CÁC MÃ CÓ FLOW VỪA ĐẸP HOẶC SMDT VỪA ĐẸP
        # TRONG VÙNG TỪ CHUẨN BỊ ĐÁY ĐẾN XÁC NHẬN ĐÁY
        # =========================

        signal_window_df = stock_signal_df[
            (stock_signal_df["date"] >= prepare_date)
            & (stock_signal_df["date"] <= selected_confirm_date)
            & (
                (stock_signal_df["flow_ma_vua_tich_cuc"] == True)
                | (stock_signal_df["smdt_ma_vua_vuot_70"] == True)
            )
        ].copy()

        if signal_window_df.empty:

            st.info("Không có mã nào có Flow hoặc SMDT vừa đẹp trong giai đoạn này.")

        else:

            signal_window_df = signal_window_df.merge(
                ticker_branch_df,
                on="ticker",
                how="left"
            )

            signal_window_df["nhom_nganh"] = signal_window_df["nganh"].apply(
                lambda x: "Ngành chủ lực" if x in nganh_chu_luc else "Ngành phụ"
            )

            # =========================
            # GOM LẠI THEO MÃ
            # =========================

            records = []

            for ticker in signal_window_df["ticker"].drop_duplicates():

                ticker_tmp = signal_window_df[
                    signal_window_df["ticker"] == ticker
                ].sort_values("date").copy()

                nganh = ticker_tmp["nganh"].iloc[0]
                nhom_nganh = ticker_tmp["nhom_nganh"].iloc[0]

                flow_rows = ticker_tmp[
                    ticker_tmp["flow_ma_vua_tich_cuc"] == True
                ]

                smdt_rows = ticker_tmp[
                    ticker_tmp["smdt_ma_vua_vuot_70"] == True
                ]

                flow_date = (
                    flow_rows["date"].min()
                    if not flow_rows.empty else pd.NaT
                )

                smdt_date = (
                    smdt_rows["date"].min()
                    if not smdt_rows.empty else pd.NaT
                )

                last_row = ticker_tmp.sort_values("date").iloc[-1]

                records.append({
                    "Mã": ticker,
                    "Ngành": nganh,
                    "Nhóm ngành": nhom_nganh,
                    "Flow vừa đẹp": flow_date,
                    "SMDT vừa đẹp": smdt_date,
                    "SMDT hiện tại": last_row["smdt_ma"],
                    "Dòng tiền hiện tại": last_row["cashflow_ma"],
                    "Có cả Flow + SMDT": (
                        pd.notna(flow_date)
                        and pd.notna(smdt_date)
                    )
                })

            signal_summary_df = pd.DataFrame(records)

            signal_summary_df = signal_summary_df.sort_values(
                [
                    "Có cả Flow + SMDT",
                    "SMDT hiện tại"
                ],
                ascending=[False, False]
            ).reset_index(drop=True)

            # =========================
            # CHIA 2 BẢNG: CHỦ LỰC / PHỤ
            # =========================

            chu_luc_df = signal_summary_df[
                signal_summary_df["Nhóm ngành"] == "Ngành chủ lực"
            ].copy()

            phu_df = signal_summary_df[
                signal_summary_df["Nhóm ngành"] == "Ngành phụ"
            ].copy()

            def format_signal_table(df):

                if df.empty:
                    return df

                show_df = df.copy()

                show_df["Flow vừa đẹp"] = pd.to_datetime(
                    show_df["Flow vừa đẹp"],
                    errors="coerce"
                ).dt.strftime("%d/%m/%Y")

                show_df["SMDT vừa đẹp"] = pd.to_datetime(
                    show_df["SMDT vừa đẹp"],
                    errors="coerce"
                ).dt.strftime("%d/%m/%Y")

                show_df["SMDT hiện tại"] = (
                    show_df["SMDT hiện tại"]
                    .round(2)
                )

                show_df["Có cả Flow + SMDT"] = (
                    show_df["Có cả Flow + SMDT"]
                    .map({
                        True: "Có",
                        False: "Không"
                    })
                )

                return show_df[
                    [
                        "Mã",
                        "Ngành",
                        "Flow vừa đẹp",
                        "SMDT vừa đẹp",
                        "SMDT hiện tại",
                        "Dòng tiền hiện tại",
                        "Có cả Flow + SMDT"
                    ]
                ]

            col_left, col_right = st.columns(2)

            with col_left:

                st.markdown("##### Ngành chủ lực")

                if chu_luc_df.empty:

                    st.info("Không có mã ngành chủ lực có Flow/SMDT đẹp trong giai đoạn này.")

                else:

                    st.dataframe(
                        format_signal_table(chu_luc_df),
                        hide_index=True,
                        use_container_width=True,
                        height=360
                    )

            with col_right:

                st.markdown("##### Ngành phụ")

                if phu_df.empty:

                    st.info("Không có mã ngành phụ có Flow/SMDT đẹp trong giai đoạn này.")

                else:

                    st.dataframe(
                        format_signal_table(phu_df),
                        hide_index=True,
                        use_container_width=True,
                        height=360
                    )
# =========================
# TOP 1 CỦA CÁC ĐÁY
# =========================

st.subheader("Top 1 của tất cả các đáy")

if os.path.exists("top1_signal_sequence.parquet"):

    top1_all_df = pd.read_parquet(
        "top1_signal_sequence.parquet"
    )

elif os.path.exists("flow/top1_signal_sequence.parquet"):

    top1_all_df = pd.read_parquet(
        "flow/top1_signal_sequence.parquet"
    )

else:

    top1_all_df = pd.DataFrame()


if top1_all_df.empty:

    st.info("Chưa có dữ liệu Top 1.")

else:

    analysis_df = top1_all_df.copy()

    # =========================
    # TÍNH LỆCH ĐÁY
    # =========================

    analysis_df["Lệch đáy"] = (
        analysis_df["Đáy cổ phiếu"]
        - analysis_df["Ngày đáy thị trường"]
    ).dt.days

    analysis_df["Thuộc ngành chủ lực"] = analysis_df[
        "Ngành"
    ].isin(
        [
            "Ngân hàng",
            "Chứng khoán",
            "BĐS Dân cư",
            "Xây dựng",
            "Thép",
            "Sóng ngành Vin"
        ]
    )

    # =========================
    # BẢNG CHI TIẾT
    # =========================

    detail_df = analysis_df.copy()

    detail_df["Ngày đáy thị trường"] = (
        pd.to_datetime(
            detail_df["Ngày đáy thị trường"]
        )
        .dt.strftime("%d/%m/%Y")
    )

    detail_df["Đáy cổ phiếu"] = (
        pd.to_datetime(
            detail_df["Đáy cổ phiếu"]
        )
        .dt.strftime("%d/%m/%Y")
    )

    detail_df["Đỉnh cổ phiếu"] = (
        pd.to_datetime(
            detail_df["Đỉnh cổ phiếu"]
        )
        .dt.strftime("%d/%m/%Y")
    )

    detail_df["Hiệu suất"] = (
        detail_df["Hiệu suất"]
        .round(1)
        .astype(str)
        + "%"
    )

    detail_df["Thuộc ngành chủ lực"] = (
        detail_df["Thuộc ngành chủ lực"]
        .map({
            True: "Có",
            False: "Không"
        })
    )

    st.dataframe(
        detail_df[
            [
                "Ngày đáy thị trường",
                "Top 1",
                "Ngành",
                "Thuộc ngành chủ lực",
                "Đáy cổ phiếu",
                "Lệch đáy",
                "Đỉnh cổ phiếu",
                "Hiệu suất"
            ]
        ],
        hide_index=True,
        use_container_width=True,
        height=350
    )

    # =========================
    # THỐNG KÊ NHÓM LỆCH ĐÁY
    # =========================

    st.subheader(
        "Hiệu suất theo thời điểm tạo đáy của cổ phiếu"
    )

    analysis_df["Nhóm lệch đáy"] = pd.cut(
        analysis_df["Lệch đáy"],
        bins=[
            -999,
            -5,
            -1,
            0,
            999
        ],
        labels=[
            "Tạo đáy sớm >5 phiên",
            "Tạo đáy sớm 1-5 phiên",
            "Đúng ngày thị trường",
            "Tạo đáy sau thị trường"
        ]
    )

    summary_df = (
        analysis_df
        .groupby("Nhóm lệch đáy")
        .agg(
            So_ma=("Top 1", "count"),
            Hieu_suat_TB=("Hiệu suất", "mean"),
            Hieu_suat_Max=("Hiệu suất", "max")
        )
        .reset_index()
    )

    summary_df["Hieu_suat_TB"] = (
        summary_df["Hieu_suat_TB"]
        .round(1)
        .astype(str)
        + "%"
    )

    summary_df["Hieu_suat_Max"] = (
        summary_df["Hieu_suat_Max"]
        .round(1)
        .astype(str)
        + "%"
    )

    st.dataframe(
        summary_df,
        hide_index=True,
        use_container_width=True
    )

# =========================
# RULE: NGÀNH VỪA VƯỢT SMDT 70
# MÃ TRONG NGÀNH VƯỢT TỪ <70 LÊN >100
# =========================

st.subheader("Rule chọn mã: Ngành vừa vượt SMDT, mã vượt từ <70 lên >100")

# đọc stock_signal_df
if "stock_signal_df" not in globals():

    if os.path.exists("stock_signal_df.parquet"):

        stock_signal_df = pd.read_parquet(
            "stock_signal_df.parquet"
        )

    elif os.path.exists("flow/stock_signal_df.parquet"):

        stock_signal_df = pd.read_parquet(
            "flow/stock_signal_df.parquet"
        )

    else:

        stock_signal_df = pd.DataFrame()


# đọc ticker_branch_df
if "ticker_branch_df" not in globals():

    if os.path.exists("ticker_branch_df.parquet"):

        ticker_branch_df = pd.read_parquet(
            "ticker_branch_df.parquet"
        )

    elif os.path.exists("flow/ticker_branch_df.parquet"):

        ticker_branch_df = pd.read_parquet(
            "flow/ticker_branch_df.parquet"
        )

    else:

        ticker_branch_df = pd.DataFrame()


if stock_signal_df.empty or ticker_branch_df.empty:

    st.info("Chưa có đủ dữ liệu stock_signal_df hoặc ticker_branch_df.")

else:

    stock_signal_df["date"] = pd.to_datetime(
        stock_signal_df["date"]
    )

    stock_signal_df["ticker"] = (
        stock_signal_df["ticker"]
        .astype(str)
    )

    ticker_branch_df["ticker"] = (
        ticker_branch_df["ticker"]
        .astype(str)
    )

    # =========================
    # TẠO CỘT SMDT HÔM TRƯỚC CỦA MÃ
    # =========================

    stock_signal_df = stock_signal_df.sort_values(
        ["ticker", "date"]
    ).reset_index(drop=True)

    stock_signal_df["smdt_ma_prev"] = (
        stock_signal_df
        .groupby("ticker")["smdt_ma"]
        .shift(1)
    )

    stock_signal_df["ma_vuot_70_len_100"] = (
        (stock_signal_df["smdt_ma_prev"] < 70)
        & (stock_signal_df["smdt_ma"] > 100)
    )

    # =========================
    # LẤY NGÀY NGÀNH VỪA VƯỢT SMDT 70
    # =========================

    sector_signal_df = sector_all_df[
        sector_all_df["smdt_vua_vuot_70"] == True
    ].copy()

    if sector_signal_df.empty:

        st.info("Không có ngày ngành vừa vượt SMDT 70.")

    else:

        result_records = []

        for _, sector_row in sector_signal_df.iterrows():

            signal_date = sector_row["date"]
            nganh = sector_row["nganh"]
            smdt_nganh = sector_row["smdt"]

            sector_tickers = (
                ticker_branch_df[
                    ticker_branch_df["nganh"] == nganh
                ]["ticker"]
                .drop_duplicates()
                .tolist()
            )

            if len(sector_tickers) == 0:
                continue

            stock_candidates = stock_signal_df[
                (stock_signal_df["date"] == signal_date)
                & (stock_signal_df["ticker"].isin(sector_tickers))
                & (stock_signal_df["ma_vuot_70_len_100"] == True)
            ].copy()

            if stock_candidates.empty:
                continue

            for _, stock_row in stock_candidates.iterrows():

                result_records.append({
                    "Ngày ngành vượt SMDT": signal_date,
                    "Ngành": nganh,
                    "SMDT ngành": smdt_nganh,
                    "Mã": stock_row["ticker"],
                    "SMDT mã hôm trước": stock_row["smdt_ma_prev"],
                    "SMDT mã ngày vượt": stock_row["smdt_ma"],
                    "Dòng tiền mã": stock_row.get("cashflow_ma", ""),
                    "Flow mã num": stock_row.get("flow_ma_num", None)
                })

        rule_df = pd.DataFrame(result_records)

        if not rule_df.empty:
        
            rule_df = (
                rule_df
                .sort_values(
                    [
                        "Ngày ngành vượt SMDT",
                        "Ngành",
                        "SMDT mã ngày vượt"
                    ],
                    ascending=[
                        True,
                        True,
                        False
                    ]
                )
                .groupby(
                    [
                        "Ngày ngành vượt SMDT",
                        "Ngành"
                    ],
                    as_index=False
                )
                .head(1)
                .reset_index(drop=True)
            )
        if rule_df.empty:

            st.info("Không có mã nào thỏa rule: ngành vừa vượt SMDT và mã vượt từ <70 lên >100.")

        else:

            rule_show = rule_df.copy()

            rule_show["Ngày ngành vượt SMDT"] = (
                rule_show["Ngày ngành vượt SMDT"]
                .dt.strftime("%d/%m/%Y")
            )

            rule_show["SMDT ngành"] = (
                rule_show["SMDT ngành"]
                .round(2)
            )

            rule_show["SMDT mã hôm trước"] = (
                rule_show["SMDT mã hôm trước"]
                .round(2)
            )

            rule_show["SMDT mã ngày vượt"] = (
                rule_show["SMDT mã ngày vượt"]
                .round(2)
            )

            st.dataframe(
                rule_show[
                    [
                        "Ngày ngành vượt SMDT",
                        "Ngành",
                        "SMDT ngành",
                        "Mã",
                        "SMDT mã hôm trước",
                        "SMDT mã ngày vượt",
                        "Dòng tiền mã",
                        "Flow mã num"
                    ]
                ],
                hide_index=True,
                use_container_width=True,
                height=400
            )
