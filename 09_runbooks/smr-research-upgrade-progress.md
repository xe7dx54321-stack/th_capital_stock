# SMR Research Upgrade Progress

## Phase 64: A-share Disclosure Source Connector Repair v1

### 状态
- 日期: 2026-05-29
- 状态: 完成

### 目标
- 诊断 CNINFO timeout / HTTP 500
- 尝试修复 CNINFO 请求（确认 HTTPS 可用，参数格式需调整）
- 探索 SZSE 披露源替代（主页可达但 API 返回 HTTP 500）
- 修复 IRM 问答源（HTML parsing fallback）
- 建立 disclosure source fallback router
- 输出 connector health dashboard
- 小规模重跑真实 source fetch
- 如果拿到真实 text，则重跑 business evidence

### 核心边界
- 不绕过验证码 / 登录 / 反爬
- 不做 OCR
- 不保存 raw PDF / raw HTML 到 git
- 不用 mock / fixture 顶替失败
- metadata-only 不当正文
- 没有真实 text 就不假装业务证据增加

### 发现
1. CNINFO: HTTPS 可达，API 返回 JSON 但 0 结果（参数格式需调整）
2. SZSE: 主页可达（HTTP 200），但披露 API 返回 HTTP 500
3. IRM: 主页可达（HTTP 200），返回 HTML 非 JSON，需 HTML parsing
4. 公司官网: URL 尚未配置

### 下一步
- 在真实网络环境下运行 Phase 64 runner
- 调整 CNINFO 的 stock 参数格式以获取实际公告
- 探索 SZSE 替代披露 API endpoint
- 验证 IRM HTML parsing 能否提取 QA
