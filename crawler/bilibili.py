import subprocess
import json

OPENCLI_PATH = r"C:\Users\WANG\AppData\Roaming\npm\opencli.cmd"

def crawl_bilibili(keyword=None, limit=5):
    """
    采集 B 站数据。
    - 若提供 keyword，则调用搜索接口。
    - 否则调用热榜接口。
    """
    if keyword and keyword.strip():
        cmd = [
            OPENCLI_PATH,
            "bilibili", "search", keyword.strip(),
            "--limit", str(limit),
            "-f", "json"
        ]
        mode = f"搜索 '{keyword}'"
    else:
        cmd = [
            OPENCLI_PATH,
            "bilibili", "hot",
            "--limit", str(limit),
            "-f", "json"
        ]
        mode = "热榜"

    print(f"📺 B站采集模式：{mode}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8')
        if result.returncode != 0:
            print(f"❌ B站采集失败: {result.stderr.strip()}")
            return []
        data = json.loads(result.stdout)
        if isinstance(data, list):
            videos = data
        elif isinstance(data, dict) and "items" in data:
            videos = data["items"]
        else:
            videos = []
        results = []
        for v in videos:
            title = v.get("title", "").strip()
            if title:
                results.append({
                    "title": title,
                    "author": v.get("owner", {}).get("name", ""),
                    "likes": v.get("stat", {}).get("like", 0),
                    "url": v.get("short_link", "") or v.get("url", "")
                })
        return results
    except subprocess.TimeoutExpired:
        print("⏰ B站采集超时")
        return []
    except json.JSONDecodeError as e:
        print(f"📄 B站 JSON 解析失败: {e}")
        return []
    except Exception as e:
        print(f"❌ B站爬虫错误: {e}")
        return []