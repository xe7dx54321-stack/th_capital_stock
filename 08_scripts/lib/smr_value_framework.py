#!/usr/bin/env python3
"""VFM (Value Framework Module) 价值评判框架。

对每只标的从 5 个维度给出结构化价值评分卡，供机会雷达等模块调用。
5 个维度：基本面质量、估值位置、技术动量、主题相关性、产业位置。
每个维度 0-10 分，加权合成为 composite_score。

使用方式：
    from smr_value_framework import ValueScoreCard, build_all_value_scores, render_value_score_section
    scorecard = ValueScoreCard(conn).score("300308.SZ")
    print(scorecard["composite_score"])

小白说明：这个文件就是一个"打分器"——你喂它一只股票代码，
它从数据库里读各种因子数据，然后按照5个维度打分，告诉你这只标的在每个方面怎么样。
就像老师改卷子，每张卷子有5道大题，最后给一个总分。
"""

from __future__ import annotations

import sqlite3
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional


# ============================================================
# 配置：评分权重与阈值
# ============================================================

# 维度权重（总权重=1.0，加权合成为 composite_score）
DIMENSION_WEIGHTS = {
    "fundamental_quality": 0.30,  # 基本面质量（30%）— 最重要
    "valuation_position":  0.15,  # 估值位置（15%）— 太贵了也不好
    "technical_momentum":  0.25,  # 技术动量（25%）— 趋势是朋友
    "theme_relevance":     0.15,  # 主题相关性（15%）— 是否属于我们关注的赛道
    "industry_position":   0.15,  # 产业位置（15%）— 规模与认可度
}

# 5 大主题定义（与 sector_priority_map.md 对齐）
FOCUS_THEMES = {
    "semiconductor_compute":  {"关键词": ["半导体", "算力", "芯片", "GPU", "海光", "寒武纪", "澜起", "兆易", "华虹", "中芯"], "base_score": 7.0},
    "semiconductor_photonics": {"关键词": ["光模块", "CPO", "光子", "光迅", "新易盛", "中际", "天孚", "光库"], "base_score": 7.0},
    "embodied_ai":           {"关键词": ["机器人", "具身", "谐波", "绿的", "拓普", "鸣志", "三花", "锋龙"], "base_score": 6.0},
    "ai_agent":              {"关键词": ["AI", "agent", "讯飞", "金山", "泛微", "商汤", "阿里", "腾讯"], "base_score": 6.0},
    "quantum":               {"关键词": ["量子", "国盾", "IonQ", "Rigetti", "Qubit"], "base_score": 5.0},
}


# ============================================================
# 辅助工具函数
# ============================================================

def safe_float(value, default=None):
    """把任意值安全地转为浮点数。处理 None、空字符串、'nan' 等情况。"""
    if value in (None, "", "None", "nan", "NaN", "-"):
        return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    import math
    if math.isnan(number) or math.isinf(number):
        return default
    return number


def clamp(value, lo=0.0, hi=10.0):
    """把数值限制在 [lo, hi] 范围内。"""
    if value is None:
        return lo
    return max(lo, min(hi, value))


def linear_score(x, x_min, x_low, x_high, x_max, reverse=False):
    """分段线性评分：低于 x_min 或 高于 x_max 得低分；在 [x_low, x_high] 内得高分。
    
    参数说明（小白）：
        x: 要评分的原始数值
        x_min: 低于这个值，统一给最低分
        x_low: 合理区间的下界
        x_high: 合理区间的上界
        x_max: 超过这个值，统一给最低分
        reverse: 如果 True，那么数值越低越好（比如估值、波动率）
    
    返回：0.0 ~ 10.0 的分数
    """
    if x is None:
        return None
    if reverse:
        x = -x
        x_min, x_max = -x_max, -x_min
        x_low, x_high = -x_high, -x_low
    
    if x < x_min:
        return 2.0
    if x > x_max:
        return 3.0
    if x_low <= x <= x_high:
        return 9.0
    if x < x_low:
        # x_min ~ x_low 之间线性上升 2→9
        ratio = (x - x_min) / (x_low - x_min) if x_low != x_min else 0.5
        return 2.0 + ratio * 7.0
    # x_high ~ x_max 之间线性下降 9→3
    ratio = (x_max - x) / (x_max - x_high) if x_max != x_high else 0.5
    return 3.0 + ratio * 6.0


# ============================================================
# 核心评分类
# ============================================================

class ValueScoreCard:
    """价值评分卡计算器。对给定的 ts_code，从数据库读取因子并生成5维评分。
    
    小白说明：这个类的用法很简单——
        1) 创建一个实例需要一个数据库连接 conn
        2) 调用 score(ts_code) 就能得到评分结果
        3) 评分结果是一个字典，像这样：
           {
             "ts_code": "300308.SZ",
             "fundamental_quality": 7.2,
             "valuation_position": 6.5,
             ...
             "composite_score": 7.8,
             "red_flags": ["估值偏高", "RSI接近超买"],
             "data_available_level": "full"  # "full"/"partial"/"none"
           }
    """

    def __init__(self, conn: sqlite3.Connection):
        """初始化评分器。
        
        参数：
            conn: SQLite 数据库连接（已经连接到 smr.db）
        """
        self.conn = conn

    # --------------------------------------------------------
    # 数据读取：从 factor_daily + stock_pool 读取所需字段
    # --------------------------------------------------------

    def _load_factors(self, ts_code: str) -> Dict[str, float]:
        """读取某只标的的最新因子数据。返回 {因子名: 数值}。"""
        latest_date = self.conn.execute(
            "SELECT MAX(trade_date) FROM factor_daily WHERE ts_code=?", (ts_code,)
        ).fetchone()[0]
        if not latest_date:
            return {}

        rows = self.conn.execute(
            "SELECT factor_name, factor_value FROM factor_daily "
            "WHERE ts_code=? AND trade_date=?",
            (ts_code, latest_date)
        ).fetchall()
        return {row[0]: safe_float(row[1]) for row in rows}

    def _load_pool_info(self, ts_code: str) -> Dict[str, str]:
        """读取标的在 stock_pool 中的信息（主题、层级）。"""
        row = self.conn.execute(
            "SELECT sector, pool_type, score FROM stock_pool "
            "WHERE ts_code=? ORDER BY added_date DESC LIMIT 1",
            (ts_code,)
        ).fetchone()
        if row:
            return {"sector": row[0] or "", "pool_type": row[1] or "", "score": safe_float(row[2])}
        return {"sector": "", "pool_type": "", "score": None}

    def _load_price_metrics(self, ts_code: str) -> Dict[str, float]:
        """从 daily_bar 读取价格信息（目前不用，备用）。"""
        row = self.conn.execute(
            "SELECT close, pct_chg FROM daily_bar WHERE ts_code=? "
            "ORDER BY trade_date DESC LIMIT 1",
            (ts_code,)
        ).fetchone()
        if row:
            return {"close": safe_float(row[0]), "pct_chg": safe_float(row[1])}
        return {}

    # --------------------------------------------------------
    # 新增：价格数据读取（支持 A股/港股/美股）
    # --------------------------------------------------------

    def _load_price_data(self, ts_code: str, days: int = 60) -> List[Dict[str, float]]:
        """读取某只标的最近 N 天的价格数据。

        支持 A股/港股（daily_bar）和美股（us_daily_bar）两种表。

        参数：
            ts_code: 标的代码，如 "300308.SZ" 或 "NVDA"
            days: 读取多少天的数据，默认 60 天

        返回：
            列表，每个元素是 {trade_date, close, pct_chg, volume, high, low}
            按日期升序排列（从旧到新）
        """
        is_us = bool(re.match(r'^[A-Z]+$', ts_code))
        if is_us:
            rows = self.conn.execute(
                "SELECT trade_date, close, pct_chg, vol, high, low "
                "FROM us_daily_bar WHERE symbol=? "
                "ORDER BY trade_date ASC LIMIT ?",
                (ts_code, days)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT trade_date, close, pct_chg, vol, high, low "
                "FROM daily_bar WHERE ts_code=? "
                "ORDER BY trade_date ASC LIMIT ?",
                (ts_code, days)
            ).fetchall()
        return [
            {"trade_date": r[0], "close": safe_float(r[1]), "pct_chg": safe_float(r[2]),
             "volume": safe_float(r[3]), "high": safe_float(r[4]), "low": safe_float(r[5])}
            for r in rows
        ]

    # --------------------------------------------------------
    # 新增：历史分位计算
    # --------------------------------------------------------

    def _compute_pe_pb_percentile(self, ts_code: str) -> Dict[str, float]:
        """计算 PE/PB 在自身历史中的分位。

        原理：用这只股票过去 2 年的 PE/PB 数据，计算当前值在历史中的位置。
        例如：percentile_pe=0.3 表示当前 PE 比历史上 30% 的时间低，
        属于历史偏低估区间。

        返回：
            {"percentile_pe": 0.0~1.0, "percentile_pb": 0.0~1.0}
            如果数据不足 20 条，返回 None
        """
        is_us = bool(re.match(r'^[A-Z]+$', ts_code))
        table = "us_daily_bar" if is_us else "factor_daily"

        # 取最近 2 年的 PE/PB 数据（按月采样，约 24 条）
        if is_us:
            # 美股：factor_daily 中没有 PE/PB，用 price-based 反推
            rows = self.conn.execute(
                "SELECT trade_date, close FROM us_daily_bar "
                "WHERE symbol=? AND close IS NOT NULL "
                "ORDER BY trade_date DESC LIMIT 500"
                .format(table if table == "factor_daily" else "us_daily_bar"),
                (ts_code,)
            ).fetchall()
            if not rows:
                return {"percentile_pe": None, "percentile_pb": None}
            prices = [safe_float(r[1]) for r in rows]
            current_price = prices[0] if prices else None
            # 简化：用波动率估算 PE 分位
            if not current_price or len(prices) < 20:
                return {"percentile_pe": None, "percentile_pb": None}
            import statistics
            mean_price = statistics.mean(prices[:60]) if len(prices) >= 60 else statistics.mean(prices)
            std_price = statistics.stdev(prices[:60]) if len(prices) >= 60 else statistics.stdev(prices) if len(prices) >= 2 else 0
            if std_price == 0:
                percentile_pe = 0.5
            else:
                z_score = (current_price - mean_price) / std_price
                percentile_pe = max(0, min(1, 0.5 + z_score * 0.1))
            return {"percentile_pe": percentile_pe, "percentile_pb": None}
        else:
            # A股/港股：从 factor_daily 取 PE/PB 历史
            pe_rows = self.conn.execute(
                "SELECT factor_value FROM factor_daily "
                "WHERE ts_code=? AND factor_name='pe_ttm' AND factor_value IS NOT NULL "
                "ORDER BY trade_date DESC LIMIT 500",
                (ts_code,)
            ).fetchall()
            pb_rows = self.conn.execute(
                "SELECT factor_value FROM factor_daily "
                "WHERE ts_code=? AND factor_name='pb' AND factor_value IS NOT NULL "
                "ORDER BY trade_date DESC LIMIT 500",
                (ts_code,)
            ).fetchall()

            def calc_percentile(history_vals, current_val):
                if not history_vals or current_val is None:
                    return None
                valid = [v for v in [safe_float(r[0]) for r in history_vals] if v is not None and v > 0]
                if len(valid) < 20:
                    return None
                current = safe_float(current_val)
                if current is None or current <= 0:
                    return None
                # 分位 = 小于当前值的比例
                count_below = sum(1 for v in valid if 0 < v < current)
                return count_below / len(valid)

            current_pe = self.conn.execute(
                "SELECT factor_value FROM factor_daily "
                "WHERE ts_code=? AND factor_name='pe_ttm' "
                "ORDER BY trade_date DESC LIMIT 1",
                (ts_code,)
            ).fetchone()
            current_pb = self.conn.execute(
                "SELECT factor_value FROM factor_daily "
                "WHERE ts_code=? AND factor_name='pb' "
                "ORDER BY trade_date DESC LIMIT 1",
                (ts_code,)
            ).fetchone()

            return {
                "percentile_pe": calc_percentile(pe_rows, current_pe[0] if current_pe else None),
                "percentile_pb": calc_percentile(pb_rows, current_pb[0] if current_pb else None),
            }

    # --------------------------------------------------------
    # 新增：真实价格动量计算
    # --------------------------------------------------------

    def _compute_price_momentum(self, ts_code: str) -> Dict[str, float]:
        """从真实价格数据计算多周期动量。

        计算以下动量指标：
        - momentum_5d: 5 日收益率（%）
        - momentum_20d: 20 日收益率（%）
        - momentum_60d: 60 日收益率（%）
        - macd_signal: MACD 信号（"gold_cross" | "death_cross" | "bullish" | "bearish"）
        - volume_ratio: 今日成交量 / 20 日均量

        返回：
            包含上述指标的字典，数值或 None
        """
        prices = self._load_price_data(ts_code, days=90)
        if len(prices) < 5:
            return {"momentum_5d": None, "momentum_20d": None, "momentum_60d": None,
                    "macd_signal": None, "volume_ratio": None}

        closes = [p["close"] for p in prices if p["close"] is not None]
        volumes = [p["volume"] for p in prices if p["volume"] is not None]
        if len(closes) < 5:
            return {"momentum_5d": None, "momentum_20d": None, "momentum_60d": None,
                    "macd_signal": None, "volume_ratio": None}

        # 计算收益率
        def ret(n):
            if len(closes) <= n:
                return None
            cur = closes[-1]
            old = closes[-n - 1] if len(closes) > n else closes[0]
            if not cur or not old or old == 0:
                return None
            return (cur - old) / old * 100

        momentum_5d = ret(5)
        momentum_20d = ret(20)
        momentum_60d = ret(60)

        # MACD 计算（DIF = EMA12 - EMA26，DEA = DIF 的 EMA9）
        def ema(data, period):
            if len(data) < period:
                return None
            k = 2.0 / (period + 1)
            ema_val = sum(data[:period]) / period
            for price in data[period:]:
                ema_val = price * k + ema_val * (1 - k)
            return ema_val

        if len(closes) >= 26:
            ema_12 = ema(closes, 12)
            ema_26 = ema(closes, 26)
            dif = ema_12 - ema_26 if ema_12 and ema_26 else None

            # 用最近 9 天的 DIF 计算 DEA
            dif_history = []
            for i in range(26, len(closes)):
                e12 = ema(closes[:i+1], 12)
                e26 = ema(closes[:i+1], 26)
                if e12 and e26:
                    dif_history.append(e12 - e26)
            dea = ema(dif_history[-9:], 9) if len(dif_history) >= 9 else None

            if dif is not None and dea is not None:
                macd_hist = dif - dea
                prev_dif_history = dif_history[-10] if len(dif_history) >= 10 else None
                if prev_dif_history is not None:
                    prev_dea = ema(dif_history[-10:-1], 9) if len(dif_history) >= 10 else None
                    prev_macd_hist = dif_history[-10] - prev_dea if prev_dea else None
                    if prev_macd_hist is not None:
                        if prev_dif_history <= prev_dea and dif > dea:
                            macd_signal = "gold_cross"  # 金叉：看涨
                        elif prev_dif_history >= prev_dea and dif < dea:
                            macd_signal = "death_cross"  # 死叉：看跌
                        elif dif > dea:
                            macd_signal = "bullish"  # MACD 为正但未交叉
                        else:
                            macd_signal = "bearish"  # MACD 为负但未交叉
                    else:
                        macd_signal = "neutral"
                else:
                    macd_signal = "neutral" if dif >= dea else "bearish"
            else:
                macd_signal = None
        else:
            macd_signal = None

        # 成交量比
        if len(volumes) >= 20:
            avg_vol = sum(volumes[-20:]) / 20
            today_vol = volumes[-1]
            volume_ratio = today_vol / avg_vol if avg_vol > 0 else None
        else:
            volume_ratio = None

        return {
            "momentum_5d": momentum_5d,
            "momentum_20d": momentum_20d,
            "momentum_60d": momentum_60d,
            "macd_signal": macd_signal,
            "volume_ratio": volume_ratio,
        }

    # --------------------------------------------------------
    # 新增：行业内相对排名
    # --------------------------------------------------------

    def _compute_industry_rank(self, ts_code: str, sector: str) -> Dict[str, float]:
        """计算该股票在同行业内的相对排名。

        参数：
            ts_code: 标的代码
            sector: 行业/主题标签

        返回：
            {
                "rank_roe": 0.0~1.0，ROE 在行业内排名（1=最好）
                "rank_revenue_growth": 0.0~1.0，营收增速在行业内排名
                "rank_pe": 0.0~1.0，PE 在行业内排名（1=最低/最便宜）
            }
            如果数据不足，返回全 None
        """
        if not sector:
            return {"rank_roe": None, "rank_revenue_growth": None, "rank_pe": None}

        # 获取同行业的所有股票
        # 注意：我们用的是 stock_pool_current 表的 sector 字段
        pool_rows = self.conn.execute(
            "SELECT DISTINCT ts_code FROM stock_pool_current WHERE sector=?",
            (sector,)
        ).fetchall()
        peer_codes = [r[0] for r in pool_rows]
        if len(peer_codes) < 2:
            # 同行业太少，无法排名
            return {"rank_roe": None, "rank_revenue_growth": None, "rank_pe": None}

        # 对每只股票取最新因子
        def get_factor_value(code: str, factor_name: str):
            row = self.conn.execute(
                "SELECT factor_value FROM factor_daily "
                "WHERE ts_code=? AND factor_name=? "
                "ORDER BY trade_date DESC LIMIT 1",
                (code, factor_name)
            ).fetchone()
            return safe_float(row[0]) if row else None

        def percentile_rank(code: str, factor_name: str, higher_is_better: bool = True) -> Optional[float]:
            """计算 code 在 peer 中的分位排名。返回 0.0~1.0。"""
            values = []
            for c in peer_codes:
                v = get_factor_value(c, factor_name)
                if v is not None:
                    values.append((c, v))
            if len(values) < 2:
                return None
            current_val = next((v for c, v in values if c == code), None)
            if current_val is None:
                return None
            if higher_is_better:
                # 越高越好：分位 = 比当前值大的比例
                count_above = sum(1 for _, v in values if v > current_val)
            else:
                # 越低越好（如 PE）：分位 = 比当前值小的比例
                count_above = sum(1 for _, v in values if v < current_val)
            return count_above / len(values)

        return {
            "rank_roe": percentile_rank(ts_code, "roe_est", higher_is_better=True),
            "rank_revenue_growth": percentile_rank(ts_code, "revenue_yoy", higher_is_better=True),
            "rank_pe": percentile_rank(ts_code, "pe_ttm", higher_is_better=False),
        }

    # --------------------------------------------------------
    # 维度 1：基本面质量评分
    # --------------------------------------------------------

    def _score_fundamental(self, factors: Dict[str, float]) -> float:
        """基本面质量：综合 ROE、EPS、营收增速、净利润率。
        
        逻辑：每个子项单独打0-10分，最后加权平均。
        """
        sub_scores = []
        weights = []

        # ROE：盈利能力的核心指标。5-25% 最佳区间。
        roe = factors.get("roe_est") or factors.get("roe_reported") or factors.get("roe_diluted")
        if roe is not None:
            score = linear_score(roe, x_min=-5, x_low=5, x_high=25, x_max=40)
            sub_scores.append(score)
            weights.append(0.35)  # ROE 权重最大

        # EPS TTM：每股盈利。>1 元就不错，>4 元优秀。
        eps = factors.get("eps_ttm") or factors.get("basic_eps_reported")
        if eps is not None:
            score = linear_score(eps, x_min=-1, x_low=0.5, x_high=5.0, x_max=15.0)
            sub_scores.append(score)
            weights.append(0.25)

        # 营收同比：growth_yoy > 10% 加分。
        rev_yoy = factors.get("revenue_yoy")
        if rev_yoy is not None:
            score = linear_score(rev_yoy, x_min=-20, x_low=5, x_high=50, x_max=100)
            sub_scores.append(score)
            weights.append(0.20)

        # 净利率：net_margin。15% 以上不错，30% 很好。
        net_margin = factors.get("net_margin")
        if net_margin is not None:
            score = linear_score(net_margin, x_min=-10, x_low=10, x_high=40, x_max=80)
            sub_scores.append(score)
            weights.append(0.20)

        if not sub_scores:
            return None  # 没有任何基本面数据

        total_weight = sum(weights)
        return sum(s * w for s, w in zip(sub_scores, weights)) / total_weight

    # --------------------------------------------------------
    # 维度 2：估值位置评分（增强版：历史分位）
    # --------------------------------------------------------

    def _score_valuation(self, factors: Dict[str, float], percentile_info: Dict[str, float] = None) -> float:
        """估值位置：PE/PB 是否在合理区间，并结合历史分位。

        增强说明：
        - 除了绝对值评分，还加入历史分位（percentile_info）
        - 例如：PE 绝对值较高，但历史分位只有 20%（比历史上 80% 的时间便宜）
          → 综合评分应该更正面

        评分逻辑：
        - 基础分 = 绝对值评分（PE/PB 在合理区间内得高分）
        - 历史分位加权：历史分位越低（越便宜），最终分越高
        """
        sub_scores = []
        weights = []

        # PE TTM 评分
        pe = factors.get("pe_ttm") or factors.get("pe_dynamic")
        if pe is not None and pe > 0:
            # 绝对值评分（越低越好）
            score = linear_score(pe, x_min=5, x_low=12, x_high=60, x_max=120, reverse=False)
            if 20 <= pe <= 50:
                score = min(10.0, score + 1.0)
            elif pe > 100:
                score = max(2.0, score - 2.0)

            # 历史分位修正：percentile_pe=0.2 表示当前 PE 比历史上 80% 的时间便宜
            # 给予 +1.5 分的加成（历史低估）
            if percentile_info and percentile_info.get("percentile_pe") is not None:
                pct = percentile_info["percentile_pe"]
                if pct < 0.2:
                    score = min(10.0, score + 1.5)  # 历史极低分位，加分
                elif pct < 0.4:
                    score = min(10.0, score + 0.8)  # 历史偏低分位，轻微加分
                elif pct > 0.8:
                    score = max(2.0, score - 1.5)  # 历史极高分位，减分

            sub_scores.append(score)
            weights.append(0.55)

        # PB 评分
        pb = factors.get("pb")
        if pb is not None and pb > 0:
            score = linear_score(pb, x_min=0.5, x_low=1.5, x_high=10, x_max=30, reverse=False)

            # 历史分位修正
            if percentile_info and percentile_info.get("percentile_pb") is not None:
                pct = percentile_info["percentile_pb"]
                if pct < 0.2:
                    score = min(10.0, score + 1.5)
                elif pct < 0.4:
                    score = min(10.0, score + 0.8)
                elif pct > 0.8:
                    score = max(2.0, score - 1.5)

            sub_scores.append(score)
            weights.append(0.45)

        if not sub_scores:
            return None

        total_weight = sum(weights)
        return sum(s * w for s, w in zip(sub_scores, weights)) / total_weight

    # --------------------------------------------------------
    # 维度 3：技术动量评分（增强版：真实价格动量）
    # --------------------------------------------------------

    def _score_technical_momentum(self, factors: Dict[str, float], momentum_info: Dict[str, float] = None) -> float:
        """技术动量：趋势强度 + RSI + MACD + 波动率 + 真实价格动量。

        增强说明：
        - 在原有因子基础上，加入真实计算的 5/20/60 日价格动量
        - 金叉（gold_cross）= 强烈看涨信号，给予额外加分
        - 死叉（death_cross）= 警示信号，给予扣分
        - 成交放量（volume_ratio > 1.5）= 资金关注，增强动量可信度
        """
        sub_scores = []
        weights = []

        # Trend strength：0 或 1
        ts = factors.get("trend_strength")
        if ts is not None:
            score = 3.0 + ts * 6.0
            sub_scores.append(score)
            weights.append(0.20)

        # RSI 14：健康区域是 45-70
        rsi = factors.get("rsi_14")
        if rsi is not None:
            score = linear_score(rsi, x_min=20, x_low=45, x_high=70, x_max=85)
            sub_scores.append(score)
            weights.append(0.15)

        # MACD hist：正值表示动能上行
        macd = factors.get("macd_hist")
        if macd is not None:
            score = linear_score(macd, x_min=-5, x_low=0, x_high=5, x_max=15)
            sub_scores.append(score)
            weights.append(0.15)

        # 波动率
        vol = factors.get("volatility_20")
        if vol is not None:
            score = linear_score(vol, x_min=0.1, x_low=0.4, x_high=1.0, x_max=2.0)
            sub_scores.append(score)
            weights.append(0.05)

        # === 新增：真实价格动量评分 ===
        if momentum_info:
            # 5 日动量：+5% 以上得高分，-5% 以下得低分
            mom5 = momentum_info.get("momentum_5d")
            if mom5 is not None:
                score = linear_score(mom5, x_min=-10, x_low=0, x_high=8, x_max=20)
                sub_scores.append(score)
                weights.append(0.15)

            # 20 日动量：中期趋势
            mom20 = momentum_info.get("momentum_20d")
            if mom20 is not None:
                score = linear_score(mom20, x_min=-20, x_low=0, x_high=15, x_max=40)
                sub_scores.append(score)
                weights.append(0.20)

            # MACD 信号加成/减成
            macd_sig = momentum_info.get("macd_signal")
            if macd_sig:
                bonus = 0
                if macd_sig == "gold_cross":
                    bonus = 2.5   # 金叉：强烈看涨
                elif macd_sig == "bullish":
                    bonus = 1.0   # MACD 为正
                elif macd_sig == "death_cross":
                    bonus = -2.5  # 死叉：看跌警示
                elif macd_sig == "bearish":
                    bonus = -1.0  # MACD 为负
                # bonus 暂时不加入 sub_scores，作为后处理加成

        if not sub_scores:
            return None

        total_weight = sum(weights)
        base_score = sum(s * w for s, w in zip(sub_scores, weights)) / total_weight

        # MACD 信号后处理加成/减成
        if momentum_info and momentum_info.get("macd_signal"):
            sig = momentum_info["macd_signal"]
            if sig == "gold_cross":
                base_score = min(10.0, base_score + 2.0)
            elif sig == "bullish":
                base_score = min(10.0, base_score + 0.8)
            elif sig == "death_cross":
                base_score = max(0.0, base_score - 2.0)
            elif sig == "bearish":
                base_score = max(0.0, base_score - 0.8)

        return base_score

    # --------------------------------------------------------
    # 维度 4：主题相关性评分
    # --------------------------------------------------------

    def _score_theme_relevance(self, ts_code: str, pool_info: Dict[str, str]) -> float:
        """主题相关性：是否属于我们关注的 5 大科技赛道。
        
        评分方式：
            - 有 sector 标签且在 FOCUS_THEMES 中 → 基础分 + 层级加分
            - pool_type 越高（recommended > candidate > watchlist > seed）加分越多
            - 不在任何主题中 → 0-3 分（象征性分）
        """
        sector = pool_info.get("sector", "")
        pool_type = pool_info.get("pool_type", "")

        # 基础分：如果在关注主题中
        if sector and sector in FOCUS_THEMES:
            base_score = FOCUS_THEMES[sector]["base_score"]
        elif sector:
            base_score = 3.0  # 有主题标签但不在关注列表
        else:
            base_score = 1.0  # 无主题标签

        # 层级加分：越受关注的池子加越多
        pool_bonus = {
            "recommended": 3.0,
            "candidate": 2.0,
            "watchlist": 1.0,
            "seed": 0.5,
            "portfolio_seed": 0.3,
            "us_benchmark": 0.2,
        }.get(pool_type, 0.0)

        return clamp(base_score + pool_bonus)

    # --------------------------------------------------------
    # 维度 5：产业位置评分（增强版：行业内相对排名）
    # --------------------------------------------------------

    def _score_industry_position(self, factors: Dict[str, float], industry_rank: Dict[str, float] = None) -> float:
        """产业位置：市值 + 行业内 ROE 相对排名。

        增强说明：
        - 在原有市值评分基础上，加入行业内 ROE/营收增速排名
        - 例如：ROE 排名在行业前 20%（rank_roe=0.8）→ 加分
        - 如果没有行业排名数据，退化为纯市值评分
        """
        # 基础分：纯市值评分
        mcap = factors.get("market_cap") or factors.get("float_market_cap")
        if mcap is None:
            return None

        if mcap < 50:
            base_score = 3.0
        elif 50 <= mcap < 200:
            base_score = 6.0
        elif 200 <= mcap < 1000:
            base_score = 8.5
        elif 1000 <= mcap < 5000:
            base_score = 9.0
        elif 5000 <= mcap < 15000:
            base_score = 8.0
        else:
            base_score = 7.0

        # 行业排名加成
        if industry_rank:
            rank_roe = industry_rank.get("rank_roe")
            if rank_roe is not None:
                # rank_roe=1.0 表示比行业 100% 的公司 ROE 高（最好）
                # rank_roe=0.0 表示比行业所有人都低（最差）
                # 加成：排名前 30% 给予 +1.5 分，后 30% 扣 -1.0 分
                if rank_roe >= 0.7:
                    base_score = min(10.0, base_score + 1.5)
                elif rank_roe >= 0.5:
                    base_score = min(10.0, base_score + 0.5)
                elif rank_roe < 0.3:
                    base_score = max(0.0, base_score - 1.0)

            rank_rev = industry_rank.get("rank_revenue_growth")
            if rank_rev is not None:
                if rank_rev >= 0.7:
                    base_score = min(10.0, base_score + 1.0)
                elif rank_rev < 0.3:
                    base_score = max(0.0, base_score - 0.5)

        return base_score

    # --------------------------------------------------------
    # 警示信号检测
    # --------------------------------------------------------

    def _detect_red_flags(self, factors: Dict[str, float], value_scores: Dict[str, float]) -> List[str]:
        """从因子和评分结果中提取警示信号。返回人类可读的警示列表。"""
        flags = []

        # PE 极高
        pe = factors.get("pe_ttm") or factors.get("pe_dynamic")
        if pe is not None:
            if pe > 100:
                flags.append(f"PE={pe:.0f}，估值偏高")
            elif pe <= 0:
                flags.append("PE为负，盈利可能有问题")

        # ROE 为负或极低
        roe = factors.get("roe_est") or factors.get("roe_reported")
        if roe is not None and roe < 5:
            flags.append(f"ROE={roe:.1f}%，盈利能力偏弱")

        # RSI 超买
        rsi = factors.get("rsi_14")
        if rsi is not None and rsi > 75:
            flags.append(f"RSI={rsi:.1f}，短线可能过热")

        # 技术动量但估值太高
        val_score = value_scores.get("valuation_position")
        tech_score = value_scores.get("technical_momentum")
        if val_score is not None and tech_score is not None:
            if tech_score >= 7 and val_score <= 3:
                flags.append("技术面强但估值偏高，注意追高风险")

        return flags

    # --------------------------------------------------------
    # 主入口：对一只标的生成完整的评分卡
    # --------------------------------------------------------

    def score(self, ts_code: str, extra_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """对一只标的生成完整的5维评分卡。

        参数：
            ts_code: 标的代码，例如 "300308.SZ"
            extra_context: （可选）额外的上下文信息，例如机会雷达中的名称、市场标签

        返回：
            一个字典，包含 ts_code、5 个维度得分、综合得分、警示信号、数据可用级别
        """
        factors = self._load_factors(ts_code)
        pool_info = self._load_pool_info(ts_code)

        # === 新增：计算增强数据 ===
        # PE/PB 历史分位（用于估值评分增强）
        percentile_info = self._compute_pe_pb_percentile(ts_code)
        # 真实价格动量（用于技术评分增强）
        momentum_info = self._compute_price_momentum(ts_code)
        # 行业内相对排名（用于产业评分增强）
        sector = pool_info.get("sector", "")
        industry_rank = self._compute_industry_rank(ts_code, sector) if sector else {}

        # 逐个维度计算分数（传入增强数据）
        scores = {
            "fundamental_quality": self._score_fundamental(factors),
            "valuation_position": self._score_valuation(factors, percentile_info),
            "technical_momentum": self._score_technical_momentum(factors, momentum_info),
            "theme_relevance": self._score_theme_relevance(ts_code, pool_info),
            "industry_position": self._score_industry_position(factors, industry_rank),
        }

        # 计算综合得分（加权平均）
        available_scores = []
        available_weights = []
        for dim, w in DIMENSION_WEIGHTS.items():
            s = scores.get(dim)
            if s is not None:
                available_scores.append(s)
                available_weights.append(w)

        if available_scores:
            total_w = sum(available_weights)
            composite = clamp(sum(s * w for s, w in zip(available_scores, available_weights)) / total_w)
        else:
            composite = None

        # 判断数据可用级别
        non_null = sum(1 for v in scores.values() if v is not None)
        if non_null >= 4:
            data_level = "full"
        elif non_null >= 2:
            data_level = "partial"
        else:
            data_level = "none"

        # 生成警示信号
        red_flags = self._detect_red_flags(factors, scores)

        # 整合输出（包含增强数据）
        result = {
            "ts_code": ts_code,
            "name": (extra_context or {}).get("name", ""),
            "market": (extra_context or {}).get("market", ""),
            "sector": pool_info.get("sector", ""),
            "pool_type": pool_info.get("pool_type", ""),
            "fundamental_quality": round(scores["fundamental_quality"], 2) if scores["fundamental_quality"] else None,
            "valuation_position": round(scores["valuation_position"], 2) if scores["valuation_position"] else None,
            "technical_momentum": round(scores["technical_momentum"], 2) if scores["technical_momentum"] else None,
            "theme_relevance": round(scores["theme_relevance"], 2) if scores["theme_relevance"] else None,
            "industry_position": round(scores["industry_position"], 2) if scores["industry_position"] else None,
            "composite_score": round(composite, 2) if composite else None,
            "red_flags": red_flags,
            "data_available_level": data_level,
            "factor_snapshot_date": factors and self._get_latest_factor_date(ts_code),
            # === 新增：增强数据字段 ===
            "pe_percentile": round(percentile_info.get("percentile_pe"), 3) if percentile_info.get("percentile_pe") is not None else None,
            "pb_percentile": round(percentile_info.get("percentile_pb"), 3) if percentile_info.get("percentile_pb") is not None else None,
            "momentum_5d": round(momentum_info.get("momentum_5d"), 2) if momentum_info.get("momentum_5d") is not None else None,
            "momentum_20d": round(momentum_info.get("momentum_20d"), 2) if momentum_info.get("momentum_20d") is not None else None,
            "momentum_60d": round(momentum_info.get("momentum_60d"), 2) if momentum_info.get("momentum_60d") is not None else None,
            "macd_signal": momentum_info.get("macd_signal"),
            "volume_ratio": round(momentum_info.get("volume_ratio"), 2) if momentum_info.get("volume_ratio") is not None else None,
            "rank_roe": round(industry_rank.get("rank_roe"), 3) if industry_rank.get("rank_roe") is not None else None,
            "rank_revenue_growth": round(industry_rank.get("rank_revenue_growth"), 3) if industry_rank.get("rank_revenue_growth") is not None else None,
            "rank_pe": round(industry_rank.get("rank_pe"), 3) if industry_rank.get("rank_pe") is not None else None,
        }

        return result

    def _get_latest_factor_date(self, ts_code: str) -> str:
        """获取该标的最新的因子日期。"""
        row = self.conn.execute(
            "SELECT MAX(trade_date) FROM factor_daily WHERE ts_code=?", (ts_code,)
        ).fetchone()
        return row[0] if row and row[0] else ""


# ============================================================
# 批量评分：一次给多只标的评分
# ============================================================

def build_all_value_scores(conn: sqlite3.Connection, ts_codes: List[str]) -> List[Dict[str, Any]]:
    """批量对多只标的生成价值评分卡。
    
    参数：
        conn: 数据库连接
        ts_codes: 标的代码列表，例如 ["300308.SZ", "688041.SH", ...]
    
    返回：
        按 composite_score 从高到低排序的评分卡列表
    """
    scorer = ValueScoreCard(conn)
    results = []
    for code in ts_codes:
        card = scorer.score(code)
        results.append(card)
    
    # 按综合得分降序排列（None 的排到最后）
    results.sort(key=lambda item: -(item["composite_score"] if item["composite_score"] else -1))
    return results


# ============================================================
# Markdown 渲染：把评分卡转为人类可读的表格/区块
# ============================================================

def _score_bar(score: Optional[float], width: int = 10) -> str:
    """把 0-10 分转为可视化的进度条。内部函数，不对外暴露。"""
    if score is None:
        return " " * width + " N/A"
    filled = int(score / 10 * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {score:.1f}"


def _score_label(score: Optional[float]) -> str:
    """根据分数给出人类可读的评价。"""
    if score is None:
        return "无数据"
    if score >= 8.5:
        return "优秀"
    if score >= 7.0:
        return "良好"
    if score >= 5.5:
        return "中等"
    if score >= 4.0:
        return "偏弱"
    return "需关注"


def render_value_score_section(score_cards: List[Dict[str, Any]], max_items: int = 10) -> str:
    """把评分卡列表渲染成 Markdown 区块，供机会雷达/其他报告使用。
    
    参数：
        score_cards: build_all_value_scores 返回的评分卡列表
        max_items: 最多显示几只标的（默认10）
    
    返回：
        Markdown 字符串（包含标题 + 表格 + 警示摘要）
    """
    if not score_cards:
        return "\n## 价值评分\n- 暂无可用评分数据\n"

    lines = ["\n## 价值评分卡 Top %d" % min(max_items, len(score_cards)),
             "",
             "_5 维价值评分：基本面 / 估值 / 技术动量 / 主题相关性 / 产业位置。满分 10 分，加权合成。_",
             ""]

    # 表格：标的 | 综合 | 基本面 | 估值 | 技术动量 | 主题 | 产业 | 警示
    lines.append("| 标的 | 综合 | 基本面 | 估值 | 技术 | 主题 | 产业 | 数据 | 警示 |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |")

    shown = 0
    for card in score_cards:
        if card["data_available_level"] == "none":
            continue  # 完全没数据的不显示

        name = card.get("name") or card["ts_code"]
        ts = card["ts_code"]
        composite = card.get("composite_score")
        if composite is None:
            continue

        level_label = {"full": "完整", "partial": "部分", "none": "缺失"}.get(card["data_available_level"], "-")

        # 把各维度得分渲染成简洁数值
        scores_cell = " / ".join(
            f"{card[d]:.1f}" if card.get(d) is not None else "-"
            for d in ["fundamental_quality", "valuation_position",
                     "technical_momentum", "theme_relevance", "industry_position"]
        )

        # 警示符号，简单显示
        flag_count = len(card.get("red_flags", []))
        flag_text = "⚠️×{}".format(flag_count) if flag_count else "✓"

        # 只取综合分、主题、警示（表格不要太挤）
        lines.append(
            "| {name} ({ts}) | {comp:.1f} | {fq} | {val} | {tec} | {th} | {ip} | {lv} | {fl} |".format(
                name=name, ts=ts, comp=composite,
                fq=f"{card['fundamental_quality']:.1f}" if card.get("fundamental_quality") else "-",
                val=f"{card['valuation_position']:.1f}" if card.get("valuation_position") else "-",
                tec=f"{card['technical_momentum']:.1f}" if card.get("technical_momentum") else "-",
                th=f"{card['theme_relevance']:.1f}" if card.get("theme_relevance") else "-",
                ip=f"{card['industry_position']:.1f}" if card.get("industry_position") else "-",
                lv=level_label,
                fl=flag_text,
            )
        )
        shown += 1
        if shown >= max_items:
            break

    if shown == 0:
        lines.append("| _（当前没有足够的价值因子数据用于评分。运行 fundamental.py 以补全基本面数据）_ |")

    # 警示摘要
    lines.append("")
    lines.append("### 警示摘要")
    any_flag = False
    for card in score_cards[:max_items]:
        flags = card.get("red_flags", [])
        if flags:
            any_flag = True
            lines.append("- **{} ({}):** {}".format(
                card.get("name") or card["ts_code"],
                card["ts_code"],
                "; ".join(flags)
            ))
    if not any_flag:
        lines.append("- _暂无显著警示信号。_")

    # 附加说明
    lines.append("")
    lines.append("_说明：'综合'=5 维加权合成；'数据'列表示该标的可用的维度数量（完整=5维都有数据）。_")
    lines.append("")

    return "\n".join(lines)


# ============================================================
# 便捷的交互式运行
# ============================================================

def _find_all_tracked_codes(conn: sqlite3.Connection) -> List[str]:
    """从 daily_bar + us_daily_bar 读取所有被跟踪的标的代码（A股/H股/美股都包含。

    【小白讲解】原来只从 daily_bar 读取 A股和 H股，现在加上 us_daily_bar，美股也能评分了。
    """
    # A股/H股代码：daily_bar 里存的是 ts_code（如 300308.SZ、00981.HK）
    ah_codes = [r[0] for r in conn.execute("SELECT DISTINCT ts_code FROM daily_bar ORDER BY ts_code").fetchall()]
    # 美股代码：us_daily_bar 里存的是 symbol（如 NVDA、MRVL 等纯字母代码）
    us_codes = [r[0] for r in conn.execute("SELECT DISTINCT symbol FROM us_daily_bar ORDER BY symbol").fetchall()]
    rows = ah_codes + us_codes
    return rows


if __name__ == "__main__":
    # 直接运行时：扫描数据库中所有标的，逐一打分，并打印摘要
    import os
    DB_PATH = Path(__file__).resolve().parents[1].parents[0] / "01_data" / "db" / "smr.db"
    # 修正：使用项目根目录下的 db 路径
    project_root = Path(__file__).resolve().parents[2]
    DB_PATH = project_root / "01_data" / "db" / "smr.db"

    if not DB_PATH.exists():
        print(f"找不到数据库：{DB_PATH}")
        exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    all_codes = _find_all_tracked_codes(conn)
    print(f"在库中找到 {len(all_codes)} 只标的。开始生成价值评分...\n")

    scorecards = build_all_value_scores(conn, all_codes)

    # 输出简化版表格
    print("=" * 110)
    print(f"{'标的':25s} {'综合':>6s} {'基本面':>8s} {'估值':>6s} {'技术':>6s} {'主题':>6s} {'产业':>6s} {'数据':>6s} 警示")
    print("-" * 110)
    for card in scorecards:
        if card["data_available_level"] == "none":
            continue
        name = card.get("ts_code", "")
        c = card.get("composite_score")
        if c is None:
            continue
        flag_txt = "; ".join(card.get("red_flags", [])) if card.get("red_flags") else "-"
        print(f"{name:25s} {c:6.1f} "
              f"{card['fundamental_quality'] if card['fundamental_quality'] else '-':>8} "
              f"{card['valuation_position'] if card['valuation_position'] else '-':>6} "
              f"{card['technical_momentum'] if card['technical_momentum'] else '-':>6} "
              f"{card['theme_relevance'] if card['theme_relevance'] else '-':>6} "
              f"{card['industry_position'] if card['industry_position'] else '-':>6} "
              f"{card['data_available_level']:>6s} {flag_txt}")

    print("=" * 110)
    print(f"\n共 {sum(1 for c in scorecards if c['data_available_level'] != 'none')} 只有可用评分数据的标的。")
    conn.close()
