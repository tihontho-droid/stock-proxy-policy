# =========================
# 8. TÍNH SẴN RETURN 5/10/20 PHIÊN CHO TỪNG MÃ
# =========================

holding_periods = [5, 10, 20]

price_sector_df = price_sector_df.sort_values(
    ["ticker", "date"]
).reset_index(drop=True)

for n in holding_periods:
    price_sector_df[f"close_after_{n}d"] = (
        price_sector_df.groupby("ticker")["close"].shift(-n)
    )

    price_sector_df[f"return_{n}d_pct"] = (
        price_sector_df[f"close_after_{n}d"] / price_sector_df["close"] - 1
    ) * 100


# =========================
# 9. LỌC NGÀNH ĐẸP TẠI NGÀY TẠO ĐÁY
# =========================

bottom_sector_df = sector_all_df[
    (sector_all_df["date"].isin(bottom_dates))
    & (sector_all_df["nganh_dep"])
].copy()

bottom_sector_df = bottom_sector_df.rename(columns={
    "date": "bottom_date"
})


# =========================
# 10. GỘP GIÁ CỔ PHIẾU VÀO NGÀNH ĐẸP
# =========================

price_sector_bottom = price_sector_df.rename(columns={
    "date": "bottom_date",
    "close": "close_bottom"
})

stock_after_bottom_df = bottom_sector_df.merge(
    price_sector_bottom,
    on=["bottom_date", "nganh"],
    how="inner"
)


# =========================
# 11. CHỌN CỘT KẾT QUẢ
# =========================

stock_after_bottom_df = stock_after_bottom_df[
    [
        "bottom_date",
        "nganh",
        "ticker",
        "close_bottom",

        "smdt",
        "flow_num",
        "cashflow",
        "flow_vua_tich_cuc",
        "smdt_vua_vuot_70",
        "nganh_vua_dep",

        "close_after_5d",
        "return_5d_pct",
        "close_after_10d",
        "return_10d_pct",
        "close_after_20d",
        "return_20d_pct"
    ]
].copy()

stock_after_bottom_df = stock_after_bottom_df.rename(columns={
    "smdt": "smdt_bottom",
    "flow_num": "flow_num_bottom",
    "cashflow": "cashflow_bottom"
})

stock_after_bottom_df = stock_after_bottom_df.sort_values(
    ["bottom_date", "return_20d_pct"],
    ascending=[True, False]
).reset_index(drop=True)

stock_after_bottom_df
