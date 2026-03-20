#!/usr/bin/env python3
"""
localize.py — Market Analyst Skill
繁體 ↔ 簡體 localization helper.
Uses opencc for base conversion + financial term overrides from term-glossary.md.

Usage:
  from scripts.localize import localize
  zh_cn_text = localize(zh_tw_text, target="zh-CN")
"""

import re
from pathlib import Path

# ── Term overrides (subset of references/term-glossary.md) ───────────────────
# Format: { Traditional: Simplified }
TERM_OVERRIDES: dict[str, str] = {
    "聯準會": "美联储",
    "漲跌幅": "涨跌幅",
    "停損": "止损",
    "停利": "止盈",
    "選擇權": "期权",
    "期貨": "期货",
    "槓桿": "杠杆",
    "波動率": "波动率",
    "財報": "财报",
    "獲利": "盈利",
    "營收": "营收",
    "淨利": "净利润",
    "每股盈餘": "每股收益",
    "本益比": "市盈率",
    "布林通道": "布林带",
    "移動平均線": "移动平均线",
    "支撐": "支撑",
    "壓力": "阻力",
    "盤前": "盘前",
    "盤後": "盘后",
    "開盤": "开盘",
    "收盤": "收盘",
    "熔斷機制": "熔断机制",
    "通膨": "通胀",
    "消費者物價指數": "消费者价格指数",
    "國內生產毛額": "国内生产总值",
    "避險基金": "对冲基金",
    "內線交易": "内幕交易",
    "投資組合": "投资组合",
    "資產配置": "资产配置",
    "損益": "盈亏",
    "未實現獲利": "未实现收益",
    "已實現獲利": "已实现收益",
    "持倉成本": "持仓成本",
    "空頭市場": "熊市",
    "多頭市場": "牛市",
    "做多": "做多",
    "放空": "做空",
    "保證金": "保证金",
    "指數": "指数",
    "相對強弱指標": "相对强弱指数",
    "板塊熱力圖": "板块热力图",
    "重要新聞": "重要新闻",
    "技術訊號": "技术信号",
    "社群情緒": "社群情绪",
    "市場賭注": "市场赔率",
    "明日展望": "明日展望",
    "市場總覽": "市场总览",
}

# Section title map
SECTION_TITLES = {
    "zh-TW": {
        "market_overview": "市場總覽",
        "breaking_news": "重要新聞",
        "technical_signals": "技術訊號",
        "sector_heatmap": "板塊熱力圖",
        "polymarket": "市場賭注",
        "reddit_sentiment": "社群情緒",
        "portfolio_pnl": "投資組合損益",
        "tomorrow_preview": "明日展望",
    },
    "zh-CN": {
        "market_overview": "市场总览",
        "breaking_news": "重要新闻",
        "technical_signals": "技术信号",
        "sector_heatmap": "板块热力图",
        "polymarket": "市场赔率",
        "reddit_sentiment": "社群情绪",
        "portfolio_pnl": "投资组合盈亏",
        "tomorrow_preview": "明日展望",
    },
}


def localize(text: str, target: str = "zh-CN") -> str:
    """
    Convert Traditional Chinese text to target locale.
    Applies opencc for character conversion, then financial term overrides.

    Args:
        text: Input Traditional Chinese text
        target: "zh-CN" (Simplified) or "zh-TW" (no-op, return as-is)

    Returns:
        Localized string
    """
    if target == "zh-TW":
        return text

    # Step 1: opencc base conversion
    try:
        import opencc
        converter = opencc.OpenCC("t2s")  # Traditional → Simplified
        result = converter.convert(text)
    except ImportError:
        # Fallback: apply overrides only (no opencc)
        result = text

    # Step 2: Apply financial term overrides
    for tw_term, cn_term in TERM_OVERRIDES.items():
        result = result.replace(tw_term, cn_term)

    return result


def get_section_title(section_key: str, lang: str = "zh-TW") -> str:
    """Get localized section title."""
    return SECTION_TITLES.get(lang, SECTION_TITLES["zh-TW"]).get(
        section_key, section_key
    )


def localize_report(report_dict: dict, target: str = "zh-CN") -> dict:
    """
    Deep-localize all string values in a report dict.
    Recursively traverses nested dicts and lists.
    """
    if isinstance(report_dict, str):
        return localize(report_dict, target)
    elif isinstance(report_dict, dict):
        return {k: localize_report(v, target) for k, v in report_dict.items()}
    elif isinstance(report_dict, list):
        return [localize_report(item, target) for item in report_dict]
    return report_dict


if __name__ == "__main__":
    sample = "聯準會本週維持利率不動，投資組合損益如下：停損 $580，選擇權到期。"
    print("原文（繁體）：", sample)
    print("轉換（簡體）：", localize(sample, "zh-CN"))
