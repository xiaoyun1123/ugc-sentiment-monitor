# 🤖 Multi-Platform UGC Monitoring AI Agent

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B)](https://streamlit.io/)
[![OpenCLI](https://img.shields.io/badge/OpenCLI-0.1%2B-0F766E)](https://github.com/jackwener/opencli)
[![DeepSeek](https://img.shields.io/badge/AI-DeepSeek-536DFE)](https://deepseek.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](./LICENSE)

> **一句话简介**：自动采集小红书、B站、知乎的UGC内容，调用DeepSeek进行情感分析，并通过Streamlit仪表盘可视化结果。

## 📌 项目概述

本项目是一个端到端的 **AI Agent 系统**，专注于多平台用户生成内容（UGC）的自动化监控与情感分析。它能够：

- **定时或手动触发**采集任务
- **关键词搜索**或**热榜追踪**小红书、B站、知乎
- **调用大模型**分析每条内容的情感倾向（正面/负面/中性）
- **结构化存储**到 SQLite 数据库
- **可视化展示**数据趋势、情感分布、词云，并支持 CSV 导出

## ✨ 核心功能

- ✅ **多平台采集**：小红书（关键词搜索）、B站（搜索+热榜）、知乎（搜索+热榜）
- ✅ **AI 情感分析**：基于 DeepSeek API，对标题/内容进行三分类标注
- ✅ **数据持久化**：SQLite 轻量级数据库，自动建表与增量写入
- ✅ **交互式仪表盘**：Streamlit 构建，包含数据表格、饼图、趋势图、词云、Top 排行
- ✅ **任务控制台**：Web 界面输入关键词、选择平台、一键启动采集
- ✅ **命令行入口**：支持 `argparse` 参数，可集成到定时任务
- ✅ **数据导出**：仪表盘内一键下载当前筛选数据为 CSV

## 🏗️ 系统架构

```mermaid
graph LR
    A[用户] --> B{控制方式}
    B -->|命令行| C[main.py]
    B -->|Web界面| D[Streamlit 任务控制台]
    
    C --> E[爬虫模块]
    D --> E
    
    subgraph 爬虫模块
        E1[小红书 crawler]
        E2[B站 crawler]
        E3[知乎 crawler]
    end
    
    E1 & E2 & E3 --> F[OpenCLI]
    F --> G[浏览器登录态]
    
    E --> H[AI 分析模块]
    H --> I[DeepSeek API]
    
    E --> J[数据库模块]
    J --> K[(SQLite)]
    
    K --> L[Streamlit 仪表盘]
    L --> M[可视化图表 / CSV导出]
```
