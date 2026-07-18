/**
 * ChatBot 聊天界面组件
 *
 * 功能：
 *   1:1 复现 Codex / Trae 的聊天界面设计
 *   - 左侧：会话列表侧边栏（新建对话 + 历史会话列表）
 *   - 中间：根据状态显示不同页面
 *     · 空状态（没有对话）：欢迎页，引导语 + 大输入框 + 推荐任务卡片
 *     · 工作状态（有对话）：聊天消息流 + 执行过程 + 结果展示 + 底部输入框
 *   - 支持新建会话、切换会话、恢复历史消息
 *   - 支持 Markdown 格式渲染回复内容
 *
 * 小白讲解：
 *   就像 Codex 或 Trae 打开时的体验：
 *   - 第一次进入，中间区域显示"今天想分析点什么？"，下面有输入框和几个推荐任务
 *   - 输入问题点发送后，中间区域切换成聊天界面，展示分析过程和结果
 *   - 左边始终是会话列表，可以随时切换或新建
 */

import { useState, useRef, useEffect } from "react";
import {
  Send, Bot, User, Loader2, Trash2,
  TrendingUp, Newspaper, BarChart3, Target,
  ArrowUp, Sparkles,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  fetchSessions, createSession, fetchSessionMessages, deleteSession,
  type ChatSession, type SessionMessage,
} from "../../lib/api";
import SessionSidebar from "./SessionSidebar";


/**
 * 聊天消息类型
 */
interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  intent?: string;
}


/**
 * Workflow 回复类型
 */
interface WorkflowResponse {
  taskType: string;
  status: string;
  response: string;
  data: Record<string, unknown>;
  executionHistory: Array<{ stepId: string; message: string; data?: unknown }>;
  workflowSummary: { totalSteps: number; completedSteps: number };
  extractedMemories?: Array<{ title: string; content: string; category: string; confidence: number }>;
}


/**
 * 推荐任务列表
 *
 * 空状态欢迎页显示的推荐任务卡片
 * 参考 Codex/Trae 的设计：给用户几个常见选项降低使用门槛
 */
const suggestedTasks = [
  {
    icon: BarChart3,
    title: "今日A股复盘",
    description: "扫描涨跌幅榜、资金流向，生成今日市场总结",
    message: "帮我做一份今天的A股复盘",
    color: "from-blue-500 to-cyan-500",
  },
  {
    icon: TrendingUp,
    title: "涨跌幅归因分析",
    description: "分析今天涨幅前10和跌幅前10的股票原因",
    message: "做一份今天涨跌幅前10的归因分析",
    color: "from-purple-500 to-pink-500",
  },
  {
    icon: Target,
    title: "机会雷达扫描",
    description: "全市场扫描放量异动、价格突破、估值极端等信号",
    message: "今天有哪些机会",
    color: "from-orange-500 to-red-500",
  },
  {
    icon: Newspaper,
    title: "最新市场新闻",
    description: "获取最新的财经新闻和市场动态",
    message: "最近有什么重要的市场新闻",
    color: "from-green-500 to-emerald-500",
  },
];


/**
 * 发送聊天请求（使用 Workflow 引擎）
 *
 * 参数：
 *   message: 用户消息
 *   sessionId: 当前会话 ID（可选，传入后消息会保存到对应会话）
 *
 * 返回：
 *   Promise<WorkflowResponse>: Workflow 响应
 */
async function sendChatRequest(message: string, sessionId?: string, chatHistory?: Array<{role: string; content: string}>): Promise<WorkflowResponse> {
  const body: Record<string, unknown> = { message };
  if (sessionId) body.sessionId = sessionId;
  // 传递对话历史，让后端知道之前的上下文
  if (chatHistory && chatHistory.length > 0) {
    body.conversationContext = { chatHistory };
  }

  const response = await fetch("/api/chat/workflow", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error("聊天服务请求失败");
  }

  return response.json();
}


/**
 * 格式化时间显示（HH:MM）
 */
function formatTime(date: Date): string {
  const hours = date.getHours().toString().padStart(2, "0");
  const minutes = date.getMinutes().toString().padStart(2, "0");
  return `${hours}:${minutes}`;
}


/**
 * 意图标签映射
 *
 * 把后端的英文意图标识转换为中文显示
 */
function getIntentLabel(intent: string): string {
  const labels: Record<string, string> = {
    stock_analysis: "股票分析",
    value_score: "价值评分",
    opportunity_radar: "机会雷达",
    discovery_candidates: "新发现",
    market_news: "市场新闻",
    help: "帮助",
    unknown: "未知",
    stock_deep_analysis: "深度分析",
    opportunity_scan: "机会扫描",
    discovery: "新发现",
    portfolio_review: "组合回顾",
    daily_brief: "每日简报",
    thesis_update: "投资论更新",
    risk_analysis: "风险分析",
    competitor_analysis: "竞争对手分析",
    trend_analysis: "趋势分析",
    chat: "自由对话",
  };
  return labels[intent] || intent;
}


/**
 * 用户消息气泡组件
 */
function UserMessageBubble({ content, timestamp }: { content: string; timestamp: Date }) {
  return (
    <div className="flex justify-end mb-4">
      <div className="flex items-start gap-2 max-w-[70%] flex-row-reverse">
        <div className="flex flex-col items-center flex-shrink-0">
          <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
            <User size={16} className="text-white" />
          </div>
          <span className="text-xs text-gray-400 mt-1">{formatTime(timestamp)}</span>
        </div>
        <div className="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-md">
          <p className="text-sm whitespace-pre-wrap">{content}</p>
        </div>
      </div>
    </div>
  );
}


/**
 * AI 消息气泡组件（含 Markdown 渲染）
 */
function AssistantMessageBubble({ content, timestamp, intent }: { content: string; timestamp: Date; intent?: string }) {
  return (
    <div className="flex justify-start mb-4">
      <div className="flex items-start gap-2 max-w-[85%]">
        <div className="flex flex-col items-center flex-shrink-0">
          <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center">
            <Bot size={16} className="text-white" />
          </div>
          <span className="text-xs text-gray-400 mt-1">{formatTime(timestamp)}</span>
        </div>
        <div className="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          {intent && intent !== "help" && (
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">
              <span className="bg-gray-200 dark:bg-gray-700 px-2 py-0.5 rounded-full">
                {getIntentLabel(intent)}
              </span>
            </div>
          )}
          <div className="text-sm">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
              h1: ({ children }) => <h1 className="text-lg font-bold mt-2 mb-1">{children}</h1>,
              h2: ({ children }) => <h2 className="text-base font-bold mt-2 mb-1">{children}</h2>,
              h3: ({ children }) => <h3 className="text-sm font-bold mt-2 mb-1">{children}</h3>,
              ul: ({ children }) => <ul className="list-disc list-inside mt-1 mb-1">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside mt-1 mb-1">{children}</ol>,
              li: ({ children }) => <li className="text-sm">{children}</li>,
              strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              table: ({ children }) => <div className="overflow-x-auto my-2 border border-gray-300 dark:border-gray-600 rounded-lg"><table className="w-full text-xs">{children}</table></div>,
              th: ({ children }) => <th className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-left font-semibold bg-gray-100 dark:bg-gray-700">{children}</th>,
              td: ({ children }) => <td className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-left">{children}</td>,
              p: ({ children }) => <p className="mb-1">{children}</p>,
            }}>
              {content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}


/**
 * 加载中状态组件（AI 正在思考）
 */
function LoadingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="flex items-start gap-2 max-w-[85%]">
        <div className="flex flex-col items-center flex-shrink-0">
          <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center">
            <Bot size={16} className="text-white" />
          </div>
        </div>
        <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          <div className="flex items-center gap-2">
            <Loader2 size={16} className="text-gray-500 animate-spin" />
            <span className="text-sm text-gray-500">正在思考中...</span>
          </div>
        </div>
      </div>
    </div>
  );
}


/**
 * 将 session 消息记录转换为前端 ChatMessage 数组
 *
 * 参数：
 *   messages: 后端返回的 session 消息列表（按时间正序）
 * 返回：
 *   ChatMessage 数组
 */
function sessionMessagesToChatMessages(messages: SessionMessage[]): ChatMessage[] {
  return messages.map((msg) => ({
    id: `session-${msg.id}`,
    role: msg.role,
    content: msg.content,
    timestamp: new Date(msg.created_at),
    intent: msg.intent || undefined,
  }));
}


/**
 * 判断当前是否处于"空状态"
 *
 * 空状态 = 没有任何用户消息（只有欢迎语或完全为空）
 * 此时显示欢迎页而非聊天界面
 *
 * 参数：
 *   messages: 当前消息列表
 * 返回：
 *   true = 显示欢迎页, false = 显示聊天工作区
 */
function isEmptyState(messages: ChatMessage[]): boolean {
  // 如果有用户消息，就不是空状态
  return !messages.some(msg => msg.role === "user");
}


/**
 * 主聊天组件
 *
 * 1:1 复现 Codex / Trae 的聊天界面设计
 */
export default function ChatPanel() {
  // === 聊天状态 ===
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const welcomeInputRef = useRef<HTMLTextAreaElement>(null);

  // === Session 管理状态 ===
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0);


  /**
   * 组件初始化时加载会话列表
   *
   * 如果有会话，自动选中最近的一个
   * 如果没有会话，保持空状态显示欢迎页
   */
  useEffect(() => {
    async function initSessions() {
      try {
        const result = await fetchSessions("active");
        if (result.success && result.sessions.length > 0) {
          // 自动选中第一个会话（最新的）
          await selectSession(result.sessions[0]);
        }
      } catch (err) {
        console.warn("加载会话列表失败:", err);
      }
    }
    initSessions();
  }, []);


  /**
   * 空状态时自动聚焦欢迎页输入框
   */
  useEffect(() => {
    if (isEmptyState(messages) && !isLoading) {
      welcomeInputRef.current?.focus();
    }
  }, [messages, isLoading]);


  /**
   * 滚动到最新消息
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);


  /**
   * 切换会话
   *
   * 从后端加载该会话的所有消息，替换当前显示的消息列表
   */
  async function selectSession(session: ChatSession) {
    setCurrentSessionId(session.id);
    try {
      const result = await fetchSessionMessages(session.id);
      if (result.success && result.messages.length > 0) {
        setMessages(sessionMessagesToChatMessages(result.messages));
      } else {
        // 空会话，显示欢迎页
        setMessages([]);
      }
    } catch (err) {
      console.error("加载会话消息失败:", err);
    }
  }


  /**
   * 新建会话
   *
   * 创建新会话后自动切换到空状态欢迎页
   */
  function handleCreateSession(session: ChatSession) {
    setCurrentSessionId(session.id);
    setMessages([]);
    setSidebarRefreshKey(k => k + 1);
  }


  /**
   * 触发侧边栏刷新
   */
  function refreshSidebar() {
    setSidebarRefreshKey(k => k + 1);
  }


  /**
   * 发送消息（核心方法）
   *
   * 1. 如果没有当前会话，自动创建一个
   * 2. 添加用户消息到界面
   * 3. 调用后端 Workflow 引擎获取 AI 回复
   * 4. 添加 AI 回复到界面
   * 5. 刷新侧边栏（更新标题、消息数等）
   *
   * 参数：
   *   text: 要发送的消息内容（如果不传，使用 inputValue）
   */
  async function handleSend(text?: string) {
    const message = (text || inputValue).trim();
    if (!message || isLoading) return;

    // 如果没有当前会话，自动创建一个
    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        const result = await createSession();
        if (result.success && result.session) {
          sessionId = result.session.id;
          setCurrentSessionId(sessionId);
        }
      } catch (err) {
        console.warn("自动创建会话失败:", err);
      }
    }

    // 添加用户消息
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: message,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      // 构建对话历史：把当前 session 中已有的消息传给后端
      // 只传最近 10 条，避免 prompt 太长超出 token 限制
      // 修复：助手消息保留 2000 字（之前 500 字太短，报告被裁剪后后端无法理解上下文）
      const chatHistory = messages.slice(-10).map(msg => ({
        role: msg.role,
        content: msg.role === "user" ? msg.content.substring(0, 300) : msg.content.substring(0, 2000),
      }));

      const response = await sendChatRequest(message, sessionId || undefined, chatHistory);

      // 构建执行步骤信息
      let executionInfo = "";
      if (response.workflowSummary) {
        executionInfo = `\n\n---\n\n**📋 执行信息**\n- 任务类型：${getIntentLabel(response.taskType)}\n- 执行步骤：${response.workflowSummary.completedSteps}/${response.workflowSummary.totalSteps} 步`;
      }

      // 构建提取的记忆信息
      let memoriesInfo = "";
      if (response.extractedMemories && response.extractedMemories.length > 0) {
        memoriesInfo = `\n\n**🧠 可沉淀记忆（${response.extractedMemories.length} 条）**\n`;
        response.extractedMemories.forEach((mem, i) => {
          memoriesInfo += `${i + 1}. **${mem.title}**（${mem.category}）\n   ${mem.content.substring(0, 80)}${mem.content.length > 80 ? "..." : ""}\n`;
        });
      }

      // 添加 AI 回复
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response + executionInfo + memoriesInfo,
        timestamp: new Date(),
        intent: response.taskType,
      };
      setMessages(prev => [...prev, assistantMessage]);

      // 刷新侧边栏
      refreshSidebar();
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `抱歉，发生了错误：${error instanceof Error ? error.message : "未知错误"}`,
        timestamp: new Date(),
        intent: "unknown",
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }


  /**
   * 键盘事件处理
   *
   * Enter 发送，Shift+Enter 换行
   */
  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }


  /**
   * 清空当前会话
   *
   * 删除当前会话并回到空状态欢迎页
   */
  async function handleClearHistory() {
    if (!window.confirm("确定要清空当前对话吗？此操作不可恢复。")) return;

    if (currentSessionId) {
      try {
        await deleteSession(currentSessionId);
        setCurrentSessionId(null);
        refreshSidebar();
      } catch (err) {
        console.error("删除会话失败:", err);
        alert("删除会话失败，请稍后重试");
        return;
      }
    }

    setMessages([]);
  }


  /**
   * 判断当前是否显示空状态欢迎页
   */
  const showWelcome = isEmptyState(messages);


  return (
    <div className="flex h-full bg-white dark:bg-gray-900 overflow-hidden">
      {/* === 左侧：会话列表侧边栏 === */}
      <SessionSidebar
        key={sidebarRefreshKey}
        currentSessionId={currentSessionId}
        onSelectSession={selectSession}
        onCreateSession={handleCreateSession}
      />

      {/* === 中间区域：根据状态显示不同页面 === */}
      {showWelcome ? (
        /* ---------- 空状态：欢迎页 ---------- */
        <div className="flex-1 flex flex-col items-center justify-center overflow-y-auto px-6 py-8">
          <div className="w-full max-w-2xl">

            {/* 欢迎语 */}
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-2xl mb-4 shadow-lg">
                <Sparkles size={28} className="text-white" />
              </div>
              <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100 mb-2">
                今天想分析点什么？
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                直接在下方输入你的需求，或从下方推荐任务中选择一项开始
              </p>
            </div>

            {/* 大输入框 */}
            <div className="relative mb-6">
              <textarea
                ref={welcomeInputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入你的问题，例如：帮我分析中际旭创..."
                rows={3}
                className="w-full px-5 py-4 text-sm border border-gray-300 dark:border-gray-600 rounded-2xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 shadow-sm"
              />
              <button
                onClick={() => handleSend()}
                disabled={!inputValue.trim() || isLoading}
                className="absolute bottom-4 right-4 flex items-center justify-center w-9 h-9 bg-gradient-to-br from-purple-600 to-indigo-600 hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl transition-opacity shadow-md"
              >
                {isLoading ? <Loader2 size={18} className="animate-spin" /> : <ArrowUp size={18} />}
              </button>
            </div>

            {/* 推荐任务卡片 */}
            <div className="grid grid-cols-2 gap-3">
              {suggestedTasks.map((task) => (
                <button
                  key={task.title}
                  onClick={() => handleSend(task.message)}
                  disabled={isLoading}
                  className="group flex flex-col items-start p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-purple-300 dark:hover:border-purple-600 hover:shadow-md transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className={`inline-flex items-center justify-center w-8 h-8 bg-gradient-to-br ${task.color} rounded-lg mb-2`}>
                    <task.icon size={16} className="text-white" />
                  </div>
                  <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-1">
                    {task.title}
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                    {task.description}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* ---------- 工作状态：聊天界面 ---------- */
        <div className="flex flex-col flex-1 overflow-hidden">

          {/* 顶部工具栏 */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center">
                <Bot size={14} className="text-white" />
              </div>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-200">SMR 研究助手</span>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleClearHistory}
                disabled={isLoading}
                title="清空当前对话"
                className="flex items-center gap-1 text-xs text-gray-400 hover:text-red-500 transition-colors disabled:opacity-40"
              >
                <Trash2 size={13} />
                <span>清空</span>
              </button>
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                <span className="text-xs text-gray-400">在线</span>
              </div>
            </div>
          </div>

          {/* 消息流区域 */}
          <div className="flex-1 overflow-y-auto px-4 py-4">
            {messages.map((msg) =>
              msg.role === "user" ? (
                <UserMessageBubble key={msg.id} content={msg.content} timestamp={msg.timestamp} />
              ) : (
                <AssistantMessageBubble key={msg.id} content={msg.content} timestamp={msg.timestamp} intent={msg.intent} />
              )
            )}
            {isLoading && <LoadingIndicator />}
            <div ref={messagesEndRef} />
          </div>

          {/* 底部输入区域 */}
          <div className="px-4 py-3 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-end gap-2">
              <div className="flex-1 relative">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="输入你的问题..."
                  rows={1}
                  className="w-full px-4 py-2.5 text-sm border border-gray-300 dark:border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none max-h-32 bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400"
                  style={{ minHeight: "44px" }}
                />
              </div>
              <button
                onClick={() => handleSend()}
                disabled={!inputValue.trim() || isLoading}
                className="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl transition-opacity shadow-md"
              >
                {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-2 text-center">
              按 Enter 发送，Shift+Enter 换行
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
