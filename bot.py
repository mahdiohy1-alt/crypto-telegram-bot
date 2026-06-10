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

# روابط GIFs
GIF_NEW = "https://media.giphy.com/media/92wH9E5FNKtqje8vGP/giphy.gif"
GIF_TP1 = "https://media.giphy.com/media/YnkMc6mife5p6JAHFl/giphy.gif"
GIF_TP2 = "https://media.giphy.com/media/l0Ex6kAKAoFRsFh6M/giphy.gif"
GIF_SL  = "https://media.giphy.com/media/eKrgVyZ7ZVccg/giphy.gif"
GIF_EXIT = "https://media.giphy.com/media/3o7TKVUn7iM8FMEU24/giphy.gif"

# ==================== 🌐 نظام الويب (لإرضاء Render) 🌐 ====================
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is live and running!"

def run_web():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# ==================== 🛠️ محرك التداول 🛠️ ====================
def run_trading_bot():
    exchange = ccxt.binance({'enableRateLimit': True})
    
    def send_telegram(gif_url, text):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAnimation"
            requests.post(url, json={"chat_id": CHAT_ID, "animation": gif_url, "caption": text, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"خطأ في إرسال تليجرام: {e}", flush=True)

    print("🚀 البوت بدأ العمل الآن...", flush=True)
    send_telegram(GIF_NEW, "🤖 *تم تشغيل البوت بنجاح!* أنا الآن أراقب الأسواق.")

    while True:
        for symbol in WATCHLIST:
            try:
                # سطر طباعة إجباري للتأكد من الفحص
                print(f"🔍 جاري فحص {symbol}...", flush=True)
                
                bars = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
                df = pd.DataFrame(bars, columns=['t', 'o', 'h', 'l', 'close', 'v'])
                df['rsi'] = ta.momentum.rsi(df['close'], window=14)
                df['lb'] = ta.volatility.bollinger_lband(df['close'], window=20, window_dev=2)
                
                rsi_val = df['rsi'].iloc[-1]
                price = df['close'].iloc[-1]
                
                # شرط الدخول
                if rsi_val < 30 and price <= df['lb'].iloc[-1]:
                    print(f"✅ تم العثور على فرصة في {symbol}!", flush=True)
                    entry = price
                    sl = entry * 0.99
                    tp1 = entry * 1.01
                    tp2 = entry * 1.025
                    
                    send_telegram(GIF_NEW, f"🔔 *إشارة دخول: {symbol}*\n💵 السعر: {entry:.4f}\n🛑 SL: {sl:.4f}\n🎯 TP1: {tp1:.4f}\n🚀 TP2: {tp2:.4f}")
                    
                    highest_price = entry
                    tp1_hit = False
                    start_monitor = time.time()
                    
                    # حلقة المراقبة (لمدة ساعة)
                    while (time.time() - start_monitor) < 3600:
                        time.sleep(20)
                        current = exchange.fetch_ticker(symbol)['last']
                        
                        if current > highest_price: highest_price = current
                        
                        if current < (highest_price * 0.995):
                            send_telegram(GIF_EXIT, f"⚠️ *خروج مبكر!* بدأ الربح بالتناقص في {symbol}\nالسعر: {current:.4f}")
                            break
                        if current >= tp1 and not tp1_hit:
                            send_telegram(GIF_TP1, f"🟨 *هدف أول!* {symbol}\nالسعر: {current:.4f}")
                            tp1_hit = True
                        if current >= tp2:
                            send_telegram(GIF_TP2, f"🟩 *ربح كامل!* {symbol}\nالسعر: {current:.4f}")
                            break
                        if current <= sl:
                            send_telegram(GIF_SL, f"🟥 *خسارة!* ضرب وقف الخسارة: {symbol}\nالسعر: {current:.4f}")
                            break
            except Exception as e:
                print(f"خطأ في فحص {symbol}: {e}", flush=True)
        time.sleep(30)

# ==================== 🚀 التشغيل المتزامن 🚀 ====================
if __name__ == "__main__":
    Thread(target=run_web).start()
    run_trading_bot()
