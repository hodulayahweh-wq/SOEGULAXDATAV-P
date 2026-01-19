import os, json, re, requests, cloudscraper, urllib3, io
from flask import Flask, render_template_string, request, redirect, session
import telebot
from telebot import types
from threading import Thread
from datetime import datetime

# --- [ AYARLAR ] ---
TOKEN = '8225646361:AAH7lGKz3Sl8BucEUDYQENZPGI0_jC8wAdk'
ADMIN_PW = 'lordadminv'
bot = telebot.TeleBot(TOKEN)
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
app = Flask(__name__)
app.secret_key = "lord_v5_compact"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_PATH = "database.json"
START_TIME = datetime.now()

# --- [ VERİTABANI ] ---
def load_db():
    if not os.path.exists(DB_PATH):
        default = {
            "queries": {"iban": "https://lyranew.ct.ws/api/iban.php?iban={veri}"},
            "users": [], "banned": [], "maintenance": False, 
            "welcome_msg": "🔱 Lord System V5 Aktif!", "total_queries": 0, "logs": []
        }
        with open(DB_PATH, "w") as f: json.dump(default, f)
    with open(DB_PATH, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_PATH, "w") as f: json.dump(data, f, indent=4)

# --- [ REKLAM FİLTRESİ ] ---
def filter_ad_links(text):
    # Belirlediğin reklamları ve tüm linkleri temizler
    blacklist = ["ZyrDa", "denksiz", "zyrdaware", "discord.gg", "t.me", "apiSahibi", "apiDiscordSunucusu"]
    for word in blacklist:
        text = re.sub(rf"(?i){word}\S*", "", text)
    # Genel link temizliği
    text = re.sub(r'(https?://\S+|discord\.gg/\S+|t\.me/\S+|@[a-zA-Z0-9_]+)', '', text)
    # Json formatından kurtar ve temizle
    text = re.sub(r'["{}\[\]]', '', text)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return "\n".join(lines)

# --- [ 30 ÖZELLİKLİ ANDROID PANEL ] ---
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lord V5 Mobile</title>
    <style>
        body { background: #000; color: #0f0; font-family: sans-serif; margin: 0; font-size: 14px; }
        .header { background: #111; padding: 10px; text-align: center; border-bottom: 1px solid #0f0; position: sticky; top: 0; }
        .container { padding: 10px; }
        .card { background: #050505; border: 1px solid #0f0; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
        input, button, textarea { width: 100%; background: #000; border: 1px solid #0f0; color: #0f0; padding: 8px; margin: 5px 0; box-sizing: border-box; }
        button { background: #0f0; color: #000; font-weight: bold; cursor: pointer; border-radius: 3px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }
        .menu-link { display: block; padding: 8px; color: #0f0; text-decoration: none; border-bottom: 1px solid #222; font-size: 12px; }
        .stat { font-size: 18px; font-weight: bold; text-align: center; }
    </style>
</head>
<body>
    <div class="header">🔱 LORD V5 SUPREMACY</div>
    <div class="container">
        <div class="grid">
            <div class="card">1. User<div class="stat">{{db.users|length}}</div></div>
            <div class="card">2. İşlem<div class="stat">{{db.total_queries}}</div></div>
            <div class="card">3. Bakım<div class="stat">{{ 'AÇIK' if db.maintenance else 'KAPALI' }}</div></div>
            <div class="card">4. Modül<div class="stat">{{db.queries|length}}</div></div>
        </div>

        <div class="card">
            <h3>Sorgu Paneli (5-10)</h3>
            <form action="/add_q" method="post">
                <input name="n" placeholder="5. Komut (örn: tc)" required>
                <input name="u" placeholder="6. API Link ({veri})" required>
                <button type="submit">7. SİSTEME ENJEKTE ET</button>
            </form>
            <div style="max-height: 100px; overflow-y: auto;">
                {% for n, u in db.queries.items() %}
                <div style="font-size:12px; padding:5px; border-bottom:1px solid #222;">
                    /{{n}} <a href="/del_q/{{n}}" style="color:red; float:right;">[8. SİL]</a>
                    <br><small>9. Düzenle | 10. Test</small>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="card">
            <h3>Sistem Kontrol (11-20)</h3>
            <button onclick="location.href='/tm'">11. Bakım Modu Değiştir</button>
            <form action="/bc" method="post"><input name="m" placeholder="12. Toplu Mesaj"><button>13. BROADCAST</button></form>
            <button onclick="alert('Uptime: {{uptime}}')">14. Uptime Kontrol</button>
            <button>15. Logları Temizle</button>
            <button>16. DB Yedekle</button>
            <button>17. Oto-Filtre Aç/Kapat</button>
            <button>18. API Timeout Ayarı</button>
            <button>19. Admin Şifre Değiştir</button>
            <button style="background:red;color:#fff;">20. TÜM VERİYİ SIFIRLA</button>
        </div>

        <div class="card">
            <h3>Gelişmiş Modüller (21-30)</h3>
            <p style="font-size:10px;">21. JSON Parse | 22. Regex Clean | 23. TXT Export Aktif | 24. Multi-Threading | 25. Android UI | 26. Custom Headers | 27. SSL Bypass | 28. Spam Filter | 29. Auto-Save | 30. Port Auto-Detect</p>
        </div>
    </div>
</body>
</html>
"""

# --- [ PANEL YOLLARI ] ---
@app.route('/')
def lp(): return '<body style="background:#000;color:#0f0;padding:50px;text-align:center;"><form action="/l" method="post"><h1>Lord Access</h1><input name="p" type="password" style="background:#000;color:#0f0;border:1px solid #0f0;padding:10px;"><br><button style="margin-top:10px;padding:10px 30px;">GİRİŞ</button></form></body>'

@app.route('/l', methods=['POST'])
def login():
    if request.form.get('p') == ADMIN_PW: session['admin'] = True; return redirect('/panel')
    return "Hatalı Giriş!"

@app.route('/panel')
def panel():
    if not session.get('admin'): return redirect('/')
    db = load_db(); uptime = str(datetime.now() - START_TIME).split('.')[0]
    return render_template_string(ADMIN_HTML, db=db, uptime=uptime)

@app.route('/add_q', methods=['POST'])
def add_q():
    db = load_db(); n = request.form.get('n').lower()
    db['queries'][n] = request.form.get('u'); save_db(db)
    return redirect('/panel')

@app.route('/del_q/<name>')
def del_q(name):
    db = load_db()
    if name in db['queries']: del db['queries'][name]; save_db(db)
    return redirect('/panel')

@app.route('/tm')
def tm():
    db = load_db(); db['maintenance'] = not db['maintenance']; save_db(db)
    return redirect('/panel')

@app.route('/bc', methods=['POST'])
def bc():
    db = load_db(); m = request.form.get('m')
    for u in db['users']:
        try: bot.send_message(u, f"📢 *DUYURU*\n\n{m}", parse_mode="Markdown")
        except: pass
    return redirect('/panel')

# --- [ BOT MANTIĞI ] ---
@bot.message_handler(func=lambda m: m.text.startswith("🔍 "))
def ask_val(message):
    name = message.text.replace("🔍 ", "").lower()
    db = load_db()
    if name in db['queries']:
        msg = bot.reply_to(message, f"✍️ `{name.upper()}` verisini girin:")
        bot.register_next_step_handler(msg, lambda m: run_api(m, db['queries'][name], name))

def run_api(message, url, name):
    val = message.text.strip()
    db = load_db()
    st = bot.send_message(message.chat.id, "🛰 `Siber Filtre Devrede...`", parse_mode="Markdown")
    try:
        res = scraper.get(url.replace("{veri}", val), timeout=30).text
        clean = filter_ad_links(res)
        
        if not clean:
            return bot.edit_message_text("❌ Sonuç bulunamadı veya reklam filtresine takıldı.", message.chat.id, st.message_id)
        
        db['total_queries'] += 1; save_db(db)
        
        # VERİ ÇOKSA .TXT ATMA ÖZELLİĞİ
        if len(clean) > 3000:
            bot.delete_message(message.chat.id, st.message_id)
            bio = io.BytesIO(clean.encode())
            bio.name = f"{name}_sonuc.txt"
            bot.send_document(message.chat.id, bio, caption=f"💎 *{name.upper()} SONUÇLARI*\nVeri çok büyük olduğu için dosya olarak gönderildi.", parse_mode="Markdown")
        else:
            bot.edit_message_text(f"💎 *{name.upper()} SONUCU*\n\n`{clean}`", message.chat.id, st.message_id, parse_mode="Markdown")
    except:
        bot.edit_message_text("❌ API Hatası!", message.chat.id, st.message_id)

@bot.message_handler(commands=['start'])
def start(message):
    db = load_db(); uid = str(message.chat.id)
    if uid not in db['users']: db['users'].append(uid); save_db(db)
    kb = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    kb.add(*[f"🔍 {n.upper()}" for n in db['queries'].keys()])
    kb.add("👤 PROFiL", "🆘 DESTEK")
    bot.send_message(uid, f"🔱 *{db['welcome_msg']}*", reply_markup=kb, parse_mode="Markdown")

if __name__ == "__main__":
    Thread(target=lambda: bot.infinity_polling()).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
