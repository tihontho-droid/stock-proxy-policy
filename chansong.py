import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from streamlit_lightweight_charts import renderLightweightCharts
 
st.set_page_config(layout="wide")

st.title("Giao dịch theo sóng thị trường") 

# =========================
# DANH SÁCH MÃ NGHIÊN CỨU
# =========================
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
def load_vnindex():
    df = pd.read_csv("vnindex_price.csv")

    df["ticker"] = "VNINDEX"
    df["date"] = pd.to_datetime(df["date"])

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df
 
@st.cache_data
def load_price_data():
    df1 = pd.read_csv("all_price_group1.csv")
    df2 = pd.read_csv("all_price_group2.csv")

    df = pd.concat([df1, df2], ignore_index=True).copy()

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


@st.cache_data
def load_bottom_signal():
    df = pd.read_parquet("bottom_signal_df.parquet")
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data
def load_sector():
    df = pd.read_parquet("sector_all_df.parquet")
    df["date"] = pd.to_datetime(df["date"])
    return df

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

@st.cache_data
def load_top_signal():
    df = pd.read_parquet("top_signal_df.parquet")
    df["date"] = pd.to_datetime(df["date"])

    return df

top_signal_df = load_top_signal()

@st.cache_data
def load_market_cycle():
    df = pd.read_csv("market_cycle.csv")

    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"])

    return df

# =========================
# LOAD DATA
# =========================

price_all = load_price_data()
vnindex = load_vnindex()
vnindex_df = vnindex.copy()

zigzag_all = load_zigzag_data()

bottom_signal_df = load_bottom_signal()

sector_all_df = load_sector()
stock_signal_df = load_stock_signal()
ticker_branch_df = load_ticker_branch()
market_cycle_df = load_market_cycle()

# =========================
# FILTER UNIVERSE (IMPORTANT)
# =========================
tickers_use = ticker_list_202 + ["VNINDEX"]

price_all = price_all[
    price_all["ticker"].isin(tickers_use)
].copy()

zigzag_all = zigzag_all[
    zigzag_all["ticker"].isin(tickers_use)
].copy()

stock_signal_df = stock_signal_df[
    stock_signal_df["ticker"].isin(ticker_list_202)
].copy()

ticker_branch_df = ticker_branch_df[
    ticker_branch_df["ticker"].isin(ticker_list_202)
].copy()

# =========================
# MAP NGÀNH
# =========================
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
    vnindex
    .sort_values("date")
    .reset_index(drop=True)
)

df_vnindex_zigzag = (
    zigzag_all[
        (zigzag_all["ticker"] == "VNINDEX")
        &
        (zigzag_all["percent"] == 5)
    ]
    .sort_values("date")
    .reset_index(drop=True)
)

if df_vnindex_price.empty:
    st.error(
        "Không tìm thấy dữ liệu VNINDEX trong all_price_data.csv"
    )
    st.stop()

if df_vnindex_zigzag.empty:
    st.error(
        "Không tìm thấy ZigZag VNINDEX percent = 5"
    )
    st.stop()


# =========================
# CHUẨN BỊ DỮ LIỆU NẾN
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
            "vertLines": {"color": "#eeeeee"},
            "horzLines": {"color": "#eeeeee"}
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
# DROPDOWN CHỌN ĐÁY
# =========================

signal_df = (
    bottom_signal_df
    .sort_values("date")
    .reset_index(drop=True)
)

bottom_events = []

prepare_date = None
prev_confirm = False

for _, row in signal_df.iterrows():

    current_date = pd.to_datetime(
        row["date"]
    )

    if row["chuan_bi_tao_day"]:

        prepare_date = current_date

    current_confirm = bool(
        row["xac_nhan_tao_day"]
    )

    # chỉ lấy ngày xác nhận đầu tiên
    if current_confirm and not prev_confirm:

        if prepare_date is not None:

            bottom_events.append({
                "prepare_date": prepare_date,
                "confirm_date": current_date
            })

    prev_confirm = current_confirm

bottom_events_df = pd.DataFrame(bottom_events)

if bottom_events_df.empty:

    st.warning(
        "Không tìm thấy tín hiệu xác nhận đáy."
    )
    st.stop()

bottom_events_df = (
    bottom_events_df
    .sort_values(
        "confirm_date",
        ascending=False
    )
    .reset_index(drop=True)
)

bottom_events_df["dropdown_text"] = (
    bottom_events_df["confirm_date"]
    .dt.strftime("%Y-%m-%d")
    +
    " | Chuẩn bị: "
    +
    bottom_events_df["prepare_date"]
    .dt.strftime("%Y-%m-%d")
)

selected_text = st.selectbox(
    "Chọn đáy",
    bottom_events_df["dropdown_text"]
)

selected_row = bottom_events_df[
    bottom_events_df["dropdown_text"]
    == selected_text
]

if selected_row.empty:

    st.error(
        "Không tìm thấy dữ liệu đáy được chọn."
    )
    st.stop()

selected_row = selected_row.iloc[0]

selected_prepare_date = pd.to_datetime(
    selected_row["prepare_date"]
)

selected_confirm_date = pd.to_datetime(
    selected_row["confirm_date"]
)

            
# =========================
# HIỂN THỊ CHUẨN BỊ / XÁC NHẬN ĐÁY
# =========================

prepare_match = bottom_signal_df[
    bottom_signal_df["date"] == selected_prepare_date
]

confirm_match = bottom_signal_df[
    bottom_signal_df["date"] == selected_confirm_date
]

if prepare_match.empty or confirm_match.empty:

    st.info(
        "Không tìm thấy đủ dữ liệu chuẩn bị / xác nhận đáy."
    )

else:

    prepare_row = prepare_match.iloc[0]
    confirm_row = confirm_match.iloc[0]

    prepare_date_str = (
        selected_prepare_date.strftime("%Y-%m-%d")
    )

    confirm_date_str = (
        selected_confirm_date.strftime("%Y-%m-%d")
    )

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

    labels = [
        "Chờ mua",
        "Mua",
        "Chờ bán",
        "Bán"
    ]

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
                xanchor="center"
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
                    showarrow=False,
                    font=dict(
                        size=22
                    )
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

        st.markdown(
            legend_html,
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

        st.markdown(
            legend_html,
            unsafe_allow_html=True
        )

# =========================
# NGÀNH DẪN SÓNG SAU ĐÁY THỊ TRƯỜNG
# =========================

near_window_days = 7

sector_near_bottom = sector_all_df[
    (sector_all_df["date"] >= selected_confirm_date - pd.Timedelta(days=near_window_days))
    &
    (sector_all_df["date"] <= selected_confirm_date + pd.Timedelta(days=near_window_days))
    &
    (sector_all_df["smdt_vua_vuot_70"] == True)
].copy()

if sector_near_bottom.empty:

    st.info(
        "Không có ngành nào vượt SMDT 70 quanh đáy này."
    )

else:

    sector_near_bottom = (
        sector_near_bottom
        .sort_values(
            ["date", "smdt"],
            ascending=[True, False]
        )
        .reset_index(drop=True)
    )

    sector_near_bottom["Lệch ngày"] = (
        sector_near_bottom["date"]
        - selected_confirm_date
    ).dt.days

    sector_near_bottom["Ngày vượt"] = (
        sector_near_bottom["date"].dt.strftime("%Y-%m-%d")
    )

    sector_near_bottom["SMDT"] = (
        sector_near_bottom["smdt"]
        .round(2)
    )

    sector_table = sector_near_bottom[
        [
            "nganh",
            "Ngày vượt",
            "Lệch ngày",
            "SMDT"
        ]
    ].rename(
        columns={
            "nganh": "Ngành"
        }
    )

    # =========================
    # NGÀNH CHỦ LỰC
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
        sector_table["Ngành"]
        .isin(nganh_chu_luc)
    ].copy()

    phu_df = sector_table[
        ~sector_table["Ngành"]
        .isin(nganh_chu_luc)
    ].copy()


    col1, col2 = st.columns(2)

    with col1:

        st.markdown("#### Ngành chủ lực")

        if chu_luc_df.empty:

            st.info("Chưa có ngành chủ lực.")

        else:

            st.dataframe(
                chu_luc_df,
                use_container_width=True,
                hide_index=True
            )

    with col2:

        st.markdown("#### Ngành phụ")

        if phu_df.empty:

            st.info("Chưa có ngành phụ.")

        else:

            st.dataframe(
                phu_df,
                use_container_width=True,
                hide_index=True
            )

# =========================
# CỔ PHIẾU TẠO ĐÁY QUANH VNINDEX
# =========================

st.subheader("Cổ phiếu tạo đáy quanh đáy VNINDEX")

# lấy từ dropdown phía trên
selected_date = selected_confirm_date
window_days = 5  # hoặc giữ slider nếu muốn

def build_bottom_stock_table(
    selected_date,
    window_days,
    zigzag_all,
    stock_signal_df,
    sector_all_df,
    ticker_branch_map
):

    selected_date = pd.to_datetime(selected_date)

    stock_bottoms = zigzag_all[
        (zigzag_all["ticker"] != "VNINDEX") &
        (zigzag_all["type"] == 2)
    ].copy()

    matched_bottoms = stock_bottoms[
        (stock_bottoms["date"] - selected_date).abs().dt.days <= window_days
    ].copy()

    if matched_bottoms.empty:
        return pd.DataFrame()

    result_rows = []

    smdt_window_days = 7

    zigzag_grouped = zigzag_all.groupby("ticker")

    for _, row in matched_bottoms.iterrows():

        ticker = row["ticker"]
        sector = ticker_branch_map.get(ticker, "Không xác định")

        bottom_date = row["date"]
        bottom_price = row["price"]
        zigzag_percent = row["percent"]

        # =========================
        # NEXT PEAK
        # =========================
        try:
            ticker_zigzag = zigzag_grouped.get_group(ticker).sort_values("date").reset_index(drop=True)
        except:
            continue

        matched_idx = ticker_zigzag[
            (ticker_zigzag["date"] == bottom_date) &
            (ticker_zigzag["type"] == 2)
        ].index

        if len(matched_idx) == 0:
            continue

        zz_idx = matched_idx[0]

        if zz_idx + 1 >= len(ticker_zigzag):
            continue

        next_peak = ticker_zigzag.iloc[zz_idx + 1]

        if next_peak["type"] != 1:
            continue

        peak_date = next_peak["date"]
        peak_price = next_peak["price"]

        return_pct = (peak_price - bottom_price) / bottom_price * 100

        # =========================
        # SMDT STOCK
        # =========================
        stock_smdt = stock_signal_df[
            (stock_signal_df["ticker"] == ticker) &
            (stock_signal_df["smdt_ma_vua_vuot_70"] == True) &
            ((stock_signal_df["date"] - selected_date).abs().dt.days <= smdt_window_days)
        ]

        if stock_smdt.empty:
            stock_smdt_near = "Không"
            stock_smdt_cross_date = None
            stock_smdt_value = None
            stock_smdt_delay = None
        else:
            stock_smdt = stock_smdt.copy()
            stock_smdt["abs_days"] = (stock_smdt["date"] - selected_date).abs().dt.days
            best = stock_smdt.sort_values("abs_days").iloc[0]

            stock_smdt_near = "Có"
            stock_smdt_cross_date = best["date"]
            stock_smdt_value = best["smdt_ma"]
            stock_smdt_delay = (stock_smdt_cross_date - selected_date).days

        # =========================
        # SMDT SECTOR
        # =========================
        sector_smdt = sector_all_df[
            (sector_all_df["nganh"] == sector) &
            (sector_all_df["smdt_vua_vuot_70"] == True) &
            ((sector_all_df["date"] - selected_date).abs().dt.days <= smdt_window_days)
        ]

        if sector_smdt.empty:
            sector_smdt_near = "Không"
            sector_smdt_cross_date = None
            sector_smdt_value = None
            sector_smdt_delay = None
        else:
            sector_smdt = sector_smdt.copy()
            sector_smdt["abs_days"] = (sector_smdt["date"] - selected_date).abs().dt.days
            best = sector_smdt.sort_values("abs_days").iloc[0]

            sector_smdt_near = "Có"
            sector_smdt_cross_date = best["date"]
            sector_smdt_value = best["smdt"]
            sector_smdt_delay = (sector_smdt_cross_date - selected_date).days

        # =========================
        # APPEND
        # =========================
        result_rows.append({
            "Ticker": ticker,
            "Ngành": sector,
            "Percent ZigZag": int(zigzag_percent),

            "Ngày đáy CP": bottom_date.date(),
            "Giá đáy CP": round(bottom_price, 2),
            "Lệch ngày": abs((bottom_date - selected_date).days),

            "Ngày đỉnh tiếp theo": peak_date.date(),
            "Giá đỉnh tiếp theo": round(peak_price, 2),
            "Hiệu suất đáy -> đỉnh (%)": round(return_pct, 2),

            "SMDT mã vượt gần đáy TT": stock_smdt_near,
            "Ngày SMDT mã vượt": stock_smdt_cross_date.date() if stock_smdt_cross_date is not None else None,
            "SMDT mã tại ngày vượt": round(stock_smdt_value, 2) if stock_smdt_value is not None else None,
            "Lệch ngày SMDT mã": stock_smdt_delay,

            "SMDT ngành vượt gần đáy TT": sector_smdt_near,
            "Ngày SMDT ngành vượt": sector_smdt_cross_date.date() if sector_smdt_cross_date is not None else None,
            "SMDT ngành tại ngày vượt": round(sector_smdt_value, 2) if sector_smdt_value is not None else None,
            "Lệch ngày SMDT ngành": sector_smdt_delay
        })

    result_df = pd.DataFrame(result_rows)

    if result_df.empty:
        return result_df

    return result_df.sort_values(
        "Hiệu suất đáy -> đỉnh (%)",
        ascending=False
    )


# =========================
# RUN TABLE
# =========================

result_df = build_bottom_stock_table(
    selected_date,
    window_days,
    zigzag_all,
    stock_signal_df,
    sector_all_df,
    ticker_branch_map
)

if result_df.empty:
    st.warning("Không có cổ phiếu nào tạo đáy quanh VNINDEX")
else:
    st.dataframe(result_df, use_container_width=True)


# =========================
# BOX TÌM MÃ VÀ VẼ ZIGZAG CỔ PHIẾU
# =========================

st.subheader("Tra cứu biểu đồ ZigZag theo mã cổ phiếu")

ticker_input = st.text_input(
    "Nhập mã cổ phiếu",
    value="VIX"
).upper().strip()

if ticker_input:

    df_stock_price = price_all[
        price_all["ticker"] == ticker_input
    ].sort_values("date")

    df_stock_zigzag = zigzag_all[
        zigzag_all["ticker"] == ticker_input
    ].sort_values("date")

    if df_stock_price.empty or df_stock_zigzag.empty:
        st.warning(f"Không đủ dữ liệu cho mã {ticker_input}")

    else:

        # =========================
        # CANDLESTICK DATA
        # =========================
        candles_stock = [
            {
                "time": row["date"].strftime("%Y-%m-%d"),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"])
            }
            for _, row in df_stock_price.iterrows()
        ]

        # =========================
        # ZIGZAG LINE + MARKERS
        # =========================
        zigzag_line_stock = []
        markers_stock = []

        for _, row in df_stock_zigzag.iterrows():

            time_str = row["date"].strftime("%Y-%m-%d")
            price_val = float(row["price"])

            zigzag_line_stock.append({
                "time": time_str,
                "value": price_val
            })

            if row["type"] == 1:
                markers_stock.append({
                    "time": time_str,
                    "position": "aboveBar",
                    "shape": "arrowDown",
                    "color": "#F23670",
                    "text": f"Đỉnh {price_val:.2f}"
                })

            elif row["type"] == 2:
                markers_stock.append({
                    "time": time_str,
                    "position": "belowBar",
                    "shape": "arrowUp",
                    "color": "#00A86B",
                    "text": f"Đáy {price_val:.2f}"
                })

        # =========================
        # SMDT STOCK MARKERS
        # =========================
        smdt_cross_df = stock_signal_df[
            (stock_signal_df["ticker"] == ticker_input) &
            (stock_signal_df["smdt_ma_vua_vuot_70"] == True)
        ]

        for _, row in smdt_cross_df.iterrows():

            if pd.isna(row["date"]) or pd.isna(row["smdt_ma"]):
                continue

            markers_stock.append({
                "time": row["date"].strftime("%Y-%m-%d"),
                "position": "aboveBar",
                "shape": "circle",
                "color": "#2962FF",
                "text": f"SMDT {row['smdt_ma']:.2f}"
            })

        # =========================
        # SMDT SECTOR MARKERS
        # =========================
        ticker_sector = ticker_branch_map.get(ticker_input, None)

        if ticker_sector:

            sector_cross_df = sector_all_df[
                (sector_all_df["nganh"] == ticker_sector) &
                (sector_all_df["smdt_vua_vuot_70"] == True)
            ]

            for _, row in sector_cross_df.iterrows():

                if pd.isna(row["date"]) or pd.isna(row["smdt"]):
                    continue

                markers_stock.append({
                    "time": row["date"].strftime("%Y-%m-%d"),
                    "position": "belowBar",
                    "shape": "circle",
                    "color": "#FF9800",
                    "text": f"Ngành {row['smdt']:.2f}"
                })

        # =========================
        # SORT MARKERS (SAFE)
        # =========================
        markers_stock = sorted(
            markers_stock,
            key=lambda x: x["time"]
        )

        # =========================
        # CHART CONFIG
        # =========================
        chart_stock = {
            "chart": {
                "height": 520,
                "layout": {
                    "background": {"type": "solid", "color": "#ffffff"},
                    "textColor": "#000000"
                },
                "grid": {
                    "vertLines": {"color": "#eeeeee"},
                    "horzLines": {"color": "#eeeeee"}
                },
                "rightPriceScale": {"borderColor": "#cccccc"},
                "timeScale": {
                    "borderColor": "#cccccc",
                    "timeVisible": True
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

        # =========================
        # RENDER
        # =========================
        renderLightweightCharts(
            [chart_stock],
            key=f"stock_chart_{ticker_input}"
        )

# =========================
# DROPDOWN CHỌN CHU KỲ THỊ TRƯỜNG
# =========================

st.subheader("Giai đoạn thị trường")

cycle_dropdown = (
    market_cycle_df
    .sort_values("start_date", ascending=False)
    .reset_index(drop=True)
)

# Hiển thị tên chu kỳ
cycle_dropdown["cycle_name"] = cycle_dropdown["cycle_type"].replace({
    "up_cycle": "Uptrend",
    "down_cycle": "Downtrend",
    "sideways": "Sideways"
})

cycle_dropdown["dropdown_text"] = (
    cycle_dropdown["start_date"].dt.strftime("%Y-%m-%d")
    + " → "
    + cycle_dropdown["end_date"].dt.strftime("%Y-%m-%d")
    + " | "
    + cycle_dropdown["cycle_name"]
)

selected_cycle = st.selectbox(
    "Chọn giai đoạn",
    cycle_dropdown["dropdown_text"]
)

selected_row = cycle_dropdown[
    cycle_dropdown["dropdown_text"] == selected_cycle
].iloc[0]

cycle_start = selected_row["start_date"]
cycle_end = selected_row["end_date"]
cycle_type = selected_row["cycle_type"]
cycle_type_display = selected_row["cycle_name"]

start_price = selected_row["start_price"]
end_price = selected_row["end_price"]
return_point = selected_row["return_point"]
return_pct = selected_row["return_pct"]


# =========================
# UP CYCLE
# =========================

if cycle_type == "up_cycle":

    # Ngày chuẩn bị tạo đáy
    prepare_date = cycle_start

    prepare_match = bottom_signal_df[
        bottom_signal_df["date"] == prepare_date
    ]

    confirm_match = (
        bottom_signal_df[
            (bottom_signal_df["date"] >= prepare_date)
            &
            (bottom_signal_df["xac_nhan_tao_day"] == True)
        ]
        .sort_values("date")
        .head(1)
    )

    if not prepare_match.empty and not confirm_match.empty:

        prepare_row = prepare_match.iloc[0]
        confirm_row = confirm_match.iloc[0]

        confirm_date = confirm_row["date"]

        col1, col2 = st.columns(2)

        with col1:

            fig_prepare = make_pie(
                prepare_row,
                f"Cận đáy - {prepare_date.strftime('%Y-%m-%d')}"
            )

            st.plotly_chart(
                fig_prepare,
                use_container_width=True,
                config={"displayModeBar": False}
            )

            st.markdown(
                legend_html,
                unsafe_allow_html=True
            )

        with col2:

            fig_confirm = make_pie(
                confirm_row,
                f"Đáy - {confirm_date.strftime('%Y-%m-%d')}"
            )

            st.plotly_chart(
                fig_confirm,
                use_container_width=True,
                config={"displayModeBar": False}
            )

            st.markdown(
                legend_html,
                unsafe_allow_html=True
            )

    else:

        st.info("Không tìm thấy dữ liệu chuẩn bị/xác nhận tạo đáy cho chu kỳ này.")
     
# =========================
# DOWN CYCLE
# =========================

elif cycle_type == "down_cycle":

    # Ngày chuẩn bị tạo đỉnh
    prepare_date = cycle_start

    prepare_match = top_signal_df[
        top_signal_df["date"] == prepare_date
    ]

    confirm_match = (
        top_signal_df[
            (top_signal_df["date"] >= prepare_date)
            &
            (top_signal_df["xac_nhan_tao_dinh"] == True)
        ]
        .sort_values("date")
        .head(1)
    )

    if not prepare_match.empty and not confirm_match.empty:

        prepare_row = prepare_match.iloc[0]
        confirm_row = confirm_match.iloc[0]

        confirm_date = confirm_row["date"]

        col1, col2 = st.columns(2)

        # =========================
        # CẬN ĐỈNH
        # =========================
        with col1:

            fig_prepare = make_pie(
                prepare_row,
                f"Cận đỉnh - {prepare_date.strftime('%Y-%m-%d')}"
            )

            st.plotly_chart(
                fig_prepare,
                use_container_width=True,
                config={"displayModeBar": False}
            )

            st.markdown(
                legend_html,
                unsafe_allow_html=True
            )

        # =========================
        # XÁC NHẬN ĐỈNH
        # =========================
        with col2:

            fig_confirm = make_pie(
                confirm_row,
                f"Đỉnh - {confirm_date.strftime('%Y-%m-%d')}"
            )

            st.plotly_chart(
                fig_confirm,
                use_container_width=True,
                config={"displayModeBar": False}
            )

            st.markdown(
                legend_html,
                unsafe_allow_html=True
            )

    else:

        st.info("Không tìm thấy dữ liệu chuẩn bị/xác nhận tạo đỉnh cho chu kỳ này.")

# =========================
# DATA
# =========================

df_vnindex_price = (
    vnindex
    .sort_values("date")
    .reset_index(drop=True)
)

if df_vnindex_price.empty:
    st.error("Không tìm thấy dữ liệu VNINDEX")
    st.stop()


# =========================
# CANDLES
# =========================

candles = []

for _, r in df_vnindex_price.iterrows():
    candles.append({
        "time": r["date"].strftime("%Y-%m-%d"),
        "open": float(r["open"]),
        "high": float(r["high"]),
        "low": float(r["low"]),
        "close": float(r["close"])
    })


# =========================
# UP TREND MARKERS (NEW)
# =========================

up_markers = []

# =========================
# REGIME LINES
# =========================

regime_lines = []

for _, r in market_cycle_df.iterrows():

    start = r["start_date"]
    end = r["end_date"]
    ctype = r["cycle_type"]

    df_slice = df_vnindex_price[
        (df_vnindex_price["date"] >= start) &
        (df_vnindex_price["date"] <= end)
    ].dropna()

    if df_slice.empty or len(df_slice) < 3:
        continue

    start_t = start.strftime("%Y-%m-%d")
    end_t = end.strftime("%Y-%m-%d")

    # =========================
    # UPTREND
    # =========================
    if ctype == "up_cycle":

        start_val = float(df_slice["low"].iloc[0])
        end_val = float(df_slice["high"].iloc[-1])

        regime_lines.append({
            "type": "Line",
            "data": [
                {"time": start_t, "value": start_val},
                {"time": end_t, "value": end_val}
            ],
            "options": {
                "color": "#00C853",
                "lineWidth": 2
            }
        })

        # =========================
        # LABEL TRÊN CHART (FIXED)
        # =========================

        up_markers.append({
            "time": start_t,
            "position": "belowBar",
            "shape": "text",
            "color": "#00C853",
            "text": f"Đáy {r['start_price']:.2f}"
        })

        up_markers.append({
            "time": end_t,
            "position": "aboveBar",
            "shape": "text",
            "color": "#D50000",
            "text": f"Đỉnh {r['end_price']:.2f}"
        })


    # =========================
    # SIDEWAYS
    # =========================
    elif ctype == "sideways":

        upper = float(df_slice["high"].quantile(0.95))
        lower = float(df_slice["low"].quantile(0.05))

        if lower <= 0:
            continue

        range_pct = (upper - lower) / lower

        if range_pct > 0.12:
            continue

        mid = (upper + lower) / 2

        regime_lines.append({
            "type": "Line",
            "data": [
                {"time": start_t, "value": upper},
                {"time": end_t, "value": upper}
            ],
            "options": {
                "color": "#2962FF",
                "lineWidth": 1
            }
        })

        regime_lines.append({
            "type": "Line",
            "data": [
                {"time": start_t, "value": lower},
                {"time": end_t, "value": lower}
            ],
            "options": {
                "color": "#2962FF",
                "lineWidth": 1
            }
        })

        regime_lines.append({
            "type": "Line",
            "data": [
                {"time": start_t, "value": mid},
                {"time": end_t, "value": mid}
            ],
            "options": {
                "color": "#90CAF9",
                "lineWidth": 1,
                "lineStyle": 2,
                "priceLineVisible": False
            }
        })

    else:
        continue


# =========================
# TRANSITION (DOWN → UP)
# =========================

transitions = []

cycles = market_cycle_df.sort_values("start_date").reset_index(drop=True)

for i in range(len(cycles) - 1):

    curr = cycles.iloc[i]
    nxt = cycles.iloc[i + 1]

    if curr["cycle_type"] == "down_cycle" and nxt["cycle_type"] == "up_cycle":

        curr_start = curr["start_date"]
        nxt_start = nxt["start_date"]

        df_curr = df_vnindex_price[df_vnindex_price["date"] == curr_start]
        df_next = df_vnindex_price[df_vnindex_price["date"] == nxt_start]

        if df_curr.empty or df_next.empty:
            continue

        start_high = float(df_curr["high"].iloc[0])
        end_low = float(df_next["low"].iloc[0])

        transitions.append({
            "type": "Line",
            "data": [
                {"time": curr_start.strftime("%Y-%m-%d"), "value": start_high},
                {"time": nxt_start.strftime("%Y-%m-%d"), "value": end_low}
            ],
            "options": {
                "color": "#D50000",
                "lineWidth": 2,
                "lineStyle": 0,
                "priceLineVisible": False
            }
        })


# =========================
# CHART
# =========================
st.write("")
st.subheader("Diễn biến thị trường trong từng giai đoạn")
st.write("Chú thích: Các đoạn không thuộc Uptrend hoặc Downtrend được hiểu là Sideways.")

chart = {
    "chart": {
        "height": 600,
        "layout": {
            "background": {"type": "solid", "color": "#ffffff"},
            "textColor": "#000000"
        },
        "grid": {
            "vertLines": {"color": "#eeeeee"},
            "horzLines": {"color": "#eeeeee"}
        },
        "timeScale": {
            "timeVisible": True,
            "secondsVisible": False
        },
        "crosshair": {
            "mode": 1
        }
    },

    "series": [
        {
            "type": "Candlestick",
            "data": candles,
            "markers": up_markers
        },
        *regime_lines,
        *transitions
    ]
}


# =========================
# RENDER
# =========================

renderLightweightCharts(
    [chart],
    key="vnindex_regime_final_clean_markers"
)

# =========================
# TỔNG QUAN SÓNG NGÀNH
# =========================

import plotly.graph_objects as go

st.subheader("Tổng quan sóng ngành")

# ----------------------------------
# Lọc theo chu kỳ
# ----------------------------------

sector_cycle = (
    sector_all_df[
        (sector_all_df["date"] >= cycle_start) &
        (sector_all_df["date"] <= cycle_end)
    ]
    .copy()
)

if sector_cycle.empty:
    st.info("Không có dữ liệu.")
    st.stop()

# ----------------------------------
# Mapping màu
# ----------------------------------

color_map = {
    "Tiếp tục đổ vào": "#00C853",      # xanh đậm
    "Nhen nhóm đổ vào": "#81C784",     # xanh nhạt
    "Đang thoát ra": "#FFA000",        # cam
    "Tiếp tục thoát ra": "#F44336"     # đỏ
}

# ----------------------------------
# Chuẩn bị dữ liệu
# ----------------------------------

sector_cycle["date_str"] = sector_cycle["date"].dt.strftime("%d/%m")

dates = sorted(sector_cycle["date_str"].unique())

sectors = (
    sector_cycle.groupby("nganh")["flow_num"]
    .sum()
    .sort_values(ascending=False)
    .index.tolist()
)

fig = go.Figure()

# ----------------------------------
# Vẽ từng ngành
# ----------------------------------

for sector in sectors:

    df_sector = (
        sector_cycle[
            sector_cycle["nganh"] == sector
        ]
        .set_index("date_str")
    )

    for d in dates:

        if d not in df_sector.index:

            fig.add_trace(
                go.Scatter(
                    x=[d],
                    y=[sector],
                    mode="text",
                    text=["--"],
                    textfont=dict(
                        size=14,
                        color="#666666"
                    ),
                    hoverinfo="skip",
                    showlegend=False
                )
            )

        else:

            row = df_sector.loc[d]

            color = color_map.get(
                row["cashflow"],
                "#BDBDBD"
            )

            fig.add_trace(
                go.Scatter(
                    x=[d],
                    y=[sector],
                    mode="markers",
                    marker=dict(
                        size=15,
                        color=color
                    ),
                    hovertemplate=
                        "<b>%{y}</b><br>"
                        "Ngày: %{x}<br>"
                        f"Cashflow: {row['cashflow']}<br>"
                        f"SMDT: {row['smdt']:.2f}"
                        "<extra></extra>",
                    showlegend=False
                )
            )

# ----------------------------------
# Layout
# ----------------------------------

fig.update_layout(

    height=max(500, len(sectors) * 45),

    plot_bgcolor="white",

    paper_bgcolor="white",

    margin=dict(
        l=20,
        r=20,
        t=20,
        b=20
    ),

    xaxis=dict(

        title="",

        side="top",

        tickangle=0,

        showgrid=False,

        zeroline=False

    ),

    yaxis=dict(

        title="",

        autorange="reversed",

        showgrid=True,

        gridcolor="#EEEEEE"

    )

)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ----------------------------------
# Chú thích
# ----------------------------------

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown("🟢 Tiếp tục đổ vào")

with c2:
    st.markdown("🟩 Nhen nhóm đổ vào")

with c3:
    st.markdown("🟠 Đang thoát ra")

with c4:
    st.markdown("🔴 Tiếp tục thoát ra")

with c5:
    st.markdown("-- Không tín hiệu")
