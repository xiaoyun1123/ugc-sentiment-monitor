import subprocess
import json

OPENCLI_PATH = r"C:\Users\WANG\AppData\Roaming\npm\opencli.cmd"

def crawl_zhihu(keyword=None, limit=5):
    """
    采集知乎数据。
    - 若提供 keyword，则调用搜索接口。
    - 否则调用热榜接口。
    """
    if keyword and keyword.strip():
        cmd = [
            OPENCLI_PATH,
            "zhihu", "search", keyword.strip(),
            "--limit", str(limit),
            "-f", "json"
        ]
        mode = f"搜索 '{keyword}'"
    else:
        cmd = [
            OPENCLI_PATH,
            "zhihu", "hot",
            "--limit", str(limit),
            "-f", "json"
        ]
        mode = "热榜"

    print(f"📚 知乎采集模式：{mode}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding='utf-8')
        if result.returncode != 0:
            print(f"❌ 知乎采集失败: {result.stderr.strip()}")
            return []
        data = json.loads(result.stdout)
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and "data" in data:
            items = data["data"]
        else:
            items = []
        results = []
        for item in items:
            title = item.get("title", "").strip()
            if title:
                results.append({
                    "title": title,
                    "author": item.get("author", {}).get("name", "") if isinstance(item.get("author"), dict) else item.get("author", ""),
                    "likes": item.get("hot_value", 0) or item.get("vote_count", 0),
                    "url": item.get("url", "")
                })
        return results
    except subprocess.TimeoutExpired:
        print("⏰ 知乎采集超时")
        return []
    except json.JSONDecodeError as e:
        print(f"📄 知乎 JSON 解析失败: {e}")
        return []
    except Exception as e:
        print(f"❌ 知乎爬虫错误: {e}")
        return []