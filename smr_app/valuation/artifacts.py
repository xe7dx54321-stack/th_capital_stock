"""
制品生成 - 保存估值模型 JSON、Markdown 和 CSV

功能说明：
    把估值结果保存为 JSON（可复算）、Markdown（可阅读）和 CSV（可分析）。
    核心原则：保存的 JSON 必须能完全复算所有数字。

参数说明：
    save_model(result, output_dir) - 保存模型到文件
    to_markdown(result) - 转换为 Markdown 表格
    to_csv(result) - 转换为 CSV

返回值说明：
    save_model 返回文件路径字典
    to_markdown 返回 Markdown 字符串
    to_csv 返回 CSV 字符串

异常处理：
    文件写入失败时抛出 IOError
"""

import json
import os
from datetime import datetime


class ArtifactGenerator:
    """
    制品生成器

    小白讲解：
        这是"打包员"——把厨师做好的菜打包成三种格式：
        - JSON：机器可读，包含全部输入和输出，可以重新验证计算
        - Markdown：人可读，包含摘要表格和分析结论
        - CSV：Excel 可分析，包含逐年预测数据
    """

    def save_model(self, result, output_dir: str, entity_key: str = None) -> dict:
        """
        保存估值模型到文件

        参数:
            result: ValuationResult 对象
            output_dir: 输出目录
            entity_key: 实体标识（用于文件名）

        返回:
            {"json": 路径, "markdown": 路径, "csv": 路径}
        """
        os.makedirs(output_dir, exist_ok=True)
        key = entity_key or result.entity_key or "unknown"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"valuation_{key}_{timestamp}"

        paths = {}

        # JSON
        json_path = os.path.join(output_dir, f"{base_name}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self._result_to_dict(result), f, ensure_ascii=False, indent=2)
        paths["json"] = json_path

        # Markdown
        md_path = os.path.join(output_dir, f"{base_name}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self.to_markdown(result))
        paths["markdown"] = md_path

        # CSV
        csv_path = os.path.join(output_dir, f"{base_name}.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(self.to_csv(result))
        paths["csv"] = csv_path

        return paths

    def to_markdown(self, result) -> str:
        """转换为 Markdown 格式"""
        lines = []
        lines.append(f"# 估值报告 - {result.entity_key}")
        lines.append(f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 摘要
        lines.append("## 摘要\n")
        lines.append("| 指标 | 值 |")
        lines.append("|---|---|")
        for key, value in result.summary.items():
            if isinstance(value, float):
                lines.append(f"| {key} | {value:.4f} |")
            else:
                lines.append(f"| {key} | {value} |")

        # 预测表
        lines.append("\n## 逐年预测\n")
        if result.projections:
            years = sorted(set(
                year for proj in result.projections.values()
                for year in proj.keys()
            )) if result.projections else []

            if years:
                header = "| 指标 | " + " | ".join(str(y) for y in years) + " |"
                sep = "|---|" + "---|" * len(years)
                lines.append(header)
                lines.append(sep)

                for metric, year_values in result.projections.items():
                    row = f"| {metric} |"
                    for year in years:
                        val = year_values.get(year, "")
                        if isinstance(val, float):
                            row += f" {val:.4f} |"
                        else:
                            row += f" {val} |"
                    lines.append(row)

        # 假设表
        lines.append("\n## 假设表\n")
        lines.append("| 年份 | 变量 | 标签 | 值 | 单位 | 来源 | 类型 |")
        lines.append("|---|---|---|---|---|---|---|")
        for a in result.assumptions_table:
            atype = "假设" if a.get("is_assumption") else "事实"
            lines.append(
                f"| {a.get('year')} | {a.get('variable')} | {a.get('label')} | "
                f"{a.get('value')} | {a.get('unit')} | {a.get('source')} | {atype} |"
            )

        # 警告
        if result.warnings:
            lines.append("\n## 警告\n")
            for w in result.warnings:
                lines.append(f"- {w}")

        return "\n".join(lines)

    def to_csv(self, result) -> str:
        """转换为 CSV 格式"""
        lines = ["year,metric,value"]

        for metric, year_values in result.projections.items():
            for year, value in sorted(year_values.items()):
                lines.append(f"{year},{metric},{value}")

        return "\n".join(lines)

    def _result_to_dict(self, result) -> dict:
        """把 ValuationResult 转换为可序列化的字典"""
        return {
            "entity_key": result.entity_key,
            "projections": result.projections,
            "summary": result.summary,
            "assumptions_table": result.assumptions_table,
            "input_snapshot": result.input_snapshot,
            "warnings": result.warnings,
            "generated_at": datetime.now().isoformat(),
        }
