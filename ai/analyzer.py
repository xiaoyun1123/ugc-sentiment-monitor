import os
import requests
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("请在 .env 文件中设置 DEEPSEEK_API_KEY")

def analyze_sentiment(text):
    """
    调用 DeepSeek API 对文本进行情感分析
    返回：positive / negative / neutral
    """
    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""请判断以下文本的情感倾向，只返回一个词：positive（正面）、negative（负面）或 neutral（中性）。

文本："{text}"

情感倾向："""
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 10
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        sentiment = result["choices"][0]["message"]["content"].strip().lower()
        
        # 标准化输出
        if "positive" in sentiment:
            return "positive"
        elif "negative" in sentiment:
            return "negative"
        else:
            return "neutral"
    except Exception as e:
        print(f"AI 分析出错: {e}")
        return "unknown"