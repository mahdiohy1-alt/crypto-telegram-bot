import os
import time
import requests
import pandas as pd
import ta
import ccxt
from flask import Flask
from threading import Thread

# ==================== 🔑 الإعدادات الأساسية 🔑 ====================
TELEGRAM_TOKEN = '8659171008:AAHIdMFNA4q7NsPZ5d9lgvgkpucAz9PLsOM'
CHAT_ID = '6750615824'
WATCHLIST = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT']

# روابط الـ GIFs
GIF_NEW = "https://media.giphy.com/media/92wH9E5FNKtqje8vGP/giphy.gif"
GIF_TP1 = "https://media.giphy.com/media/YnkMc6mife5p6JAHFl/giphy.gif"
GIF_TP2 = "https://media.giphy.com/media/l0Ex6kAKAoFRsFh6M/giphy.gif"
GIF_SL  = "https://media.giphy.com/media/eKrgVyZ7ZVccg/giphy.gif"

# ==================== 🌐 خادم الويب الوهمي لـ Render 🌐 ====================
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
def run_web(): app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
Thread(target=run_web).start()

# ==================== 🛠️ دالات العمل 🛠️ ====================
data_exchange = ccxt.binance({'enableRateLimit': True})

def send_telegram(gif_url, text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAnimation"
        requests.post(url, json={"chat_id": CHAT_ID, "animation": gif_url, "caption": text, "parse_mode": "Markdown"})
    except: pass

def get_data(symbol):
    bars = data_exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
    df = pd.DataFrame(bars, columns=['t', 'o', 'high', 'low', 'close', 'v'])
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['low_band'] = ta.volatility.bollinger_lband(df['close'], window=20, window_dev=2)
    return df

# ==================== 🧠 منطق المراقبة والصفقات 🧠 ====================
def monitor(symbol, entry, tp1, tp2, sl):
    print(f"🔄 مراقبة {symbol} | الدخول: {entry}")
    while True:
        try:
            price = data_exchange.fetch_ticker(symbol)['last']
            if price <= sl:
                send_telegram(GIF_SL, f"🟥 ضرب وقف الخسارة: {symbol}\nالسعر: {price}")
                break
            if price >= tp1:
                send_telegram(GIF_TP1, f"🟨 تحقق الهدف الأول: {symbol}\nالسعر: {price}")
                # هنا يتم تحديث الـ SL لسعر الدخول بعد الهدف الأول
                sl = entry 
            if price >= tp2:
                send_telegram(GIF_TP2, f"🟩 تحقق الهدف الثاني (ربح كامل): {symbol}\nالسعر: {price}")
                break
            time.sleep(10)
        except: break

# ==================== 🚀 الحلقة الرئيسية 🚀 ====================
print("📡 البوت جاهز ويعمل الآن...")
while True:
    for symbol in WATCHLIST:
        try:
            df = get_data(symbol)
            if df['rsi'].iloc[-1] < 30 and df['close'].iloc[-1] <= df['low_band'].iloc[-1]:
                entry = df['close'].iloc[-1]
                msg = f"🔔 صفقة جديدة: {symbol}\n💵 الدخول: {entry}\n🛑 SL: {entry*0.99:.4f}\n🚀 TP2: {entry*1.025:.4f}"
                send_telegram(GIF_NEW, msg)
                monitor(symbol, entry, entry*1.01, entry*1.025, entry*0.99)
        except: pass
        time.sleep(5)
