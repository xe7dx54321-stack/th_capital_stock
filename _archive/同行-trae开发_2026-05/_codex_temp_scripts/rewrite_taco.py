#!/usr/bin/env python3
"""
Rewrite the TACO article with khazix style and proper image descriptions.
Then regenerate visuals and re-enqueue to wechat bridge.
"""

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CN_TZ = ZoneInfo("Asia/Shanghai")
ROOT = Path("/Users/apple/Documents/同行资本内容部门/内容生产系统")
PACK_DIR = ROOT / "05_draft_packs" / "taco_prediction_skill_20260409"
VISUAL_DIR = PACK_DIR / "visual-assets"
BRIDGE_OUTBOX = ROOT / "07_wechat_bridge_outbox"
SCRIPTS_DIR = ROOT / "09_runbooks" / "scripts"

# ========== Step 1: Rewrite wechat.md with khazix style ==========
WECHAT_MD = r"""# 微信稿｜今天你 TACO 了没？一套能帮你少亏钱的预测方法

最近每天盯特朗普的人，情绪大概率已经分裂了。

昨天说得像要狠狠干，今天语气又软了。上午像要把市场掀翻，下午又给了退路。

![TACO概率追踪工具](visual-assets/02__github_com_kirinjin2046_trump_skill.png)

很多人现在最大的问题，不是信息不够。

**是你永远分不清，这次到底是真升级，还是又一次 TACO。**

所谓 TACO，Trump Always Chickens Out。市场里已经把它当成一种熟悉的剧本了：

特朗普先把话说得很重，市场和对手都被吓一轮。但当真正的经济、政治、金融成本开始压上来，他又会往后退一步，给自己找一个台阶。

问题在于，普通人每次都是被动接收结果。等你意识到"哦，他又怂了"，行情早就走完一截了。

所以这篇不想再写成"特朗普今天又变了"的情绪稿。

**真正该学的，不是猜他下一句话，而是做一套能持续更新的 TACO 预测 skill。**

## 你真正要预测的，不是发言，是让步概率

很多人做判断，第一步就错了。

他们盯的是：
- 特朗普今天怎么说
- 标题写得多吓人
- 社交媒体情绪多炸

但真正该盯的不是这些表层动作。

**在这一轮表态之后，特朗普有没有足够大的动机继续硬顶下去。**

这才是 TACO 的核心。

因为特朗普的表态从来不只是情绪表达，它更像一种谈判动作。先抬高要价，先制造压迫感，先逼市场和对手先慌。

但如果后面的代价开始变得太高，他往往就会换一种说法，或者给出一个不那么难看的撤退版本。

所以你要预测的，不是"他是不是嘴硬"。

**这轮嘴硬背后，有没有足够大的现实约束，会逼他退。**

![约束识别：四类关键信号](visual-assets/81__slot_2.png)

## 这套 skill 的结构，5 层就够了

![TACO预测Skill五层架构](visual-assets/82__slot_3.png)

### 第 1 层：事件识别层

先把所有新动作归到同一个事件对象里，不要被零碎标题牵着跑。

这层只回答三件事：
1. 他这次说了什么
2. 他这次真的做了什么
3. 市场现在在为什么事波动

注意，**"说了什么"和"做了什么"必须分开记。** 很多时候市场被收割，就是因为大家把口头威胁直接当成落地动作了。

### 第 2 层：约束识别层

这是最关键的一层。

你要让系统去追的，不是更多情绪，而是更多约束。至少盯这四类：

- **市场反噬**：美股、债市、油价、美元有没有开始明显给负反馈
- **内部松动**：共和党内部、商界、盟友有没有开始释放不耐烦信号
- **口风软化**：白宫或核心官员有没有开始放"可谈、可延迟、可重新评估"的口风
- **核心利益受损**：真打下去会不会伤到特朗普最想保的东西——市场、选民感受、谈判筹码、个人叙事

一句话：**TACO 概率上升，不是因为他忽然变温和，而是因为继续强硬的成本开始变大。**

### 第 3 层：让步触发器层

这里要给系统明确的 trigger，不然它只会写空泛分析。

比如：
- 从"绝不退让"切成"仍有协商空间"
- 从"明确升级"切成"继续观察、继续评估"
- 从"亲自放狠话"切成"由官员释放更软版本"
- 从"打到底"切成"先给 24 小时 / 48 小时窗口"

这些不是语言修辞小变化。它们经常就是让步的前奏。

### 第 4 层：叙事一致性层

特朗普有一个很典型的特征：他不会轻易承认自己退了，但他很擅长把"退一步"包装成"我迫使对方让步了，所以我现在选择更大的胜利"。

所以系统不能只判断他会不会退，还要判断：**他有没有一个体面的叙事出口。**

如果有出口，他就更容易 TACO。如果没有出口，他就更容易继续顶。

### 第 5 层：概率输出层

最后才是概率。不要一上来就问"今天几成"。

正确顺序是：先判断事件对象 → 再判断约束 → 再判断让步触发器 → 再判断叙事出口 → 最后才给一个区间概率。

这也是为什么我更愿意把 trump.kirinjin.com 看成展示面板，而不是判断核心。真正的核心，不是网页上那个数字本身，而是你背后那套"为什么今天概率升了 / 为什么今天概率降了"的结构。

## 最小可用 workflow：4 步循环

![TACO预测4步工作流](visual-assets/83__slot_4.png)

### Step 1：抓原始输入

每天固定抓这几类输入：特朗普本人最新表态、白宫/核心官员口风、关键市场反馈、盟友/对手/商界的反向压力。

这一步不要急着下结论，只做归档和标签。

### Step 2：做事件归并

把同一天所有噪音收成一个问题：今天市场真正围绕哪一个 Trump 风险在波动？

是伊朗战争升级预期？是关税再抬升预期？还是谈判破裂预期？

如果这一步不做，后面就会被一堆碎片化 headline 带偏。

### Step 3：跑 TACO 评分

给每个事件打 5 组分：

1. `rhetoric_intensity`：口头强硬程度
2. `real_action_depth`：真实动作深度
3. `market_pain`：市场和经济反噬强度
4. `face_saving_exit`：有没有体面撤退路径
5. `constraint_pressure`：政治、盟友、资本、选民的现实约束

然后用一个很朴素的规则就够了：口头强硬高但真实动作浅 + 市场痛感快速上升 + 体面出口开始出现 + 现实约束越来越强。这四件事一旦同时出现，TACO 概率就该上调。

### Step 4：输出给自己看的结论

不要只输出一个百分比。每天至少输出这 4 行：
- 今天的核心事件是什么
- 为什么 TACO 概率上升/下降
- 最关键的 2 个新增 trigger
- 明天最该继续盯什么

这样你看的是"一个会更新的方法"，不是"一个今天碰巧对了的数字"。

## 最想强调的一点

很多人把 TACO 当段子。

但真正有用的不是这个词本身，而是它提醒你：特朗普这种高波动人物，不适合靠情绪去猜，更适合靠**动机 + 约束 + 退路**去判断。

你一旦把这个东西做成 skill，思路就会变得非常清楚：

不是盯 headline，不是盯情绪，不是盯他说得有多凶。

**而是盯：他还顶不顶得住。**

这就是 TACO 真正值得学的方法论价值。

## 如果今天就要上手

我会这么配：

- 用 trump.kirinjin.com 当实时结果面板
- 用 github.com/KirinJin2046/trump-skill 当方法启发
- 但把自己的版本再补三层：市场痛感、约束压力、体面退路

因为真正能让你少亏钱的，不是"抄一个 repo"，而是把这套东西变成你自己每天都能更新的判断系统。

## 边界

第一，TACO 是市场俗称，不是正式政策概念。第二，第三方概率站和低 star repo 只能做启发，不能当权威结论。第三，这篇讲的是观察和推理方法，不是投资建议。

但哪怕只把它当方法论，这个题也很值得写。因为现在市场最缺的，不是更多情绪，而是一套能帮普通人把特朗普噪音拆开看的结构。

## 参考来源

- TACO 概率追踪页：https://trump.kirinjin.com/
- GitHub：https://github.com/KirinJin2046/trump-skill
"""

# ========== Step 2: Rewrite inline-visual-plan.md with specific image descriptions ==========
VISUAL_PLAN = r"""# Inline Visual Plan

- `draft_key`: `taco_prediction_skill_20260409`
- `topic_title`: `今天你 TACO 了没？一套能帮你少亏钱的预测方法`
- `approved_angle`: `别再被特朗普的反复横跳来回收割。把 TACO 从一个市场梗，拆成一套可复用的方法论：如何做一个 agent / skill，去读特朗普发言、识别让步触发器、判断他背后的真实动机，并估算这次 TACO 的概率。`

## Visual Strategy

- `core_visual_goal`: `用图片完成证据锚定、结构解释和流程展示，服务"TACO预测方法论"的理解和记忆。`
- `preferred_asset_order`: `原始截图 > 结构解释图 > 流程图 > AI生成图`
- `hard_rule`: `AI 生成图只能解释结构，不能证明事实。`

## Platform Slots

### `微信公众号`

- `slot_1`: `首屏后 / why-now 段后`
- `job`: `原始证据锚点：展示 TACO 概率追踪网站或 trump-skill GitHub repo 的界面截图`
- `preferred_asset`: `原始截图 > 官方资产`
- `note`: `展示 trump-skill repo 界面或 TACO 概率追踪页面，让读者直观看到"已经有人在追踪这件事了"。`

- `slot_2`: `约束识别段后`
- `job`: `分类总结图：将四类约束信号（市场反噬、内部松动、口风软化、核心利益受损）做成清晰的分类卡片图`
- `preferred_asset`: `结构图 / 分类卡`
- `note`: `四象限或四列布局的分类图，每类约束配一个图标和1-2个具体信号示例。标题"约束识别：四类关键信号"。配色用深蓝底白字，每类用不同强调色区分。`

- `slot_3`: `5层skill结构段后`
- `job`: `架构图：展示 TACO 预测 Skill 的五层架构（事件识别→约束识别→让步触发器→叙事一致性→概率输出），用层级嵌套或流程箭头表示递进关系`
- `preferred_asset`: `架构图 / 层级图`
- `note`: `五层从下到上或从左到右的层级架构图，每层标注名称和核心问题。用箭头连接表示信息流方向。标题"TACO预测Skill五层架构"。配色与品牌色#0f4c81呼应。`

- `slot_4`: `4步工作流段后`
- `job`: `流程图：展示4步循环工作流（抓原始输入→做事件归并→跑TACO评分→输出结论），用环形或线性箭头表示循环`
- `preferred_asset`: `流程图 / 工作流图`
- `note`: `四步循环流程图，每步标注名称和核心动作。用环形箭头表示每天循环刷新。标题"TACO预测4步工作流"。配色与slot_3保持一致。`

## Source Candidates

- `candidate_1`: `https://trump.kirinjin.com/`
- `asset_type`: `网页标题区截图`
- `best_use`: `正文前中段，作为原始来源与对象说明图`

- `candidate_2`: `https://github.com/KirinJin2046/trump-skill`
- `asset_type`: `Repo header / README 首屏截图`
- `best_use`: `首屏后，证明对象真实存在且具备 traction`

## Human QC

- 这张图是在证明事实、解释结构，还是只是在装饰？
- 第一张正文图能不能当作原始证据锚点？
- 有没有哪一段本应放图，但现在读起来一片纯文字？
"""

def main():
    print("=== Step 1: Rewrite wechat.md ===")
    wechat_path = PACK_DIR / "wechat.md"
    wechat_path.write_text(WECHAT_MD, encoding="utf-8")
    print(f"Written: {wechat_path}")

    print("\n=== Step 2: Rewrite inline-visual-plan.md ===")
    plan_path = PACK_DIR / "inline-visual-plan.md"
    plan_path.write_text(VISUAL_PLAN, encoding="utf-8")
    print(f"Written: {plan_path}")

    print("\n=== Step 3: Regenerate visual assets ===")
    env = {
        **__import__("os").environ,
        "TH_MARKET_ENABLE_AI_VISUAL_FALLBACK": "true",
    }
    try:
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "market_content_polish_builder.py"),
             "--draft-pack-dir", str(PACK_DIR), "--write"],
            capture_output=True, text=True, timeout=300, env=env,
            cwd=str(SCRIPTS_DIR),
        )
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout[-2000:]}")
        if result.stderr:
            print(f"STDERR: {result.stderr[-2000:]}")
    except subprocess.TimeoutExpired:
        print("TIMEOUT after 300s")
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Step 4: Re-enqueue to wechat bridge ===")
    try:
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "market_wechat_bridge_enqueue.py"),
             "--draft-pack-dir", str(PACK_DIR), "--write"],
            capture_output=True, text=True, timeout=120,
            cwd=str(SCRIPTS_DIR),
        )
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout[-2000:]}")
        if result.stderr:
            print(f"STDERR: {result.stderr[-2000:]}")
    except subprocess.TimeoutExpired:
        print("TIMEOUT after 120s")
    except Exception as e:
        print(f"Error: {e}")

    print("\n=== Done ===")

if __name__ == "__main__":
    main()
