import sqlite3

def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    # 原有的笔记表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT,
        title TEXT,
        author TEXT,
        likes INTEGER,
        url TEXT,
        sentiment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 新增评论表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT,
        note_id TEXT,
        note_title TEXT,
        content TEXT,
        author TEXT,
        likes INTEGER,
        sentiment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成（含 notes 和 comments 表）")

def insert_note(platform, title, author, likes, url):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notes (platform, title, author, likes, url) VALUES (?, ?, ?, ?, ?)",
        (platform, title, author, likes, url)
    )
    conn.commit()
    conn.close()

def update_note_sentiment(note_id, sentiment):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE notes SET sentiment = ? WHERE id = ?", (sentiment, note_id))
    conn.commit()
    conn.close()

# 新增：评论相关操作
def insert_comment(platform, note_id, note_title, content, author, likes):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO comments (platform, note_id, note_title, content, author, likes) VALUES (?, ?, ?, ?, ?, ?)",
        (platform, note_id, note_title, content, author, likes)
    )
    comment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return comment_id

def update_comment_sentiment(comment_id, sentiment):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE comments SET sentiment = ? WHERE id = ?", (sentiment, comment_id))
    conn.commit()
    conn.close()