import streamlit as st
import pandas as pd 
import plotly.graph_objects as go
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(layout="wide")

st.title("Giao dịch theo sóng thị trường") 
 
ticker_list_202 = [
    "AAA", "ABB", "ACB", "AGG", "AGR", "ANV", "APG", "APS", "ASM",
    "BCC", "BCM", "BFC", "BID", "BMI", "BMP", "BSI", "BSR", "BVB",
    "BVH", "BVS", "C4G", "CEO", "CII", "CMG", "CMX", "CNG", "CSV",
    "CTD", "CTG", "CTI", "CTR", "CTS", "D2D", "DBC", "DCM", "DDV",
    "DGC", "DGW", "DHC", "DIG", "DPG", "DPM", "DPR", "DRC", "DTD",
    "DXG", "DXS", "EIB", "EVF", "FCN", "FIT", "FMC", "FOX", "FPT",
    "FRT", "FTS", "GAS", "GEG", "GEX", "GIL", "GMD", "GVR", "HAG",
    "HAH", "HCM", "HDB", "HDC", "HDG", "HHS", "HHV", "HPG", "HQC",
    "HSG", "HT1", "HTN", "HUT", "HVN", "IDC", "IDI", "IDJ", "IJC",
    "ITC", "JVC", "KBC", "KDH", "KHG", "KLB", "KSB", "L14", "LAS",
    "LCG", "LDG", "LHG", "LPB", "LSS", "MBB", "MBS", "MHC", "MIG",
    "MPC", "MSB", "MSH", "MSN", "MSR", "MST", "MWG", "NAB", "NBC",
    "NDN", "NKG", "NLG", "NT2", "NTC", "NTL", "NVB", "NVL", "OCB",
    "OIL", "ORS", "PC1", "PDR", "PET", "PGB", "PHR", "PLC", "PLX",
    "PNJ", "POW", "PPC", "PTB", "PVC", "PVD", "PVS", "PVT", "QCG",
    "QNS", "QTP", "REE", "SAB", "SAM", "SBT", "SCR", "SGB", "SHB",
    "SHS", "SIP", "SMC", "SSB", "SSI", "STB", "SZC", "TCB", "TCH",
    "TCM", "TCX", "TDC", "TDH", "TLG", "TLH", "TNG", "TPB", "TTF",
    "TV2", "VCB", "VCG", "VCI", "VCS", "VDS", "VEA", "VGC",
    "VGI", "VGS", "VHC", "VHM", "VIB", "VIC", "VIP", "VIX", "VJC",
    "VND", "VNM", "VOS", "VPB", "VPI", "VPL", "VPX", "VRE", "VSC",
    "VTP", "YEG"
]

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

# chỉ giữ VNINDEX + 202 mã nghiên cứu
tickers_use = ticker_list_202 + ["VNINDEX"]

price_all = price_all[
    price_all["ticker"].isin(tickers_use)
].copy()

zigzag_all = zigzag_all[
    zigzag_all["ticker"].isin(tickers_use)
].copy()

@st.cache_data
def load_bottom_signal():
    df = pd.read_parquet("bottom_signal_df.parquet")
    df["date"] = pd.to_datetime(df["date"])
    return df


bottom_signal_df = load_bottom_signal()

@st.cache_data
def load_sector():
    df = pd.read_parquet("sector_all_df.parquet")

    df["date"] = pd.to_datetime(df["date"])

    return df

sector_all_df = load_sector()

@st.cache_data
def load_stock_signal():
    df = pd.read_parquet("stock_signal_df.parquet")
    df["date"] = pd.to_datetime(df["date"])
    df["ticker"] = df["ticker"].astype(str).str.upper()
    return df


@st.cache_data
def load_ticker_branch():
    df = pd.read_parquet("ticker_branch_df.parquet")
    df["ticker"] = df["ticker"].astype(str).str.upper()
    return df


stock_signal_df = load_stock_signal()
ticker_branch_df = load_ticker_branch()
sector_all_df = load_sector()

stock_signal_df = stock_signal_df[
    stock_signal_df["ticker"].isin(ticker_list_202)
].copy()

ticker_branch_df = ticker_branch_df[
    ticker_branch_df["ticker"].isin(ticker_list_202)
].copy()

ticker_branch_map = dict(
    zip(
        ticker_branch_df["ticker"],
        ticker_branch_df["nganh"]
    )
)


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

start_date = pd.to_datetime("2015-01-01")
window_days = 2

# các ngày xác nhận đáy
confirmed_dates = (
    bottom_signal_df[
        bottom_signal_df["xac_nhan_tao_day"] == True
    ]["date"]
    .dropna()
    .sort_values()
    .reset_index(drop=True)
)

# các đáy ZigZag VNINDEX
vnindex_bottoms = df_vnindex_zigzag[
    (df_vnindex_zigzag["type"] == 2)
    &
    (df_vnindex_zigzag["date"] >= start_date)
].copy()

matched_bottoms = []

for _, row in vnindex_bottoms.iterrows():

    bottom_date = pd.to_datetime(row["date"])

    # xác nhận đáy phải đến sau 1-2 ngày
    future_confirm = confirmed_dates[
        (confirmed_dates >= bottom_date)
        &
        (confirmed_dates <= bottom_date + pd.Timedelta(days=7))
    ]
    if future_confirm.empty:
        continue

    temp = row.copy()

    temp["confirm_date"] = future_confirm.iloc[0]

    temp["delay_days"] = (
        future_confirm.iloc[0]
        - bottom_date
    ).days

    matched_bottoms.append(temp)

vnindex_bottoms = pd.DataFrame(matched_bottoms)

if vnindex_bottoms.empty:
    st.warning(
        "Không có đáy ZigZag VNINDEX nào được xác nhận sau 1-2 ngày."
    )
    st.stop()

vnindex_bottoms = (
    vnindex_bottoms
    .sort_values("date")
    .reset_index(drop=True)
)

vnindex_bottoms["dropdown_text"] = (
    vnindex_bottoms["date"]
    .dt.strftime("%Y-%m-%d")
    +
    " | Xác nhận: "
    +
    vnindex_bottoms["confirm_date"]
    .dt.strftime("%Y-%m-%d")
)

selected_text = st.selectbox(
    "Chọn đáy VNINDEX",
    vnindex_bottoms["dropdown_text"]
)

selected_row = vnindex_bottoms[
    vnindex_bottoms["dropdown_text"]
    == selected_text
].iloc[0]

# ngày đáy ZigZag VNINDEX
selected_date = pd.to_datetime(
    selected_row["date"]
)

selected_bottom_date = (
    selected_row["date"]
    .date()
)

# ngày xác nhận đáy
selected_confirm_date = pd.to_datetime(
    selected_row["confirm_date"]
)

# =========================
# NGÀNH DẪN SÓNG SAU ĐÁY THỊ TRƯỜNG
# =========================


lead_window_days = 10

near_window_days = 7

sector_near_bottom = sector_all_df[
    (sector_all_df["date"] >= selected_confirm_date - pd.Timedelta(days=near_window_days))
    &
    (sector_all_df["date"] <= selected_confirm_date + pd.Timedelta(days=near_window_days))
    &
    (sector_all_df["smdt_vua_vuot_70"] == True)
].copy()

if sector_near_bottom.empty:

    st.info("Không có ngành nào vừa vượt SMDT 70 sau đáy thị trường này.")

else:

    sector_near_bottom = (
        sector_near_bottom
        .sort_values(["date", "smdt"], ascending=[True, False])
        .reset_index(drop=True)
    )

    sector_near_bottom["Lệch ngày "] = (
        sector_near_bottom["date"] - selected_confirm_date
    ).dt.days

    sector_near_bottom["Ngày SMDT ngành vượt"] = (
        sector_near_bottom["date"].dt.date
    )

    sector_near_bottom["SMDT ngành"] = (
        sector_near_bottom["smdt"].round(2)
    )

    sector_table = sector_near_bottom[
        [
            "nganh",
            "Ngày SMDT ngành vượt",
            "Lệch ngày ",
            "SMDT ngành"
        ]
    ].rename(columns={
        "nganh": "Ngành"
    })

    # =========================
    # CHIA NGÀNH CHỦ LỰC / NGÀNH PHỤ
    # =========================
    
    nganh_chu_luc = [
        "Ngân hàng",
        "Chứng khoán",
        "BĐS Dân cư",
        "Xây dựng",
        "Thép",
        "Sóng ngành Vin"
    ]
    
    chu_luc_df = sector_table[
        sector_table["Ngành"].isin(nganh_chu_luc)
    ].copy()
    
    phu_df = sector_table[
        ~sector_table["Ngành"].isin(nganh_chu_luc)
    ].copy()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Ngành chủ lực")
        if chu_luc_df.empty:
            st.info("Chưa có ngành chủ lực.")
        else:
            st.dataframe(
                chu_luc_df,
                use_container_width=True
            )

    with col2:
        st.markdown("### Ngành phụ")
        if phu_df.empty:
            st.info("Chưa có ngành phụ.")
        else:
            st.dataframe(
                phu_df,
                use_container_width=True
            )
# =========================
# HIỂN THỊ CHUẨN BỊ / XÁC NHẬN ĐÁY
# =========================

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
    selected_prepare_date = pd.to_datetime(
        prepare_row["date"]
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

