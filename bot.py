import os
import time
import requests
import pandas as pd
import ta
import ccxt
from flask import Flask
from threading import Thread

# ==================== 🔑 الإعدادات (تم إدخالها) 🔑 ====================
TELEGRAM_TOKEN = '8659171008:AAHIdMFNA4q7NsPZ5d9lgvgkpucAz9PLsOM'
CHAT_ID = '6750615824'
WATCHLIST = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT']

# روابط GIFs
GIF_NEW = "https://media.giphy.com/media/92wH9E5FNKtqje8vGP/giphy.gif"
GIF_TP1 = "https://media.giphy.com/media/YnkMc6mife5p6JAHFl/giphy.gif"
GIF_TP2 = "https://media.giphy.com/media/l0Ex6kAKAoFRsFh6M/giphy.gif"
GIF_SL  = "https://media.giphy.com/media/eKrgVyZ7ZVccg/giphy.gif"
GIF_EXIT = "https://media.giphy.com/media/3o7TKVUn7iM8FMEU24/giphy.gif"

# ==================== 🌐 نظام الويب 🌐 ====================
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is live!"

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# ==================== 🛠️ محرك التداول الاحترافي 🛠️ ====================
def run_trading_bot():
    exchange = ccxt.binance({'enableRateLimit': True})
    
    def send_telegram(gif_url, text):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAnimation"
            requests.post(url, json={"chat_id": CHAT_ID, "animation": gif_url, "caption": text, "parse_mode": "Markdown"})
        except Exception as e: print(f"خطأ في إرسال تليجرام: {e}")

    # رسالة نجاح الربط عند التشغيل
    send_telegram(GIF_NEW, "🚀 **تم التشغيل بنجاح!**\nالبوت متصل الآن ويراقب الأسواق.\nسأقوم بإبلاغك فور ظهور أي صفقة.")

    while True:
        for symbol in WATCHLIST:
            try:
                # جلب البيانات
                bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
                df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'close', 'v'])
                df['rsi'] = ta.momentum.rsi(df['close'], window=14)
                df['lb'] = ta.volatility.bollinger_lband(df['close'], window=20, window_dev=2)
                
                # شرط الدخول
                if df['rsi'].iloc[-1] < 30 and df['close'].iloc[-1] <= df['lb'].iloc[-1]:
                    entry = df['close'].iloc[-1]
                    sl = entry * 0.99
                    tp1 = entry * 1.01
                    tp2 = entry * 1.025
                    
                    send_telegram(GIF_NEW, f"🔔 *إشارة دخول: {symbol}*\n💵 السعر: {entry:.4f}\n🛑 SL: {sl:.4f}\n🎯 TP1: {tp1:.4f}\n🚀 TP2: {tp2:.4f}")
                    
                    highest_price = entry
                    tp1_hit = False
                    
                    # حلقة المراقبة
                    while True:
                        time.sleep(20)
                        current_price = exchange.fetch_ticker(symbol)['last']
                        
                        if current_price > highest_price: highest_price = current_price
                        
                        # الخروج عند تناقص الربح (0.5%)
                        if current_price < (highest_price * 0.995):
                            send_telegram(GIF_EXIT, f"⚠️ *خروج مبكر!* بدأ الربح بالتناقص في {symbol}\nالسعر: {current_price:.4f}\nالقمة: {highest_price:.4f}")
                            break
                        
                        if current_price >= tp1 and not tp1_hit:
                            send_telegram(GIF_TP1, f"🟨 *هدف أول!* {symbol}\nالسعر: {current_price:.4f}")
                            tp1_hit = True
                        
                        if current_price >= tp2:
                            send_telegram(GIF_TP2, f"🟩 *ربح كامل!* {symbol}\nالسعر: {current_price:.4f}")
                            break
                            
                        if current_price <= sl:
                            send_telegram(GIF_SL, f"🟥 *خسارة!* ضرب وقف الخسارة: {symbol}\nالسعر: {current_price:.4f}")
                            break
            except Exception as e: print(f"خطأ في {symbol}: {e}")
        time.sleep(30)

# ==================== 🚀 التشغيل المتزامن 🚀 ====================
if __name__ == "__main__":
    Thread(target=run_web).start()
    run_trading_bot()
