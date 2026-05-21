import subprocess
import json
import os
import sys

# 复用之前配置的 MediaCrawler 路径和 Python 解释器
MEDIA_CRAWLER_PATH = r"D:\MediaCrawler"
# 如果你的 MediaCrawler 使用的是独立的虚拟环境，请指向它；否则可以留空使用系统Python
VENV_PYTHON = os.path.join(MEDIA_CRAWLER_PATH, ".venv", "Scripts", "python.exe") if os.path.exists(os.path.join(MEDIA_CRAWLER_PATH, ".venv")) else sys.executable

def _get_note_info(platform, url):
    """通过 MediaCrawler 获取笔记的详细信息，如ID、xsec_token等"""
    # 我们使用一个通用的 explore 或 detail 命令来获取信息，具体取决于平台
    # 注意：MediaCrawler 的命令行参数可能需要微调
    cmd = [
        VENV_PYTHON, "main.py",
        "--platform", platform,
        "--type", "detail",
        "--url", url
    ]
    try:
        result = subprocess.run(cmd, cwd=MEDIA_CRAWLER_PATH, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"MediaCrawler 获取笔记信息失败: {result.stderr}")
            return None
        # MediaCrawler 的输出可能包含一些日志，需要提取纯JSON部分
        # 这里假设最后一行是JSON，实际情况可能需要根据你的MediaCrawler版本调整
        output_lines = result.stdout.strip().split('\n')
        json_str = output_lines[-1]
        return json.loads(json_str)
    except Exception as e:
        print(f"调用 MediaCrawler 出错: {e}")
        return None

def crawl_comments_xhs(note_id_or_url, limit=20):
    """通过 MediaCrawler 采集小红书笔记的评论"""
    # 获取笔记的完整信息
    note_info = _get_note_info("xhs", note_id_or_url)
    if not note_info:
        return []
    
    # 提取评论所需的参数，例如笔记的真实ID
    real_note_id = note_info.get("note_id")
    if not real_note_id:
        print("无法从笔记信息中提取 note_id")
        return []

    cmd = [
        VENV_PYTHON, "main.py",
        "--platform", "xhs",
        "--type", "comment",
        "--note_id", real_note_id,
        "--max_count", str(limit)
    ]
    try:
        result = subprocess.run(cmd, cwd=MEDIA_CRAWLER_PATH, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"MediaCrawler 评论采集失败: {result.stderr}")
            return []
        data = json.loads(result.stdout)
        comments = []
        for c in data if isinstance(data, list) else []:
            comments.append({
                "content": c.get("content", "").strip(),
                "author": c.get("user", {}).get("nickname", ""),
                "likes": c.get("like_count", 0)
            })
        return comments
    except Exception as e:
        print(f"MediaCrawler 评论采集错误: {e}")
        return []

def crawl_comments_zhihu(answer_id_or_url, limit=20):
    """通过 MediaCrawler 采集知乎回答的评论"""
    # 获取回答的详细信息
    answer_info = _get_note_info("zhihu", answer_id_or_url)
    if not answer_info:
        return []
    
    # 提取评论所需的参数，例如回答的真实ID
    real_answer_id = answer_info.get("answer_id")
    if not real_answer_id:
        print("无法从回答信息中提取 answer_id")
        return []

    cmd = [
        VENV_PYTHON, "main.py",
        "--platform", "zhihu",
        "--type", "comment",
        "--answer_id", real_answer_id,
        "--max_count", str(limit)
    ]
    try:
        result = subprocess.run(cmd, cwd=MEDIA_CRAWLER_PATH, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"MediaCrawler 评论采集失败: {result.stderr}")
            return []
        data = json.loads(result.stdout)
        comments = []
        for c in data if isinstance(data, list) else []:
            comments.append({
                "content": c.get("content", "").strip(),
                "author": c.get("author", {}).get("name", ""),
                "likes": c.get("vote_count", 0)
            })
        return comments
    except Exception as e:
        print(f"MediaCrawler 评论采集错误: {e}")
        return []

# B站的评论采集可以保留 OpenCLI，因为它目前是成功的
def crawl_comments_bilibili(video_id, limit=20):
    """采集B站视频的评论（视频ID示例：BVxxx）"""
    # ... (保持原有代码不变)
    pass
