import sqlite3

DATABASE = 'database.db'

conn = sqlite3.connect(DATABASE)
c = conn.cursor()

# إنشاء جدول المعلمين
c.execute('''
CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
)
''')

# إنشاء جدول الأخبار
c.execute('''
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
conn.close()

print("تم إنشاء الجداول بنجاح!")
