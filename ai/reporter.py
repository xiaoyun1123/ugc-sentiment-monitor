import sqlite3
import os
from dotenv import load_dotenv
import requests

load_dotenv()

def generate_weekly_report():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, sentiment FROM notes ORDER BY created_at DESC LIMIT 20")
    notes = cursor.fetchall()
    conn.close()

    if not notes:
        return "暂无数据，无法生成周报。"

    note_texts = "\n".join([f"- {title} (情感: {sentiment})" for title, sentiment in notes])
    prompt = f"以下是本周采集到的小红书笔记列表，请用中文写一份简洁的周报总结（200字以内），概括主要内容、情感倾向和值得关注的要点：\n{note_texts}"

    headers = {
        "Authorization": f"Bearer {os.getenv('DEEPSEEK_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 400
    }

    response = requests.post("https://api.deepseek.com/v1/chat/completions", json=data, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    report = generate_weekly_report()
    with open("weekly_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print("✅ 周报已生成：weekly_report.txt")
    print(report)