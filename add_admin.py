import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def add_teacher(username, password):
    password_hash = generate_password_hash(password)
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO teachers (username, password_hash) VALUES (?, ?)',
        (username, password_hash)
    )
    conn.commit()
    conn.close()
    print(f"تم إضافة المعلم: {username}")

if __name__ == '__main__':
    teachers = [
        ("abdelnaser", "AbdNaser@123"),  
        ("hussein", "Hus#2026!X9q"),
        ("shaaban", "Sh@aban_78Zq!")
    ]

    for username, password in teachers:
        add_teacher(username, password)
