import subprocess
import json

OPENCLI_PATH = r"C:\Users\WANG\AppData\Roaming\npm\opencli.cmd"

def crawl_xhs(keyword, limit=5):
    if not keyword or not keyword.strip():
        print("⚠️ 小红书采集需要提供关键词")
        return []
    cmd = [
    OPENCLI_PATH,
    "xiaohongshu", "search", keyword.strip(),
    "--limit", str(limit),
    "-f", "json"
]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8')
        if result.returncode != 0:
            stderr = result.stderr.strip()
            print(f"❌ OpenCLI 执行失败 (code {result.returncode})")
            if "AUTH_REQUIRED" in stderr or "login wall" in stderr or result.returncode == 77:
                print("🔐 小红书需要登录！请在 Edge 浏览器中登录 https://www.xiaohongshu.com 并保持浏览器运行")
            else:
                print(f"   错误详情: {stderr}")
            return []

        data = json.loads(result.stdout)
        if isinstance(data, list):
            notes = data
        elif isinstance(data, dict) and "items" in data:
            notes = data["items"]
        else:
            notes = []

        results = []
        for note in notes:
            title = note.get("title", "").strip()
            if title:
                results.append({
                    "title": title,
                    "author": note.get("author", ""),
                    "likes": note.get("likes", "0"),
                    "url": note.get("url", "")
                })
        return results

    except subprocess.TimeoutExpired:
        print("⏰ 小红书采集超时")
        return []
    except json.JSONDecodeError as e:
        print(f"📄 小红书 JSON 解析失败: {e}")
        return []
    except Exception as e:
        print(f"❌ 小红书采集异常: {e}")
        return []