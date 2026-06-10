Chờ_mua_ngành.ipynb
File
em muốn biến ý tưởng này lên streamlit 
Pasted text(20).txt
Document
em gửi, chị đọc r làm cho em phần đó đi
Pasted text(21).txt
Document
vầy đúng k
Pasted text(22).txt
Document
sửa cho em
Pasted text(23).txt
Document
viết lại cho em đoạn này để copy đi
Chờ_mua_ngành(1).ipynb
File
sao có 1 số ngày xác nhận không giống trong file này làm sao cho giống file này đi 
Pasted text(24).txt
Document
viết lại bản đầy đủ cho em đi
Pasted text(25).txt
Document
viết cho em bản đầy đủ từ đầu đến cuối để copy đi
Chờ_mua_ngành(2).ipynb
File
làm cho em 1 bảng tạo đáy y chang notebook đi, viết đầy đủ để em copy
Pasted text(26).txt
Document
?
Em muốn biểu đồ tròn trông như này
hai cái miếng trắng là gì z 
Pasted text(27).txt
Document
sửa lại từ đoạn này đi
Pasted text(28).txt
Document
sửa cho em từ đoạn này đi
Edit
cho nó lên cùng 1 hàng luôn 
các ô nó k đều nhau
nó bị như này

cho HAG lên cùng hàng với top 1 luôn
làm sao cho chữ top 1 nhỏ và ở trên đầu HAG, ngành thì ở giữa khung, còn lại giữ nguyên
Pasted text(29).txt
Document
chỉnh lại từ phần top5 trở xuống đi
Pasted text(30).txt
Document
đây là code của em tiếp theo, em muốn giải ngân 1 tỷ vào danh mục gồm mã chính chiếm 80% dành cho mã top 1 giai đoạn đáy nhất định, mã phụ chiếm 20% dành cho mã top 2 giai đoạn đáy nhất định nhưng vẫn là mua theo tín hiệu của mã nhé, khi xuất hiện đáy tiếp theo thì có thể bán để mua mã tiếp theo, nếu chưa xuất hiện đáy tiếp theo mà các tín hiệu dòng tiền và SMDT tiêu cực thì cũng bán, sau đó tổng kết lại hiệu suất được bao nhiêu
Pasted text(31).txt
Document
thêm nút bấm để phân tích hay gì đó ngay tra cứu đáy cho chạy nhanh hơn đi
Pasted text(32).txt
Document
tại sao khi mỗi lần bấm chạy phân tích là lỗi?
Pasted text(33).txt
Document
vậy app của em như này thì làm sao cho nó chạy nhanh hơn

Có 3 chỗ làm app em chậm nhất trong file hiện tại: API đã cache rồi, nhưng bung price_detail, build ticker_branch_df, và get_top_stock_for_bottom() vẫn chạy lại mỗi lần bấm phân tích.

Làm nhanh nhất như này:

1. Đổi nút phân tích thành form

Thay đoạn selectbox + button bằng:

with st.form("analysis_form"):

    selected_confirm_date_str = st.selectbox(
        "Chọn ngày xác nhận đáy",
        confirm_dates
    )

    run_analysis = st.form_submit_button(
        "Phân tích đáy này",
        type="primary"
    )

if not run_analysis:
    st.info("Chọn ngày rồi bấm phân tích.")
    st.stop()

selected_confirm_date = pd.to_datetime(selected_confirm_date_str)
2. Cache phần bung giá

Đặt đoạn này phía trên phần dùng price_detail:

@st.cache_data(ttl=86400)
def build_price_detail(price_data):

    price_all_df = pd.DataFrame(
        price_data["TotalTradeReply"]["stockTotals"]
    )

    price_expand = price_all_df.explode("totalDatas").copy()

    price_detail = pd.DataFrame(
        price_expand["totalDatas"].tolist()
    )

    price_detail["ticker"] = price_expand["ticker"].values
    price_detail["date"] = pd.to_datetime(price_detail["date"])

    for col in ["open", "high", "low", "close", "vol"]:
        if col in price_detail.columns:
            price_detail[col] = pd.to_numeric(
                price_detail[col],
                errors="coerce"
            )

    if "vol" not in price_detail.columns:
        price_detail["vol"] = 0

    price_detail["value"] = (
        price_detail["close"] * price_detail["vol"] * 1000
    )

    price_detail = price_detail[
        ["date", "ticker", "open", "high", "low", "close", "vol", "value"]
    ].dropna().sort_values(["ticker", "date"]).reset_index(drop=True)

    return price_detail

Rồi thay toàn bộ đoạn bung giá cũ bằng:

price_detail = build_price_detail(price_data)
3. Cache map ticker-ngành
@st.cache_data(ttl=86400)
def build_ticker_branch_df(branch_data):

    branch_df = pd.DataFrame(
        branch_data["BranchPathReply"]["branchs"]
    )

    ticker_branch_df = branch_df[["name", "tickers"]].copy()

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

    sector_name_map = {
        "Ngân hàng thương mại truyền thống": "Ngân hàng",
        "Môi giới chứng khoán": "Chứng khoán",
        "Bất động sản dân cư": "BĐS Dân cư",
        "Bất động sản dân cư": "BĐS Dân cư",
        "Thương mại (Bán buôn) sắt thép": "Thép"
    }

    ticker_branch_df["nganh"] = ticker_branch_df["nganh"].replace(
        sector_name_map
    )

    return ticker_branch_df

Rồi dùng:

ticker_branch_df = build_ticker_branch_df(branch_data)
4. Cache hàm Top 10

Thêm decorator:

@st.cache_data(ttl=86400)
def get_top_stock_for_bottom(selected_confirm_date):

Nhưng trước đó đổi ngày thành string cho cache ổn hơn:

top_stock_df = get_top_stock_for_bottom(
    selected_confirm_date_str
).head(10)

và trong hàm thêm dòng đầu:

selected_confirm_date = pd.to_datetime(selected_confirm_date)

Làm 3 phần này trước là app sẽ nhanh hơn rõ nhất.
Quan trọng nhất là cache price_detail và ticker_branch_df, vì hiện tại mỗi lần em bấm phân tích, app lại explode dữ liệu giá toàn thị trường lại từ đầu.

Pasted text(34).txt
Document
làm lại cho em nguyên bài đi

Đúng, app của em đang chậm vì nhiều đoạn xử lý lớn nằm ngoài cache và bị chạy lại mỗi lần rerun. Em thay toàn bộ file hiện tại bằng bản refactor này: API, bảng giá, ngành, đáy đều được cache riêng; phần phân tích chỉ chạy sau khi bấm nút.

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

nganh_chu_luc = [
    "Ngân hàng",
    "Chứng khoán",
    "BĐS Dân cư",
    "Xây dựng",
    "Thép",
    "Sóng ngành Vin"
]

sector_name_map = {
    "Ngân hàng thương mại truyền thống": "Ngân hàng",
    "Môi giới chứng khoán": "Chứng khoán",
    "Bất động sản dân cư": "BĐS Dân cư",
    "Bất động sản dân cư": "BĐS Dân cư",
    "Thương mại (Bán buôn) sắt thép": "Thép"
}


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


@st.cache_data(ttl=86400)
def build_waves_data(wave_data, start_date):
    if "StockWaveReply" in wave_data:
        stock_waves = wave_data["StockWaveReply"]["stockWaves"]
    else:
        stock_waves = wave_data["StockWaveRequest"]["stockWaves"]

    waves_df = pd.DataFrame(stock_waves)
    waves_data_df = pd.DataFrame(waves_df["waveDatas"].tolist())

    waves_data_df["date"] = pd.to_datetime(waves_data_df["date"])

    waves_data_df = waves_data_df[
        ["date", "waitbuy", "buy", "waitsell", "sell", "reliability"]
    ].copy()

    waves_data_df = waves_data_df[
        waves_data_df["date"] >= pd.to_datetime(start_date)
    ].copy()

    return waves_data_df.sort_values("date").reset_index(drop=True)


@st.cache_data(ttl=86400)
def build_smdt_detail(smdt_data, start_date):
    smdt_branch_df = pd.DataFrame(
        smdt_data["SMDTBranchReply"]["SMDTDatas"]
    )

    smdt_expand = smdt_branch_df.explode("smdts").copy()
    smdt_detail = pd.DataFrame(smdt_expand["smdts"].tolist())

    smdt_detail["nganh"] = smdt_expand["keyName"].values
    smdt_detail["date"] = pd.to_datetime(smdt_detail["date"])
    smdt_detail["smdt"] = pd.to_numeric(
        smdt_detail["smdt"],
        errors="coerce"
    )

    smdt_detail = smdt_detail[
        smdt_detail["date"] >= pd.to_datetime(start_date)
    ].copy()

    return (
        smdt_detail[["date", "nganh", "smdt"]]
        .sort_values(["nganh", "date"])
        .reset_index(drop=True)
    )


@st.cache_data(ttl=86400)
def build_flow_detail(flow_data):
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
    flow_detail["nganh"] = flow_detail["nganh"].replace(sector_name_map)

    return flow_detail[["date", "nganh", "cashflow", "flow_num"]]


@st.cache_data(ttl=86400)
def build_sector_all_df(smdt_detail, flow_detail):
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

    return sector_all_df


@st.cache_data(ttl=86400)
def build_market_df(waves_data_df, sector_all_df):
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

    return market_df.sort_values("date").reset_index(drop=True)


@st.cache_data(ttl=86400)
def build_bottom_signal_df(market_df):
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

    market_df = market_df.copy()

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

    return bottom_signal_df


@st.cache_data(ttl=86400)
def build_marker_df(bottom_signal_df):
    marker_df = bottom_signal_df.copy()
    marker_df = marker_df.sort_values("date").reset_index(drop=True)

    xac_nhan_df = marker_df[
        marker_df["xac_nhan_tao_day"] == True
    ].copy()

    xac_nhan_df = xac_nhan_df.sort_values("date").reset_index(drop=True)

    marker_rows = []
    last_marker_idx = None

    for _, row in xac_nhan_df.iterrows():

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

            if current_idx - last_marker_idx > 5:
                marker_rows.append(row)
                last_marker_idx = current_idx

    return pd.DataFrame(marker_rows)


@st.cache_data(ttl=86400)
def build_price_detail(price_data):
    price_all_df = pd.DataFrame(
        price_data["TotalTradeReply"]["stockTotals"]
    )

    price_expand = price_all_df.explode("totalDatas").copy()
    price_detail = pd.DataFrame(
        price_expand["totalDatas"].tolist()
    )

    price_detail["ticker"] = price_expand["ticker"].values
    price_detail["date"] = pd.to_datetime(price_detail["date"])

    for col in ["open", "high", "low", "close", "vol"]:
        if col in price_detail.columns:
            price_detail[col] = pd.to_numeric(
                price_detail[col],
                errors="coerce"
            )

    if "vol" not in price_detail.columns:
        price_detail["vol"] = 0

    price_detail["value"] = (
        price_detail["close"] * price_detail["vol"] * 1000
    )

    return (
        price_detail[
            ["date", "ticker", "open", "high", "low", "close", "vol", "value"]
        ]
        .dropna()
        .sort_values(["ticker", "date"])
        .reset_index(drop=True)
    )


@st.cache_data(ttl=86400)
def build_ticker_branch_df(branch_data):
    branch_df = pd.DataFrame(
        branch_data["BranchPathReply"]["branchs"]
    )

    ticker_branch_df = branch_df[["name", "tickers"]].copy()

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
    ticker_branch_df["nganh"] = ticker_branch_df["nganh"].replace(sector_name_map)

    return ticker_branch_df


@st.cache_data(ttl=86400)
def get_top_stock_for_bottom(
    selected_confirm_date_str,
    bottom_signal_df,
    sector_all_df,
    ticker_branch_df,
    price_detail,
    min_avg_value,
    min_wave_return,
    max_holding_sessions
):
    selected_confirm_date = pd.to_datetime(selected_confirm_date_str)

    all_signal_dates = (
        bottom_signal_df["date"]
        .sort_values()
        .reset_index(drop=True)
    )

    if selected_confirm_date not in all_signal_dates.values:
        return pd.DataFrame()

    confirm_idx = all_signal_dates[
        all_signal_dates == selected_confirm_date
    ].index[0]

    start_idx = max(confirm_idx - 5, 0)
    end_idx = min(confirm_idx + 5, len(all_signal_dates) - 1)

    window_dates = all_signal_dates.iloc[start_idx:end_idx + 1]

    lead_sector_tmp = sector_all_df[
        (sector_all_df["date"].isin(window_dates))
        & (
            (sector_all_df["flow_vua_tich_cuc"] == True)
            | (sector_all_df["smdt_vua_vuot_70"] == True)
        )
    ].copy()

    if lead_sector_tmp.empty:
        return pd.DataFrame()

    selected_sectors = (
        lead_sector_tmp["nganh"]
        .drop_duplicates()
        .tolist()
    )

    selected_tickers_tmp = ticker_branch_df[
        ticker_branch_df["nganh"].isin(selected_sectors)
    ].copy()

    if selected_tickers_tmp.empty:
        return pd.DataFrame()

    price_sector_tmp = price_detail.merge(
        selected_tickers_tmp,
        on="ticker",
        how="inner"
    )

    records = []

    for ticker in price_sector_tmp["ticker"].drop_duplicates():

        ticker_df = price_sector_tmp[
            price_sector_tmp["ticker"] == ticker
        ].sort_values("date").reset_index(drop=True)

        if ticker_df.empty:
            continue

        nearest_after = ticker_df[
            ticker_df["date"] >= selected_confirm_date
        ].copy()

        if nearest_after.empty:
            continue

        market_idx = nearest_after.index[0]

        zone_before = 10
        zone_after = 5

        bottom_start_idx = max(market_idx - zone_before, 0)
        bottom_end_idx = min(market_idx + zone_after, len(ticker_df) - 1)

        stock_bottom_zone = ticker_df.iloc[
            bottom_start_idx:bottom_end_idx + 1
        ].copy()

        if stock_bottom_zone.empty:
            continue

        stock_bottom_row = stock_bottom_zone.sort_values("low").iloc[0]

        stock_bottom_date = stock_bottom_row["date"]
        stock_bottom_price = stock_bottom_row["close"]

        stock_bottom_idx = ticker_df[
            ticker_df["date"] == stock_bottom_date
        ].index[0]

        liq_start_idx = max(stock_bottom_idx - 20, 0)

        avg_value_20 = ticker_df.iloc[
            liq_start_idx:stock_bottom_idx + 1
        ]["value"].mean()

        if avg_value_20 < min_avg_value:
            continue

        peak_end_idx = min(
            stock_bottom_idx + max_holding_sessions,
            len(ticker_df) - 1
        )

        period_after_bottom = ticker_df.iloc[
            stock_bottom_idx:peak_end_idx + 1
        ].copy()

        if period_after_bottom.empty:
            continue

        peak_idx = period_after_bottom["high"].idxmax()
        peak_row = ticker_df.loc[peak_idx]

        peak_price = peak_row["high"]
        peak_date = peak_row["date"]

        return_pct = (
            peak_price / stock_bottom_price - 1
        ) * 100

        if return_pct < min_wave_return:
            continue

        nganh = ticker_df["nganh"].iloc[0]

        records.append({
            "ticker": ticker,
            "nganh": nganh,
            "nhom_nganh": "chủ lực" if nganh in nganh_chu_luc else "phụ",
            "market_bottom_date": selected_confirm_date,
            "stock_bottom_date": stock_bottom_date,
            "peak_date": peak_date,
            "return_pct": return_pct,
            "avg_value_20": avg_value_20
        })

    if len(records) == 0:
        return pd.DataFrame()

    return (
        pd.DataFrame(records)
        .sort_values("return_pct", ascending=False)
        .reset_index(drop=True)
    )


with st.spinner("Đang tải dữ liệu..."):
    wave_data, smdt_data, flow_data, price_data, branch_data = load_all_data()

waves_data_df = build_waves_data(wave_data, start_date)
smdt_detail = build_smdt_detail(smdt_data, start_date)
flow_detail = build_flow_detail(flow_data)
sector_all_df = build_sector_all_df(smdt_detail, flow_detail)
market_df = build_market_df(waves_data_df, sector_all_df)
bottom_signal_df = build_bottom_signal_df(market_df)
xac_nhan_marker_df = build_marker_df(bottom_signal_df)
price_detail = build_price_detail(price_data)
ticker_branch_df = build_ticker_branch_df(branch_data)


# =========================
# VNINDEX CHART
# =========================

price_all_df = pd.DataFrame(
    price_data["TotalTradeReply"]["stockTotals"]
)

vnindex_row = price_all_df[
    price_all_df["ticker"].isin(
        ["VNINDEX", "VN-INDEX", "VN_INDEX", "VNI", "INDEX"]
    )
].copy()

if vnindex_row.empty:

    st.warning("Không tìm thấy VNINDEX trong dữ liệu giá.")

else:

    vnindex_ticker = vnindex_row["ticker"].iloc[0]
    vnindex_df = pd.DataFrame(vnindex_row["totalDatas"].iloc[0])

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
                    "background": {"type": "solid", "color": "transparent"},
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
# TRA CỨU NGÀY XÁC NHẬN ĐÁY
# =========================

st.subheader("🔎 Tra cứu ngày xác nhận đáy")

confirm_df = xac_nhan_marker_df.copy()
confirm_df = confirm_df.sort_values("date").reset_index(drop=True)

confirm_dates = confirm_df["date"].dt.strftime("%Y-%m-%d").tolist()

if len(confirm_dates) == 0:

    st.warning("Chưa có ngày xác nhận tạo đáy.")
    st.stop()


with st.form("analysis_form"):

    selected_confirm_date_str = st.selectbox(
        "Chọn ngày xác nhận đáy",
        confirm_dates
    )

    run_analysis = st.form_submit_button(
        "Phân tích đáy này",
        type="primary"
    )


if not run_analysis:

    st.info("Chọn ngày xác nhận đáy rồi bấm 'Phân tích đáy này' để chạy phân tích.")
    st.stop()


selected_confirm_date = pd.to_datetime(selected_confirm_date_str)


# =========================
# BIỂU ĐỒ TRÒN CHUẨN BỊ / XÁC NHẬN
# =========================

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
            font=dict(size=14, color="#333")
        ),
        height=250,
        margin=dict(t=35, b=5, l=5, r=5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        annotations=[
            dict(
                text=f"<b>{total}</b>",
                x=0.5,
                y=0.5,
                font=dict(size=22, color="#111111"),
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


# =========================
# LỘ TRÌNH DẪN SÓNG
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

window_dates = all_signal_dates.iloc[start_idx:end_idx + 1]

lead_sector_df = sector_all_df[
    (sector_all_df["date"].isin(window_dates))
    & (
        (sector_all_df["flow_vua_tich_cuc"] == True)
        | (sector_all_df["smdt_vua_vuot_70"] == True)
    )
].copy()

lead_sector_df["nhom_nganh"] = lead_sector_df["nganh"].apply(
    lambda x: "Ngành chủ lực" if x in nganh_chu_luc else "Ngành phụ"
)

lead_sector_df["giai_doan"] = lead_sector_df["date"].apply(
    lambda x: "Trước đáy" if x < selected_confirm_date
    else ("Ngày xác nhận" if x == selected_confirm_date else "Sau đáy")
)

lead_sector_show = lead_sector_df[
    ["date", "giai_doan", "nganh", "nhom_nganh", "cashflow", "smdt"]
].copy()

lead_sector_show["date"] = lead_sector_show["date"].dt.strftime("%Y-%m-%d")
lead_sector_show["smdt"] = lead_sector_show["smdt"].round(2)

lead_sector_show = lead_sector_show.sort_values(
    ["date", "nhom_nganh", "nganh"]
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

st.subheader("Lộ trình dẫn sóng")

col_left, col_right = st.columns(2)

with col_left:

    st.markdown("##### Ngành chủ lực")

    if chu_luc_df.empty:
        st.info("Không có ngành chủ lực dẫn sóng quanh đáy này.")
    else:
        st.dataframe(
            chu_luc_df[["Ngày", "Giai đoạn", "Ngành", "Dòng tiền", "SMDT"]],
            hide_index=True,
            use_container_width=True,
            height=250
        )

with col_right:

    st.markdown("##### Ngành phụ")

    if phu_df.empty:
        st.info("Không có ngành phụ dẫn sóng quanh đáy này.")
    else:
        st.dataframe(
            phu_df[["Ngày", "Giai đoạn", "Ngành", "Dòng tiền", "SMDT"]],
            hide_index=True,
            use_container_width=True,
            height=250
        )


# =========================
# TOP 10 CỔ PHIẾU TĂNG MẠNH
# =========================

min_avg_value = 5_000_000_000
min_wave_return = 15
max_holding_sessions = 120

st.subheader("Top 10 cổ phiếu tăng mạnh")

top_stock_df = get_top_stock_for_bottom(
    selected_confirm_date_str,
    bottom_signal_df,
    sector_all_df,
    ticker_branch_df,
    price_detail,
    min_avg_value,
    min_wave_return,
    max_holding_sessions
).head(10)

if top_stock_df.empty:

    st.info("Không tìm thấy cổ phiếu thanh khoản cao phù hợp trong các ngành quanh đáy này.")

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

Bản này đã bỏ việc xử lý lặp lại nhiều lần trong thân app. Khi em đổi ngày, app vẫn rerun theo cơ chế của Streamlit, nhưng các đoạn nặng như bung giá, merge ngành, tạo bảng tín hiệu, map ticker-ngành sẽ được lấy từ cache nên nhanh hơn nhiều.

Pasted text(35).txt
Document
sửa full 

Được, em dùng lại file hiện tại nhưng bỏ cache quá tay, chỉ cache API + price_detail + ticker_branch_df. File em gửi đang cache nhiều DataFrame lớn nên bị chậm hơn.

Em sửa theo 3 bước này là đúng nhất:

1. Xóa các decorator @st.cache_data ở các hàm này:

build_waves_data
build_smdt_detail
build_flow_detail
build_sector_all_df
build_market_df
build_bottom_signal_df
build_marker_df
get_top_stock_for_bottom

Chỉ giữ cache cho:

post_api
load_all_data
build_price_detail
build_ticker_branch_df

2. Hàm get_top_stock_for_bottom đổi lại thành không cache:

def get_top_stock_for_bottom(
    selected_confirm_date,
    bottom_signal_df,
    sector_all_df,
    ticker_branch_df,
    price_detail,
    min_avg_value,
    min_wave_return,
    max_holding_sessions
):
    selected_confirm_date = pd.to_datetime(selected_confirm_date)

    all_signal_dates = (
        bottom_signal_df["date"]
        .sort_values()
        .reset_index(drop=True)
    )

    if selected_confirm_date not in all_signal_dates.values:
        return pd.DataFrame()

    confirm_idx = all_signal_dates[
        all_signal_dates == selected_confirm_date
    ].index[0]

    start_idx = max(confirm_idx - 5, 0)
    end_idx = min(confirm_idx + 5, len(all_signal_dates) - 1)

    window_dates = all_signal_dates.iloc[start_idx:end_idx + 1]

    lead_sector_tmp = sector_all_df[
        (sector_all_df["date"].isin(window_dates))
        & (
            (sector_all_df["flow_vua_tich_cuc"] == True)
            | (sector_all_df["smdt_vua_vuot_70"] == True)
        )
    ].copy()

    if lead_sector_tmp.empty:
        return pd.DataFrame()

    selected_sectors = (
        lead_sector_tmp["nganh"]
        .drop_duplicates()
        .tolist()
    )

    selected_tickers_tmp = ticker_branch_df[
        ticker_branch_df["nganh"].isin(selected_sectors)
    ].copy()

    if selected_tickers_tmp.empty:
        return pd.DataFrame()

    price_sector_tmp = price_detail.merge(
        selected_tickers_tmp,
        on="ticker",
        how="inner"
    )

    records = []

    for ticker in price_sector_tmp["ticker"].drop_duplicates():

        ticker_df = price_sector_tmp[
            price_sector_tmp["ticker"] == ticker
        ].sort_values("date").reset_index(drop=True)

        nearest_after = ticker_df[
            ticker_df["date"] >= selected_confirm_date
        ].copy()

        if nearest_after.empty:
            continue

        market_idx = nearest_after.index[0]

        zone_before = 10
        zone_after = 5

        bottom_start_idx = max(market_idx - zone_before, 0)
        bottom_end_idx = min(market_idx + zone_after, len(ticker_df) - 1)

        stock_bottom_zone = ticker_df.iloc[
            bottom_start_idx:bottom_end_idx + 1
        ].copy()

        if stock_bottom_zone.empty:
            continue

        stock_bottom_row = stock_bottom_zone.sort_values("low").iloc[0]

        stock_bottom_date = stock_bottom_row["date"]
        stock_bottom_price = stock_bottom_row["close"]

        stock_bottom_idx = ticker_df[
            ticker_df["date"] == stock_bottom_date
        ].index[0]

        liq_start_idx = max(stock_bottom_idx - 20, 0)

        avg_value_20 = ticker_df.iloc[
            liq_start_idx:stock_bottom_idx + 1
        ]["value"].mean()

        if avg_value_20 < min_avg_value:
            continue

        peak_end_idx = min(
            stock_bottom_idx + max_holding_sessions,
            len(ticker_df) - 1
        )

        period_after_bottom = ticker_df.iloc[
            stock_bottom_idx:peak_end_idx + 1
        ].copy()

        if period_after_bottom.empty:
            continue

        peak_idx = period_after_bottom["high"].idxmax()
        peak_row = ticker_df.loc[peak_idx]

        peak_price = peak_row["high"]
        peak_date = peak_row["date"]

        return_pct = (
            peak_price / stock_bottom_price - 1
        ) * 100

        if return_pct < min_wave_return:
            continue

        nganh = ticker_df["nganh"].iloc[0]

        records.append({
            "ticker": ticker,
            "nganh": nganh,
            "nhom_nganh": "chủ lực" if nganh in nganh_chu_luc else "phụ",
            "market_bottom_date": selected_confirm_date,
            "stock_bottom_date": stock_bottom_date,
            "peak_date": peak_date,
            "return_pct": return_pct,
            "avg_value_20": avg_value_20
        })

    if len(records) == 0:
        return pd.DataFrame()

    return (
        pd.DataFrame(records)
        .sort_values("return_pct", ascending=False)
        .reset_index(drop=True)
    )

3. Chỗ gọi Top 10 sửa thành:

top_stock_df = get_top_stock_for_bottom(
    selected_confirm_date,
    bottom_signal_df,
    sector_all_df,
    ticker_branch_df,
    price_detail,
    min_avg_value,
    min_wave_return,
    max_holding_sessions
).head(10)

Lý do: cache hàm get_top_stock_for_bottom làm chậm vì Streamlit phải hash bottom_signal_df, sector_all_df, ticker_branch_df, price_detail mỗi lần chạy. Chỉ cache price_detail và ticker_branch_df là đủ.

thôi giờ xóa hết đi, làm lại từ đầu nha

Ừ, làm lại từ đầu cho sạch là đúng.

Mình nên chia app thành 4 phần thôi:

1. Load API + cache
2. Xác định đáy thị trường
3. Chọn ngày đáy để phân tích
4. Tính ngành/mã dẫn sóng + backtest

Mai em gửi chị yêu cầu bản mới theo format này:

- Cần dùng những API nào
- Cần hiện những bảng nào
- Logic mua/bán chính xác là gì

rồi chị viết lại full app gọn hơn, không chắp vá từ code cũ nữa.

làm cho em phần 1 đi

Phần 1 là load API + cache, em dán vào đầu file mới:

import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from streamlit_lightweight_charts import renderLightweightCharts


st.set_page_config(
    page_title="Giao dịch theo sóng thị trường",
    layout="wide"
)

st.title("📉 Giao dịch theo sóng thị trường")

START_DATE = "2023-06-08"
ACCOUNT = "uyen.png"


# =========================
# 1. LOAD API + CACHE
# =========================

@st.cache_data(ttl=86400)
def post_api(url, payload):
    response = requests.post(
        url,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=86400)
def load_api_data(account):

    wave_data = post_api(
        "https://stocktraders.vn/service/data/getStockWave",
        {
            "StockWaveRequest": {
                "account": account
            }
        }
    )

    smdt_branch_data = post_api(
        "https://stocktraders.vn/service/data/getSMDTBranch",
        {
            "SMDTBranchRequest": {
                "account": account
            }
        }
    )

    cashflow_branch_data = post_api(
        "https://stocktraders.vn/service/data/getCashFlowBranch",
        {
            "CashFlowBranchRequest": {
                "account": account
            }
        }
    )

    price_data = post_api(
        "https://stocktraders.vn/service/data/getTotalTrade",
        {
            "TotalTradeRequest": {
                "account": account
            }
        }
    )

    branch_data = post_api(
        "https://stocktraders.vn/service/data/getBranchPath",
        {
            "BranchPathRequest": {
                "account": account
            }
        }
    )

    return {
        "wave_data": wave_data,
        "smdt_branch_data": smdt_branch_data,
        "cashflow_branch_data": cashflow_branch_data,
        "price_data": price_data,
        "branch_data": branch_data
    }


with st.spinner("Đang tải dữ liệu API..."):

    api_data = load_api_data(ACCOUNT)


wave_data = api_data["wave_data"]
smdt_branch_data = api_data["smdt_branch_data"]
cashflow_branch_data = api_data["cashflow_branch_data"]
price_data = api_data["price_data"]
branch_data = api_data["branch_data"]


st.success("Đã tải dữ liệu API.")

Phần này chỉ làm nhiệm vụ tải 5 API và cache 1 ngày. Tiếp theo mình sẽ làm phần 2: chuẩn hóa dữ liệu thành bảng waves_data_df, sector_all_df, price_detail, ticker_branch_df.

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

branch_data = post_api(
    "https://stocktraders.vn/service/data/getBranchPath",
    {"BranchPathRequest": {"account": account}}
)    
return wave_data, smdt_data, flow_data, price_data, branch_data

with st.spinner("Đang tải dữ liệu..."):
wave_data, smdt_data, flow_data, price_data, branch_data = load_all_data()

=========================
1. STOCK WAVE
=========================

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

=========================
2. SMDT TOÀN BỘ NGÀNH
=========================

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

=========================
3. FLOW TOÀN BỘ NGÀNH
=========================

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

=========================
CHUẨN HÓA TÊN NGÀNH FLOW CHO KHỚP SMDT
=========================

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

=========================
4. GỘP SMDT + FLOW NGÀNH
=========================

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

=========================
5. GỘP TÍN HIỆU NGÀNH THEO NGÀY
=========================

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

=========================
6. TẠO BẢNG TẠO ĐÁY GIỐNG NOTEBOOK
=========================

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

=========================
7. TẠO BẢNG TÍN HIỆU
=========================

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

=========================
8. LẤY MARKER TỪ BẢNG
Không thay đổi bảng gốc
Nếu các điểm xác nhận gần nhau trong 5 phiên thì chỉ hiện 1 marker
=========================

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

=========================
9. LẤY DỮ LIỆU VNINDEX
=========================

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
=========================
10. TRA CỨU NGÀY XÁC NHẬN ĐÁY
=========================

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

run_analysis = st.button(
"Phân tích đáy này",
type="primary"
)

if not run_analysis:

st.info("Chọn ngày xác nhận đáy rồi bấm 'Phân tích đáy này' để chạy phân tích.")
st.stop()

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


Đáy được chọn: {confirm_date_str}


Ngày chuẩn bị tạo đáy: {prepare_date_str}


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
=========================
NGÀNH DẪN SÓNG TRƯỚC VÀ SAU ĐÁY
=========================

nganh_chu_luc = [
"Ngân hàng",
"Chứng khoán",
"BĐS Dân cư",
"Xây dựng",
"Thép",
"Sóng ngành Vin"
]

lấy 5 phiên trước và 5 phiên sau ngày xác nhận đáy

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

window_dates = all_signal_dates.iloc[start_idx + 1]

lead_sector_df = sector_all_df[
(sector_all_df["date"].isin(window_dates))
& (
(sector_all_df["flow_vua_tich_cuc"] == True)
| (sector_all_df["smdt_vua_vuot_70"] == True)
)
].copy()

phân nhóm ngành

lead_sector_df["nhom_nganh"] = lead_sector_df["nganh"].apply(
lambda x: "Ngành chủ lực" if x in nganh_chu_luc else "Ngành phụ"
)

giai đoạn quanh đáy

lead_sector_df["giai_doan"] = lead_sector_df["date"].apply(
lambda x: "Trước đáy" if x < selected_confirm_date
else ("Ngày xác nhận" if x == selected_confirm_date else "Sau đáy")
)

chỉ hiện tín hiệu dòng tiền và SMDT

lead_sector_df["tin_hieu"] = ""

lead_sector_df.loc[
lead_sector_df["flow_vua_tich_cuc"],
"tin_hieu"
] += "Dòng tiền tích cực "

lead_sector_df.loc[
lead_sector_df["smdt_vua_vuot_70"],
"tin_hieu"
] += "SMDT vượt 70"

lead_sector_show = lead_sector_df[
[
"date",
"giai_doan",
"nganh",
"nhom_nganh",
"cashflow",
"smdt"
]
].copy()

lead_sector_show["date"] = lead_sector_show["date"].dt.strftime("%Y-%m-%d")
lead_sector_show["smdt"] = lead_sector_show["smdt"].round(2)

lead_sector_show = lead_sector_show.sort_values(
["date", "nhom_nganh", "nganh"]
).reset_index(drop=True)

chu_luc_df = lead_sector_show[
lead_sector_show["nhom_nganh"] == "Ngành chủ lực"
].copy()

phu_df = lead_sector_show[
lead_sector_show["nhom_nganh"] == "Ngành phụ"
].copy()

st.subheader("Lộ trình dẫn sóng")

col_left, col_right = st.columns(2)

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

with col_left:

st.markdown("##### Ngành chủ lực")

if chu_luc_df.empty:

    st.info("Không có ngành chủ lực dẫn sóng quanh đáy này.")

else:

    st.dataframe(
        chu_luc_df[
            [
                "Ngày",
                "Giai đoạn",
                "Ngành",
                "Dòng tiền",
                "SMDT"
            ]
        ],
        hide_index=True,
        use_container_width=True,
        height=250
    )

with col_right:

st.markdown("##### Ngành phụ")

if phu_df.empty:

    st.info("Không có ngành phụ dẫn sóng quanh đáy này.")

else:

    st.dataframe(
        phu_df[
            [
                "Ngày",
                "Giai đoạn",
                "Ngành",
                "Dòng tiền",
                "SMDT"
            ]
        ],
        hide_index=True,
        use_container_width=True,
        height=250
    )
=========================
HÀM CHUNG: TÍNH TOP CỔ PHIẾU CHO MỖI NGÀY ĐÁY
=========================

min_avg_value = 5_000_000_000
min_wave_return = 15
max_holding_sessions = 120

map ticker với ngành

branch_df = pd.DataFrame(
branch_data["BranchPathReply"]["branchs"]
)

ticker_branch_df = branch_df[
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

sector_name_map = {
"Ngân hàng thương mại truyền thống": "Ngân hàng",
"Môi giới chứng khoán": "Chứng khoán",
"Bất động sản dân cư": "BĐS Dân cư",
"Bất động sản dân cư": "BĐS Dân cư",
"Thương mại (Bán buôn) sắt thép": "Thép"
}

ticker_branch_df["nganh"] = ticker_branch_df["nganh"].replace(sector_name_map)

bung giá toàn bộ mã một lần

price_all_df = pd.DataFrame(
price_data["TotalTradeReply"]["stockTotals"]
)

price_expand = price_all_df.explode("totalDatas").copy()

price_detail = pd.DataFrame(
price_expand["totalDatas"].tolist()
)

price_detail["ticker"] = price_expand["ticker"].values
price_detail["date"] = pd.to_datetime(price_detail["date"])

for col in ["open", "high", "low", "close", "vol"]:
if col in price_detail.columns:
price_detail[col] = pd.to_numeric(
price_detail[col],
errors="coerce"
)

if "vol" not in price_detail.columns:
price_detail["vol"] = 0

price_detail["value"] = (
price_detail["close"] * price_detail["vol"] * 1000
)

price_detail = price_detail[
[
"date",
"ticker",
"open",
"high",
"low",
"close",
"vol",
"value"
]
].dropna().sort_values(["ticker", "date"]).reset_index(drop=True)

def get_top_stock_for_bottom(selected_confirm_date):

all_signal_dates = (
    bottom_signal_df["date"]
    .sort_values()
    .reset_index(drop=True)
)

if selected_confirm_date not in all_signal_dates.values:
    return pd.DataFrame()

confirm_idx = all_signal_dates[
    all_signal_dates == selected_confirm_date
].index[0]

start_idx = max(confirm_idx - 5, 0)
end_idx = min(confirm_idx + 5, len(all_signal_dates) - 1)

window_dates = all_signal_dates.iloc[start_idx:end_idx + 1]

lead_sector_tmp = sector_all_df[
    (sector_all_df["date"].isin(window_dates))
    & (
        (sector_all_df["flow_vua_tich_cuc"] == True)
        | (sector_all_df["smdt_vua_vuot_70"] == True)
    )
].copy()

if lead_sector_tmp.empty:
    return pd.DataFrame()

selected_sectors = (
    lead_sector_tmp["nganh"]
    .drop_duplicates()
    .tolist()
)

selected_tickers_tmp = ticker_branch_df[
    ticker_branch_df["nganh"].isin(selected_sectors)
].copy()

if selected_tickers_tmp.empty:
    return pd.DataFrame()

price_sector_tmp = price_detail.merge(
    selected_tickers_tmp,
    on="ticker",
    how="inner"
)

records = []

for ticker in price_sector_tmp["ticker"].drop_duplicates():

    ticker_df = price_sector_tmp[
        price_sector_tmp["ticker"] == ticker
    ].sort_values("date").reset_index(drop=True)

    if ticker_df.empty:
        continue

    nearest_after = ticker_df[
        ticker_df["date"] >= selected_confirm_date
    ].copy()

    if nearest_after.empty:
        continue

    market_idx = nearest_after.index[0]

    zone_before = 10
    zone_after = 5

    bottom_start_idx = max(market_idx - zone_before, 0)
    bottom_end_idx = min(market_idx + zone_after, len(ticker_df) - 1)

    stock_bottom_zone = ticker_df.iloc[
        bottom_start_idx:bottom_end_idx + 1
    ].copy()

    if stock_bottom_zone.empty:
        continue

    stock_bottom_row = stock_bottom_zone.sort_values("low").iloc[0]

    stock_bottom_date = stock_bottom_row["date"]
    stock_bottom_price = stock_bottom_row["close"]

    stock_bottom_idx = ticker_df[
        ticker_df["date"] == stock_bottom_date
    ].index[0]

    liq_start_idx = max(stock_bottom_idx - 20, 0)

    avg_value_20 = ticker_df.iloc[
        liq_start_idx:stock_bottom_idx + 1
    ]["value"].mean()

    if avg_value_20 < min_avg_value:
        continue

    peak_end_idx = min(
        stock_bottom_idx + max_holding_sessions,
        len(ticker_df) - 1
    )

    period_after_bottom = ticker_df.iloc[
        stock_bottom_idx:peak_end_idx + 1
    ].copy()

    if period_after_bottom.empty:
        continue

    peak_idx = period_after_bottom["high"].idxmax()
    peak_row = ticker_df.loc[peak_idx]

    peak_price = peak_row["high"]
    peak_date = peak_row["date"]

    return_pct = (
        peak_price / stock_bottom_price - 1
    ) * 100

    if return_pct < min_wave_return:
        continue

    nganh = ticker_df["nganh"].iloc[0]

    records.append({
        "ticker": ticker,
        "nganh": nganh,
        "nhom_nganh": "chủ lực" if nganh in nganh_chu_luc else "phụ",
        "market_bottom_date": selected_confirm_date,
        "stock_bottom_date": stock_bottom_date,
        "peak_date": peak_date,
        "return_pct": return_pct,
        "avg_value_20": avg_value_20
    })

if len(records) == 0:
    return pd.DataFrame()

return (
    pd.DataFrame(records)
    .sort_values("return_pct", ascending=False)
    .reset_index(drop=True)
)
=========================
TOP 10 CỔ PHIẾU TĂNG MẠNH
=========================

st.subheader("Top 10 cổ phiếu tăng mạnh")

top_stock_df = get_top_stock_for_bottom(
selected_confirm_date
).head(10)

if top_stock_df.empty:

st.info(
    "Không tìm thấy cổ phiếu thanh khoản cao phù hợp trong các ngành quanh đáy này."
)

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
Close
