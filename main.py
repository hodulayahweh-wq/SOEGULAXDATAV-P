import os, subprocess, sys, time, json, re, requests, cloudscraper, urllib3
from flask import Flask, render_template, request, redirect, session
import telebot
from telebot import types
from threading import Thread

# --- [ OTO KURULUM ] ---
def setup():
    packages = ['pyTelegramBotAPI', 'requests', 'cloudscraper', 'flask', 'urllib3', 'gunicorn']
    for p in packages:
        try: __import__(p.replace('pyTelegramBotAPI', 'telebot'))
        except: subprocess.check_call([sys.executable, "-m", "pip", "install", p])

setup()

# --- [ AYARLAR ] ---
TOKEN = '8352899544:AAHDjjDUau5i3klnSwjOd4F8B3OgoT6uARo' # BotFather'dan aldığın token
bot = telebot.TeleBot(TOKEN)
scraper = cloudscraper.create_scraper()
app = Flask(__name__)
app.secret_key = "lord_secret_key"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DB_FILE = "database.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f: json.dump({"queries": {}, "users": []}, f)

def load_db():
    with open(DB_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

# --- [ BOT MANTIĞI ] ---
def main_menu():
    db = load_db()
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    # Adminin eklediği sorguları buton yap
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
    bot.send_message(uid, "🔱 *LORD SYSTEM V3* \nSistem aktif, komutlar yüklendi.", 
                     parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text.startswith("🔍 "))
def handle_query(message):
    cmd = message.text.replace("🔍 ", "").lower()
    db = load_db()
    if cmd in db['queries']:
        api_url = db['queries'][cmd]
        msg = bot.reply_to(message, f"📌 Lütfen `{cmd.upper()}` için veri giriniz:")
        bot.register_next_step_handler(msg, lambda m: execute(m, api_url, cmd))

def execute(message, api_url, cmd):
    val = message.text.strip()
    target = api_url.replace("{veri}", val)
    status = bot.send_message(message.chat.id, "⚡ `Veri Ayıklanıyor...`", parse_mode="Markdown")
    try:
        # IBAN ve JS kalkanlı siteler için scraper
        res = scraper.get(target, timeout=20, verify=False).text
        # Saf veri: Linkleri ve reklamları temizle
        clean = re.sub(r'https?://\S+|t\.me/\S+|@[a-zA-Z0-9_]+', '', res).strip()
        bot.edit_message_text(f"💎 *SONUÇ:*\n\n`{clean if clean else 'Veri bulunamadı.'}`", 
                             message.chat.id, status.message_id, parse_mode="Markdown")
    except:
        bot.edit_message_text("❌ API Hatası!", message.chat.id, status.message_id)

# --- [ WEB PANEL ] ---
@app.route('/')
def home():
    return '<h2>Lord Login</h2><form action="/login" method="post"><input type="password" name="pw"><button>Giriş</button></form>'

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('pw') == "lordadminv":
        session['admin'] = True
        return redirect('/panel')
    return "Hatalı Şifre"

@app.route('/panel')
def panel():
    if not session.get('admin'): return redirect('/')
    db = load_db()
    return render_template('admin.html', queries=db['queries'])

@app.route('/add', methods=['POST'])
def add():
    db = load_db()
    db['queries'][request.form.get('cmd').lower()] = request.form.get('api')
    save_db(db)
    return redirect('/panel')

@app.route('/del/<cmd>')
def delete(cmd):
    db = load_db()
    if cmd in db['queries']: del db['queries'][cmd]
    save_db(db)
    return redirect('/panel')

if __name__ == "__main__":
    Thread(target=lambda: bot.infinity_polling()).start()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
