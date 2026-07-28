"""
研究记忆持久化模块（Research Memory Persistence）

功能说明：
    阶段 7「记忆持久化」：把「每一次做出的投资决策、主题筛选结论、公司信号计划」
    写入到工作记忆目录（memory/projects/...）里，做到：
        1. 跨会话（跨 chat session）能找回我上次研究过什么
        2. 给未来的「主题 → 个股 → 买入 → 跟踪 → 卖出」全周期复盘留痕
        3. 小白友好：不会写一堆看不懂的 json 结构，每一个归档都有人类可读的 .md 摘要

    归档范围（3 类，master plan 阶段 9）：
        * 主题预期差（theme_expectation_gap）：候选矩阵 + TOP 3 + 待办
        * 公司信号计划（company_signal_plan）：4 态分布 + 传导进度 + 建仓 ready
        * 投资决策（pair_switch_decision / thesis_update / portfolio_decision）：
          最终结论 + 关键假设 + 风险 + 后续动作

参数说明：
    ResearchMemory.from_env()           - 从 env(SMR_MEMORY_ROOT) 构造实例，
                                          默认路径 PROJECT_ROOT/memory
    persist_theme_gap(...)               - 归档一次 theme_expectation_gap 工作流的产物
    persist_signal_plan(...)             - 归档一次 company_signal_plan 的产物
    persist_decision(...)                - 归档任意"投资决策"（任意工作流最后都可调用）
    list_recent(kind, days)              - 查最近 N 天我做了什么（小白查历史用）

返回值说明：
    - 所有 persist_* 返回 (archive_dir: Path, summary_md_path: Path)
    - 失败时返回 (None, None)（不抛异常，不会让主工作流崩）

异常处理：
    - memory 目录不可写 / 磁盘满 → try/except，返回 (None, None) + 打 warning
    - 参数类型错 / 空 → 跳过写 json，只写 summary.md（降级）
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _json_default(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, set):
        return list(obj)
    raise TypeError(f"Type {type(obj).__name__} not JSON serializable")


def _safe_stem(s: str) -> str:
    """把任意字符串变成文件名安全的 stem（Windows 不能有 <>:"\\|?*）"""
    bad = '<>:"/\\|?*\n\r\t'
    out = "".join(c if c not in bad else "_" for c in s).strip()
    if not out:
        out = "untitled"
    return out[:80]


class ResearchMemory:
    """
    研究记忆持久化（小白版讲解）
        1) from_env() 初始化（读取 SMR_MEMORY_ROOT，默认写在项目目录 memory）
        2) 每次工作流结尾，调一次 persist_xxx(...)
        3) 记忆目录会自动建：memory/projects/<project>/<YYYYMMDD>/<kind>_<name>_<ts>/
           里面每次有：meta.json + summary.md + 可选 payload.json
    """

    def __init__(self, root: Path, project_name: str = "default"):
        self.root = Path(root).expanduser().resolve()
        self.project_name = project_name
        self.project_dir = self.root / "projects" / _safe_stem(project_name)
        self.project_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls, project_name: str | None = None) -> "ResearchMemory":
        """
        从环境变量 SMR_MEMORY_ROOT 构建；
        若未设置，默认用 <PROJECT_ROOT>/memory
        """
        root = os.environ.get("SMR_MEMORY_ROOT") or str(PROJECT_ROOT / "memory")
        return cls(Path(root), project_name=project_name or cls._default_project())

    @staticmethod
    def _default_project() -> str:
        # 小白友好：如果项目目录名里有 TH 就拿 TH_... 里的项目名
        name = PROJECT_ROOT.name or "default"
        # 去中文 / 特殊字符时保留，只 stem
        return _safe_stem(name)

    # ------------------------------------------------------------------
    # 通用：建归档目录 + 写 meta + 写 summary_md + 写 payload
    # ------------------------------------------------------------------
    def _mk_archive_dir(self, kind: str, name: str) -> Path:
        today = datetime.now().strftime("%Y%m%d")
        ts = datetime.now().strftime("%H%M%S")
        d = self.project_dir / today / f"{kind}_{_safe_stem(name)}_{ts}"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @staticmethod
    def _write(path: Path, text: str) -> None:
        try:
            path.write_text(text, encoding="utf-8")
        except Exception:
            pass  # 磁盘满 / 不可写就静默忽略

    # ------------------------------------------------------------------
    # 1) 主题预期差归档（theme_expectation_gap 工作流结尾）
    # ------------------------------------------------------------------
    def persist_theme_gap(
        self,
        *,
        theme_name: str,
        theme_id: str,
        top_candidates: list[dict],
        universe_summary: dict,
        artifacts_dir: str,
        extra: Optional[dict] = None,
    ) -> tuple[Optional[Path], Optional[Path]]:
        """
        归档一次「主题预期差筛选」结果

        参数：
            theme_name / theme_id   - 主题名
            top_candidates          - list[dict] 每条至少 ticker/name/score/recommendation
            universe_summary        - {included_count, excluded_count, ...}
            artifacts_dir           - 本次工作流输出目录（绝对路径）
            extra                   - 其他想记的（运行时间、人、机器）
        返回 (archive_dir, summary_md_path)，错了返回 (None, None)
        """
        try:
            d = self._mk_archive_dir("theme_gap", theme_id or theme_name)
            meta = {
                "kind": "theme_expectation_gap",
                "theme_name": theme_name,
                "theme_id": theme_id,
                "top_candidates": top_candidates[:10],
                "universe_summary": universe_summary,
                "artifacts_dir": artifacts_dir,
                "created_at_iso": datetime.now(timezone.utc).isoformat(),
                "extra": extra or {},
            }
            self._write(d / "meta.json", json.dumps(meta, ensure_ascii=False, indent=2))
            self._write(d / "payload.json",
                        json.dumps({"top_candidates": top_candidates,
                                    "universe_summary": universe_summary},
                                   default=_json_default, ensure_ascii=False, indent=2))
            md_lines = [
                f"# 主题预期差归档：{theme_name}（{theme_id}）",
                "",
                f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- 候选全览：入选 {universe_summary.get('included_count', '?')} 只，"
                f"排除 {universe_summary.get('excluded_count', '?')} 只",
                f"- 工作流制品目录：`{artifacts_dir}`",
                "",
                "## TOP 候选",
                "",
                "| # | Ticker | 名称 | 总分 | 推荐 |",
                "|---:|---|---|---:|---|",
            ]
            for i, c in enumerate(top_candidates[:10], 1):
                md_lines.append(
                    f"| {i} | {c.get('ticker','-')} | {c.get('name','-')} | "
                    f"{c.get('total_score','-')} | {c.get('recommendation_label','') or c.get('recommendation','')} |"
                )
            md_lines.append("")
            if extra:
                md_lines.append("## 额外备注")
                md_lines.append("")
                for k, v in extra.items():
                    md_lines.append(f"- {k}: {v}")
                md_lines.append("")
            self._write(d / "summary.md", "\n".join(md_lines))
            return d, d / "summary.md"
        except Exception:
            return None, None

    # ------------------------------------------------------------------
    # 2) 公司信号计划归档（company_signal_plan 工作流结尾）
    # ------------------------------------------------------------------
    def persist_signal_plan(
        self,
        *,
        plan: Any,  # CompanySignalPlan（延迟导入，避免循环）
        timelines: list[Any],  # list[TransmissionTimeline]
        artifacts_dir: str,
        extra: Optional[dict] = None,
    ) -> tuple[Optional[Path], Optional[Path]]:
        """
        归档一次「公司信号计划」

        参数：
            plan              - CompanySignalPlan（整份，会 asdict）
            timelines         - list[TransmissionTimeline]
            artifacts_dir     - 本次制品目录
            extra             - 附加字段
        """
        try:
            ticker = getattr(plan, "ticker", "UNKNOWN")
            name = getattr(plan, "name", "") or ticker
            d = self._mk_archive_dir("signal_plan", ticker)
            # payload（简化，不让 memory 爆）
            payload = {
                "plan": asdict(plan) if is_dataclass(plan) else {"error": "not dataclass"},
                "timelines": [],
            }
            for t in timelines:
                try:
                    t_dict = {
                        "ticker": t.ticker, "name": t.name,
                        "template_id": t.template.template_id,
                        "template_name": t.template.name,
                        "overall_progress_pct": t.overall_progress_pct,
                        "notes": t.notes, "warnings": t.warnings,
                    }
                    payload["timelines"].append(t_dict)
                except Exception:
                    continue
            meta = {
                "kind": "company_signal_plan",
                "ticker": ticker, "name": name,
                "plan_id": getattr(plan, "plan_id", ""),
                "state_summary": getattr(plan, "state_summary", {}),
                "overall_confidence": getattr(plan, "overall_confidence", None),
                "building_position_ready": getattr(plan, "building_position_ready", None),
                "artifacts_dir": artifacts_dir,
                "created_at_iso": datetime.now(timezone.utc).isoformat(),
                "extra": extra or {},
            }
            self._write(d / "meta.json", json.dumps(meta, ensure_ascii=False, indent=2))
            self._write(d / "payload.json",
                        json.dumps(payload, default=_json_default, ensure_ascii=False, indent=2))
            lines = [
                f"# 公司信号计划归档：{name}（{ticker}）",
                "",
                f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- plan_id：`{getattr(plan, 'plan_id','')}`",
                f"- 总体信心度：**{float(getattr(plan, 'overall_confidence', 0) or 0):.0%}**",
                f"- 建仓准备度：{'✅' if getattr(plan, 'building_position_ready', False) else '⛔'}",
                f"- 工作流制品：`{artifacts_dir}`",
                "",
                "## 信号 4 态分布",
                "",
            ]
            state_summ = getattr(plan, "state_summary", {}) or {}
            for st, label in [("observing","观察期"), ("first_confirm","首次确认"),
                              ("double_confirm","双变量确认"), ("invalidated","已证伪")]:
                lines.append(f"- {label}：{state_summ.get(st, 0)} 条")
            lines.append("")
            lines.append("## 传导轴进度")
            lines.append("")
            for t in timelines:
                lines.append(
                    f"- {t.template.name} → **{t.overall_progress_pct:.1f}%**；"
                    f"{t.notes}"
                )
                if t.warnings:
                    for w in t.warnings[:3]:
                        lines.append(f"  - ⚠️ {w}")
            lines.append("")
            if extra:
                lines.append("## 额外")
                for k, v in extra.items():
                    lines.append(f"- {k}: {v}")
                lines.append("")
            self._write(d / "summary.md", "\n".join(lines))
            return d, d / "summary.md"
        except Exception:
            return None, None

    # ------------------------------------------------------------------
    # 3) 投资决策归档（pair_switch / thesis_update / portfolio 都能挂）
    # ------------------------------------------------------------------
    def persist_decision(
        self,
        *,
        decision_kind: str,      # pair_switch / thesis_update / portfolio / custom
        title: str,
        conclusion: str,         # 人话：最后结论（"不换" / "换仓 1/3" ...）
        key_assumptions: list[str],
        risks: list[str],
        next_actions: list[str],
        artifacts_dir: str,
        extra: Optional[dict] = None,
    ) -> tuple[Optional[Path], Optional[Path]]:
        """
        归档任意一个"投资决策"

        参数：
            decision_kind   - 决策类型
            title           - 标题
            conclusion      - 结论（一句话）
            key_assumptions - 关键假设列表
            risks           - 风险列表
            next_actions    - 后续动作
            artifacts_dir   - 工作流制品目录
        """
        try:
            d = self._mk_archive_dir(f"decision_{decision_kind}", title)
            meta = {
                "kind": "decision", "decision_kind": decision_kind,
                "title": title, "conclusion": conclusion,
                "key_assumptions": key_assumptions, "risks": risks,
                "next_actions": next_actions, "artifacts_dir": artifacts_dir,
                "created_at_iso": datetime.now(timezone.utc).isoformat(),
                "extra": extra or {},
            }
            self._write(d / "meta.json", json.dumps(meta, ensure_ascii=False, indent=2))
            lines = [
                f"# 决策归档：{title}",
                "",
                f"- 类型：{decision_kind}",
                f"- 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- 最终结论：**{conclusion}**",
                f"- 制品目录：`{artifacts_dir}`",
                "",
                "## 关键假设",
                ""
            ]
            if key_assumptions:
                for a in key_assumptions:
                    lines.append(f"- {a}")
            else:
                lines.append("- （空，请下次写出来，不写没法复盘）")
            lines.append("")
            lines.append("## 风险")
            lines.append("")
            if risks:
                for r in risks:
                    lines.append(f"- {r}")
            else:
                lines.append("- （没写风险=风险极高，下次补上）")
            lines.append("")
            lines.append("## 后续动作")
            lines.append("")
            if next_actions:
                for n in next_actions:
                    lines.append(f"- [ ] {n}")
            lines.append("")
            if extra:
                lines.append("## 附加")
                lines.append("")
                for k, v in extra.items():
                    lines.append(f"- {k}: {v}")
                lines.append("")
            self._write(d / "summary.md", "\n".join(lines))
            return d, d / "summary.md"
        except Exception:
            return None, None

    # ------------------------------------------------------------------
    # 查询：最近 N 天我做了什么
    # ------------------------------------------------------------------
    def list_recent(
        self, kind: Optional[str] = None, days: int = 30,
    ) -> list[dict]:
        """
        按归档目录，列出最近 N 天做过的归档（给小白找历史）

        参数：
            kind   - 可选过滤：'theme_gap' / 'signal_plan' / 'decision_*'，None=全
            days   - 回溯 N 天
        返回 list[dict]：{date, kind, path, title}
        """
        results: list[dict] = []
        now = datetime.now()
        cutoff = (now - timedelta(days=max(0, days))).date()
        project = self.project_dir
        if not project.exists():
            return results
        # 子目录结构：project_dir / <YYYYMMDD> / <kind>_<name>_<ts> /
        for day_dir in project.iterdir():
            if not day_dir.is_dir():
                continue
            try:
                day_date = datetime.strptime(day_dir.name, "%Y%m%d").date()
            except ValueError:
                continue
            if day_date < cutoff:
                continue
            for sub in day_dir.iterdir():
                if not sub.is_dir():
                    continue
                # 推断 kind / title
                name_split = sub.name.split("_")
                k = name_split[0] if name_split else ""
                # kind 过滤
                if kind and not k.startswith(kind):
                    continue
                title = "_".join(name_split[1:-1]) if len(name_split) >= 3 else sub.name
                results.append({
                    "date": day_dir.name,
                    "kind": k,
                    "title": title,
                    "path": str(sub),
                    "summary_md": str(sub / "summary.md") if (sub / "summary.md").exists() else "",
                    "created_at": datetime.fromtimestamp(sub.stat().st_mtime).isoformat(timespec="seconds"),
                })
        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results
