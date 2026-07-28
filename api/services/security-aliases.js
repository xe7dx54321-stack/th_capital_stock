/**
 * MVP 证券别名表。
 *
 * 这是自然语言路由和工作流实体解析的单一数据源，避免两处各自
 * 维护公司名称。只收录当前自用研究池及明确支持的标的；未来应由
 * 证券主数据表替代。
 */
export const STOCK_NAME_MAP = Object.freeze({
  "300308.SZ": "中际旭创", "000063.SZ": "中兴通讯", "688205.SH": "德科立",
  "300274.SZ": "阳光电源", "002396.SZ": "星网锐捷", "301165.SZ": "锐捷网络",
  "000938.SZ": "紫光股份", "688629.SH": "华丰科技",
  "688025.SH": "杰普特", "688800.SH": "澜起科技", "002281.SZ": "光迅科技",
  "002837.SZ": "英维克", "300394.SZ": "天孚通信", "300502.SZ": "新易盛",
  "300620.SZ": "光库科技", "872808.BJ": "中讯四方", "09988.HK": "阿里巴巴",
  "301171.SZ": "华如科技", "00020.HK": "蒙牛乳业", "002230.SZ": "科大讯飞",
  "603039.SH": "泛微网络", "688111.SH": "金山办公", "002957.SZ": "科瑞技术",
  "002050.SZ": "三花智控", "002600.SZ": "领益智造", "002796.SZ": "世运电路",
  "09980.HK": "网易", "300124.SZ": "汇川技术", "301368.SZ": "丰立智能",
  "600580.SH": "卧龙电驱", "601689.SH": "拓普集团", "603728.SH": "鸣志电器",
  "688017.SH": "绿的谐波", "688322.SH": "奥比中光", "300593.SZ": "新雷能",
  "603986.SH": "兆易创新", "688525.SH": "芯海科技", "00981.HK": "中芯国际",
  "01347.HK": "华虹半导体", "301269.SZ": "华大九天", "688041.SH": "海光信息",
  "688256.SH": "寒武纪", "688521.SH": "芯原股份", "688027.SH": "国盾量子",
  "300757.SZ": "罗博特科", "688627.SH": "精智达",
});

export function resolveKnownTicker(input) {
  const text = String(input || "").trim();
  if (!text) return null;
  const normalized = text.toUpperCase();
  for (const [code, name] of Object.entries(STOCK_NAME_MAP)) {
    if (code === normalized || code.replace(/\.(SZ|SH|BJ|HK)$/i, "") === normalized || name === text) {
      return code;
    }
  }
  return null;
}

export function resolveKnownTickers(query) {
  const text = String(query || "");
  if (!text) return [];
  const matches = [];
  for (const [code, name] of Object.entries(STOCK_NAME_MAP)) {
    const bare = code.replace(/\.(SZ|SH|BJ|HK)$/i, "");
    if (text.includes(name) || new RegExp(`\\b${bare}(?:\\.(?:SZ|SH|BJ|HK))?\\b`, "i").test(text)) {
      if (!matches.includes(code)) matches.push(code);
    }
  }
  const explicitPattern = /\b(\d{6}\.(?:SZ|SH|BJ|HK))\b/gi;
  for (const match of text.matchAll(explicitPattern)) {
    const code = match[1].toUpperCase();
    if (!matches.includes(code)) matches.push(code);
  }
  return matches;
}

export function firstKnownAShareTicker(query) {
  return resolveKnownTickers(query).find((ticker) => /\.(SZ|SH|BJ)$/i.test(ticker)) || null;
}
