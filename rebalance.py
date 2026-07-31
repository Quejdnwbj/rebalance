import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==================== 🔧 使用者設定區塊 ====================
# Google Spreadsheet CSV 匯出網址 (已開啟公開權限)
CSV_URL = "https://docs.google.com/spreadsheets/d/1w3-5YsBYOuch_TMlFhBGEw_AlQtgwiIw4iezlXxumfk/export?format=csv&gid=123456"

REBALANCE_TARGET_WEIGHT = 0.50  # 目標權重 (50%)
REBALANCE_THRESHOLD = 0.058     # 再平衡觸發偏離門檻 (5.8%)
# ==========================================================

def load_data_from_url(url):
    """從 Google Sheet CSV 網址讀取並解析資料"""
    print(f"📥 正在從 Google Sheet 下載資料...")
    # 跳過前 8 列的中繼資料，從欄位名稱開始讀取
    df = pd.read_csv(url, skiprows=8)
    
    # 清除完全空白的列與日期欄位為空的值
    df = df.dropna(subset=['日期'])
    df['日期'] = df['日期'].str.strip()
    df = df[df['日期'] != '']
    
    # 將日期轉換成 Datetime 索引
    df['日期'] = pd.to_datetime(df['日期'])
    df = df.set_index('日期')
    df = df.sort_index()
    
    # 清理數值型欄位（去除 $, %, 逗號等符號）
    numeric_cols = ['收盤價', '持有股數', '正2市值', '現金餘額', '總資產', '交易股數', '交易金額']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('$', '', regex=False)
            df[col] = df[col].astype(str).str.replace(',', '', regex=False)
            df[col] = df[col].astype(str).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    pct_cols = ['正2權重', '實際權重']
    for col in pct_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('%', '', regex=False)
            df[col] = df[col].astype(str).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce') / 100.0
            
    # 對應舊程式碼的 Price 欄位
    df['Price'] = df['收盤價']
    return df

def run_backtest(df):
    """執行 50:50 歷史回測"""
    # 我們可以直接使用 Google Sheet 中已經算好的回測資料
    # 或者用 Python 程式重新跑一次回測來驗證
    rebalance_events = df[df['觸發再平衡'] == '是']
    rebalance_count = len(rebalance_events)
    return df, rebalance_count

def check_current_status(df):
    """檢查最新狀態，判斷是否需要再平衡"""
    if len(df) < 2:
        raise ValueError("數據不足，無法計算漲跌幅。")
        
    latest_date = df.index[-1]
    latest_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    latest_price = latest_row['收盤價']
    prev_price = prev_row['收盤價']
    
    # 計算最新一期的漲跌幅 (因為資料是按月記錄，所以這代表月漲跌幅)
    monthly_change = (latest_price - prev_price) / prev_price
    
    # 計算正2權重偏離程度
    # 如果 Excel 中有現成的 總資產 與 正2市值，我們直接抓取計算
    etf_value = latest_row['正2市值']
    cash_value = latest_row['現金餘額']
    total_value = latest_row['總資產']
    
    current_ratio = etf_value / total_value if total_value > 0 else 0
    deviation = current_ratio - REBALANCE_TARGET_WEIGHT
    
    # 判斷是否需要再平衡
    need_rebalance = abs(deviation) >= REBALANCE_THRESHOLD
    
    date_str = latest_date.strftime('%Y-%m-%d')
    
    print("\n" + "="*20 + " 偵測結果 " + "="*20)
    if need_rebalance:
        # 計算平衡所需交易金額與股數
        target_etf_value = total_value * REBALANCE_TARGET_WEIGHT
        trade_amount = target_etf_value - etf_value  # 正為買入，負為賣出
        shares_to_trade = trade_amount / latest_price
        
        action = "買入" if trade_amount > 0 else "賣出"
        
        print(f"🚨 【需要再平衡】")
        print(f"📅 日期：{date_str}")
        print(f"📈 收盤價格：{latest_price:,.2f}")
        print(f"📅 本月漲跌幅：{monthly_change:+.2%}")
        print(f"💰 總資產：${total_value:,.2f} 元")
        print(f"⚖️ 當前正2權重：{current_ratio:.2%} (偏離目標 {deviation:+.2%})")
        print(f"🛠️ 再平衡建議：請【{action}】金額 ${abs(trade_amount):,.2f} 元 (約 {abs(shares_to_trade):.2f} 股)")
    else:
        print(f"⏳ 【無需再平衡】")
        print(f"📅 日期：{date_str}")
        print(f"📈 收盤價格：{latest_price:,.2f}")
        print(f"📊 當日/當期漲跌金額：{latest_price - prev_price:+.2f} 元")
        print(f"📊 當日/當期漲跌幅：{monthly_change:+.2%}")
        print(f"⚖️ 當前正2權重：{current_ratio:.2%} (未達到 {REBALANCE_THRESHOLD:.1%} 的偏離門檻)")
    print("="*48 + "\n")

def plot_backtest_results(df):
    """繪製並儲存回測結果圖表"""
    plt.figure(figsize=(12, 6))
    
    # 支援中文顯示
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Microsoft JhengHei', 'SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    
    plt.plot(df.index, df['總資產'], label='50:50 再平衡資產曲線', color='#2ca02c', linewidth=2)
    
    # 標註再平衡點
    rebal_points = df[df['觸發再平衡'] == '是']
    plt.scatter(rebal_points.index, rebal_points['總資產'], color='red', marker='^', s=60, label='再平衡事件', zorder=5)
    
    # 標註再平衡日期文字
    for date, row in rebal_points.iterrows():
        plt.annotate(
            date.strftime('%Y-%m'), 
            (date, row['總資產']),
            textcoords="offset points", 
            xytext=(0, 8), 
            ha='center', 
            fontsize=7, 
            color='darkred',
            rotation=45,
            bbox=dict(boxstyle="round,pad=0.1", fc="white", alpha=0.6, ec="red", lw=0.5)
        )
    
    plt.title('50:50 策略歷史回測 (Google Sheet 數據源)')
    plt.xlabel('日期')
    plt.ylabel('總資產價值 (TWD)')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)
    
    chart_path = "backtest_chart.png"
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    print(f"📈 回測資產曲線圖已儲存至：{chart_path}")
    plt.close()

if __name__ == "__main__":
    print("🚀 啟動 50:50 Excel/Google Sheet 回測與自動偵測系統...")
    try:
        # 1. 讀取 Google Sheet 資料
        df = load_data_from_url(CSV_URL)
        
        # 2. 執行回測與繪圖
        df, count = run_backtest(df)
        print(f"📊 歷史回測完成！區間：{df.index[0].date()} 至 {df.index[-1].date()}")
        print(f"🔄 回測期間總再平衡次數：{count} 次")
        plot_backtest_results(df)
        
        # 3. 檢查最新狀態
        check_current_status(df)
        
    except Exception as e:
        print(f"❌ 執行時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
