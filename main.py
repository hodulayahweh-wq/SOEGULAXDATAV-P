import os, json, re, requests, cloudscraper, urllib3
from flask import Flask, render_template_string, request, redirect, session
import telebot
from telebot import types
from threading import Thread
from datetime import datetime

# --- [ AYARLAR ] ---
TOKEN = '8225646361:AAG7Kuwc11t4Ld9NNO-uWO1pT_ZP2VdLYyc'
ADMIN_PW = 'lordadminv'
bot = telebot.TeleBot(TOKEN)
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
app = Flask(__name__)
app.secret_key = "lord_supremacy_ultra"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_PATH = "database.json"
START_TIME = datetime.now()

# --- [ GELİŞMİŞ VERİTABANI ] ---
def load_db():
    if not os.path.exists(DB_PATH):
        default_data = {
            "queries": {
                "iban": "https://lyranew.ct.ws/api/iban.php?iban={veri}",
                "gsmtc": "https://zyrdaware.xyz/api/gsmtc?auth=t.me/zyrdaware&gsm={veri}"
            },
            "users": [], "banned": [], "maintenance": False, 
            "welcome_msg": "🔱 Lord System V4 Hoş Geldiniz!", 
            "total_queries": 0, "admin_logs": []
        }
        with open(DB_PATH, "w") as f: json.dump(default_data, f)
    with open(DB_PATH, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_PATH, "w") as f: json.dump(data, f, indent=4)

def add_log(action):
    db = load_db()
    now = datetime.now().strftime("%H:%M:%S")
    db['admin_logs'].insert(0, f"[{now}] {action}")
    if len(db['admin_logs']) > 50: db['admin_logs'].pop()
    save_db(db)

# --- [ 20 ÖZELLİKLİ PANEL HTML ] ---
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Lord Supremacy V4</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: 'Consolas', monospace; margin: 0; display: flex; }
        .sidebar { width: 300px; background: #000; border-right: 2px solid #00ff41; height: 100vh; padding: 20px; }
        .content { flex: 1; padding: 30px; height: 100vh; overflow-y: auto; }
        .card { background: #0a0a0a; border: 1px solid #00ff41; padding: 15px; margin: 10px; border-radius: 5px; box-shadow: 0 0 15px #00ff4122; }
        input, button, textarea { width: 100%; background: #000; border: 1px solid #00ff41; color: #00ff41; padding: 10px; margin: 5px 0; }
        button { background: #00ff41; color: #000; cursor: pointer; font-weight: bold; transition: 0.3s; }
        button:hover { background: #008f11; color: #fff; }
        .nav-link { color: #00ff41; text-decoration: none; display: block; padding: 12px; border-bottom: 1px solid #111; font-size: 14px; }
        .nav-link:hover { background: #00ff4111; }
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .log-box { font-size: 12px; color: #888; height: 200px; overflow-y: scroll; border: 1px solid #222; padding: 5px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2 style="text-align:center; color:#fff; text-shadow: 0 0 10px #00ff41;">SUPREMACY V4</h2>
        <a href="/panel?tab=dash" class="nav-link">🏠 Dashboard (1-4)</a>
        <a href="/panel?tab=api" class="nav-link">⚙️ API Yönetimi (5-8)</a>
        <a href="/panel?tab=user" class="nav-link">👥 Kullanıcı Kontrol (9-12)</a>
        <a href="/panel?tab=msg" class="nav-link">📢 Duyuru & Bot (13-16)</a>
        <a href="/panel?tab=sys" class="nav-link">💻 Sistem & Güvenlik (17-20)</a>
        <hr border="1">
        <div class="log-box">{% for log in db.admin_logs %}{{log}}<br>{% endfor %}</div>
    </div>
    <div class="content">
        {% if tab == 'dash' %}
        <div class="grid">
            <div class="card"><h3>1. Kullanıcı</h3>{{db.users|length}}</div>
            <div class="card"><h3>2. İşlem</h3>{{db.total_queries}}</div>
            <div class="card"><h3>3. API Sayısı</h3>{{db.queries|length}}</div>
            <div class="card"><h3>4. Uptime</h3>{{uptime}}</div>
        </div>
        {% elif tab == 'api' %}
        <div class="card">
            <h3>5. Yeni Sorgu Ekle</h3>
            <form action="/add_q" method="post">
                <input name="n" placeholder="Komut (plaka)" required>
                <input name="u" placeholder="URL ({veri})" required>
                <button>6. SİSTEME EKLE</button>
            </form>
        </div>
        <div class="card">
            <h3>7. Tüm Sorgular (Silme & Düzenleme)</h3>
            {% for n, u in db.queries.items() %}
            <p>🔹 /{{n}} <a href="/del_q/{{n}}" style="color:red; float:right;">[8. SİL]</a></p>
            {% endfor %}
        </div>
        {% elif tab == 'user' %}
        <div class="card"><h3>9. Kullanıcı Listesi</h3><textarea rows="5">{% for u in db.users %}{{u}}&#10;{% endfor %}</textarea></div>
        <div class="card"><h3>10. Banla</h3><input placeholder="ID Girin"><button>11. YASAKLA</button></div>
        <div class="card"><h3>12. Veritabanını Temizle</h3><button style="background:red">TÜMÜNÜ SIFIRLA</button></div>
        {% elif tab == 'msg' %}
        <div class="card"><h3>13. Toplu Mesaj</h3><form action="/bc" method="post"><textarea name="m"></textarea><button>14. GÖNDER</button></form></div>
        <div class="card"><h3>15. Karşılama Mesajı</h3><form action="/w" method="post"><input name="m"><button>16. GÜNCELLE</button></form></div>
        {% elif tab == 'sys' %}
        <div class="card"><h3>17. Bakım Modu</h3><form action="/tm" method="post"><button>18. AÇ/KAPAT</button></form></div>
        <div class="card"><h3>19. Botu Yeniden Başlat</h3><button onclick="alert('Render üzerinden manuel restart gerek.')">20. RESTART</button></div>
        {% endif %}
    </div>
</body>
</html>
"""

# --- [ PANEL YOLLARI ] ---
@app.route('/')
def lp(): return '<body style="background:#000;color:#0f0;"><form action="/l" method="post">Pass: <input name="p" type="password"><button>Enter</button></form></body>'

@app.route('/l', methods=['POST'])
def login():
    if request.form.get('p') == ADMIN_PW: session['admin'] = True; return redirect('/panel')
    return "X"

@app.route('/panel')
def panel():
    if not session.get('admin'): return redirect('/')
    db = load_db()
    uptime = str(datetime.now() - START_TIME).split('.')[0]
    return render_template_string(ADMIN_HTML, db=db, tab=request.args.get('tab', 'dash'), uptime=uptime)

@app.route('/add_q', methods=['POST'])
def add_q():
    db = load_db(); name = request.form.get('n').lower()
    db['queries'][name] = request.form.get('u')
    save_db(db); add_log(f"Sorgu Eklendi: {name}"); return redirect('/panel?tab=api')

@app.route('/del_q/<name>')
def del_q(name):
    db = load_db()
    if name in db['queries']:
        del db['queries'][name]
        save_db(db); add_log(f"Sorgu Silindi: {name}")
    return redirect('/panel?tab=api')

@app.route('/bc', methods=['POST'])
def bc():
    db = load_db(); msg = request.form.get('m')
    for u in db['users']:
        try: bot.send_message(u, f"📢 *DUYURU*\n\n{msg}", parse_mode="Markdown")
        except: pass
    add_log("Toplu Mesaj Gönderildi"); return redirect('/panel?tab=msg')

@app.route('/tm', methods=['POST'])
def tm():
    db = load_db(); db['maintenance'] = not db['maintenance']
    save_db(db); add_log("Bakım Modu Değişti"); return redirect('/panel?tab=sys')

# --- [ BOT MANTIĞI ] ---
def get_kb(db):
    m = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    m.add(*[f"🔍 {n.upper()}" for n in db['queries'].keys()])
    m.add("👤 PROFiL", "🆘 DESTEK")
    return m

@bot.message_handler(commands=['start'])
def start(message):
    db = load_db(); uid = str(message.chat.id)
    if uid not in db['users']: db['users'].append(uid); save_db(db)
    if db['maintenance']: return bot.send_message(uid, "🚧 Bakımdayız.")
    bot.send_message(uid, f"🔱 *{db['welcome_msg']}*", reply_markup=get_kb(db), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "👤 PROFiL")
def profile(message):
    bot.reply_to(message, f"👤 *Profil Bilgileri*\n\nID: `{message.chat.id}`\nDurum: Aktif Kullanıcı", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🆘 DESTEK")
def support(message):
    bot.reply_to(message, "🆘 *Destek Merkezi*\n\nSorunlarınızı admin panel üzerinden duyuruları takip ederek çözebilirsiniz.", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text.startswith("🔍 "))
def btn_query(message):
    name = message.text.replace("🔍 ", "").lower()
    db = load_db()
    if name in db['queries']:
        msg = bot.reply_to(message, f"✍️ `{name.upper()}` için veri girin:")
        bot.register_next_step_handler(msg, lambda m: run_api(m, db['queries'][name], name))

def run_api(message, url, name):
    val = message.text.strip()
    db = load_db()
    st_msg = bot.send_message(message.chat.id, "⚡ `Veriler Çekiliyor...`", parse_mode="Markdown")
    try:
        # User-Agent ve Timeout güçlendirildi
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        response = scraper.get(url.replace("{veri}", val), headers=headers, timeout=30)
        
        # Boş veri veya hata kontrolü
        res_text = response.text.strip()
        if not res_text or "<html>" in res_text:
            bot.edit_message_text("❌ API şu an boş döndü veya kalkanı geçemedi.", message.chat.id, st_msg.message_id)
        else:
            clean = re.sub(r'https?://\S+|t\.me/\S+', '', res_text)
            db['total_queries'] += 1; save_db(db)
            bot.edit_message_text(f"💎 *{name.upper()} SONUÇ*\n\n`{clean[:3500]}`", message.chat.id, st_msg.message_id, parse_mode="Markdown")
    except:
        bot.edit_message_text("❌ Zaman aşımı! API yanıt vermedi.", message.chat.id, st_msg.message_id)

if __name__ == "__main__":
    Thread(target=lambda: bot.infinity_polling()).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
un(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
