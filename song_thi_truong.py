import streamlit as st
import pandas as pd
import requests
from streamlit_lightweight_charts import renderLightweightCharts
import plotly.graph_objects as go


st.set_page_config(
    page_title="Bảng tạo đáy thị trường",
    layout="wide"
)

st.title("📉 Giao dịch theo sóng thị trường")

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

    # chỉ dùng marker xác nhận đáy, không dùng chuẩn bị
    markers = []

    for _, row in xac_nhan_marker_df.iterrows():

        markers.append({
            "time": row["date"].strftime("%Y-%m-%d"),
            "position": "belowBar",
            "color": "#00C853",
            "shape": "arrowUp",
            "text": "Xác nhận đáy"
        })

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

# Chỉ lấy những ngày xác nhận đáy đang được dùng làm marker trên biểu đồ
confirm_df = xac_nhan_marker_df.copy()

confirm_df = confirm_df.sort_values("date").reset_index(drop=True)

confirm_dates = confirm_df["date"].dt.strftime("%Y-%m-%d").tolist()

if len(confirm_dates) == 0:

    st.warning("Chưa có ngày xác nhận tạo đáy.")

else:

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

    else:

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
                padding:18px 22px;
                border-radius:18px;
                margin-bottom:18px;
                border:1px solid #ECEEF5;
            ">
                <div style="font-size:18px; font-weight:700;">
                    Đáy được chọn: {confirm_date_str}
                </div>
                <div style="font-size:15px; color:#666; margin-top:4px;">
                    Ngày chuẩn bị tạo đáy: {prepare_date_str}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        labels = ["Chờ mua", "Mua", "Chờ bán", "Bán"]

        colors = [
            "#11D99A",  # Chờ mua
            "#00A86B",  # Mua
            "#FFA114",  # Chờ bán
            "#F23670"   # Bán
        ]

        legend_html = """
        <div style="
            display:flex;
            justify-content:center;
            gap:22px;
            margin-top:-18px;
            margin-bottom:10px;
            font-size:15px;
            color:#444;
        ">
            <div><span style="color:#11D99A; font-size:22px;">●</span> Chờ mua</div>
            <div><span style="color:#00A86B; font-size:22px;">●</span> Mua</div>
            <div><span style="color:#FFA114; font-size:22px;">●</span> Chờ bán</div>
            <div><span style="color:#F23670; font-size:22px;">●</span> Bán</div>
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
                        hole=0.62,
                        marker=dict(
                            colors=colors,
                            line=dict(
                                color="white",
                                width=2
                            )
                        ),
                        textinfo="value",
                        textfont=dict(
                            size=20,
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
                        size=18,
                        color="#333"
                    )
                ),
                height=250,
                margin=dict(
                    t=60,
                    b=30,
                    l=20,
                    r=20
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                annotations=[
                    dict(
                        text=f"<b>{total}</b>",
                        x=0.5,
                        y=0.5,
                        font=dict(
                            size=38,
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
                use_container_width=True
            )

            st.markdown(legend_html, unsafe_allow_html=True)

            st.markdown(
                f"""
                <div style="
                    text-align:center;
                    font-size:15px;
                    color:#555;
                    margin-top:8px;
                ">
                    Chờ mua: <b>{prepare_row["waitbuy"]}</b> |
                    Mua: <b>{prepare_row["buy"]}</b> |
                    Chờ bán: <b>{prepare_row["waitsell"]}</b> |
                    Bán: <b>{prepare_row["sell"]}</b>
                </div>
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
                use_container_width=True
            )

            st.markdown(legend_html, unsafe_allow_html=True)

            st.markdown(
                f"""
                <div style="
                    text-align:center;
                    font-size:15px;
                    color:#555;
                    margin-top:8px;
                ">
                    Chờ mua: <b>{confirm_row["waitbuy"]}</b> |
                    Mua: <b>{confirm_row["buy"]}</b> |
                    Chờ bán: <b>{confirm_row["waitsell"]}</b> |
                    Bán: <b>{confirm_row["sell"]}</b>
                </div>
                </div>
                """,
                unsafe_allow_html=True
            )
