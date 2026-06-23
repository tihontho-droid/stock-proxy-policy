import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_lightweight_charts import renderLightweightCharts

st.set_page_config(layout="wide")

st.title("Giao dịch theo sóng thị trường")

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


# =========================
# LOAD DATA
# =========================

price_all = load_price_data()
zigzag_all = load_zigzag_data()

bottom_signal_df = load_bottom_signal()

sector_all_df = load_sector()
# =========================
# LẤY DATA VNINDEX
# =========================

df_vnindex_price = (
    price_all[
        price_all["ticker"] == "VNINDEX"
    ]
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

    st.markdown(
        f"""
        ### Ngành dẫn sóng quanh đáy
        Ngày xác nhận đáy: **{selected_confirm_date.strftime('%Y-%m-%d')}**
        """
    )

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
