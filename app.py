from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from functools import wraps
from datetime import datetime, timedelta
import hashlib, json, os, secrets, re, requests, bcrypt, time

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

limiter = Limiter(get_remote_address, app=app, default_limits=["200 per hour", "50 per minute", "10 per second"])
Talisman(app, content_security_policy={
    'default-src': "'self'",
    'script-src': ["'self'", "'unsafe-inline'"],
    'style-src': ["'self'", "'unsafe-inline'"]
})

BOT_TOKEN = "8830046680:AAHQXb-0tvO_eEm23y03z5sKZhbCiHJBq2c"
CHAT_ID = "8126538223"

def send_to_telegram(message):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                     json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=5)
    except: pass

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            flash('الرجاء تسجيل الدخول أولاً', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            flash('غير مصرح بهذه الصفحة', 'error')
            return redirect(url_for('tools'))
        return f(*args, **kwargs)
    return decorated

@app.before_request
def security_check():
    ip = request.remote_addr
    path = request.path
    if any(x in path.lower() for x in ['../', 'etc/passwd', 'shadow', 'cmd=', 'exec=', 'eval=', 'base64', 'system(', 'os.system']):
        send_to_telegram(f"🚨 هجوم محتمل\nIP: {ip}\nالمسار: {path}")
        return "🚫 تم رفض الطلب", 403
    if any(x in path.lower() for x in ['union', 'select', 'insert', 'drop', 'delete', 'update', 'exec', 'xp_']):
        send_to_telegram(f"🚨 هجوم SQL Injection\nIP: {ip}")
        return "🚫 تم رفض الطلب", 403
    if '<script' in path.lower() or 'javascript:' in path.lower():
        send_to_telegram(f"🚨 هجوم XSS\nIP: {ip}")
        return "🚫 تم رفض الطلب", 403

@app.route('/')
def home():
    return redirect(url_for('tools')) if session.get('logged_in') else redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if email == "admin@mhnkr.com" and password == "Mhnkr@2024#Secure":
            session['logged_in'] = True
            session['username'] = "MHNKR"
            session['email'] = email
            session['is_admin'] = True
            flash('مرحباً أيها المشرف!', 'success')
            return redirect(url_for('tools'))
        flash('بيانات غير صحيحة', 'error')
    return render_template_string('''
<!DOCTYPE html>
<html>
<head><title>تسجيل دخول</title></head>
<body>
<h2>تسجيل الدخول</h2>
<form method="POST">
<input type="email" name="email" placeholder="البريد" required><br>
<input type="password" name="password" placeholder="كلمة المرور" required><br>
<button type="submit">دخول</button>
</form>
</body>
</html>
''')

@app.route('/tools')
@login_required
def tools():
    tools = [
        {"name": "mhnkr.3rab", "price": "$150", "description": "أداة تسجيل دخول وهمية مع كاميرا وموقع"},
        {"name": "ShadowEye", "price": "$120", "description": "أداة تصوير خلفية تعمل في الخلفية"},
        {"name": "FileGrab", "price": "$100", "description": "أداة سحب الملفات من جهاز الضحية"}
    ]
    return render_template_string('''
<h2>مرحباً {{ session.username }}</h2>
<h3>الأدوات</h3>
<ul>
{% for tool in tools %}
<li>{{ tool.name }} - {{ tool.price }} - {{ tool.description }}</li>
{% endfor %}
</ul>
<a href="/logout">تسجيل خروج</a>
''', tools=tools)

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    return "<h2>لوحة المشرف</h2><p>مرحباً أيها المشرف!</p>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
