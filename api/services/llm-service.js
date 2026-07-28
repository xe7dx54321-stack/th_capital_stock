/**
 * 统一 LLM 配置服务
 * 
 * 功能：
 *   1. 读取项目模型配置（model_profiles.json）
 *   2. 加载本地 .env 文件中的 API key
 *   3. 支持多种模型提供商（MiniMax、Anthropic、OpenAI）
 *   4. 提供统一的聊天完成和 Embedding 接口
 * 
 * 小白讲解：
 *   这个服务就像一个"模型管家"——它知道有哪些 AI 模型可用、它们的 API key 在哪里、
 *   怎么调用它们。不管用的是 MiniMax 还是 Claude，它都提供统一的调用方式，
 *   其他模块不用管具体是哪个模型。
 */

import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";


const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "..", "..");

const DEFAULT_LLM_TIMEOUT_MS = 60_000;
const DEFAULT_MAX_OUTPUT_TOKENS = 16_000;

function readPositiveInteger(value, fallback) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}


/**
 * 本地环境文件路径
 */
const LOCAL_ENV_PATHS = [
  path.join(PROJECT_ROOT, ".smr_env.local"),
  path.join(PROJECT_ROOT, "00_control", "local_model_env.env"),
  path.join(PROJECT_ROOT, ".env"),
];


/**
 * 加载本地环境变量
 * 
 * 小白讲解：从 .env 文件里读取 API key 等配置，加到环境变量里
 */
function loadLocalEnv() {
  for (const envPath of LOCAL_ENV_PATHS) {
    if (fs.existsSync(envPath)) {
      const result = dotenv.config({ path: envPath });
      if (result.error) {
        console.warn(`加载环境文件失败 ${envPath}:`, result.error.message);
      } else {
        console.log(`已加载环境文件: ${envPath}`);
      }
      break;
    }
  }
}

loadLocalEnv();


/**
 * 模型配置路径
 */
const MODEL_PROFILES_PATH = path.join(
  process.env.SMR_MODEL_RUNTIME_DIR || path.join(PROJECT_ROOT, "12_smr_agents", "model_runtime"),
  "model_profiles.json"
);


/**
 * 加载模型配置文件
 */
function loadModelProfiles() {
  if (!fs.existsSync(MODEL_PROFILES_PATH)) {
    console.warn("模型配置文件不存在:", MODEL_PROFILES_PATH);
    return { providers: {}, model_slots: {} };
  }

  try {
    const raw = fs.readFileSync(MODEL_PROFILES_PATH, "utf-8");
    return JSON.parse(raw);
  } catch (e) {
    console.error("加载模型配置失败:", e.message);
    return { providers: {}, model_slots: {} };
  }
}


/**
 * 获取指定提供商的配置
 */
function getProviderConfig(providerName) {
  const profiles = loadModelProfiles();
  const provider = profiles.providers?.[providerName];
  if (!provider) return null;

  const apiKeyEnv = provider.api_key_env;
  const baseUrlEnv = provider.base_url_env;
  const apiKeyAliases = provider.api_key_env_aliases || [];
  const apiKey = process.env[apiKeyEnv] || apiKeyAliases.map((name) => process.env[name]).find(Boolean);
  const baseUrl = process.env[baseUrlEnv] || provider.default_base_url;

  // 历史配置中的 messages 与 anthropic_messages 表达的是同一种协议。
  const apiStyle = provider.api_style === "messages" ? "anthropic_messages" : provider.api_style;

  return {
    provider: providerName,
    enabled: provider.enabled,
    apiKey,
    baseUrl,
    apiStyle,
    anthropicVersion: provider.anthropic_version || "2023-06-01",
    hasApiKey: !!apiKey,
    hasBaseUrl: !!baseUrl,
  };
}


/**
 * 获取可用的模型槽位配置
 */
function getModelSlot(slotName) {
  const profiles = loadModelProfiles();
  const slot = profiles.model_slots?.[slotName];
  if (!slot) return null;

  const providerConfig = getProviderConfig(slot.provider);
  return {
    ...slot,
    providerConfig,
  };
}


/**
 * 列出所有可用的提供商
 */
function listAvailableProviders() {
  const profiles = loadModelProfiles();
  const result = [];
  for (const [name, provider] of Object.entries(profiles.providers || {})) {
    const config = getProviderConfig(name);
    result.push(config);
  }
  return result;
}


/**
 * 选择可用的提供商（优先 MiniMax，其次 Anthropic，最后 OpenAI）
 */
function selectAvailableProvider(preference = ["minimax", "anthropic", "openai"]) {
  for (const name of preference) {
    const config = getProviderConfig(name);
    if (config?.enabled && config.hasApiKey) {
      return config;
    }
  }
  return null;
}


/**
 * 构建请求头
 */
function buildHeaders(providerConfig) {
  const headers = {
    "Content-Type": "application/json",
  };

  if (providerConfig.apiStyle === "anthropic_messages") {
    headers["x-api-key"] = providerConfig.apiKey;
    headers["anthropic-version"] = providerConfig.anthropicVersion;
  } else {
    headers["Authorization"] = `Bearer ${providerConfig.apiKey}`;
  }

  return headers;
}


/**
 * 构建 API 端点 URL
 */
function buildEndpoint(providerConfig, endpoint) {
  const base = (providerConfig.baseUrl || "").replace(/\/$/, "");
  return `${base}${endpoint}`;
}

async function fetchWithTimeout(endpoint, init = {}, timeoutMs = DEFAULT_LLM_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(endpoint, { ...init, signal: controller.signal });
  } catch (error) {
    if (controller.signal.aborted) {
      throw new Error(`模型请求超时（${timeoutMs}ms）`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * 兼容不同模型供应商的消息响应结构，并跳过 thinking/reasoning 内容块。
 * MiniMax 的 Anthropic 兼容接口可能先返回 thinking 块、再返回 text 块，
 * 因此不能只读取 content[0].text。
 */
function extractChatCompletionContent(data, apiStyle = "anthropic_messages") {
  if (!data || typeof data !== "object") return "";

  if (apiStyle === "anthropic_messages") {
    if (typeof data.content === "string") return data.content.trim();
    if (Array.isArray(data.content)) {
      return data.content
        .map((block) => {
          if (typeof block === "string") return block;
          if (!block || typeof block !== "object") return "";
          return typeof block.text === "string" ? block.text : "";
        })
        .filter(Boolean)
        .join("\n")
        .trim();
    }
    return "";
  }

  const messageContent = data.choices?.[0]?.message?.content;
  if (typeof messageContent === "string") return messageContent.trim();
  if (Array.isArray(messageContent)) {
    return messageContent
      .map((part) => typeof part === "string" ? part : part?.text || "")
      .filter(Boolean)
      .join("\n")
      .trim();
  }
  if (typeof data.output_text === "string") return data.output_text.trim();
  return "";
}

function describeEmptyModelResponse(data) {
  const topLevelKeys = data && typeof data === "object" ? Object.keys(data).slice(0, 12) : [];
  const contentTypes = Array.isArray(data?.content)
    ? data.content.map((block) => block?.type || typeof block).slice(0, 12)
    : [];
  const stopReason = data?.stop_reason || "未知";
  const outputTokens = data?.usage?.output_tokens ?? "未知";
  return `响应字段=${topLevelKeys.join(",") || "无"}；内容块=${contentTypes.join(",") || "无"}；停止原因=${stopReason}；输出tokens=${outputTokens}`;
}


/**
 * 发送聊天补全请求
 * 
 * 参数：
 *   messages: 消息列表 [{ role: "user"|"assistant"|"system", content: "..." }]
 *   options: { model: string, maxTokens: number, temperature: number }
 *   providerConfig: 提供商配置（可选，自动选择）
 * 
 * 返回：
 *   Promise<{ content: string, usage: object }>
 */
async function createChatCompletion(messages, options = {}, providerConfig = null) {
  const slotName = options.slotName || "reasoning_primary";
  const slot = getModelSlot(slotName);
  const slotProvider = slot?.providerConfig;
  const provider = providerConfig || (
    slotProvider?.enabled && slotProvider.hasApiKey ? slotProvider : selectAvailableProvider()
  );

  if (!provider) {
    throw new Error("没有可用的模型提供商（请检查 API key 是否配置）");
  }

  if (!provider.hasApiKey) {
    throw new Error(`${provider.provider} 的 API key 未配置`);
  }

  const model = options.model || (
    slot?.provider === provider.provider && slot.model ? slot.model : getDefaultModel(provider, slotName)
  );
  const maxOutputTokens = readPositiveInteger(process.env.LLM_MAX_OUTPUT_TOKENS, DEFAULT_MAX_OUTPUT_TOKENS);
  const maxTokens = Math.min(readPositiveInteger(options.maxTokens, maxOutputTokens), maxOutputTokens);
  const temperature = options.temperature ?? 0.7;
  const timeoutMs = readPositiveInteger(options.timeoutMs || process.env.LLM_REQUEST_TIMEOUT_MS, DEFAULT_LLM_TIMEOUT_MS);

  let endpoint;
  let body;

  if (provider.apiStyle === "anthropic_messages") {
    endpoint = buildEndpoint(provider, "/v1/messages");
    const systemMsg = messages.find(m => m.role === "system");
    const nonSystemMsgs = messages.filter(m => m.role !== "system");
    body = {
      model,
      max_tokens: maxTokens,
      temperature,
      messages: nonSystemMsgs.map(m => ({ role: m.role, content: m.content })),
    };
    if (systemMsg) {
      body.system = systemMsg.content;
    }
  } else {
    endpoint = buildEndpoint(provider, "/v1/chat/completions");
    body = {
      model,
      max_tokens: maxTokens,
      temperature,
      messages,
    };
  }

  const response = await fetchWithTimeout(endpoint, {
    method: "POST",
    headers: buildHeaders(provider),
    body: JSON.stringify(body),
  }, timeoutMs);

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`模型请求失败 (${response.status}): ${errText}`);
  }

  const data = await response.json();

  const content = extractChatCompletionContent(data, provider.apiStyle);
  if (!content) {
    throw new Error(`模型返回成功，但未包含可用文本（${describeEmptyModelResponse(data)}）`);
  }
  return { content, usage: data.usage };
}


/**
 * 创建 Embedding 向量
 * 
 * 参数：
 *   input: 文本或文本数组
 *   options: { model: string }
 *   providerConfig: 提供商配置
 * 
 * 返回：
 *   Promise<{ embedding: number[], usage: object }>
 */
async function createEmbedding(input, options = {}, providerConfig = null) {
  const provider = providerConfig || selectAvailableProvider();

  if (!provider) {
    throw new Error("没有可用的模型提供商（请检查 API key 是否配置）");
  }

  if (!provider.hasApiKey) {
    throw new Error(`${provider.provider} 的 API key 未配置`);
  }

  // Embedding 统一用 OpenAI 兼容接口
  const model = options.model || "text-embedding-3-small";
  const endpoint = buildEndpoint(provider, "/v1/embeddings");

  const timeoutMs = readPositiveInteger(options.timeoutMs || process.env.LLM_REQUEST_TIMEOUT_MS, DEFAULT_LLM_TIMEOUT_MS);
  const response = await fetchWithTimeout(endpoint, {
    method: "POST",
    headers: buildHeaders({
      ...provider,
      apiStyle: "openai",
    }),
    body: JSON.stringify({
      model,
      input,
      encoding_format: "float",
    }),
  }, timeoutMs);

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Embedding 请求失败 (${response.status}): ${errText}`);
  }

  const data = await response.json();
  return {
    embedding: data.data?.[0]?.embedding || [],
    usage: data.usage,
  };
}


/**
 * 获取默认模型名称
 */
function getDefaultModel(providerConfig, slotName = "reasoning_primary") {
  const slot = getModelSlot(slotName);
  if (slot?.provider === providerConfig.provider && slot.model) return slot.model;

  switch (providerConfig.provider) {
    case "minimax":
      return "MiniMax-M2.7";
    case "anthropic":
      return "claude-sonnet-4-6";
    case "openai":
      return "gpt-4o-mini";
    default:
      return "gpt-4o-mini";
  }
}


/**
 * 检查模型是否可用
 */
function isModelAvailable() {
  return !!selectAvailableProvider();
}


export {
  loadLocalEnv,
  loadModelProfiles,
  getProviderConfig,
  getModelSlot,
  listAvailableProviders,
  selectAvailableProvider,
  extractChatCompletionContent,
  createChatCompletion,
  createEmbedding,
  fetchWithTimeout,
  getDefaultModel,
  isModelAvailable,
  MODEL_PROFILES_PATH,
  LOCAL_ENV_PATHS,
};
