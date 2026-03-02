from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from uuid import uuid4

app = Flask(__name__)
app.secret_key = "secret_key_very_secure"
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'news')
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_news_image_column():
    conn = get_db_connection()
    columns = conn.execute("PRAGMA table_info(news)").fetchall()
    column_names = {column["name"] for column in columns}
    if "image_path" not in column_names:
        conn.execute("ALTER TABLE news ADD COLUMN image_path TEXT")
        conn.commit()
    conn.close()

def is_allowed_image(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS

def save_news_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    if not is_allowed_image(file_storage.filename):
        return None

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    original_name = secure_filename(file_storage.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid4().hex}.{extension}"
    save_path = os.path.join(UPLOAD_FOLDER, unique_name)
    file_storage.save(save_path)
    return f"uploads/news/{unique_name}"

ensure_news_image_column()

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM teachers WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['teacher'] = user['username']
            return redirect(url_for('add_news'))  # بعد الدخول يتحول لصفحة Admin
        else:
            error = "اسم المستخدم أو كلمة المرور خاطئة!"
    return render_template('login.html', error=error)


    return redirect(url_for("news"))

@app.route('/logout')
def logout():
    session.pop('teacher', None)
    return redirect(url_for('login'))

# صفحة Admin خاصة بالمعلمين فقط
@app.route('/admin', methods=['GET', 'POST'])
def add_news():
    if 'teacher' not in session:
        return redirect(url_for('login'))

    news_list = get_all_news_from_db()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']  # ← ده ناقص عندك

        image = request.files.get('image')
        image_path = save_news_image(image)
        save_news_to_db(title, content, image_path)
        return redirect(url_for('add_news'))

    return render_template('teachers.html', news_list=news_list)

from datetime import datetime, timedelta

@app.route('/news/<int:news_id>')
def news_detail(news_id):
    conn = get_db_connection()
    news_item = conn.execute(
        'SELECT * FROM news WHERE id = ?', 
        (news_id,)
    ).fetchone()
    conn.close()

    if news_item is None:
        return "الخبر غير موجود", 404

    formatted_date = ""
    created_at = news_item["created_at"]

    if created_at:
        dt = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
        # تحويل الوقت لـ Cairo (UTC+2)
        dt += timedelta(hours=2)
        formatted_date = dt.strftime("%d-%m-%Y | %I:%M %p")

    return render_template(
        'news_detail.html',
        news=news_item,
        formatted_date=formatted_date
    )
def save_news_to_db(title, content, image_path=None):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO news (title, content, image_path) VALUES (?, ?, ?)",
        (title, content, image_path)
    )
    conn.commit()
    conn.close()

@app.route("/delete_news/<int:news_id>", methods=["POST"])
def delete_news(news_id):
    if 'teacher' not in session:
        return "غير مسموح", 403

    conn = get_db_connection()
    conn.execute("DELETE FROM news WHERE id = ?", (news_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("news"))

# ===== الصفحة الرئيسية =====
@app.route('/')
def home():
    news_list = get_all_news_from_db()  # أو قائمة مؤقتة إذا DB مش جاهزة
    return render_template('index.html', news_list=news_list)

def get_all_news_from_db():
    conn = get_db_connection()
    news = conn.execute('SELECT * FROM news ORDER BY id DESC').fetchall()
    conn.close()
    return news

# صفحة المعلمين - Admin Page
@app.route('/teachers', methods=['GET', 'POST'])
def teachers():
    if 'teacher' not in session:  # حماية الصفحة للمعلمين فقط
        return redirect(url_for('login'))

    news_list = get_all_news_from_db()  # جلب الأخبار
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        image = request.files.get('image')
        image_path = save_news_image(image)
        save_news_to_db(title, content, image_path)
        return redirect(url_for('teachers'))  # بعد النشر يرجع للصفحة نفسها


    return render_template('teachers.html', news_list=news_list)

# ===== عن المدرسة =====
@app.route('/about')
def about():
    return render_template('about.html')
# ===== صفحه الاخبار ====
@app.route('/news')
def news():
    news_list = get_all_news_from_db()
    return render_template('news.html', news_list=news_list)

@app.route('/top_students')
def top_students():
    # كل صورة تمثل الأوائل لكل صف
    top_groups = [
        {
            "title": "الصف الأول الثانوي - انتظام",
            "image": url_for('static', filename='images/top_first_regular.jpg')
        },
        {
            "title": "الصف الثاني الثانوي - انتظام",
            "image": url_for('static', filename='images/top_second_regular.jpg')
        }
    ]
    return render_template('top_students.html', top_groups=top_groups)
@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

# ===== صفحة التواصل =====
@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')


# ===== تشغيل التطبيق =====
if __name__ == '__main__':
    app.run(debug=True)
