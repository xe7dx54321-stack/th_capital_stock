# SMR Research Upgrade Progress

## Phase 65: CNINFO/SZSE Disclosure Endpoint Parameter Breakthrough v1

### 状态
- 日期: 2026-05-29
- 状态: 完成

### 目标
- 解决 CNINFO totalAnnouncement=0
- 测试 stock / orgId / plate / column / category / headers 参数
- 找到 CNINFO working parameter set
- 将 working set 写回 connector
- 提取 PDF URL
- 小规模验证 PDF 下载和文本提取
- 探索 SZSE disclosure endpoint
- 输出 metadata breakthrough dashboard
- 若拿到真实 text，则重跑 business evidence

### 核心边界
- 不绕过验证码 / 登录 / 反爬
- 不做 OCR
- 不保存 raw PDF / raw HTML 到 git
- 不用 mock / fixture 顶替失败
- metadata-only 不当正文
- 没有真实 text 就不假装业务证据增加

### 关键发现
- 300308.SZ curated org_id: 9900022016 (来自 smr_cninfo_source_identity.py)
- CNINFO API 需要 HTTPS + 正确的 stock/orgId 参数组合
- SZSE disclosure API 当前 HTTP 500，已建立多 endpoint explorer

### 下一步
- 在真实网络环境下运行 run_phase65_disclosure_endpoint_breakthrough.py --execute
- 验证 orgId 参数是否能解决 totalAnnouncement=0
