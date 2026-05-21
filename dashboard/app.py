import streamlit as st
import sqlite3
import pandas as pd
import sys
import os
import time
from datetime import datetime

# 尝试导入 plotly，若未安装则降级使用 st.bar_chart
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# 尝试导入词云相关库
try:
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False

# 将项目根目录加入系统路径，以便导入爬虫模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.xhs import crawl_xhs
from crawler.bilibili import crawl_bilibili
from crawler.zhihu import crawl_zhihu
from storage.db import init_db
from ai.analyzer import analyze_sentiment

# ---------- 页面配置 ----------
st.set_page_config(page_title="多平台 UGC 监控 Agent", layout="wide")
st.title("🤖 多平台 UGC 数据监控与采集 Agent")

# 初始化数据库（使用缓存只执行一次）
@st.cache_resource
def initialize_database():
    init_db()
    return True

initialize_database()

# ---------- 侧边栏导航 ----------
page = st.sidebar.radio("导航", ["📈 数据仪表盘", "💬 评论分析", "🎛️ 任务控制台"])

# ---------- 数据加载函数（带缓存）----------
@st.cache_data(ttl=60)
def load_notes_data():
    conn = sqlite3.connect("data.db")
    df = pd.read_sql_query(
        "SELECT id, platform, title, author, likes, sentiment, created_at, url "
        "FROM notes ORDER BY created_at DESC",
        conn,
        parse_dates=["created_at"]
    )
    conn.close()
    return df

@st.cache_data(ttl=60)
def load_comments_data():
    conn = sqlite3.connect("data.db")
    df = pd.read_sql_query(
        "SELECT id, platform, note_id, note_title, content, author, likes, sentiment, created_at "
        "FROM comments ORDER BY created_at DESC",
        conn,
        parse_dates=["created_at"]
    )
    conn.close()
    return df

# ---------- 通用 CSV 导出函数 ----------
def get_csv_download_link(df, filename_prefix):
    csv = df.to_csv(index=False).encode('utf-8-sig')
    return st.sidebar.download_button(
        label="📥 导出当前数据为 CSV",
        data=csv,
        file_name=f'{filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mime='text/csv',
    )

# ---------- 数据仪表盘页面 ----------
if page == "📈 数据仪表盘":
    st.header("📊 已采集数据总览")

    df_notes = load_notes_data()

    if df_notes.empty:
        st.warning("暂无数据，请先前往「任务控制台」或运行 main.py 采集数据。")
        st.stop()

    # 侧边栏筛选
    st.sidebar.header("🔍 筛选条件")
    platforms = ["全部"] + sorted(df_notes["platform"].unique().tolist())
    selected_platform = st.sidebar.selectbox("选择平台", platforms, key="notes_platform")

    if selected_platform != "全部":
        df_filtered = df_notes[df_notes["platform"] == selected_platform]
    else:
        df_filtered = df_notes

    # 日期范围筛选
    if not df_filtered.empty:
        min_date = df_filtered["created_at"].min().date()
        max_date = df_filtered["created_at"].max().date()
        date_range = st.sidebar.date_input("选择日期范围", [min_date, max_date], min_value=min_date, max_value=max_date, key="notes_date")
        if len(date_range) == 2:
            start_date, end_date = date_range
            df_filtered = df_filtered[(df_filtered["created_at"].dt.date >= start_date) & (df_filtered["created_at"].dt.date <= end_date)]

    # 统计信息
    st.sidebar.header("📈 统计信息")
    total_notes = len(df_filtered)
    st.sidebar.metric("总笔记数", total_notes)

    sentiment_counts = df_filtered["sentiment"].value_counts().reset_index()
    sentiment_counts.columns = ["情感", "数量"]
    st.sidebar.write("情感分布：")
    st.sidebar.dataframe(sentiment_counts, hide_index=True, width='stretch')

    if selected_platform == "全部":
        st.sidebar.write("各平台数据量：")
        platform_counts = df_notes["platform"].value_counts().reset_index()
        platform_counts.columns = ["平台", "数量"]
        st.sidebar.dataframe(platform_counts, hide_index=True, width='stretch')

    # CSV 导出
    get_csv_download_link(df_filtered, "notes")

    # 主区域
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📋 最新笔记数据")
        display_df = df_filtered[["platform", "title", "author", "likes", "sentiment", "created_at"]].copy()
        st.dataframe(display_df, width='stretch', hide_index=True)

    with col2:
        st.subheader("🎭 情感分布")
        if PLOTLY_AVAILABLE:
            fig = px.pie(
                sentiment_counts,
                values="数量",
                names="情感",
                title="情感占比",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.bar_chart(sentiment_counts.set_index("情感"))

    # 时间趋势图
    st.subheader("📅 每日采集数量趋势")
    if not df_filtered.empty:
        df_filtered['date'] = df_filtered['created_at'].dt.date
        daily_counts = df_filtered.groupby(['date', 'platform']).size().reset_index(name='count')
        if PLOTLY_AVAILABLE:
            fig_trend = px.line(daily_counts, x='date', y='count', color='platform', title="各平台每日采集量")
            st.plotly_chart(fig_trend, width='stretch')
        else:
            pivot_df = daily_counts.pivot(index='date', columns='platform', values='count').fillna(0)
            st.line_chart(pivot_df)

    # 词云
    if WORDCLOUD_AVAILABLE:
        st.subheader("☁️ 标题词云")
        if not df_filtered.empty:
            text = " ".join(df_filtered["title"].dropna().astype(str).tolist())
            if text.strip():
                try:
                    custom_stopwords = set(['西瓜创客', '合辑', '纯干货'])
                    wc = WordCloud(
                        width=800, height=400,
                        background_color='white',
                        colormap='viridis',
                        max_words=100,
                        font_path='msyh.ttc',
                        stopwords=custom_stopwords
                    ).generate(text)
                    fig_wc, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig_wc)
                except Exception as e:
                    st.warning(f"词云生成失败: {e}")
            else:
                st.info("暂无标题文本可生成词云")
    else:
        st.info("词云功能需要安装 wordcloud 和 matplotlib，请执行: pip install wordcloud matplotlib")

    # 点赞排行
    st.subheader("🔥 点赞数 Top 10")
    top_likes = df_filtered.nlargest(10, "likes")[["platform", "title", "likes", "sentiment"]]
    st.table(top_likes)

    # 各平台情感对比
    if selected_platform == "全部" and len(df_notes["platform"].unique()) > 1:
        st.subheader("📊 各平台情感分布对比")
        platform_sentiment = df_notes.groupby(["platform", "sentiment"]).size().reset_index(name="count")
        if PLOTLY_AVAILABLE:
            fig2 = px.bar(
                platform_sentiment,
                x="platform",
                y="count",
                color="sentiment",
                title="各平台情感数量对比",
                barmode="group"
            )
            st.plotly_chart(fig2, width='stretch')
        else:
            st.dataframe(platform_sentiment, width='stretch')

# ---------- 评论分析页面 ----------
elif page == "💬 评论分析":
    st.header("💬 评论数据总览")
    df_comments = load_comments_data()

    if df_comments.empty:
        st.warning("暂无评论数据，请先运行 main.py 采集评论。")
        st.stop()

    # 侧边栏筛选
    st.sidebar.header("🔍 筛选条件")
    platforms = ["全部"] + sorted(df_comments["platform"].unique().tolist())
    selected_platform = st.sidebar.selectbox("选择平台", platforms, key="comments_platform")

    if selected_platform != "全部":
        df_filtered = df_comments[df_comments["platform"] == selected_platform]
    else:
        df_filtered = df_comments

    # 日期范围筛选
    if not df_filtered.empty:
        min_date = df_filtered["created_at"].min().date()
        max_date = df_filtered["created_at"].max().date()
        date_range = st.sidebar.date_input("选择日期范围", [min_date, max_date], min_value=min_date, max_value=max_date, key="comments_date")
        if len(date_range) == 2:
            start_date, end_date = date_range
            df_filtered = df_filtered[(df_filtered["created_at"].dt.date >= start_date) & (df_filtered["created_at"].dt.date <= end_date)]

    # 统计信息
    st.sidebar.header("📈 统计信息")
    total_comments = len(df_filtered)
    st.sidebar.metric("总评论数", total_comments)

    sentiment_counts = df_filtered["sentiment"].value_counts().reset_index()
    sentiment_counts.columns = ["情感", "数量"]
    st.sidebar.write("情感分布：")
    st.sidebar.dataframe(sentiment_counts, hide_index=True, width='stretch')

    if selected_platform == "全部":
        st.sidebar.write("各平台评论量：")
        platform_counts = df_comments["platform"].value_counts().reset_index()
        platform_counts.columns = ["平台", "数量"]
        st.sidebar.dataframe(platform_counts, hide_index=True, width='stretch')

    # CSV 导出
    get_csv_download_link(df_filtered, "comments")

    # 主区域图表
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎭 评论情感分布")
        if PLOTLY_AVAILABLE:
            fig = px.pie(sentiment_counts, values="数量", names="情感", title="评论情感占比")
            st.plotly_chart(fig, width='stretch')
        else:
            st.bar_chart(sentiment_counts.set_index("情感"))

    with col2:
        st.subheader("📊 各平台评论数量")
        if PLOTLY_AVAILABLE:
            platform_counts = df_filtered["platform"].value_counts().reset_index()
            platform_counts.columns = ["平台", "数量"]
            fig_bar = px.bar(platform_counts, x="平台", y="数量", title="各平台评论数")
            st.plotly_chart(fig_bar, width='stretch')
        else:
            platform_counts = df_filtered["platform"].value_counts()
            st.bar_chart(platform_counts)

    # 评论时间趋势
    st.subheader("📅 每日评论数量趋势")
    if not df_filtered.empty:
        df_filtered['date'] = df_filtered['created_at'].dt.date
        daily_counts = df_filtered.groupby(['date', 'platform']).size().reset_index(name='count')
        if PLOTLY_AVAILABLE:
            fig_trend = px.line(daily_counts, x='date', y='count', color='platform', title="各平台每日评论量")
            st.plotly_chart(fig_trend, width='stretch')
        else:
            pivot_df = daily_counts.pivot(index='date', columns='platform', values='count').fillna(0)
            st.line_chart(pivot_df)

    # 评论列表
    st.subheader("📋 最新评论")
    display_cols = ["platform", "note_title", "content", "author", "likes", "sentiment", "created_at"]
    st.dataframe(df_filtered[display_cols], width='stretch', hide_index=True)

# ---------- 任务控制台页面 ----------
elif page == "🎛️ 任务控制台":
    st.header("🎛️ 启动数据采集任务")
    st.markdown("""
    输入关键词，选择平台，点击按钮即可采集笔记数据。
    
    **温馨提示**：
    - 笔记采集：本界面支持实时采集笔记并分析情感。
    - 评论采集：需要评论数据时，请使用命令行运行 `python main.py -k 关键词 -c 评论数`，或稍后通过界面扩展。
    """)

    col1, col2 = st.columns([3, 2])

    with col1:
        keyword = st.text_input("🔑 搜索关键词", value="实习", help="留空则采集热榜（小红书不支持热榜）")
        note_limit = st.slider("📏 每个平台采集笔记条数", min_value=1, max_value=20, value=3)
        comment_limit = st.slider("💬 每条笔记采集评论条数（暂未集成，请用命令行）", min_value=0, max_value=20, value=0, disabled=True)

    with col2:
        st.write("📱 选择平台：")
        run_xhs = st.checkbox("小红书", value=True)
        run_bili = st.checkbox("B站", value=True)
        run_zhihu = st.checkbox("知乎", value=True)

    if st.button("🚀 开始采集笔记", type="primary"):
        if not any([run_xhs, run_bili, run_zhihu]):
            st.warning("请至少选择一个平台。")
        else:
            st.success(f"任务已启动，关键词：**{keyword if keyword else '热榜'}**，笔记 {note_limit} 条/平台")
            progress_bar = st.progress(0, text="准备中...")
            status_text = st.empty()

            conn = sqlite3.connect("data.db")
            cursor = conn.cursor()
            total_notes = 0

            tasks = []
            if run_xhs:
                if not keyword:
                    st.warning("小红书需要关键词，已跳过")
                else:
                    tasks.append(("xiaohongshu", "小红书", lambda: crawl_xhs(keyword, note_limit)))
            if run_bili:
                tasks.append(("bilibili", "B站", lambda: crawl_bilibili(keyword=keyword if keyword else None, limit=note_limit)))
            if run_zhihu:
                tasks.append(("zhihu", "知乎", lambda: crawl_zhihu(keyword=keyword if keyword else None, limit=note_limit)))

            total_tasks = len(tasks)
            for i, (p_name, p_desc, crawler_func) in enumerate(tasks):
                status_text.text(f"正在采集 {p_desc} ({p_name}) 数据...")
                progress_bar.progress((i) / total_tasks, text=f"采集 {p_desc} 中...")

                try:
                    notes = crawler_func()
                except Exception as e:
                    st.error(f"❌ {p_desc} 采集失败: {e}")
                    continue

                if not notes:
                    st.warning(f"⚠️ {p_desc} 未获取到笔记数据")
                    continue

                for note in notes:
                    title = note.get("title", "").strip()
                    if not title:
                        continue
                    author = note.get("author", "").strip()
                    likes = note.get("likes", 0)
                    url = note.get("url", "").strip()

                    cursor.execute(
                        "INSERT INTO notes (platform, title, author, likes, url) VALUES (?, ?, ?, ?, ?)",
                        (p_name, title, author, likes, url)
                    )
                    note_id = cursor.lastrowid

                    try:
                        sentiment = analyze_sentiment(title)
                        cursor.execute("UPDATE notes SET sentiment = ? WHERE id = ?", (sentiment, note_id))
                    except:
                        cursor.execute("UPDATE notes SET sentiment = ? WHERE id = ?", ("unknown", note_id))

                    total_notes += 1

                conn.commit()
                st.success(f"✅ {p_desc} 完成，入库 {len(notes)} 条笔记")

            conn.close()
            progress_bar.progress(1.0, text="全部完成！")
            status_text.text(f"🎉 采集任务结束，共新增笔记 {total_notes} 条。")
            st.balloons()
            time.sleep(2)
            st.cache_data.clear()
            st.rerun()