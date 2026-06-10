import streamlit as st
import pandas as pd
import requests

st.subheader("VNINDEX - Tín hiệu tạo đáy")

url = "https://stocktraders.vn/service/data/getTotalTrade"

payload = {
    "TotalTradeRequest": {
        "account": "uyen.png"
    }
}

response = requests.post(url, json=payload)

st.write(response.status_code)
