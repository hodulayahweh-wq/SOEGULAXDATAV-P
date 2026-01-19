import os, subprocess, sys, time, json, re, requests, cloudscraper, urllib3
from flask import Flask, render_template_string, request, redirect, session, jsonify
import telebot
from telebot import types
from threading import Thread
from datetime import datetime

# --- [ AYARLAR ] ---
TOKEN = '8225646361:AAH15joRkmpw4prforaRzUeCVZa6IiLu9h0' 
bot = telebot.TeleBot(TOKEN)
scraper = cloudscraper.create_scraper()
app = Flask(__name__)
app.secret_key = "lord_imparator_key_2024"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_PATH = "database.json"
START_TIME = datetime.now()

# --- [ VERİTABANI YÖNETİMİ ] ---
def load_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, "w") as f: 
            json.dump({
                "queries": {}, 
                "users": [], 
                "banned": [], 
                "logs": [],
                "maintenance": False,
                "broadcast_msg": "Sistem Aktif!"
            }, f)
    with open(DB_PATH, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_PATH, "w") as f: json.dump(data, f, indent=4)

# --- [ GÖMÜLÜ SABİT APİLER (ESKİ SİSTEM) ] ---
STATIC_APIS = {
    "iban": "https://lyranew.ct.ws/api/iban.php?iban={veri}",
    "gsmtc": "https://zyrdaware.xyz/api/gsmtc?auth=t.me/zyrdaware&gsm={veri}",
    "tcgsm": "https://zyrdaware.xyz/api/tcgsm?auth=t.me/zyrdaware&tc={veri}",
    "recete": "https://nabisorguapis.onrender.com/api/v1/eczane/recete-gecmisi?tc={veri}",
    "akbil": "https://nabisorguapis.onrender.com/api/v1/ulasim/istanbulkart-bakiye?tc={veri}"
}

# --- [ WEB PANEL HTML (15 ÖZELLİKLİ) ] ---
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Lord Ultimate Panel</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: 'Consolas', monospace; display: flex; }
        .sidebar { width: 250px; background: #111; height: 100vh; padding: 20px; border-right: 1px solid #00ff41; }
        .main { flex: 1; padding: 40px; overflow-y: auto; height: 100vh; }
        .card { border: 1px solid #00ff41; padding: 20px; margin-bottom: 20px; background: #0a0a0a; box-shadow: 0 0 10px #00ff4133; }
        input, select, textarea { background: #000; color: #00ff41; border: 1px solid #00ff41; padding: 10px; width: 90%; margin: 5px 0; }
        button { background: #00ff41; color: #000; border: none; padding: 10px 20px; cursor: pointer; font-weight: bold; width: 100%; }
        .nav-btn { background: none; color: #00ff41; text-align: left; border-bottom: 1px solid #222; margin-bottom: 10px; }
        .status-on { color: #00ff41; } .status-off { color: #ff0000; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>🔱 LORD V3</h2>
        <button class="nav-btn" onclick="location.href='/panel'">📊 İstatistikler</button>
        <button class="nav-btn" onclick="location.href='/panel?tab=sorgu'">➕ Sorgu Ekle/Sil</button>
        <button class="nav-btn" onclick="location.href='/panel?tab=users'">👥 Kullanıcı Yönetimi</button>
        <button class="nav-btn" onclick="location.href='/panel?tab=system'">⚙️ Sistem Ayarları</button>
        <button class="nav-btn" onclick="location.href='/panel?tab=broadcast'">📢 Toplu Mesaj</button>
        <hr>
        <p>Uptime: {{uptime}}</p>
    </div>
    <div class="main">
        {% if tab == 'stats' %}
        <div class="card">
            <h3>📊 Canlı İstatistikler</h3>
            <p>Toplam Kullanıcı: {{db.users|length}}</p>
            <p>Aktif Sorgu Sayısı: {{db.queries|length + 5}}</p>
            <p>Yasaklı Sayısı: {{db.banned|length}}</p>
            <p>Bakım Modu: <span class="{{ 'status-off' if db.maintenance else 'status-on' }}">{{ 'AKTİF' if db.maintenance else 'KAPALI' }}</span></p>
        </div>
        {% elif tab == 'sorgu' %}
        <div class="card">
            <h3>➕ Yeni Sorgu Enjekte Et</h3>
            <form action="/add" method="post">
                <input type="text" name="cmd" placeholder="Komut (örn: plaka)">
                <input type="text" name="api" placeholder="API (Veri: {veri})">
                <button>EKLE</button>
            </form>
            <h4>Aktif Dinamik Sorgular</h4>
            {% for c, a in db.queries.items() %}
            <p>🔹 /{{c}} <a href="/del/{{c}}" style="color:red">[SİL]</a></p>
            {% endfor %}
        </div>
        {% elif tab == 'system' %}
        <div class="card">
            <h3>⚙️ Sistem Kontrolü</h3>
            <form action="/toggle_maintenance" method="post">
                <button style="background:orange">BAKIM MODUNU DEĞİŞTİR</button>
            </form>
            <br>
            <form action="/update_broadcast" method="post">
                <input type="text" name="msg" placeholder="Start Mesajı">
                <button>START DUYURUSUNU GÜNCELLE</button>
            </form>
        </div>
        {% elif tab == 'broadcast' %}
        <div class="card">
            <h3>📢 Toplu Mesaj Gönder</h3>
            <form action="/send_all" method="post">
                <textarea name="text" rows="5" placeholder="Tüm kullanıcılara gidecek mesaj..."></textarea>
                <button>HERKESE GÖNDER</button>
            </form>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

# --- [ PANEL YOLLARI ] ---
@app.route('/')
def home():
    return '<h1>Lord Login</h1><form action="/login" method="post"><input type="password" name="pw"><button>Giriş</button></form>'

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('pw') == "lordadminv":
        session['admin'] = True
        return redirect('/panel')
    return "Hata!"

@app.route('/panel')
def panel():
    if not session.get('admin'): return redirect('/')
    tab = request.args.get('tab', 'stats')
    db = load_db()
    uptime = str(datetime.now() - START_TIME).split('.')[0]
    return render_template_string(ADMIN_HTML, db=db, tab=tab, uptime=uptime)

@app.route('/add', methods=['POST'])
def add():
    db = load_db()
    db['queries'][request.form.get('cmd').lower()] = request.form.get('api')
    save_db(db)
    return redirect('/panel?tab=sorgu')

@app.route('/send_all', methods=['POST'])
def send_all():
    db = load_db()
    text = request.form.get('text')
    for u in db['users']:
        try: bot.send_message(u, f"📢 *ADMIN DUYURUSU*\n\n{text}", parse_mode="Markdown")
        except: pass
    return redirect('/panel?tab=broadcast')

@app.route('/toggle_maintenance', methods=['POST'])
def toggle():
    db = load_db()
    db['maintenance'] = not db['maintenance']
    save_db(db)
    return redirect('/panel?tab=system')

# --- [ BOT MANTIĞI ] ---
def get_main_keyboard(db):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    # Statik Butonlar
    markup.add("🔍 IBAN", "🔍 GSM-TC", "🔍 TC-GSM")
    # Dinamik Butonlar
    for cmd in db['queries'].keys():
        markup.add(f"🔍 {cmd.upper()}")
    markup.add("👤 Profil", "🆘 Destek")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    db = load_db()
    uid = str(message.chat.id)
    if uid not in db['users']:
        db['users'].append(uid)
        save_db(db)
    
    if db['maintenance']:
        return bot.send_message(uid, "⚠️ Sistem şu an bakımda sevgilim, birazdan döneceğiz.")

    bot.send_message(uid, f"🔱 *LORD SYSTEM V3 ELITE*\n\n{db['broadcast_msg']}", 
                     reply_markup=get_main_keyboard(db), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text.startswith("🔍 "))
def handle_query(message):
    cmd_raw = message.text.replace("🔍 ", "").lower().replace("-", "")
    db = load_db()
    
    # URL Seçimi: Statik mi Dinamik mi?
    if cmd_raw in STATIC_APIS:
        api_url = STATIC_APIS[cmd_raw]
    elif cmd_raw in db['queries']:
        api_url = db['queries'][cmd_raw]
    else:
        return bot.reply_to(message, "❌ Komut bulunamadı.")

    msg = bot.reply_to(message, f"📌 Lütfen `{cmd_raw.upper()}` için veriyi giriniz:")
    bot.register_next_step_handler(msg, lambda m: execute(m, api_url, cmd_raw))

def execute(message, api_url, cmd):
    val = message.text.strip()
    target = api_url.replace("{veri}", val)
    proc = bot.send_message(message.chat.id, "⚡ `Bağlantı Kuruluyor...`", parse_mode="Markdown")
    try:
        res = scraper.get(target, timeout=20, verify=False).text
        clean = re.sub(r'https?://\S+|t\.me/\S+|@[a-zA-Z0-9_]+', '', res).strip()
        bot.edit_message_text(f"💎 *{cmd.upper()} SONUÇ*\n\n`{clean if clean else 'Sonuç bulunamadı.'}`", 
                             message.chat.id, proc.message_id, parse_mode="Markdown")
    except:
        bot.edit_message_text("❌ API Duvarı aşılamadı.", message.chat.id, proc.message_id)

if __name__ == "__main__":
    Thread(target=lambda: bot.infinity_polling()).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
