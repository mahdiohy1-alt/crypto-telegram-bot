import os
import time
import requests
import pandas as pd
import ta
import ccxt
from flask import Flask
from threading import Thread

# ==================== 🔑 الإعدادات 🔑 ====================
TELEGRAM_TOKEN = '8659171008:AAHIdMFNA4q7NsPZ5d9lgvgkpucAz9PLsOM'
CHAT_ID = '6750615824'
WATCHLIST = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT']

# ==================== 🌐 نظام الويب (لـ Render) 🌐 ====================
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is live!"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ==================== 🛠️ محرك التداول (Bybit) 🛠️ ====================
def run_trading_bot():
    # تم تغيير Binance إلى Bybit
    exchange = ccxt.bybit({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    
    def send_telegram(text):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"خطأ في إرسال تليجرام: {e}", flush=True)

    print("🚀 البوت بدأ العمل الآن على Bybit...", flush=True)
    send_telegram("🤖 *تم التشغيل بنجاح على Bybit!* أراقب الأسواق الآن.")

    while True:
        for symbol in WATCHLIST:
            try:
                print(f"🔍 فحص {symbol}...", flush=True)
                
                # جلب البيانات
                bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
                df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'close', 'v'])
                df['rsi'] = ta.momentum.rsi(df['close'], window=14)
                df['lb'] = ta.volatility.bollinger_lband(df['close'], window=20, window_dev=2)
                
                rsi_val = df['rsi'].iloc[-1]
                price = df['close'].iloc[-1]
                
                # شرط الدخول
                if rsi_val < 30 and price <= df['lb'].iloc[-1]:
                    send_telegram(f"🔔 *إشارة دخول في Bybit: {symbol}*\n💵 السعر: {price:.4f}")
                    
                    # المراقبة
                    highest_price = price
                    start = time.time()
                    while (time.time() - start) < 3600:
                        time.sleep(20)
                        current = exchange.fetch_ticker(symbol)['last']
                        if current > highest_price: highest_price = current
                        
                        if current < (highest_price * 0.995):
                            send_telegram(f"⚠️ *خروج مبكر!* بدأ الربح بالتناقص في {symbol}\nالسعر: {current:.4f}")
                            break
                        if current >= (price * 1.025):
                            send_telegram(f"✅ *هدف محقق!* {symbol}\nالسعر: {current:.4f}")
                            break
            except Exception as e:
                print(f"خطأ في {symbol}: {e}", flush=True)
        time.sleep(30)

# ==================== 🚀 التشغيل 🚀 ====================
if __name__ == "__main__":
    Thread(target=run_web).start()
    run_trading_bot()
