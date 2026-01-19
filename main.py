import os, subprocess, sys, time, json, re, requests, cloudscraper, urllib3
from flask import Flask, render_template_string, request, redirect, session
import telebot
from telebot import types
from threading import Thread
from datetime import datetime

# --- [ AYARLAR ] ---
TOKEN = '8225646361:AAH15joRkmpw4prforaRzUeCVZa6IiLu9h0' 
bot = telebot.TeleBot(TOKEN)
# Cloudscraper'ı daha agresif konfigüre ettik
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
app = Flask(__name__)
app.secret_key = "lord_ultimate_sovereign"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_PATH = "database.json"
START_TIME = datetime.now()

# --- [ GELİŞMİŞ VERİTABANI ] ---
def load_db():
    if not os.path.exists(DB_PATH):
        default_data = {
            "queries": {
                "iban": "https://lyranew.ct.ws/api/iban.php?iban={veri}",
                "gsmtc": "https://zyrdaware.xyz/api/gsmtc?auth=t.me/zyrdaware&gsm={veri}",
                "tcgsm": "https://zyrdaware.xyz/api/tcgsm?auth=t.me/zyrdaware&tc={veri}",
                "akbil": "https://nabisorguapis.onrender.com/api/v1/ulasim/istanbulkart-bakiye?tc={veri}"
            },
            "users": [], "banned": [], "maintenance": False, "welcome_msg": "Lord System Aktif!", "total_queries": 0
        }
        with open(DB_PATH, "w") as f: json.dump(default_data, f)
    with open(DB_PATH, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_PATH, "w") as f: json.dump(data, f, indent=4)

# --- [ 16 ÖZELLİKLİ ELİT PANEL ] ---
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Lord Sovereign Panel</title>
    <style>
        body { background: #000; color: #0f0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; display: flex; }
        .sidebar { width: 280px; background: #0a0a0a; border-right: 1px solid #0f0; height: 100vh; padding: 20px; box-sizing: border-box; }
        .content { flex: 1; padding: 40px; height: 100vh; overflow-y: auto; }
        .card { background: #111; border: 1px solid #0f0; padding: 20px; margin-bottom: 20px; border-radius: 5px; box-shadow: 0 0 10px #0f03; }
        input, select, textarea { width: 100%; background: #000; border: 1px solid #0f0; color: #0f0; padding: 10px; margin: 10px 0; box-sizing: border-box; }
        button { width: 100%; background: #0f0; color: #000; border: none; padding: 12px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        button:hover { background: #0c0; }
        .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
        .nav-link { color: #0f0; text-decoration: none; display: block; padding: 15px; border-bottom: 1px solid #222; }
        .nav-link:hover { background: #111; }
        .badge { background: #0f0; color: #000; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 style="text-align:center;">🔱 SOVEREIGN V3</h2>
        <a href="/panel?tab=stats" class="nav-link">📊 Genel İstatistikler</a>
        <a href="/panel?tab=queries" class="nav-link">🔍 Sorgu Yönetimi (Hepsi)</a>
        <a href="/panel?tab=users" class="nav-link">👥 Kullanıcı Listesi</a>
        <a href="/panel?tab=broadcast" class="nav-link">📢 Global Duyuru</a>
        <a href="/panel?tab=settings" class="nav-link">⚙️ Sistem Ayarları</a>
        <a href="/panel?tab=logs" class="nav-link">📝 İşlem Logları</a>
        <div style="margin-top:20px; font-size: 12px; color: #888;">UPTIME: {{uptime}}</div>
    </div>
    <div class="content">
        {% if tab == 'stats' %}
            <div class="grid">
                <div class="card"><h3>Kullanıcılar</h3><h1>{{db.users|length}}</h1></div>
                <div class="card"><h3>Toplam İşlem</h3><h1>{{db.total_queries}}</h1></div>
                <div class="card"><h3>Aktif Modüller</h3><h1>{{db.queries|length}}</h1></div>
                <div class="card"><h3>Bakım Modu</h3><h1>{{ 'AÇIK' if db.maintenance else 'KAPALI' }}</h1></div>
            </div>
        {% elif tab == 'queries' %}
            <div class="card">
                <h3>🛠 Sorgu Ekle / Güncelle</h3>
                <form action="/add_q" method="post">
                    <input type="text" name="name" placeholder="Komut İsmi (örn: iban)" required>
                    <input type="text" name="url" placeholder="API URL (Veri: {veri})" required>
                    <button>SİSTEME ENJEKTE ET</button>
                </form>
            </div>
            <div class="card">
                <h3>📑 Mevcut Tüm Sorgular (Silinebilir)</h3>
                {% for n, u in db.queries.items() %}
                <div style="display:flex; justify-content:space-between; border-bottom: 1px solid #222; padding:10px;">
                    <span><b>/{{n}}</b> - {{u[:50]}}...</span>
                    <a href="/del_q/{{n}}" style="color:red; text-decoration:none;">[KALDIR]</a>
                </div>
                {% endfor %}
            </div>
        {% elif tab == 'broadcast' %}
            <div class="card">
                <h3>📢 Global Broadcast</h3>
                <form action="/broadcast" method="post">
                    <textarea name="msg" rows="5" placeholder="Tüm kullanıcılara gidecek mesaj..."></textarea>
                    <button>HERKESE GÖNDER</button>
                </form>
            </div>
        {% elif tab == 'settings' %}
            <div class="card">
                <h3>⚙️ Sistem Kontrol Merkezi</h3>
                <form action="/toggle_m" method="post"><button style="background:orange">BAKIM MODUNU DEĞİŞTİR</button></form>
                <form action="/set_msg" method="post">
                    <input type="text" name="msg" placeholder="Start Karşılama Mesajı">
                    <button>GÜNCELLE</button>
                </form>
                <button onclick="location.href='/logout'" style="background:red; color:white; margin-top:20px;">PANELİ KİLİTLE</button>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

# --- [ PANEL YOLLARI ] ---
@app.route('/')
def login_page(): return '<h1>Lord Access</h1><form action="/login" method="post"><input type="password" name="p"><button>Giriş</button></form>'

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('p') == "lordadminv":
        session['admin'] = True
        return redirect('/panel')
    return "Reddedildi."

@app.route('/panel')
def panel():
    if not session.get('admin'): return redirect('/')
    db = load_db()
    uptime = str(datetime.now() - START_TIME).split('.')[0]
    return render_template_string(ADMIN_HTML, db=db, tab=request.args.get('tab', 'stats'), uptime=uptime)

@app.route('/add_q', methods=['POST'])
def add_q():
    db = load_db()
    db['queries'][request.form.get('name').lower()] = request.form.get('url')
    save_db(db)
    return redirect('/panel?tab=queries')

@app.route('/del_q/<name>')
def del_q(name):
    db = load_db()
    if name in db['queries']: del db['queries'][name]
    save_db(db)
    return redirect('/panel?tab=queries')

# --- [ BOT MANTIĞI ] ---
def build_keyboard(db):
    m = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    # Tüm sorguları dinamik olarak buton yapıyoruz
    btns = [f"🔍 {n.upper()}" for n in db['queries'].keys()]
    m.add(*btns)
    m.add("👤 PROFiL", "🆘 DESTEK")
    return m

@bot.message_handler(commands=['start'])
def start(message):
    db = load_db()
    uid = str(message.chat.id)
    if uid not in db['users']: db['users'].append(uid); save_db(db)
    
    if db['maintenance']: return bot.send_message(uid, "🚧 *SİSTEM BAKIMDA...*", parse_mode="Markdown")
    
    bot.send_message(uid, f"🔱 *{db['welcome_msg']}*\n\nAlttaki butonları veya komutları (örn: `/iban ...`) kullanabilirsin.", 
                     reply_markup=build_keyboard(db), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text.startswith("🔍 "))
def btn_handler(message):
    cmd_name = message.text.replace("🔍 ", "").lower()
    db = load_db()
    if cmd_name in db['queries']:
        msg = bot.reply_to(message, f"📥 Lütfen `{cmd_name.upper()}` verisini girin:")
        bot.register_next_step_handler(msg, lambda m: process_query(m, db['queries'][cmd_name], cmd_name))

@bot.message_handler(commands=load_db()['queries'].keys())
def cmd_handler(message):
    cmd_name = message.text.split()[0][1:].lower()
    val = " ".join(message.text.split()[1:])
    db = load_db()
    if not val: return bot.reply_to(message, f"❌ Kullanım: `/{cmd_name} veri`")
    process_query(message, db['queries'][cmd_name], cmd_name, val)

def process_query(message, api_url, name, val=None):
    if val is None: val = message.text.strip()
    db = load_db()
    target = api_url.replace("{veri}", val)
    status_msg = bot.send_message(message.chat.id, "🛰 `Siber Kalkanlar Aşılıyor...`", parse_mode="Markdown")
    
    try:
        # Daha güçlü bypass için headers enjeksiyonu
        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
        res = scraper.get(target, headers=h, timeout=25, verify=False).text
        
        # Eğer hala JS kalkanı gelirse (ct.ws hatası)
        if "toNumbers" in res or "<html>" in res:
            bot.edit_message_text("❌ *HATA:* API Duvarı (JS-Challenge) aşılamadı. Lütfen farklı bir API kullanın.", message.chat.id, status_msg.message_id, parse_mode="Markdown")
        else:
            clean = re.sub(r'https?://\S+|t\.me/\S+|@[a-zA-Z0-9_]+', '', res).strip()
            db['total_queries'] += 1; save_db(db)
            bot.edit_message_text(f"💎 *{name.upper()} SONUÇ*\n\n`{clean if clean else 'Veri bulunamadı.'}`", message.chat.id, status_msg.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ *SİSTEM HATASI:* API yanıt vermiyor.", message.chat.id, status_msg.message_id)

if __name__ == "__main__":
    Thread(target=lambda: bot.infinity_polling()).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
