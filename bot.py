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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# ==================== 🛠️ محرك التداول 🛠️ ====================
def run_trading_bot():
    exchange = ccxt.binance({'enableRateLimit': True})
    
    def send_telegram(text):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"خطأ في الاتصال بتليجرام: {e}")

    # رسالة اختبارية فورية عند التشغيل
    print("🚀 البوت بدأ العمل الآن...")
    send_telegram("🤖 *تم تشغيل البوت بنجاح!* أنا الآن أراقب الأسواق.")

    while True:
        for symbol in WATCHLIST:
            try:
                # جلب البيانات
                bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
                df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'close', 'v'])
                df['rsi'] = ta.momentum.rsi(df['close'], window=14)
                df['lb'] = ta.volatility.bollinger_lband(df['close'], window=20, window_dev=2)
                
                rsi_val = df['rsi'].iloc[-1]
                price = df['close'].iloc[-1]
                
                # طباعة في السجلات للتأكد من أن البوت يعمل
                print(f"🔍 فحص {symbol}: RSI={rsi_val:.2f} | السعر={price:.2f}")
                
                # شرط الدخول
                if rsi_val < 30 and price <= df['lb'].iloc[-1]:
                    send_telegram(f"🔔 *إشارة دخول محتملة!* {symbol}\nالسعر: {price}\nRSI: {rsi_val:.2f}")
                    
                    # مراقبة الصفقة
                    highest_price = price
                    start_monitor = time.time()
                    while (time.time() - start_monitor) < 3600: # مراقبة ساعة
                        time.sleep(20)
                        current = exchange.fetch_ticker(symbol)['last']
                        if current > highest_price: highest_price = current
                        if current < (highest_price * 0.995):
                            send_telegram(f"⚠️ *خروج مبكر!* بدأ الربح بالتناقص في {symbol}\nالسعر الحالي: {current}")
                            break
                        if current >= (price * 1.025):
                            send_telegram(f"✅ *هدف محقق!* {symbol} عند {current}")
                            break
            except Exception as e:
                print(f"خطأ في {symbol}: {e}")
        time.sleep(30)

# ==================== 🚀 التشغيل 🚀 ====================
if __name__ == "__main__":
    Thread(target=run_web).start()
    run_trading_bot()
