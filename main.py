import sqlite3
import argparse
import re
from crawler.xhs import crawl_xhs
from crawler.bilibili import crawl_bilibili
from crawler.zhihu import crawl_zhihu
from storage.db import init_db, insert_note, update_note_sentiment
from ai.analyzer import analyze_sentiment

# 初始化数据库（仅笔记表）
init_db()

def extract_note_id(platform, url):
    """从 URL 中提取笔记/视频/回答 ID（仅用于调试，不进行评论采集）"""
    if not url:
        return None
    if platform == "xiaohongshu":
        match = re.search(r'/(?:explore|search_result)/([a-zA-Z0-9]+)', url)
        return match.group(1) if match else None
    elif platform == "bilibili":
        match = re.search(r'/(BV[a-zA-Z0-9]+)', url)
        return match.group(1) if match else None
    elif platform == "zhihu":
        match = re.search(r'/answer/(\d+)', url)
        return match.group(1) if match else None
    return None

def main():
    parser = argparse.ArgumentParser(description="多平台 UGC 采集与分析 Agent")
    parser.add_argument("--keyword", "-k", type=str, default=None,
                        help="搜索关键词，不指定时默认采集热榜（小红书需关键词）")
    parser.add_argument("--limit", "-l", type=int, default=5,
                        help="每个平台采集条数，默认5")
    parser.add_argument("--platforms", "-p", nargs="+",
                        choices=["xiaohongshu", "bilibili", "zhihu"],
                        default=["xiaohongshu", "bilibili", "zhihu"],
                        help="指定要采集的平台，可多选")
    parser.add_argument("--hot", action="store_true",
                        help="强制采集热榜（B站、知乎），小红书将跳过")
    args = parser.parse_args()

    # 确定运行模式
    use_hot = args.hot or args.keyword is None
    keyword = args.keyword if not use_hot else None
    mode_desc = "热榜" if use_hot else f"关键词: {keyword}"

    print("=" * 60)
    print(f"🚀 多平台 UGC 数据采集与分析 Agent 启动 ({mode_desc}, 笔记条数: {args.limit})")
    print("=" * 60)

    # 平台映射
    def get_xhs_crawler():
        if use_hot:
            print("⚠️ 小红书不支持热榜，跳过采集")
            return []
        return crawl_xhs(keyword, args.limit)

    platform_map = {
        "xiaohongshu": ("小红书", get_xhs_crawler),
        "bilibili":    ("B站",    lambda: crawl_bilibili(keyword=keyword, limit=args.limit)),
        "zhihu":       ("知乎",   lambda: crawl_zhihu(keyword=keyword, limit=args.limit))
    }

    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    total_notes = 0

    for p_name in args.platforms:
        if p_name not in platform_map:
            continue
        desc, crawler_func = platform_map[p_name]
        print(f"\n🕷️ 正在采集 {desc} ({p_name}) 数据...")
        try:
            data = crawler_func()
        except Exception as e:
            print(f"❌ 采集失败: {e}")
            continue

        if not data:
            print(f"⚠️ 未获取到任何笔记数据，跳过。")
            continue

        print(f"📦 采集到 {len(data)} 条笔记，正在处理...")
        for item in data:
            title = item.get("title", "").strip()
            if not title:
                continue

            author = item.get("author", "").strip()
            likes = item.get("likes", 0)
            url = item.get("url", "").strip()

            # 插入笔记
            note_id = insert_note(p_name, title, author, likes, url)

            # 笔记情感分析
            print(f"  🤖 分析笔记: {title[:30]}...", end=" ")
            try:
                sentiment = analyze_sentiment(title)
                update_note_sentiment(note_id, sentiment)
                print(f"→ {sentiment}")
            except Exception as e:
                print(f"→ 分析失败 ({e})")
                update_note_sentiment(note_id, "unknown")

            total_notes += 1

            # （静默）提取笔记ID，仅用于调试，不进行评论采集
            note_uid = extract_note_id(p_name, url)
            if note_uid:
                # 如需查看ID，可取消下一行注释
                # print(f"    📌 笔记ID: {note_uid}")
                pass

        conn.commit()
        print(f"✅ {desc} 数据入库完成。")

    conn.close()
    print("\n" + "=" * 60)
    print(f"🎉 全部流程完成！共入库笔记 {total_notes} 条。")
    print("=" * 60)

if __name__ == "__main__":
    main()