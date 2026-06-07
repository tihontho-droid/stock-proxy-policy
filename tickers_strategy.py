import streamlit as st
import pandas as pd
import numpy as np
import requests
from streamlit_lightweight_charts import renderLightweightCharts
from itertools import combinations  
from functools import reduce
import operator


# =========================
# CẤU HÌNH TRANG
# =========================

st.set_page_config(
    page_title="Flow & SMDT Backtest",
    page_icon="📈",
    layout="wide"
)


st.title("📈 Flow & SMDT Strategy Backtest")


# =========================
# LOAD API
# =========================

@st.cache_data(ttl=3600)
def load_branch_path():

    url = "https://stocktraders.vn/service/data/getBranchPath"

    payload = {
        "BranchPathRequest": {
            "account": "uyen.png"
        }
    }

    r = requests.post(url, json=payload)
    data = r.json()

    stock_data = data["BranchPathReply"]["branchs"]

    return pd.DataFrame(stock_data)


@st.cache_data(ttl=3600)
def load_total_trade():

    url = "https://stocktraders.vn/service/data/getTotalTrade"

    payload = {
        "TotalTradeRequest": {
            "account": "uyen.png"
        }
    }

    r = requests.post(url, json=payload)
    data = r.json()

    stock_data = data["TotalTradeReply"]["stockTotals"]

    return pd.DataFrame(stock_data)


@st.cache_data(ttl=3600)
def load_cashflow_branch():

    url = "https://stocktraders.vn/service/data/getCashFlowBranch"

    payload = {
        "CashFlowBranchRequest": {
            "account": "uyen.png"
        }
    }

    r = requests.post(url, json=payload)
    data = r.json()

    stock_data = data["CashFlowBranchReply"]["cashFlowBranchs"]
    df = pd.DataFrame(stock_data)

    all_rows = []

    for _, row in df.iterrows():

        date = row["date"]
        branch_datas = row["cashFlowBranchDatas"]

        for item in branch_datas:

            new_row = item.copy()
            new_row["date"] = date
            all_rows.append(new_row)

    cashflow_branch_df = pd.DataFrame(all_rows)

    cashflow_branch_df["date"] = pd.to_datetime(
        cashflow_branch_df["date"]
    )

    return cashflow_branch_df


@st.cache_data(ttl=3600)
def load_smdt_branch():

    url = "https://stocktraders.vn/service/data/getSMDTBranch"

    payload = {
        "SMDTBranchRequest": {
            "account": "uyen.png"
        }
    }

    r = requests.post(url, json=payload)
    data = r.json()

    stock_data = data["SMDTBranchReply"]["SMDTDatas"]

    return pd.DataFrame(stock_data)

@st.cache_data(ttl=3600)
def load_cashflow_ticker():

    url = "https://stocktraders.vn/service/data/getCashFlowTicker"

    payload = {
        "CashFlowTickerRequest": {
            "account": "uyen.png"
        }
    }

    r = requests.post(url, json=payload)
    data = r.json()

    stock_data = data["CashFlowTickerRequest"]["cashFlowTickers"]

    all_rows = []

    for day_data in stock_data:

        date = day_data["date"]

        for item in day_data["cashTickerDatas"]:

            row = item.copy()
            row["date"] = date
            all_rows.append(row)

    df_cashflow_ticker = pd.DataFrame(all_rows)

    df_cashflow_ticker["date"] = pd.to_datetime(
        df_cashflow_ticker["date"]
    )

    return df_cashflow_ticker


@st.cache_data(ttl=3600)
def load_smdt_ticker():

    url = "https://stocktraders.vn/service/data/getSMDTTicker"

    payload = {
        "SMDTTickerRequest": {
            "account": "uyen.png"
        }
    }

    r = requests.post(url, json=payload)
    data = r.json()

    stock_data = data["SMDTTickerReply"]["SMDTDatas"]

    df_smdt_ticker = pd.DataFrame(stock_data)

    return df_smdt_ticker

# =========================
# HÀM PHỤ
# =========================

def find_branch_by_ticker(df_branch, ticker_input):

    ticker_input = ticker_input.upper().strip()

    for _, row in df_branch.iterrows():

        tickers = row["tickers"]

        if isinstance(tickers, list):

            ticker_list = [
                str(x).upper().strip()
                for x in tickers
            ]

        else:

            ticker_list = (
                str(tickers)
                .replace("[", "")
                .replace("]", "")
                .replace("'", "")
                .replace(",", " ")
                .split()
            )

            ticker_list = [
                x.upper().strip()
                for x in ticker_list
            ]

        if ticker_input in ticker_list:

            return {
                "branch_name": row["name"],
                "branch_path": row["path"],
                "branch_val": row["val"]
            }

    return {
        "branch_name": "Không tìm thấy ngành",
        "branch_path": "",
        "branch_val": ""
    }


def get_price_by_ticker(df_total, ticker_input):

    ticker_input = ticker_input.upper().strip()

    row = df_total[
        df_total["ticker"] == ticker_input
    ]

    if row.empty:
        return pd.DataFrame()

    price_data = row.iloc[0]["totalDatas"]

    price_df = pd.DataFrame(price_data)

    price_df["date"] = pd.to_datetime(price_df["date"])

    for col in ["open", "high", "low", "close"]:

        price_df[col] = pd.to_numeric(
            price_df[col],
            errors="coerce"
        )

    price_df = price_df.sort_values(
        "date"
    ).reset_index(drop=True)

    return price_df


def normalize_text(text):

    text = str(text).lower().strip()

    replacements = {
        "à": "a", "á": "a", "ạ": "a", "ả": "a", "ã": "a",
        "â": "a", "ầ": "a", "ấ": "a", "ậ": "a", "ẩ": "a", "ẫ": "a",
        "ă": "a", "ằ": "a", "ắ": "a", "ặ": "a", "ẳ": "a", "ẵ": "a",

        "è": "e", "é": "e", "ẹ": "e", "ẻ": "e", "ẽ": "e",
        "ê": "e", "ề": "e", "ế": "e", "ệ": "e", "ể": "e", "ễ": "e",

        "ì": "i", "í": "i", "ị": "i", "ỉ": "i", "ĩ": "i",

        "ò": "o", "ó": "o", "ọ": "o", "ỏ": "o", "õ": "o",
        "ô": "o", "ồ": "o", "ố": "o", "ộ": "o", "ổ": "o", "ỗ": "o",
        "ơ": "o", "ờ": "o", "ớ": "o", "ợ": "o", "ở": "o", "ỡ": "o",

        "ù": "u", "ú": "u", "ụ": "u", "ủ": "u", "ũ": "u",
        "ư": "u", "ừ": "u", "ứ": "u", "ự": "u", "ử": "u", "ữ": "u",

        "ỳ": "y", "ý": "y", "ỵ": "y", "ỷ": "y", "ỹ": "y",

        "đ": "d"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def get_branch_keywords(branch_name):

    branch_name_norm = normalize_text(branch_name)

    keyword_groups = {
        "ngan hang": ["ngan hang"],
        "bat dong san": ["bat dong san", "dan cu"],
        "chung khoan": ["chung khoan", "moi gioi chung khoan"],
        "thep": ["thep"],
        "phan mem": ["phan mem"],
        "xay dung": ["xay dung"],
        "cao su": ["cao su"],
        "phan bon": ["phan bon"],
        "nhua": ["nhua"],
        "dien": ["dien"],
        "dau khi": ["dau khi"],
        "xi mang": ["xi mang"],
        "duong": ["duong"],
        "thuy hai san": ["thuy hai san"],
        "van tai": ["van tai"],
        "bao hiem": ["bao hiem"],
        "vien thong": ["vien thong"],
        "hang khong": ["hang khong"],
        "may mac": ["may mac"],
        "thuc pham": ["thuc pham"],
        "sua": ["sua"]
    }

    for _, keywords in keyword_groups.items():

        for keyword in keywords:

            if keyword in branch_name_norm:
                return keywords

    words = [
        word
        for word in branch_name_norm.split()
        if len(word) >= 4
    ]

    return words[:3]


def match_branch_name(api_branch_name, ticker_branch):

    api_branch_name_norm = normalize_text(api_branch_name)
    ticker_branch_norm = normalize_text(ticker_branch)

    if ticker_branch_norm in api_branch_name_norm:
        return True

    if api_branch_name_norm in ticker_branch_norm:
        return True

    keywords = get_branch_keywords(ticker_branch)

    for keyword in keywords:

        if keyword in api_branch_name_norm:
            return True

    return False


# =========================
# BOX TÌM KIẾM MÃ CỔ PHIẾU
# =========================

ticker_input = st.text_input(
    "Nhập mã cổ phiếu",
    value="NVL",
    placeholder="Ví dụ: NVL, VIC, HPG, FPT..."
)

ticker_input = ticker_input.upper().strip()

run_button = st.button("Chạy phân tích")

if ticker_input == "":
    st.warning("Vui lòng nhập mã cổ phiếu")
    st.stop()

if not run_button:
    st.info("Nhập mã cổ phiếu rồi bấm Chạy phân tích để bắt đầu.")
    st.stop()


# =========================
# LẤY GIÁ THEO MÃ
# =========================

df_total = load_total_trade()

price_df = get_price_by_ticker(
    df_total=df_total,
    ticker_input=ticker_input
)


# =========================
# BIỂU ĐỒ GIÁ MÃ CỔ PHIẾU
# =========================

st.subheader(f"Biểu đồ giá {ticker_input}")

if price_df.empty:

    st.warning(f"Không tìm thấy dữ liệu giá cho mã {ticker_input}")

else:

    candle_data = []

    for _, row in price_df.iterrows():

        candle_data.append({
            "time": row["date"].strftime("%Y-%m-%d"),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"])
        })

    price_series = [
        {
            "type": "Candlestick",
            "data": candle_data,
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

    price_options = {
        "height": 350,
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
            "barSpacing": 3,
            "rightOffset": 2,
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
                "chart": price_options,
                "series": price_series
            }
        ],
        key=f"price_chart_{ticker_input}"
    )

# =========================
# DÒNG TIỀN + SMDT CỦA MÃ CỔ PHIẾU
# =========================

df_cashflow_ticker = load_cashflow_ticker()

cashflow_ticker_selected = df_cashflow_ticker[
    df_cashflow_ticker["ticker"] == ticker_input
].copy()

if cashflow_ticker_selected.empty:

    cashflow_ticker_show = pd.DataFrame()

else:

    cashflow_ticker_show = cashflow_ticker_selected[
        [
            "date",
            "content"
        ]
    ].copy()

    cashflow_ticker_show = cashflow_ticker_show.rename(columns={
        "date": "Ngày",
        "content": "Trạng thái"
    })

    cashflow_ticker_show["Ngày"] = (
        pd.to_datetime(cashflow_ticker_show["Ngày"])
        .dt.strftime("%Y-%m-%d")
    )

    cashflow_ticker_show = cashflow_ticker_show.sort_values(
        "Ngày",
        ascending=False
    )


df_smdt_ticker = load_smdt_ticker()

smdt_ticker_row = df_smdt_ticker[
    df_smdt_ticker["keyValue"] == ticker_input
]

if smdt_ticker_row.empty:

    df_smdt_ticker_selected = pd.DataFrame()

else:

    smdt_ticker_data = smdt_ticker_row.iloc[0]["smdts"]

    df_smdt_ticker_selected = pd.DataFrame(smdt_ticker_data)

    df_smdt_ticker_selected["date"] = pd.to_datetime(
        df_smdt_ticker_selected["date"]
    )

    df_smdt_ticker_selected["smdt"] = pd.to_numeric(
        df_smdt_ticker_selected["smdt"],
        errors="coerce"
    )

    df_smdt_ticker_selected = df_smdt_ticker_selected.sort_values(
        "date"
    ).reset_index(drop=True)


left_col, right_col = st.columns([1, 1])

with left_col:

    st.write(f"Tín hiệu dòng tiền {ticker_input}")

    if cashflow_ticker_show.empty:

        st.warning(f"Không có dữ liệu dòng tiền mã {ticker_input}")

    else:

        st.dataframe(
            cashflow_ticker_show,
            hide_index=True,
            use_container_width=True,
            height=250
        )


with right_col:

    st.write(f"Sức mạnh dòng tiền SMDT {ticker_input}")

    if df_smdt_ticker_selected.empty:

        st.warning(f"Không có dữ liệu SMDT mã {ticker_input}")

    else:

        chart_data = []
        threshold_data = []

        for _, row in df_smdt_ticker_selected.iterrows():

            time_value = row["date"].strftime("%Y-%m-%d")

            chart_data.append({
                "time": time_value,
                "value": round(row["smdt"], 2)
            })

            threshold_data.append({
                "time": time_value,
                "value": 70
            })

        smdt_ticker_series = [
            {
                "type": "Line",
                "data": chart_data,
                "options": {
                    "color": "#F2C94C",
                    "lineWidth": 3,
                    "priceLineVisible": False,
                    "lastValueVisible": False
                }
            },
            {
                "type": "Line",
                "data": threshold_data,
                "options": {
                    "color": "#F2994A",
                    "lineWidth": 2,
                    "lineStyle": 2,
                    "priceLineVisible": False,
                    "lastValueVisible": False
                }
            }
        ]

        smdt_ticker_options = {
            "height": 250,
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
                "barSpacing": 80,
                "fixLeftEdge": False,
                "fixRightEdge": False,
                "rightOffset": 1
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
                    "chart": smdt_ticker_options,
                    "series": smdt_ticker_series
                }
            ],
            key=f"smdt_ticker_chart_{ticker_input}"
        )

# =========================
# TÌM NGÀNH CỦA MÃ
# =========================

df_branch = load_branch_path()

branch_info = find_branch_by_ticker(
    df_branch=df_branch,
    ticker_input=ticker_input
)

ticker_branch = branch_info["branch_name"]
ticker_branch_path = branch_info["branch_path"]
ticker_branch_val = branch_info["branch_val"]


# =========================
# HIỂN THỊ NGÀNH
# =========================

st.write(f"Ngành của {ticker_input}")
st.markdown(
    f"""
    <div style="
        background-color:#262730;
        padding:12px 16px;
        border-radius:8px;
        color:white;
        font-size:16px;
        font-weight:600;
        margin-bottom:20px;
    ">
        {ticker_branch}
    </div>
    """,
    unsafe_allow_html=True
)


# =========================
# LỌC DÒNG TIỀN THEO NGÀNH CỦA MÃ
# =========================

cashflow_branch_df = load_cashflow_branch()

cashflow_selected_raw = cashflow_branch_df[
    cashflow_branch_df["name"] == ticker_branch
].copy()

if cashflow_selected_raw.empty:

    cashflow_selected_raw = cashflow_branch_df[
        cashflow_branch_df["name"].apply(
            lambda x: match_branch_name(x, ticker_branch)
        )
    ].copy()

# chỉ giữ đúng 1 dòng / 1 ngày
cashflow_selected_raw = (
    cashflow_selected_raw
    .sort_values("date")
    .drop_duplicates(subset=["date"], keep="last")
    .reset_index(drop=True)
)

if cashflow_selected_raw.empty:

    st.warning(f"Không tìm thấy dòng tiền ngành cho: {ticker_branch}")
    cashflow_selected = pd.DataFrame()

else:

    cashflow_selected = cashflow_selected_raw[
        [
            "date",
            "content"
        ]
    ].copy()

    cashflow_selected = cashflow_selected.rename(columns={
        "date": "Ngày",
        "content": "Trạng thái"
    })

    cashflow_selected["Ngày"] = (
        pd.to_datetime(cashflow_selected["Ngày"])
        .dt.strftime("%Y-%m-%d")
    )

    cashflow_selected = cashflow_selected.sort_values(
        "Ngày",
        ascending=False
    )


# =========================
# LỌC SMDT THEO NGÀNH CỦA MÃ
# =========================

df_smdt_all = load_smdt_branch()

smdt_row = df_smdt_all[
    df_smdt_all["keyName"].apply(
        lambda x: match_branch_name(x, ticker_branch)
    )
]

if smdt_row.empty:

    df_smdt_selected = pd.DataFrame()

else:

    smdt_data = smdt_row.iloc[0]["smdts"]

    df_smdt_selected = pd.DataFrame(smdt_data)

    df_smdt_selected["date"] = pd.to_datetime(
        df_smdt_selected["date"]
    )

    df_smdt_selected["smdt"] = pd.to_numeric(
        df_smdt_selected["smdt"],
        errors="coerce"
    )

    df_smdt_selected = df_smdt_selected.sort_values(
        "date"
    ).reset_index(drop=True)


# =========================
# HIỂN THỊ BẢNG + BIỂU ĐỒ
# =========================

left_col, right_col = st.columns([1, 1])

with left_col:

    st.write("Tín hiệu dòng tiền")

    if cashflow_selected.empty:

        st.warning("Không có dữ liệu dòng tiền ngành")

    else:

        st.dataframe(
            cashflow_selected,
            hide_index=True,
            use_container_width=True,
            height=250
        )


with right_col:

    st.write("Sức mạnh dòng tiền SMDT")

    if df_smdt_selected.empty:

        st.warning("Không có dữ liệu SMDT ngành")

    else:

        chart_data = []
        threshold_data = []

        for _, row in df_smdt_selected.iterrows():

            time_value = row["date"].strftime("%Y-%m-%d")

            chart_data.append({
                "time": time_value,
                "value": round(row["smdt"], 2)
            })

            threshold_data.append({
                "time": time_value,
                "value": 70
            })

        series = [
            {
                "type": "Line",
                "data": chart_data,
                "options": {
                    "color": "#F2C94C",
                    "lineWidth": 3,
                    "priceLineVisible": False,
                    "lastValueVisible": False
                }
            },
            {
                "type": "Line",
                "data": threshold_data,
                "options": {
                    "color": "#F2994A",
                    "lineWidth": 2,
                    "lineStyle": 2,
                    "priceLineVisible": False,
                    "lastValueVisible": False
                }
            }
        ]

        chart_options = {
            "height": 250,
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
                "barSpacing": 80,
                "fixLeftEdge": False,
                "fixRightEdge": False,
                "rightOffset": 1
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
                    "chart": chart_options,
                    "series": series
                }
            ],
            key=f"smdt_branch_chart_{ticker_input}"
        )

# =========================
# GIẢI THÍCH HƯỚNG ĐI CHIẾN LƯỢC
# =========================

st.subheader("Giải thích hướng đi khi xây dựng chiến lược")

st.write(f"""
Mục tiêu là xây dựng các chiến lược Buy/Sell cho mã {ticker_input}
dựa trên 4 nhóm tín hiệu:
""")

st.write("- Dòng tiền ngành")
st.write("- SMDT ngành")
st.write(f"- Dòng tiền mã {ticker_input}")
st.write(f"- SMDT mã {ticker_input}")

st.write("Buy khi xuất hiện các điều kiện sau:")

st.write("- Dòng tiền ngành chuyển từ trạng thái thoát ra sang đổ vào 2 phiên liên tiếp.")
st.write(f"- Dòng tiền mã {ticker_input} chuyển từ trạng thái thoát ra sang đổ vào 2 phiên liên tiếp.")
st.write("- SMDT ngành vừa vượt ngưỡng 70 trong 2 phiên liên tiếp.")
st.write(f"- SMDT mã {ticker_input} vừa vượt ngưỡng 70 trong 2 phiên liên tiếp.")

st.write("Sell khi xuất hiện các điều kiện sau:")

st.write("- Dòng tiền ngành chuyển từ trạng thái đổ vào sang thoát ra 2 phiên liên tiếp.")
st.write(f"- Dòng tiền mã {ticker_input} chuyển từ trạng thái đổ vào sang thoát ra 2 phiên liên tiếp.")
st.write("- SMDT ngành vừa giảm dưới ngưỡng 70 trong 2 phiên liên tiếp.")
st.write(f"- SMDT mã {ticker_input} vừa giảm dưới ngưỡng 70 trong 2 phiên liên tiếp.")

# =========================
# BUILD DF_SIGNAL
# =========================

def build_signal(
    price_df,
    cashflow_nganh_df,
    smdt_nganh_df,
    cashflow_ticker_df,
    smdt_ticker_df
):

    cashflow_nganh_df = cashflow_nganh_df.copy()
    smdt_nganh_df = smdt_nganh_df.copy()
    cashflow_ticker_df = cashflow_ticker_df.copy()
    smdt_ticker_df = smdt_ticker_df.copy()

    cashflow_nganh_df = cashflow_nganh_df.rename(columns={
        "Ngày": "date",
        "Trạng thái": "cashflow_nganh",
        "content": "cashflow_nganh"
    })

    smdt_nganh_df = smdt_nganh_df.rename(columns={
        "Ngày": "date",
        "smdt": "smdt_nganh"
    })

    cashflow_ticker_df = cashflow_ticker_df.rename(columns={
        "Ngày": "date",
        "Trạng thái": "cashflow_ma",
        "Tín hiệu dòng tiền": "cashflow_ma",
        "content": "cashflow_ma"
    })

    smdt_ticker_df = smdt_ticker_df.rename(columns={
        "Ngày": "date",
        "smdt": "smdt_ma"
    })

    price_df["date"] = pd.to_datetime(price_df["date"])
    cashflow_nganh_df["date"] = pd.to_datetime(cashflow_nganh_df["date"])
    smdt_nganh_df["date"] = pd.to_datetime(smdt_nganh_df["date"])
    cashflow_ticker_df["date"] = pd.to_datetime(cashflow_ticker_df["date"])
    smdt_ticker_df["date"] = pd.to_datetime(smdt_ticker_df["date"])

    df_signal = price_df[
        [
            "date",
            "close"
        ]
    ].copy()

    df_signal = df_signal.merge(
        cashflow_nganh_df[
            [
                "date",
                "cashflow_nganh"
            ]
        ],
        on="date",
        how="left"
    )

    df_signal = df_signal.merge(
        smdt_nganh_df[
            [
                "date",
                "smdt_nganh"
            ]
        ],
        on="date",
        how="left"
    )

    df_signal = df_signal.merge(
        cashflow_ticker_df[
            [
                "date",
                "cashflow_ma"
            ]
        ],
        on="date",
        how="left"
    )

    df_signal = df_signal.merge(
        smdt_ticker_df[
            [
                "date",
                "smdt_ma"
            ]
        ],
        on="date",
        how="left"
    )

    df_signal = df_signal.sort_values("date").reset_index(drop=True)

    return df_signal


df_signal = build_signal(
    price_df=price_df,
    cashflow_nganh_df=cashflow_selected,
    smdt_nganh_df=df_smdt_selected,
    cashflow_ticker_df=cashflow_ticker_selected,
    smdt_ticker_df=df_smdt_ticker_selected
)


# =========================
# CHẠY BACKTEST 676 CHIẾN LƯỢC
# =========================

from itertools import combinations
from functools import reduce
import operator


# =========================
# 1. HÀM BACKTEST
# =========================

def backtest_strategy(df_signal, strategy, initial_cash=1_000_000):

    data = df_signal.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values("date").reset_index(drop=True)

    data["buy_signal"] = strategy["buy"](data).fillna(False)
    data["sell_signal"] = strategy["sell"](data).fillna(False)

    cash = initial_cash
    shares = 0
    position = 0

    trades = []
    nav_list = []

    price_col = f"price_{ticker_input}"

    for i, row in data.iterrows():

        date = row["date"]
        price = row["close"]

        if pd.isna(price):
            continue

        if position == 0 and row["buy_signal"] == True:

            shares = cash // price
            buy_value = shares * price
            cash = cash - buy_value

            buy_price = price
            buy_date = date
            position = 1

            trades.append({
                "date": date,
                "action": "BUY",
                price_col: price,
                "shares": shares,
                "value": buy_value,
                "cash_after": cash,
                "profit_pct": 0,
                "profit_value": 0
            })

        elif position == 1 and row["sell_signal"] == True:

            sell_value = shares * price
            cash = cash + sell_value

            profit_pct = ((price - buy_price) / buy_price) * 100
            profit_value = sell_value - shares * buy_price

            trades.append({
                "date": date,
                "action": "SELL",
                "buy_date": buy_date,
                "buy_price": buy_price,
                price_col: price,
                "shares": shares,
                "value": sell_value,
                "cash_after": cash,
                "profit_pct": profit_pct,
                "profit_value": profit_value
            })

            shares = 0
            position = 0

        nav = cash + shares * price

        nav_list.append({
            "date": date,
            price_col: price,
            "cash": cash,
            "shares": shares,
            "NAV": nav
        })

    nav_df = pd.DataFrame(nav_list)
    trades_df = pd.DataFrame(trades)

    final_nav = nav_df["NAV"].iloc[-1] if not nav_df.empty else initial_cash

    total_return_pct = ((final_nav - initial_cash) / initial_cash) * 100

    sell_trades = (
        trades_df[trades_df["action"] == "SELL"].copy()
        if not trades_df.empty
        else pd.DataFrame()
    )

    if sell_trades.empty:

        num_trades = 0
        num_win = 0
        num_loss = 0
        win_rate_pct = 0
        avg_win_pct = 0
        avg_loss_pct = 0
        payoff = 0
        expectancy = 0
        max_profit_pct = 0
        max_loss_pct = 0

    else:

        num_trades = len(sell_trades)

        win_trades = sell_trades[sell_trades["profit_pct"] > 0]
        loss_trades = sell_trades[sell_trades["profit_pct"] <= 0]

        num_win = len(win_trades)
        num_loss = len(loss_trades)

        win_rate_pct = (num_win / num_trades) * 100

        avg_win_pct = win_trades["profit_pct"].mean() if num_win > 0 else 0
        avg_loss_pct = loss_trades["profit_pct"].mean() if num_loss > 0 else 0

        payoff = abs(avg_win_pct / avg_loss_pct) if avg_loss_pct != 0 else 0

        expectancy = (
            (win_rate_pct / 100) * avg_win_pct
            + (1 - win_rate_pct / 100) * avg_loss_pct
        )

        max_profit_pct = sell_trades["profit_pct"].max()
        max_loss_pct = sell_trades["profit_pct"].min()

    summary = {
        "final_nav": final_nav,
        "final_cash": cash,
        "final_shares": shares,
        "final_position": position,
        "total_return_pct": total_return_pct,
        "num_trades": num_trades,
        "num_win": num_win,
        "num_loss": num_loss,
        "win_rate_pct": win_rate_pct,
        "avg_win_pct": avg_win_pct,
        "avg_loss_pct": avg_loss_pct,
        "payoff": payoff,
        "expectancy": expectancy,
        "max_profit_pct": max_profit_pct,
        "max_loss_pct": max_loss_pct
    }

    return summary, trades_df, nav_df


# =========================
# 2. CHUẨN HÓA DỮ LIỆU
# =========================

df_signal = df_signal.copy()

df_signal["date"] = pd.to_datetime(df_signal["date"])
df_signal = df_signal.sort_values("date").reset_index(drop=True)

mapping = {
    "Nhen nhóm đổ vào": 1,
    "Tiếp tục đổ vào": 1,
    "Đang thoát ra": -1,
    "Tiếp tục thoát ra": -1
}

for col in ["cashflow_nganh", "cashflow_ma"]:

    df_signal[col] = (
        df_signal[col]
        .map(mapping)
        .fillna(df_signal[col])
    )

    df_signal[col] = pd.to_numeric(
        df_signal[col],
        errors="coerce"
    ).ffill()

for col in ["smdt_nganh", "smdt_ma", "close"]:

    df_signal[col] = pd.to_numeric(
        df_signal[col],
        errors="coerce"
    )


# =========================
# 3. TẠO 8 TÍN HIỆU GIỐNG NOTEBOOK
# =========================

start_date = pd.to_datetime("2023-06-06")

df_signal = df_signal.copy()

df_signal["date"] = pd.to_datetime(df_signal["date"])

df_signal = df_signal[
    df_signal["date"] >= start_date
].copy()

df_signal = df_signal.sort_values("date").reset_index(drop=True)

st.write("Ngày bắt đầu dữ liệu:", df_signal["date"].min())
st.write("Số dòng dữ liệu sau khi lọc:", len(df_signal))


df_signal["flow_nganh_good"] = (
    (df_signal["cashflow_nganh"].shift(2) == -1) &
    (df_signal["cashflow_nganh"].shift(1) == 1) &
    (df_signal["cashflow_nganh"] == 1)
)

df_signal["flow_nganh_bad"] = (
    (df_signal["cashflow_nganh"].shift(2) == 1) &
    (df_signal["cashflow_nganh"].shift(1) == -1) &
    (df_signal["cashflow_nganh"] == -1)
)

df_signal["flow_ma_good"] = (
    (df_signal["cashflow_ma"].shift(2) == -1) &
    (df_signal["cashflow_ma"].shift(1) == 1) &
    (df_signal["cashflow_ma"] == 1)
)

df_signal["flow_ma_bad"] = (
    (df_signal["cashflow_ma"].shift(2) == 1) &
    (df_signal["cashflow_ma"].shift(1) == -1) &
    (df_signal["cashflow_ma"] == -1)
)

df_signal["smdt_nganh_good"] = (
    (df_signal["smdt_nganh"].shift(2) < 70) &
    (df_signal["smdt_nganh"].shift(1) >= 70) &
    (df_signal["smdt_nganh"] >= 70)
)

df_signal["smdt_nganh_bad"] = (
    (df_signal["smdt_nganh"].shift(2) >= 70) &
    (df_signal["smdt_nganh"].shift(1) < 70) &
    (df_signal["smdt_nganh"] < 70)
)

df_signal["smdt_ma_good"] = (
    (df_signal["smdt_ma"].shift(2) < 70) &
    (df_signal["smdt_ma"].shift(1) >= 70) &
    (df_signal["smdt_ma"] >= 70)
)

df_signal["smdt_ma_bad"] = (
    (df_signal["smdt_ma"].shift(2) >= 70) &
    (df_signal["smdt_ma"].shift(1) < 70) &
    (df_signal["smdt_ma"] < 70)
)


# =========================
# 4. TẠO BUY RULES / SELL RULES
# =========================

buy_signals = [
    "flow_nganh_good",
    "smdt_nganh_good",
    "flow_ma_good",
    "smdt_ma_good"
]

sell_signals = [
    "flow_nganh_bad",
    "smdt_nganh_bad",
    "flow_ma_bad",
    "smdt_ma_bad"
]


def make_rule(cols, mode):

    if mode == "AND":

        return lambda df, cols=cols: reduce(
            operator.and_,
            [df[c] for c in cols]
        )

    else:

        return lambda df, cols=cols: reduce(
            operator.or_,
            [df[c] for c in cols]
        )


buy_rules = {}

for r in range(1, len(buy_signals) + 1):

    for cols in combinations(buy_signals, r):

        name = "__".join(cols)

        buy_rules["buy_AND__" + name] = make_rule(
            cols,
            "AND"
        )

        if r >= 2:

            buy_rules["buy_OR__" + name] = make_rule(
                cols,
                "OR"
            )


sell_rules = {}

for r in range(1, len(sell_signals) + 1):

    for cols in combinations(sell_signals, r):

        name = "__".join(cols)

        sell_rules["sell_AND__" + name] = make_rule(
            cols,
            "AND"
        )

        if r >= 2:

            sell_rules["sell_OR__" + name] = make_rule(
                cols,
                "OR"
            )


# =========================
# 5. TẠO 676 CHIẾN LƯỢC
# =========================

strategies = {}

for buy_name, buy_func in buy_rules.items():

    for sell_name, sell_func in sell_rules.items():

        strategy_name = buy_name + "__" + sell_name

        strategies[strategy_name] = {
            "buy": buy_func,
            "sell": sell_func
        }


# =========================
# 6. CHẠY BACKTEST
# =========================

results = {}
summary_list = []

for strategy_name, strategy in strategies.items():

    summary, trades, nav = backtest_strategy(
        df_signal=df_signal,
        strategy=strategy,
        initial_cash=1_000_000
    )

    summary["strategy"] = strategy_name
    summary_list.append(summary)

    results[strategy_name] = {
        "summary": summary,
        "trades": trades,
        "nav": nav
    }


# =========================
# 7. TẠO BẢNG SUMMARY
# =========================

summary_df = pd.DataFrame(summary_list)

summary_df = summary_df[
    [
        "strategy",
        "final_nav",
        "total_return_pct",
        "num_trades",
        "num_win",
        "num_loss",
        "win_rate_pct",
        "avg_win_pct",
        "avg_loss_pct",
        "payoff",
        "max_profit_pct",
        "max_loss_pct"
    ]
]

summary_df = summary_df.sort_values(
    "total_return_pct",
    ascending=False
).reset_index(drop=True)

summary_raw = summary_df.copy()
summary_format = summary_df.copy()


# =========================
# 8. FORMAT BẢNG
# =========================

pct_cols = [
    "total_return_pct",
    "win_rate_pct",
    "avg_win_pct",
    "avg_loss_pct",
    "max_profit_pct",
    "max_loss_pct"
]

for col in pct_cols:

    summary_format[col] = (
        summary_format[col]
        .round(2)
        .astype(str)
        + "%"
    )

summary_format["final_nav"] = (
    summary_format["final_nav"]
    .round(0)
    .astype(int)
    .map("{:,}".format)
)

summary_format["payoff"] = summary_format["payoff"].round(2)

summary_format = summary_format.rename(columns={
    "strategy": "Strategy",
    "final_nav": "Final NAV",
    "total_return_pct": "Total Return",
    "num_trades": "Trades",
    "num_win": "Wins",
    "num_loss": "Losses",
    "win_rate_pct": "Win Rate",
    "avg_win_pct": "Avg Win",
    "avg_loss_pct": "Avg Loss",
    "payoff": "Payoff",
    "max_profit_pct": "Max Profit",
    "max_loss_pct": "Max Loss"
})


# =========================
# 9. HIỂN THỊ STREAMLIT
# =========================

st.write("Số điều kiện BUY:", len(buy_rules))
st.write("Số điều kiện SELL:", len(sell_rules))
st.write("Số chiến lược:", len(strategies))

st.success(f"Đã chạy backtest xong 676 chiến lược cho mã {ticker_input}")

st.subheader("Bảng xếp hạng 676 chiến lược")

st.dataframe(
    summary_format,
    hide_index=True,
    use_container_width=True,
    height=250
)


# =========================
# CHIẾN LƯỢC TOP 1
# =========================
def explain_strategy(strategy_name):

    text = strategy_name

    text = text.replace(
        "buy_AND__",
        "MUA khi đồng thời: "
    )

    text = text.replace(
        "buy_OR__",
        "MUA khi có ít nhất 1 trong các điều kiện: "
    )

    text = text.replace(
        "__sell_AND__",
        "\n\nBÁN khi đồng thời: "
    )

    text = text.replace(
        "__sell_OR__",
        "\n\nBÁN khi có ít nhất 1 trong các điều kiện: "
    )

    mapping = {
        "flow_nganh_good": "Dòng tiền ngành tích cực",
        "flow_nganh_bad": "Dòng tiền ngành tiêu cực",

        "flow_ma_good": "Dòng tiền mã tích cực",
        "flow_ma_bad": "Dòng tiền mã tiêu cực",

        "smdt_nganh_good": "SMDT ngành vượt 70",
        "smdt_nganh_bad": "SMDT ngành dưới 70",

        "smdt_ma_good": "SMDT mã vượt 70",
        "smdt_ma_bad": "SMDT mã dưới 70"
    }

    for k, v in mapping.items():
        text = text.replace(k, v)

    text = text.replace("__", " + ")

    return text

top_strategy = summary_raw.iloc[0]["strategy"]

st.subheader("Chiến lược tốt nhất")

st.info(
    explain_strategy(top_strategy)
)

top_summary = results[top_strategy]["summary"]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Return",
        f"{top_summary['total_return_pct']:.2f}%"
    )

with col2:
    st.metric(
        "Win Rate",
        f"{top_summary['win_rate_pct']:.2f}%"
    )

with col3:
    st.metric(
        "Payoff",
        f"{top_summary['payoff']:.2f}"
    )


# =========================
# BẢNG GIAO DỊCH TOP 1
# =========================

trades_top = results[top_strategy]["trades"].copy()
price_col = f"price_{ticker_input}"

if not trades_top.empty:

    trade_view = trades_top.copy()

    trade_view["date"] = pd.to_datetime(trade_view["date"])

    signal_cols = [
        "date",
        "flow_nganh_good",
        "flow_nganh_bad",
        "flow_ma_good",
        "flow_ma_bad",
        "smdt_nganh_good",
        "smdt_nganh_bad",
        "smdt_ma_good",
        "smdt_ma_bad"
    ]

    signal_at_trade = df_signal[signal_cols].copy()
    signal_at_trade["date"] = pd.to_datetime(signal_at_trade["date"])

    trade_view = trade_view.merge(
        signal_at_trade,
        on="date",
        how="left"
    )

    trade_view["PnL"] = trade_view["profit_pct"]

    trade_view = trade_view[
        [
            "date",
            "flow_nganh_good",
            "flow_nganh_bad",
            "flow_ma_good",
            "flow_ma_bad",
            "smdt_ma_good",
            "smdt_ma_bad",
            "smdt_nganh_good",
            "smdt_nganh_bad",
            "action",
            price_col,
            "PnL",
            "cash_after"
        ]
    ]

    trade_view["date"] = trade_view["date"].dt.strftime("%Y-%m-%d")

    trade_view[price_col] = trade_view[price_col].round(2)

    trade_view["PnL"] = (
        trade_view["PnL"]
        .round(2)
        .astype(str)
        + "%"
    )

    trade_view["cash_after"] = (
        trade_view["cash_after"]
        .round(0)
        .astype(int)
        .map("{:,}".format)
    )

    trade_view = trade_view.rename(columns={
        "date": "Date",
        "flow_nganh_good": "Flow ngành Good",
        "flow_nganh_bad": "Flow ngành Bad",
        "flow_ma_good": "Flow mã Good",
        "flow_ma_bad": "Flow mã Bad",
        "smdt_ma_good": "SMDT mã Good",
        "smdt_ma_bad": "SMDT mã Bad",
        "smdt_nganh_good": "SMDT ngành Good",
        "smdt_nganh_bad": "SMDT ngành Bad",
        "action": "Action",
        price_col: "Price",
        "cash_after": "Cash after"
    })

    st.subheader("Lịch sử giao dịch TOP 1")

    st.write("Chú thích: Good là điều kiện thỏa Buy - Bad là điều kiện thỏa Sell")

    st.dataframe(
        trade_view,
        hide_index=True,
        use_container_width=True,
        height=500
    )

else:

    st.warning("Chiến lược này không phát sinh giao dịch")


# =========================
# TRA CỨU NGÀY
# =========================

st.subheader(f"Tra cứu tín hiệu {ticker_input} theo ngày")

st.write("Kiểm tra những ngày có tín hiệu BUY/SELL có khớp với điều kiện đặt ra không?")

selected_date = st.date_input(
    "Chọn ngày cần tra cứu",
    value=df_signal["date"].max().date(),
    min_value=df_signal["date"].min().date(),
    max_value=df_signal["date"].max().date()
)

result = df_signal[
    df_signal["date"].dt.date == selected_date
]

if result.empty:

    st.warning("Không có dữ liệu ngày này")

else:

    result_show = result.rename(columns={
        "date": "Ngày",
        "close": f"Giá {ticker_input}",
        "cashflow_nganh": "Dòng tiền ngành",
        "smdt_nganh": "SMDT ngành",
        "cashflow_ma": "Dòng tiền mã",
        "smdt_ma": "SMDT mã"
    })

    st.dataframe(
        result_show,
        hide_index=True,
        use_container_width=True
    )

st.write("Chú thích:")
st.write("1 là tín hiệu dòng tiền nhen nhóm/tiếp tục đổ vào.")
st.write("-1 là tín hiệu dòng tiền đang/tiếp tục thoát ra.")
st.write("Lưu ý: phải đạt điều kiện 2 phiên liên tiếp thì mới ghi nhận Buy/Sell.")

# =========================
# CHIẾN LƯỢC: MUA GỐC, SAU 10 PHIÊN NẾU GIÁ <= MA10 THÌ CẮT
# CHỈ TÍNH HIỆU SUẤT TRÊN LỆNH ĐÃ SELL HOÀN CHỈNH
# =========================

def calc_closed_summary_ma10(trades_df, initial_cash=1_000_000):

    if trades_df.empty:
        sell_trades = pd.DataFrame()
    else:
        sell_trades = trades_df[
            trades_df["action"].isin(["SELL", "SELL_CUT_MA10"])
        ].copy()

    if sell_trades.empty:

        return {
            "final_nav": initial_cash,
            "total_return_pct": 0,
            "num_trades": 0,
            "num_win": 0,
            "num_loss": 0,
            "win_rate_pct": 0,
            "avg_win_pct": 0,
            "avg_loss_pct": 0,
            "payoff": 0,
            "expectancy": 0,
            "max_profit_pct": 0,
            "max_loss_pct": 0
        }

    closed_final_nav = initial_cash + sell_trades["profit_value"].sum()
    total_return_pct = ((closed_final_nav - initial_cash) / initial_cash) * 100

    num_trades = len(sell_trades)

    win_trades = sell_trades[sell_trades["profit_pct"] > 0]
    loss_trades = sell_trades[sell_trades["profit_pct"] <= 0]

    num_win = len(win_trades)
    num_loss = len(loss_trades)

    win_rate_pct = (num_win / num_trades) * 100

    avg_win_pct = win_trades["profit_pct"].mean() if num_win > 0 else 0
    avg_loss_pct = loss_trades["profit_pct"].mean() if num_loss > 0 else 0

    payoff = abs(avg_win_pct / avg_loss_pct) if avg_loss_pct != 0 else 0

    expectancy = (
        (win_rate_pct / 100) * avg_win_pct
        + (1 - win_rate_pct / 100) * avg_loss_pct
    )

    return {
        "final_nav": closed_final_nav,
        "total_return_pct": total_return_pct,
        "num_trades": num_trades,
        "num_win": num_win,
        "num_loss": num_loss,
        "win_rate_pct": win_rate_pct,
        "avg_win_pct": avg_win_pct,
        "avg_loss_pct": avg_loss_pct,
        "payoff": payoff,
        "expectancy": expectancy,
        "max_profit_pct": sell_trades["profit_pct"].max(),
        "max_loss_pct": sell_trades["profit_pct"].min()
    }


def backtest_strategy_cut_ma10_after_10day(df_signal, strategy, initial_cash=1_000_000):

    data = df_signal.copy()
    data["date"] = pd.to_datetime(data["date"])
    data = data.sort_values("date").reset_index(drop=True)

    data["MA10"] = data["close"].rolling(10).mean()

    data["buy_signal"] = strategy["buy"](data).fillna(False)
    data["sell_signal"] = strategy["sell"](data).fillna(False)

    cash = initial_cash
    shares = 0
    position = 0

    buy_price = 0
    buy_date = None
    buy_index = None

    trades = []
    nav_list = []

    price_col = f"price_{ticker_input}"

    for i, row in data.iterrows():

        date = row["date"]
        price = row["close"]
        ma10 = row["MA10"]

        if pd.isna(price):
            continue

        # BUY như chiến lược gốc
        if position == 0 and row["buy_signal"] == True:

            shares = cash // price
            buy_value = shares * price
            cash = cash - buy_value

            buy_price = price
            buy_date = date
            buy_index = i
            position = 1

            trades.append({
                "date": date,
                "action": "BUY",
                price_col: price,
                "MA10": ma10,
                "shares": shares,
                "value": buy_value,
                "cash_after": cash,
                "profit_pct": 0,
                "profit_value": 0
            })

        elif position == 1:

            days_after_buy = i - buy_index

            cut_ma10 = (
                days_after_buy >= 10
                and pd.notna(ma10)
                and price <= ma10
            )

            normal_sell = row["sell_signal"] == True

            if cut_ma10 or normal_sell:

                sell_value = shares * price
                cash = cash + sell_value

                profit_pct = ((price - buy_price) / buy_price) * 100
                profit_value = sell_value - shares * buy_price

                action_name = "SELL_CUT_MA10" if cut_ma10 else "SELL"

                trades.append({
                    "date": date,
                    "action": action_name,
                    "buy_date": buy_date,
                    "buy_price": buy_price,
                    price_col: price,
                    "MA10": ma10,
                    "shares": shares,
                    "value": sell_value,
                    "cash_after": cash,
                    "profit_pct": profit_pct,
                    "profit_value": profit_value
                })

                shares = 0
                position = 0
                buy_price = 0
                buy_date = None
                buy_index = None

        nav = cash + shares * price

        nav_list.append({
            "date": date,
            price_col: price,
            "MA10": ma10,
            "cash": cash,
            "shares": shares,
            "NAV": nav
        })

    nav_df = pd.DataFrame(nav_list)
    trades_df = pd.DataFrame(trades)

    summary = calc_closed_summary_ma10(
        trades_df=trades_df,
        initial_cash=initial_cash
    )

    return summary, trades_df, nav_df


# =========================
# CHẠY SO SÁNH GỐC VS CẮT MA10
# =========================

base_strategy = strategies[top_strategy]

summary_cut_ma10, trades_cut_ma10, nav_cut_ma10 = backtest_strategy_cut_ma10_after_10day(
    df_signal=df_signal,
    strategy=base_strategy,
    initial_cash=1_000_000
)

summary_base_closed = calc_closed_summary_ma10(
    trades_df=results[top_strategy]["trades"],
    initial_cash=1_000_000
)

compare_ma10 = pd.DataFrame([
    {
        "Phiên bản": "Gốc - chỉ tính lệnh đã SELL",
        **summary_base_closed
    },
    {
        "Phiên bản": "Sau 10 phiên, cắt nếu giá <= MA10",
        **summary_cut_ma10
    }
])

compare_ma10 = compare_ma10[[
    "Phiên bản",
    "final_nav",
    "total_return_pct",
    "num_trades",
    "num_win",
    "num_loss",
    "win_rate_pct",
    "avg_win_pct",
    "avg_loss_pct",
    "payoff",
    "max_profit_pct",
    "max_loss_pct"
]]

compare_ma10_show = compare_ma10.copy()

for col in [
    "total_return_pct",
    "win_rate_pct",
    "avg_win_pct",
    "avg_loss_pct",
    "max_profit_pct",
    "max_loss_pct"
]:

    compare_ma10_show[col] = (
        compare_ma10_show[col]
        .round(2)
        .astype(str)
        + "%"
    )

compare_ma10_show["final_nav"] = (
    compare_ma10_show["final_nav"]
    .round(0)
    .astype(int)
    .map("{:,}".format)
)

compare_ma10_show["payoff"] = (
    compare_ma10_show["payoff"]
    .round(2)
)

compare_ma10_show = compare_ma10_show.rename(columns={
    "final_nav": "Final NAV",
    "total_return_pct": "Total Return",
    "num_trades": "Trades",
    "num_win": "Wins",
    "num_loss": "Losses",
    "win_rate_pct": "Win Rate",
    "avg_win_pct": "Avg Win",
    "avg_loss_pct": "Avg Loss",
    "payoff": "Payoff",
    "max_profit_pct": "Max Profit",
    "max_loss_pct": "Max Loss"
})

st.subheader("So sánh chiến lược gốc và chiến lược cắt theo MA10 sau 10 phiên")

st.dataframe(
    compare_ma10_show,
    hide_index=True,
    use_container_width=True
)


# =========================
# LỊCH SỬ GIAO DỊCH BẢN CẮT MA10
# =========================

st.subheader("Lịch sử giao dịch - Sau 10 phiên, cắt nếu giá <= MA10")

if trades_cut_ma10.empty:

    st.warning("Không phát sinh giao dịch.")

else:

    trades_cut_ma10_show = trades_cut_ma10.copy()

    trades_cut_ma10_show["date"] = pd.to_datetime(
        trades_cut_ma10_show["date"]
    ).dt.strftime("%Y-%m-%d")

    if "buy_date" in trades_cut_ma10_show.columns:
        trades_cut_ma10_show["buy_date"] = pd.to_datetime(
            trades_cut_ma10_show["buy_date"]
        ).dt.strftime("%Y-%m-%d")

    num_cols = [
        f"price_{ticker_input}",
        "MA10",
        "buy_price",
        "shares",
        "value",
        "cash_after",
        "profit_pct",
        "profit_value"
    ]

    for col in num_cols:
        if col in trades_cut_ma10_show.columns:
            trades_cut_ma10_show[col] = pd.to_numeric(
                trades_cut_ma10_show[col],
                errors="coerce"
            ).round(2)

    trades_cut_ma10_show = trades_cut_ma10_show.rename(columns={
        "date": "Date",
        "action": "Action",
        "buy_date": "Buy Date",
        "buy_price": "Buy Price",
        f"price_{ticker_input}": "Price",
        "MA10": "MA10",
        "shares": "Shares",
        "value": "Value",
        "cash_after": "Cash After",
        "profit_pct": "PnL %",
        "profit_value": "PnL"
    })

    st.dataframe(
        trades_cut_ma10_show,
        hide_index=True,
        use_container_width=True,
        height=400
    )

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12,6))

ax.plot(
    data["date"],
    data["close_norm"],
    label="Giá"
)

ax.plot(
    data["date"],
    data["smdt_nganh_norm"],
    label="SMDT ngành"
)

ax.plot(
    data["date"],
    data["smdt_ma_norm"],
    label="SMDT mã"
)

ax.legend()

st.pyplot(fig)
