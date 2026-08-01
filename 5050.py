import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yfinance as yf


def backtest_5050_strategy(
    df, initial_capital=1000000, threshold=0.05, execution_delay=True
):
    """50:50 正2 與現金動態再平衡回測引擎

    Parameters:
    - df: 包含 0050_Close, 00631L_Open, 00631L_Close 的 DataFrame
    - initial_capital: 初始投資本金 (預設 100 萬)
    - threshold: 再平衡觸發閾值 (預設 0.05，即正2權重高於 55% 或低於 45% 時觸發)
    - execution_delay: 是否模擬現實盲點 (T日盤後觸發，T+1日開盤價成交)
    """
    total_value = initial_capital
    cash = total_value * 0.5
    # 第一天以收盤價建立初始部位
    shares = (total_value * 0.5) / df.iloc[0]["00631L_Close"]

    history = []
    transactions = []
    rebalance_triggered = False

    # 記錄初始建倉
    transactions.append({
        "Date": df.index[0],
        "Action": "初始建倉",
        "Price": df.iloc[0]["00631L_Close"],
        "Trade_Amount": total_value * 0.5,
        "Shares_Traded": shares,
        "Cash": cash,
        "ETF_Value": total_value * 0.5,
        "Total_Value": total_value,
        "ETF_Ratio": 0.5
    })

    for i in range(len(df)):
        current_date = df.index[i]
        o_631l = df.iloc[i]["00631L_Open"]
        c_631l = df.iloc[i]["00631L_Close"]
        c_0050 = df.iloc[i]["0050_Close"]

        # --- STEP 1: 處理延遲再平衡 (在今日開盤價交易) ---
        if rebalance_triggered and execution_delay:
            # 開盤時的總資產狀況
            open_portfolio_value = cash + (shares * o_631l)
            target_etf_value = open_portfolio_value * 0.5

            # 執行再平衡
            current_etf_value = shares * o_631l
            trade_amount = target_etf_value - current_etf_value

            cash -= trade_amount
            shares = target_etf_value / o_631l
            rebalance_triggered = False  # 重置標記

            transactions.append({
                "Date": current_date,
                "Action": "再平衡(買入)" if trade_amount > 0 else "再平衡(賣出)",
                "Price": o_631l,
                "Trade_Amount": abs(trade_amount),
                "Shares_Traded": trade_amount / o_631l,
                "Cash": cash,
                "ETF_Value": target_etf_value,
                "Total_Value": open_portfolio_value,
                "ETF_Ratio": 0.5
            })

        # --- STEP 2: 計算今日收盤後的資產價值 ---
        etf_value = shares * c_631l
        total_value = cash + etf_value
        etf_ratio = etf_value / total_value if total_value > 0 else 0

        # --- STEP 3: 盤後判斷是否觸發再平衡 ---
        is_event = 0
        if abs(etf_ratio - 0.5) >= threshold:
            if execution_delay:
                rebalance_triggered = True  # 標記明天開盤執行
            else:
                # 完美流派 (不切實際的當天收盤價完美成交)
                target_etf_value = total_value * 0.5
                trade_amount = target_etf_value - etf_value
                cash -= trade_amount
                shares = target_etf_value / c_631l
                etf_value = shares * c_631l
                etf_ratio = 0.5
                is_event = 1

                transactions.append({
                    "Date": current_date,
                    "Action": "再平衡(買入)" if trade_amount > 0 else "再平衡(賣出)",
                    "Price": c_631l,
                    "Trade_Amount": abs(trade_amount),
                    "Shares_Traded": trade_amount / c_631l,
                    "Cash": cash,
                    "ETF_Value": target_etf_value,
                    "Total_Value": total_value,
                    "ETF_Ratio": 0.5
                })

        # 若是延遲交易，我們在觸發當天紀錄事件標記
        if execution_delay and rebalance_triggered:
            is_event = 1

        history.append(
            {
                "Date": current_date,
                "Total_Value": total_value,
                "Cash": cash,
                "ETF_Value": etf_value,
                "ETF_Ratio": etf_ratio,
                "Rebalance_Event": is_event,
            }
        )

    result_df = pd.DataFrame(history).set_index("Date")
    tx_df = pd.DataFrame(transactions).set_index("Date")
    return result_df, tx_df


# ==========================================
# 1. 資料獲取與預處理
# ==========================================
print("正在從 Yahoo Finance 下載台股數據...")
# 0050.TW (元大台灣50), 00631L.TW (元大台灣50正2)
tickers = {"0050": "0050.TW", "00631L": "00631L.TW"}

data_0050 = yf.download(tickers["0050"], start="2015-01-01", end="2026-07-01")
data_631l = yf.download(tickers["00631L"], start="2015-01-01", end="2026-07-01")

# 應對 yf 新版多重索引結構，確保欄位乾淨
if isinstance(data_0050.columns, pd.MultiIndex):
    data_0050.columns = data_0050.columns.droplevel(1)
if isinstance(data_631l.columns, pd.MultiIndex):
    data_631l.columns = data_631l.columns.droplevel(1)

df = pd.DataFrame(index=data_0050.index)
col_0050 = "Adj Close" if "Adj Close" in data_0050.columns else "Close"
col_631l = "Adj Close" if "Adj Close" in data_631l.columns else "Close"

df["0050_Close"] = data_0050[col_0050]
df["00631L_Open"] = data_631l["Open"]
df["00631L_Close"] = data_631l[col_631l]
df = df.dropna()

# ==========================================
# 2. 執行回測
# ==========================================
initial_money = 1000000
strat_res, tx_res = backtest_5050_strategy(
    df, initial_capital=initial_money, threshold=0.05, execution_delay=True
)

# 計算對照組：100% 全倉 0050 買入持有
df["0050_Shares"] = initial_money / df.iloc[0]["0050_Close"]
df["0050_Total_Value"] = df["0050_Shares"] * df["0050_Close"]

# ==========================================
# 3. 績效指標計算與除錯驗證
# ==========================================
final_strat = strat_res["Total_Value"].iloc[-1]
final_0050 = df["0050_Total_Value"].iloc[-1]
total_events = strat_res["Rebalance_Event"].sum()

print("\n=== 回測結果績效報告 ===")
print(f"回測時間區間: {df.index[0].date()} 至 {df.index[-1].date()}")
print(f"帳戶初始本金: ${initial_money:,.0f} 元")
print(f"【50:50再平衡策略】最終資產: ${final_strat:,.0f} 元")
print(f"【100%全倉 0050】  最終資產: ${final_0050:,.0f} 元")
print(f"回測期間內總共執行再平衡次數: {total_events} 次")

print("\n=== 再平衡交易明細 ===")
tx_print = tx_res.rename(columns={
    "Action": "動作",
    "Price": "成交價",
    "Trade_Amount": "交易金額",
    "Shares_Traded": "交易股數",
    "Cash": "交易後現金",
    "ETF_Value": "交易後ETF價值",
    "Total_Value": "交易後總資產",
    "ETF_Ratio": "交易後比率"
})

pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)
print(tx_print.to_string(formatters={
    '成交價': '{:,.2f}'.format,
    '交易金額': '${:,.0f}'.format,
    '交易股數': '{:,.0f}'.format,
    '交易後現金': '${:,.0f}'.format,
    '交易後ETF價值': '${:,.0f}'.format,
    '交易後總資產': '${:,.0f}'.format,
    '交易後比率': '{:.2%}'.format
}))

# ==========================================
# 4. 繪製資產成長曲線對比圖
# ==========================================
plt.figure(figsize=(14, 7))
plt.plot(
    strat_res.index,
    strat_res["Total_Value"],
    label="50:50 Rebalance (00631L + Cash)",
    color="#2ca02c",
    linewidth=2,
)
plt.plot(
    df.index,
    df["0050_Total_Value"],
    label="100% Buy & Hold (0050)",
    color="#d62728",
    linewidth=1.5,
    linestyle="--",
)

# 標註再平衡發生的時間點
buy_dates = tx_res[tx_res["Action"] == "再平衡(買入)"].index
sell_dates = tx_res[tx_res["Action"] == "再平衡(賣出)"].index

plt.scatter(
    buy_dates,
    strat_res.loc[buy_dates, "Total_Value"],
    color="red",
    marker="^",
    s=50,
    label="Rebalance (Buy)",
    zorder=5,
)
plt.scatter(
    sell_dates,
    strat_res.loc[sell_dates, "Total_Value"],
    color="green",
    marker="v",
    s=50,
    label="Rebalance (Sell)",
    zorder=5,
)

# 標註最終資產數值
last_date = strat_res.index[-1]
plt.annotate(
    f"${final_strat:,.0f}",
    xy=(last_date, final_strat),
    xytext=(10, -5),
    textcoords="offset points",
    color="#2ca02c",
    weight="bold",
    fontsize=10,
    va="center",
)
plt.annotate(
    f"${final_0050:,.0f}",
    xy=(last_date, final_0050),
    xytext=(10, 10),
    textcoords="offset points",
    color="#d62728",
    weight="bold",
    fontsize=10,
    va="center",
)

# 調整 X 軸範圍以容納右側的標籤
plt.xlim(strat_res.index[0], strat_res.index[-1] + pd.Timedelta(days=365))

plt.title("0050 vs 50:50 Leverage Rebalance Strategy (Reality Simulation)")
plt.xlabel("Date")
plt.ylabel("Portfolio Value (TWD)")
plt.legend()
plt.grid(True, linestyle=":", alpha=0.6)
plt.show()