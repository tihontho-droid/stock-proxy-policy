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
 
@st.cache_data
def load_trade_signal():

    df = pd.read_parquet("signal_df.parquet")

    df["date"] = pd.to_datetime(df["date"])

    return df


trade_signal_df = load_trade_signal()

@st.cache_data
def load_history():

    df = pd.read_parquet(
        "history_all.parquet"
    )

    df["date"] = pd.to_datetime(df["date"])

    return df


@st.cache_data
def load_performance():

    return pd.read_parquet(
        "performance_all.parquet"
    )

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
history_all = load_history()

performance_all = load_performance()

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
# CHỌN NGÀY
# =========================

st.subheader("📈 Danh sách tín hiệu")

trade_signal_df["date"] = pd.to_datetime(trade_signal_df["date"])

date_list = (
    trade_signal_df["date"]
    .dropna()
    .drop_duplicates()
    .sort_values(ascending=False)
    .tolist()
)

selected_date = st.selectbox(
    "Chọn ngày",
    date_list,
    format_func=lambda x: x.strftime("%d/%m/%Y")
)

# =========================
# DỮ LIỆU NGÀY ĐÓ
# =========================

today_signal = trade_signal_df[
    trade_signal_df["date"] == selected_date
].copy()

# =========================
# TÍN HIỆU
# =========================

buy_df = today_signal[
    today_signal["action"].str.contains(
        "Buy",
        case=False,
        na=False
    )
]

sell_df = today_signal[
    today_signal["action"].str.contains(
        "Sell",
        case=False,
        na=False
    )
]

hold_df = today_signal[
    today_signal["action"] == "Hold"
]


# =========================
# TÊN CỘT
# =========================

display_cols = {
    "ticker": "Mã",
    "action": "Tín hiệu",
    "invested_percent": "Nắm giữ (%)",
    "close": "Giá",
    "final_score": "Final Score"
}

# =========================
# HÀM HIỂN THỊ
# =========================

def show_table(df):

    if df.empty:

        st.info("Không có tín hiệu.")

    else:

        cols = [c for c in display_cols if c in df.columns]

        st.dataframe(
            df[cols].rename(
                columns={
                    k: display_cols[k]
                    for k in cols
                }
            ),
            hide_index=True,
            use_container_width=True
        )

# =========================
# TAB
# =========================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Tất cả",
        "Mua",
        "Bán",
        "Hold"
    ]
)

with tab1:
    show_table(today_signal)

with tab2:
    show_table(buy_df)

with tab3:
    show_table(sell_df)

with tab4:
    show_table(hold_df)

# =========================
# BOX TÌM MÃ VÀ VẼ ZIGZAG CỔ PHIẾU
# =========================

st.subheader("Tín hiệu theo mã cổ phiếu")

ticker_input = st.text_input(
    "Nhập mã cổ phiếu",
    value="VIX"
).upper().strip()

if ticker_input:

    df_stock_price = (
        price_all[
            price_all["ticker"] == ticker_input
        ]
        .sort_values("date")
        .copy()
    )

    df_stock_zigzag = (
        zigzag_all[
            zigzag_all["ticker"] == ticker_input
        ]
        .sort_values("date")
        .copy()
    )

    df_trade = (
        trade_signal_df[
            trade_signal_df["ticker"] == ticker_input
        ]
        .sort_values("date")
        .copy()
    )

    if df_stock_price.empty:

        st.warning(f"Không có dữ liệu {ticker_input}")

    else:

        # =========================
        # Candlestick
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
        # Zigzag line
        # =========================

        zigzag_line_stock = []

        markers_stock = []

        if not df_stock_zigzag.empty:

            for _, row in df_stock_zigzag.iterrows():

                zigzag_line_stock.append({

                    "time": row["date"].strftime("%Y-%m-%d"),

                    "value": float(row["price"])

                })

                # Đỉnh

                if row["type"] == 1:

                    markers_stock.append({

                        "time": row["date"].strftime("%Y-%m-%d"),

                        "position": "aboveBar",

                        "shape": "arrowDown",

                        "color": "#2962FF",

                        "text": f"Đỉnh\n{row['price']:.2f}"

                    })

                # Đáy

                else:

                    markers_stock.append({

                        "time": row["date"].strftime("%Y-%m-%d"),

                        "position": "belowBar",

                        "shape": "arrowUp",

                        "color": "#2962FF",

                        "text": f"Đáy\n{row['price']:.2f}"

                    })

        # =========================
        # Buy Sell Marker
        # =========================
        # =========================
        # Buy / Sell Marker
        # =========================
        
        for _, row in df_trade.iterrows():
        
            if row["action"] == "Hold":
                continue
        
            # BUY
            if "Buy" in row["action"]:
        
                markers_stock.append({
        
                    "time": row["date"].strftime("%Y-%m-%d"),
        
                    "position": "belowBar",
        
                    "shape": "circle",
        
                    "color": "#00C853",
        
                    "text": row["action"]
        
                })
        
            # SELL
            elif "Sell" in row["action"]:
        
                markers_stock.append({
        
                    "time": row["date"].strftime("%Y-%m-%d"),
        
                    "position": "aboveBar",
        
                    "shape": "circle",
        
                    "color": "#F23645",
        
                    "text": row["action"]
        
                })
        
        markers_stock = sorted(
            markers_stock,
            key=lambda x: x["time"]
        )
        chart_stock = {
        
            "chart": {
        
                "height": 520,
        
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
        
        renderLightweightCharts(
        
            [chart_stock],
        
            key=f"stock_chart_{ticker_input}"
        
        )

        # =========================
        # HISTORY
        # =========================
        
        history_stock = (
        
            history_all[
                history_all["ticker"] == ticker_input
            ]
        
            .sort_values("date")
        
            .copy()
        
        )
        
        st.markdown("### Lịch sử giao dịch")
        
        if history_stock.empty:
        
            st.info("Chưa có lịch sử giao dịch.")
        
        else:
        
            st.dataframe(
        
                history_stock[
                    [
        
                        "date",
        
                        "action",
        
                        "invested_percent",
        
                        "close",
        
                        "PnL"
        
                    ]
        
                ].rename(
        
                    columns={
        
                        "date":"Ngày",
        
                        "action":"Tín hiệu",
        
                        "invested_percent":"Tỷ trọng (%)",
        
                        "close":"Giá",
        
                        "PnL":"Lãi/Lỗ"
        
                    }
        
                ),
        
                hide_index=True,
        
                use_container_width=True
        
            )
        
        
        # =========================
        # PERFORMANCE
        # =========================
        
        # =========================
        # PERFORMANCE
        # =========================
        
        performance_stock = (
            performance_all[
                performance_all["ticker"] == ticker_input
            ]
        )
        
        st.markdown("### Hiệu suất")
        
        if performance_stock.empty:
        
            st.info("Chưa có dữ liệu hiệu suất.")
        
        else:
        
            p = performance_stock.iloc[0]
        
            c1, c2, c3, c4, c5, c6 = st.columns(6)
        
            c1.metric(
                "Win Rate",
                f"{p['Win Rate']:.2f}%"
            )
        
            c2.metric(
                "Số trade",
                int(p["Số trade"])
            )
        
            c3.metric(
                "NAV cuối",
                f"{p['NAV cuối']:,.0f}"
            )
        
            c4.metric(
                "TB lãi",
                f"{p['TB lãi']:,.0f}"
            )
        
            c5.metric(
                "TB lỗ",
                f"{p['TB lỗ']:,.0f}"
            )
        
            c6.metric(
                "TB lãi/ TB lỗ",
                f"{p['TB lãi/TB lỗ']:.2f}"
            )
