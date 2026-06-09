# سطر تعريف الـ app لكي لا يتوقف السيرفر المجاني
app = lambda environ, start_response: start_response('200 OK', [('Content-Type', 'text/plain')]) or [b"Bot is Running!"]
import ccxt
import pandas as pd
import ta
import time
import requests

# ==================== 🔑 إعدادات الحساب والتنبيهات 🔑 ====================
TELEGRAM_TOKEN = '8659171008:AAHIdMFNA4q7NsPZ5d9lgvgkpucAz9PLsOM'
CHAT_ID = '6750615824'

# قائمة العملات المراد مراقبتها 
WATCHLIST = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'ADA/USDT', 'AVAX/USDT']

# اتصال عام ومفتوح لجلب البيانات من منصة بينانس (مستقر جداً وسريع)
data_exchange = ccxt.binance({'enableRateLimit': True})

# روابط الـ GIFs التفاعلية لكل حالة
GIF_NEW_SIGNAL = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExM3Y0Z3ZidmF5M3Mwb2p5YndmNzh0ZzN0Nmhnd3N6eXNmd3ZmdSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/92wH9E5FNKtqje8vGP/giphy.gif" 
GIF_TP1_HIT = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbmsydW9mNHc2YnByOHg1NmFubXoxNHB1dndnY2E4ZmsxeW5mYnV6dyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/YnkMc6mife5p6JAHFl/giphy.gif" 
GIF_TP2_HIT = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjEx3FpczBtMmt3Ymk1amwwYjByMXBtMzl5N2N6MmoxNnd2ZXRreXpkMiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l0Ex6kAKAoFRsFh6M/giphy.gif" 
GIF_SL_HIT = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjEx3N2M3p3NzZ1bWRhdnVwdjd3MTNxMWh3OTNhM2o4czRpdjVnN2I5OCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/eKrgVyZ7ZVccg/giphy.gif" 
GIF_TRAILING_EXIT = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExN3g1NTA0YWZ3Ym9tcDJndWhsd3dhaDJ5Nms5Yzg3ZHJhMnRmbG45ayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/acttIrNAHa652/giphy.gif" 
GIF_TIMEOUT_PROFIT = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNzh1ZWNxeW5pdzBxN2tmbXl4N3drbW1sc3ZwaWhreXZubDRudG5oOCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/9M5jK4GXfD5v2/giphy.gif" 
GIF_REASSURANCE = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNXdyNWg1a2ZkaXQxcHNxZzJrNmtnYjQ3dmw0eTFwdXphN3d3azJ4YyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ToMjGpKniGqRNLGBrhu/giphy.gif" 

# ==================== 📡 دالات المساعدة والتنبيهات المزيّنة ====================
def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload)
    except Exception as e: print(f"خطأ تيليجرام: {e}")

def send_telegram_gif(gif_url, caption_message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAnimation"
        payload = {"chat_id": CHAT_ID, "animation": gif_url, "caption": caption_message, "parse_mode": "Markdown"}
        requests.post(url, json=payload)
    except Exception as e: send_telegram_msg(caption_message)

def get_live_data(symbol):
    bars = data_exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['bollinger_low'] = ta.volatility.bollinger_lband(df['close'], window=20, window_dev=2)
    return df

# ==================== 🧠 نظام المراقبة اللحظي بمؤقت الساعة والسعر الرابح ====================
def monitor_signal_progress(symbol, entry_price, tp1, tp2, sl):
    highest_price_reached = entry_price
    tp1_hit = False
    start_time = time.time()
    
    print(f"🔄 بدأت المراقبة اللحظية لـ {symbol}...")
    
    while True:
        time.sleep(10) 
        try:
            ticker = data_exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            if current_price > highest_price_reached:
                highest_price_reached = current_price

            if current_price <= sl:
                msg = f"🟥 *💥 ضرب وقف الخسارة | SL HIT 💥*\n\n🪙 *العملة:* {symbol}\n📉 *سعر الخروج:* {current_price}\n\n🔄 _يعود البوت الآن لمسح السوق والبحث عن فرصة جديدة..._"
                send_telegram_gif(GIF_SL_HIT, msg)
                break

            if current_price >= tp1 and not tp1_hit:
                msg = f"🟨 *🎯 تحقق الهدف الأول | TP1 HIT 🎯*\n\n🪙 *العملة:* {symbol}\n💰 *سعر الهدف:* {tp1}\n\n💡 *إجراء يدوي:* خذ نصف أرباحك الآن وانقل الـ SL لسعر الدخول (`{entry_price}`) لتأمين صفقتك تماماً! ✅"
                send_telegram_gif(GIF_TP1_HIT, msg)
                sl = entry_price 
                tp1_hit = True

            if current_price >= tp2:
                msg = f"🟩 *🎉 صفقة ناجحة بالكامل | FULL TAKE PROFIT 🎉*\n\n🪙 *العملة:* {symbol}\n🚀 *سعر الهدف النهائي:* {tp2}\n💵 *الأرباح المحققة:* +2.5% 📈\n\n🔄 _جاري العودة لمراقبة بقية السوق..._"
                send_telegram_gif(GIF_TP2_HIT, msg)
                break

            profit_percent = ((current_price - entry_price) / entry_price) * 100
            drop_from_peak = ((highest_price_reached - current_price) / highest_price_reached) * 100
            
            if profit_percent > 0.8 and drop_from_peak > 0.35:
                msg = f"🟪 *⚠️ خروج احترازي | TRAILING EXIT ALERT ⚠️*\n\n🪙 *العملة:* {symbol}\n💵 *السعر الحالي:* {current_price}\n📉 *الهبوط من القمة:* -{drop_from_peak:.2f}%\n\n💡 *إجراء يدوي:* الأرباح بدأت تتناقص! يفضل إغلاق الصفقة يدويًا الآن لتأمين كاش أرباحك قبل الانعكاس 💰"
                send_telegram_gif(GIF_TRAILING_EXIT, msg)
                break
                
            elapsed_time = time.time() - start_time
            if elapsed_time >= 3600:
                if current_price > entry_price:
                    current_profit = ((current_price - entry_price) / entry_price) * 100
                    msg = f"🟦 *⏱️ انتهاء وقت الصفقة | TIME OUT ⏱️*\n\n🪙 *العملة:* {symbol}\n📈 *الحالة:* الصفقة رابحة حالياً بنسبة +{current_profit:.2f}%\n\n💡 *إجراء يدوي:* انتهت الساعة المخصصة. اخرج من الصفقة الآن يدويًا واكتفِ بالربح المحقق لفتح المجال لفرص أخرى 🔄"
                    send_telegram_gif(GIF_TIMEOUT_PROFIT, msg)
                    break 
                else:
                    start_time += 1800 

            if profit_percent > 0.4 and current_price == highest_price_reached:
                msg = f"🟩 *🔥 طمأنينة واستمرار | HOLDING STRONG 🔥*\n\n🪙 *العملة:* {symbol}\n🚀 *قمة جديدة:* {current_price}\n\n💪 *لا تستعجل، الاتجاه قوي وانتظر هنالك مزيد من الأرباح القادمة!*"
                send_telegram_gif(GIF_REASSURANCE, msg)
                time.sleep(40)
                
        except Exception as e: print(f"خطأ أثناء المراقبة: {e}")

# ==================== 🚀 الحلقة الأساسية لتشغيل البوت 🚀 ====================
print("📡 البوت السحابي المستقر يعمل الآن ويراقب الأسواق...")

while True:
    for symbol in WATCHLIST:
        try:
            df = get_live_data(symbol)
            current_price = df['close'].iloc[-1]
            rsi = df['rsi'].iloc[-1]
            bollinger_low = df['bollinger_low'].iloc[-1]
            
            print(f"يفحص الآن: {symbol} | RSI: {rsi:.1f} | السعر: {current_price}")
            
            if rsi < 30 and current_price <= bollinger_low:
                entry = current_price
                sl_price = entry * 0.99   
                tp1_price = entry * 1.01  
                tp2_price = entry * 1.025 
                
                signal_msg = (
                    f"🔔 *إشارة صفقة جديدة | NEW SIGNAL* 🔔\n\n"
                    f"🪙 *العملة:* `{symbol}`\n"
                    f"💵 *سعر الدخول المناسب:* `{entry}`\n\n"
                    f"🟩 *الهدف الأول (TP1):* `{tp1_price:.4f}`\n"
                    f"🚀 *الهدف الثاني (TP2):* `{tp2_price:.4f}`\n"
                    f"🛑 *وقف الخسارة (SL):* `{sl_price:.4f}`\n\n"
                    f"💡 _نفّذ الصفقة يدويًا على منصتك الآن، وسيتولى البوت إرسال التحديثات بالـ GIFs فوراً!_"
                )
                
                send_telegram_gif(GIF_NEW_SIGNAL, signal_msg)
                monitor_signal_progress(symbol, entry, tp1_price, tp2_price, sl_price)
                
        except Exception as e: print(f"خطأ فحص {symbol}: {e}")
        time.sleep(5) 
        
    print("🔄 تم إنهاء فحص القائمة، إعادة الفحص بعد قليل...")
    time.sleep(20)
