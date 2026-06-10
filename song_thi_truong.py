import streamlit as st
import pandas as pd
import requests
from streamlit_lightweight_charts import renderLightweightCharts
import plotly.graph_objects as go

# =========================
# CẤU HÌNH APP
# =========================

st.set_page_config(
    page_title="Bảng tạo đáy thị trường",
    layout="wide"
)

st.title("📉 Giao dịch theo sóng thị trường")

start_date = "2023-06-08"

# =========================
# CACHE API
# =========================

@st.cache_data(ttl=86400)
def post_api(url, payload):

    r = requests.post(
        url,
        json=payload,
        timeout=30
    )

    r.raise_for_status()

    return r.json()


# =========================
# LOAD TOÀN BỘ API
# =========================

@st.cache_data(ttl=86400)
def load_all_data():

    account = "uyen.png"

    wave_data = post_api(
        "https://stocktraders.vn/service/data/getStockWave",
        {
            "StockWaveRequest": {
                "account": account
            }
        }
    )

    smdt_data = post_api(
        "https://stocktraders.vn/service/data/getSMDTBranch",
        {
            "SMDTBranchRequest": {
                "account": account
            }
        }
    )

    cashflow_data = post_api(
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

    return (
        wave_data,
        smdt_data,
        cashflow_data,
        price_data,
        branch_data
    )


# =========================
# CHẠY API
# =========================

with st.spinner("Đang tải dữ liệu..."):

    (
        wave_data,
        smdt_data,
        cashflow_data,
        price_data,
        branch_data
    ) = load_all_data()

st.success("Đã tải dữ liệu thành công")
