import streamlit as st
import requests
import pandas as pd
from streamlit_lightweight_charts import renderLightweightCharts


# =========================
# CACHE DATA
# =========================

@st.cache_data(ttl=3600)
def load_cashflow_nganh():
    url = "https://stocktraders.vn/service/data/getCashFlowBranch"
    payload = {"CashFlowBranchRequest": {"account": "uyen.png"}}

    r = requests.post(url, json=payload)
    data = r.json()

    stock_data = data["CashFlowBranchReply"]["cashFlowBranchs"]
    df = pd.DataFrame(stock_data)

    cashflow_expand = pd.json_normalize(df["cashFlowBranchDatas"])
    cashflow_expand["date"] = df["date"]
    cashflow_expand["date"] = pd.to_datetime(cashflow_expand["date"])

    return cashflow_expand


@st.cache_data(ttl=3600)
def load_smdt_nganh():
    url = "https://stocktraders.vn/service/data/getSMDTBranch"
    payload = {"SMDTBranchRequest": {"account": "uyen.png"}}

    r = requests.post(url, json=payload)
    data = r.json()

    stock_data = data["SMDTBranchReply"]["SMDTDatas"]
    df = pd.DataFrame(stock_data)

    df_bds = df[df["keyName"] == "BĐS Dân cư"]
    smdt_data = df_bds.iloc[0]["smdts"]

    df_smdt = pd.DataFrame(smdt_data)
    df_smdt["date"] = pd.to_datetime(df_smdt["date"])
    df_smdt["smdt"] = pd.to_numeric(df_smdt["smdt"], errors="coerce")

    return df_smdt.sort_values("date").reset_index(drop=True)


@st.cache_data(ttl=3600)
def load_price_nvl():
    url = "https://stocktraders.vn/service/data/getTotalTrade"
    payload = {"TotalTradeRequest": {"account": "uyen.png"}}

    r = requests.post(url, json=payload)
    data = r.json()

    stock_data = data["TotalTradeReply"]["stockTotals"]
    df = pd.DataFrame(stock_data)

    row = df[df["ticker"] == "NVL"]
    price_data = row.iloc[0]["totalDatas"]

    price_df = pd.DataFrame(price_data)
    price_df["date"] = pd.to_datetime(price_df["date"])

    return price_df.sort_values("date").reset_index(drop=True)


@st.cache_data(ttl=3600)
def load_smdt_nvl():
    url = "https://stocktraders.vn/service/data/getSMDTTicker"
    payload = {"SMDTTickerRequest": {"account": "uyen.png"}}

    r = requests.post(url, json=payload)
    data = r.json()

    stock_data = data["SMDTTickerReply"]["SMDTDatas"]
    df = pd.DataFrame(stock_data)

    df_nvl = df[df["keyValue"] == "NVL"]
    smdt_data_ma = df_nvl.iloc[0]["smdts"]

    df_smdt_ma = pd.DataFrame(smdt_data_ma)
    df_smdt_ma["date"] = pd.to_datetime(df_smdt_ma["date"])
    df_smdt_ma["smdt"] = pd.to_numeric(df_smdt_ma["smdt"], errors="coerce")

    return df_smdt_ma.sort_values("date").reset_index(drop=True)


@st.cache_data(ttl=3600)
def load_cashflow_nvl():
    url = "https://stocktraders.vn/service/data/getCashFlowTicker"
    payload = {"CashFlowTickerRequest": {"account": "uyen.png"}}

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

    df_nvl_flow = df_cashflow_ticker[
        df_cashflow_ticker["ticker"] == "NVL"
    ].copy()

    df_nvl_flow["date"] = pd.to_datetime(df_nvl_flow["date"])

    return df_nvl_flow.sort_values("date").reset_index(drop=True)


# =========================
# BUILD DF_SIGNAL
# =========================

def build_signal(
    price_df,
    cashflow_expand,
    df_smdt,
    df_nvl_flow,
    df_smdt_ma
):
    cashflow_nganh_df = cashflow_expand.copy()
    smdt_nganh_df = df_smdt.copy()
    cashflow_ma_df = df_nvl_flow.copy()
    smdt_ma_df = df_smdt_ma.copy()

    cashflow_nganh_df = cashflow_nganh_df.rename(columns={
        "content": "cashflow_nganh"
    })

    smdt_nganh_df = smdt_nganh_df.rename(columns={
        "smdt": "smdt_nganh"
    })

    cashflow_ma_df = cashflow_ma_df.rename(columns={
        "content": "cashflow_ma"
    })

    smdt_ma_df = smdt_ma_df.rename(columns={
        "smdt": "smdt_ma"
    })

    df_signal = price_df[["date", "close"]].copy()

    df_signal = df_signal.merge(
        cashflow_nganh_df[["date", "cashflow_nganh"]],
        on="date",
        how="left"
    )

    df_signal = df_signal.merge(
        smdt_nganh_df[["date", "smdt_nganh"]],
        on="date",
        how="left"
    )

    df_signal = df_signal.merge(
        cashflow_ma_df[["date", "cashflow_ma"]],
        on="date",
        how="left"
    )

    df_signal = df_signal.merge(
        smdt_ma_df[["date", "smdt_ma"]],
        on="date",
        how="left"
    )

    df_signal = df_signal.sort_values("date").reset_index(drop=True)

    return df_signal


# =========================
# LOAD 1 LẦN
# =========================

cashflow_expand = load_cashflow_nganh()
df_smdt = load_smdt_nganh()
price_df = load_price_nvl()
df_smdt_ma = load_smdt_nvl()
df_nvl_flow = load_cashflow_nvl()

df_signal = build_signal(
    price_df,
    cashflow_expand,
    df_smdt,
    df_nvl_flow,
    df_smdt_ma
)


# =========================
# UI
# =========================

st.markdown("""
<style>
.big-font {
    font-size:40px !important;
    font-weight:bold;
    text-align:left;
}
</style>

<p class="big-font">
Xây dựng chiến lược Buy/Sell mã NVL
</p>
""", unsafe_allow_html=True)

st.write("Mục tiêu là xây dựng các chiến lược Buy/Sell trên mã NVL giai đoạn từ 06/06/2023 đến 20/5/2026 dựa vào các dữ liệu được cung cấp API.")
# =========================
# 1. NGÀNH BĐS DÂN CƯ
# =========================
st.subheader("Ngành BĐS dân cư")
left_col, right_col = st.columns([1, 1])

with left_col:
    st.markdown(
    "<p style='font-size:20px;'>Tín hiệu dòng tiền</p>",
    unsafe_allow_html=True
    )

    df_cashflow_show = cashflow_expand[[
        "date",
        "content"
    ]].copy()

    df_cashflow_show = df_cashflow_show.rename(columns={
        "date": "Ngày",
        "content": "Trạng thái"
    })

    df_cashflow_show["Ngày"] = (
        pd.to_datetime(df_cashflow_show["Ngày"])
        .dt.strftime("%Y-%m-%d")
    )

    st.dataframe(
        df_cashflow_show,
        hide_index=True,
        width="stretch",
        height=250
    )


with right_col:
    st.markdown(
    "<p style='font-size:20px;'>Sức mạnh dòng tiền (SMDT)</p>",
    unsafe_allow_html=True
    )

    chart_data = []
    threshold_data = []

    for _, row in df_smdt.iterrows():
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
        key="smdt_nganh_chart"
    )


# =========================
# 2. MÃ NVL
# =========================

st.subheader("Biểu đồ giá NVL")

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
        "barSpacing": 8,
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
    key="nvl_candlestick_chart"
)


left_col, right_col = st.columns([1, 1])

with left_col:
    st.markdown(
    "<p style='font-size:20px;'>Tín hiệu dòng tiền NVL</p>",
    unsafe_allow_html=True)

    df_nvl_flow_show = df_nvl_flow[[
        "date",
        "content"
    ]].copy()

    df_nvl_flow_show = df_nvl_flow_show.rename(columns={
        "date": "Ngày",
        "content": "Tín hiệu dòng tiền"
    })

    df_nvl_flow_show["Ngày"] = (
        pd.to_datetime(df_nvl_flow_show["Ngày"])
        .dt.strftime("%Y-%m-%d")
    )

    st.dataframe(
        df_nvl_flow_show,
        hide_index=True,
        width="stretch",
        height=250
    )


with right_col:
    st.markdown(
    "<p style='font-size:20px;'>Sức mạnh dòng tiền (SMDT) NVL</p>",
    unsafe_allow_html=True
    )

    smdt_ma_data = []
    threshold_ma_data = []

    for _, row in df_smdt_ma.iterrows():
        time_value = row["date"].strftime("%Y-%m-%d")

        smdt_ma_data.append({
            "time": time_value,
            "value": round(row["smdt"], 2)
        })

        threshold_ma_data.append({
            "time": time_value,
            "value": 70
        })

    smdt_ma_series = [
        {
            "type": "Line",
            "data": smdt_ma_data,
            "options": {
                "color": "#F2C94C",
                "lineWidth": 3,
                "priceLineVisible": False,
                "lastValueVisible": False
            }
        },
        {
            "type": "Line",
            "data": threshold_ma_data,
            "options": {
                "color": "#F2994A",
                "lineWidth": 2,
                "lineStyle": 2,
                "priceLineVisible": False,
                "lastValueVisible": False
            }
        }
    ]

    renderLightweightCharts(
        [
            {
                "chart": chart_options,
                "series": smdt_ma_series
            }
        ],
        key="smdt_ma_nvl_chart"
    )

st.subheader("Giải thích hướng đi khi xây dựng chiến lược")

st.write("Buy khi xuất hiện các điều kiện sau: ")

st.write("- Dòng tiền ngành chuyển từ trạng thái thoát ra sang đổ vào 2 phiên liên tiếp.")

st.write("- Dòng tiền mã chuyển từ trạng thái thoát ra sang đổ vào 2 phiên liên tiếp.")

st.write("- SMDT ngành vừa vượt ngưỡng 70 trong 2 phiên liên tiếp.")

st.write("- SMDT mã vừa vượt ngưỡng 70 trong 2 phiên liên tiếp.")

st.write(" ")

st.write("Sell khi xuất hiện các điều kiện sau: ")

st.write("- Dòng tiền ngành chuyển từ trạng thái đổ vào sang thoát ra 2 phiên liên tiếp.")

st.write("- Dòng tiền mã chuyển từ trạng thái đổ vào sang thoát ra 2 phiên liên tiếp.")

st.write("- SMDT ngành vừa giảm dưới ngưỡng 70 trong 2 phiên liên tiếp.")

st.write("- SMDT mã vừa giảm dưới ngưỡng 70 trong 2 phiên liên tiếp.")

st.write(" ")

st.write("Ta có thể xây dựng 1 chiến lược chỉ dựa trên tín hiệu dòng tiền ngành, hoặc 1 chiến lược chỉ dựa trên SMDT mã, hoặc 1 chiến lược kết hợp tất cả các điều kiện với nhau. Mục tiêu là trong tất cả chiến lược đó, cái nào đem lại hiệu suất cao nhất đối với mã NVL giai đoạn từ 06/06/2023 đến 20/5/2026.")

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
                "price_NVL": price,
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
                "price_NVL": price,
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
            "price_NVL": price,
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

    df_signal[col] = pd.to_numeric(df_signal[col], errors="coerce").ffill()

for col in ["smdt_nganh", "smdt_ma", "close"]:
    df_signal[col] = pd.to_numeric(df_signal[col], errors="coerce")


# =========================
# 3. TẠO 8 TÍN HIỆU GIỐNG NOTEBOOK
# =========================
# =========================
# LỌC ĐỒNG BỘ NGÀY BẮT ĐẦU
# =========================

start_date = pd.to_datetime("2023-06-06")

df_signal = df_signal.copy()

df_signal["date"] = pd.to_datetime(df_signal["date"])

df_signal = df_signal[
    df_signal["date"] >= start_date
].copy()

df_signal = df_signal.sort_values("date").reset_index(drop=True)

# kiểm tra ngày bắt đầu
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

        buy_rules["buy_AND__" + name] = make_rule(cols, "AND")

        if r >= 2:
            buy_rules["buy_OR__" + name] = make_rule(cols, "OR")


sell_rules = {}

for r in range(1, len(sell_signals) + 1):

    for cols in combinations(sell_signals, r):

        name = "__".join(cols)

        sell_rules["sell_AND__" + name] = make_rule(cols, "AND")

        if r >= 2:
            sell_rules["sell_OR__" + name] = make_rule(cols, "OR")


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
st.success("Đã chạy backtest xong 676 chiến lược")

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

top_strategy = summary_raw.iloc[0]["strategy"]

st.subheader("Chiến lược tốt nhất")

st.write("Buy khi đạt 1 trong 4 điều kiện trên - Sell khi đạt 1 trong 4 điều kiện trên.")

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
            "price_NVL",
            "PnL",
            "cash_after"
        ]
    ]

    trade_view["date"] = trade_view["date"].dt.strftime("%Y-%m-%d")

    trade_view["price_NVL"] = (
        trade_view["price_NVL"]
        .round(2)
    )

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
        "price_NVL": "Price",
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

st.subheader("Tra cứu tín hiệu NVL theo ngày")

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
        "close": "Giá NVL",
        "cashflow_nganh": "Dòng tiền ngành",
        "smdt_nganh": "SMDT ngành",
        "cashflow_ma": "Dòng tiền mã",
        "smdt_ma": "SMDT mã"
    })

    st.dataframe(
        result_show,
        hide_index=True,
        width="stretch"
    )

st.write("Chú thích: ")
st.write("1 là tín hiệu dòng tiền nhen nhóm/tiếp tục đổ vào.")
st.write("-1 là tín hiệu dòng tiền đang/tiếp tục thoát ra.")
st.write("Lưu ý: phải đạt điều kiện 2 phiên liên tiếp thì mới ghi nhận Buy/Sell.")

