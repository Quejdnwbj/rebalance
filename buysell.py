import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime

# ================= 🔧 請在此填入你的正確資訊 =================

LINE_ACCESS_TOKEN = "n5vIvjU8H2sL1wQvVZ44BEIbxOkAR+B4k+FrKLgT5eDE0NQAvt8qYzDy4+YnPuYLUjYotxf2rSogE9MytkMsUaoBlMCMn888PR7Oyxa1Q2bFgmZCdH51mCvUsgcefz1p2o4BnJf7ue1noq/v3JNrLwdB04t89/1O/w1cDnyilFU="
LINE_USER_ID = "Ua8da6953f7665190daa32bc7bcfffd73"
# ========================================================================

def push_line_message(token, to_id, text):
    # 💡 改用精準的 push 網址，繞過廣播限制
    url = 'https://line.me'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    payload = {
        "to": to_id,
        "messages": [{"type": "text", "text": text}]
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("🎉 LINE 策略訊息已精準推送到你的手機！")
    else:
        print(f"⚠️ LINE 發送失敗，狀態碼：{response.status_code}")
        print("回應內容：", response.text)

def job():
    print(f"\n⏰ 觸發定時任務，目前時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 下載數據
        taiex_data = yf.download("^TWII", start="2026-01-01")

        if taiex_data.empty:
            raise ValueError("yfinance 未回傳任何數據。")

        if isinstance(taiex_data.columns, pd.MultiIndex):
            taiex_data.columns = taiex_data.columns.droplevel(1)

        columns_to_convert = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in columns_to_convert:
            taiex_data[col] = pd.to_numeric(taiex_data[col], errors='coerce')

        taiex_data = taiex_data.dropna(subset=columns_to_convert)
        
        if len(taiex_data) < 20:
            raise ValueError("有效數據太少，無法計算 20MA。")

        taiex_data.index = pd.to_datetime(taiex_data.index)

        # 2. 計算 5MA 與 20MA
        taiex_data['5MA'] = taiex_data['Close'].rolling(window=5).mean()
        taiex_data['20MA'] = taiex_data['Close'].rolling(window=20).mean()
        
        # 3. 判斷交叉訊號
        taiex_data['Signal'] = np.where(taiex_data['5MA'] > taiex_data['20MA'], 1, 0)
        taiex_data['Positions'] = taiex_data['Signal'].diff()

        # 4. 擷取最新交易訊號
        latest_row = taiex_data.iloc[-1]
        latest_position = latest_row['Positions']
        data_date = taiex_data.index[-1].strftime('%m/%d')
        
        if latest_position == 1:
            strategy_text = f"🚨 【交易訊號：請買入】(依據 {data_date} 資料)"
        elif latest_position == -1:
            strategy_text = f"🚨 【交易訊號：請賣出】(依據 {data_date} 資料)"
        else:
            strategy_text = f"⏳ 目前無交易訊號，請繼續觀望。(最新資料日期: {data_date})"

        # 5. 發送訊息
        message_content = f"📊 台股策略通知 ({datetime.now().strftime('%H:%M')})：\n\n{strategy_text}"
        push_line_message(LINE_ACCESS_TOKEN, LINE_USER_ID, message_content)
            
    except Exception as error:
        print(f"❌ 本次執行發生錯誤: {error}，將於一小時後重試。")

if __name__ == "__main__":
    print("🚀 股票策略 LINE 精準推播機器人已啟動！")
    job()
    print("😴 程式進入定時休眠，每 60 分鐘會自動檢查並發送一次...")
    while True:
        time.sleep(3600)
        job()