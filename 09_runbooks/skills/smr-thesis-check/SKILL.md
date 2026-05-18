---
name: smr-thesis-check
description: Use when checking whether the investment thesis for an open position has been invalidated. Thesis invalidation is the highest-priority exit signal, overriding all other considerations.
---

# smr-thesis-check

Use this skill for thesis invalidation detection.

## Important boundary

- This skill is the **most important risk management tool**.
- Thesis invalidation = unconditional exit recommendation.
- It does **not** consider P&L when recommending exit.
- It does **not** wait for technical confirmation.

Its job is:

> 把"投资逻辑还在不在"变成"如果不在了，立刻走人"。

## Load order

1. Read all open positions with their theses from database
2. Read latest industry/stock research from `/Users/apple/Documents/同行资本二级市场/02_research/`
3. Read latest US signals from `/Users/apple/Documents/同行资本二级市场/01_data/us_signals/`
4. Read latest risk alerts from `/Users/apple/Documents/同行资本二级市场/05_risk/`

## Core workflow

1. **For each open position**, extract the original thesis.

2. **Check thesis against current reality**:
   - Has the industry thesis changed? (e.g., policy reversal, technology route shift)
   - Has the company-specific thesis changed? (e.g., major customer loss, competitive position erosion)
   - Has the US linkage thesis changed? (e.g., US benchmark thesis broken, supply chain decoupling)
   - Has the catalyst timeline been missed without thesis playing out?

3. **Thesis status classification**:
   - **INTACT**: All core assumptions still hold, thesis on track
   - **WEAKENED**: 1-2 assumptions challenged but not disproven, monitor closely
   - **BROKEN**: Core assumption disproven, thesis no longer valid
   - **PLAYED_OUT**: Thesis has materialized as expected, take profit

4. **Action rules**:
   - INTACT → Continue holding
   - WEAKENED → Reduce position by 30-50%, set tighter stop
   - BROKEN → Exit immediately, regardless of P&L
   - PLAYED_OUT → Take profit per plan

5. **Common thesis-breaking scenarios**:
   - Embodied AI: Major customer (e.g., Tesla) shifts to in-house or alternative supplier
   - Semiconductor: Export control expansion cutting off key technology access
   - AI Agent: Major platform (e.g., Microsoft) bundles the functionality natively
   - Quantum: Government funding withdrawal or technology route obsolescence
   - CPO/Optics: Major customer (e.g., NVIDIA) changes architecture away from CPO

## Required output fields

1. **position**: ts_code and current P&L
2. **original_thesis**: The thesis as stated at entry
3. **thesis_status**: INTACT / WEAKENED / BROKEN / PLAYED_OUT
4. **evidence**: What changed and why
5. **recommended_action**: Hold / Reduce / Exit / Take Profit
6. **urgency**: Low / Medium / High / Critical

## Hard constraints

- Thesis broken = exit, no exceptions.
- Do not rationalize holding a broken thesis position.
- Do not wait for "better price" to exit a broken thesis.
- Always document why the thesis broke (learning for future).
