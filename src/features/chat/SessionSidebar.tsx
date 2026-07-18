/**
 * 会话侧边栏组件 (Session Sidebar)
 *
 * 功能：
 *   1:1 复现 Codex 的 session 侧边栏管理界面
 *   - 显示所有会话列表（置顶在前，按最后消息时间排序）
 *   - 新建会话（对应 Codex 的 "New Thread"）
 *   - 切换会话（对应 Codex 的 "thread resume"）
 *   - 置顶/取消置顶（对应 Codex 的 "pinned threads"）
 *   - 归档/取消归档（对应 Codex 的 "archive"）
 *   - 删除会话（对应 Codex 的 "purge"）
 *   - 搜索会话（对应 Codex 的 "thread list --grep"）
 *   - 切换查看活跃/归档会话
 *
 * 小白讲解：
 *   这个组件就像微信左侧的聊天列表：
 *   - 上面有搜索框和"新建聊天"按钮
 *   - 中间是所有对话列表，置顶的排最上面
 *   - 每个对话可以右键或点按钮进行置顶、归档、删除
 *   - 底部可以切换查看"全部"还是"归档"的对话
 */

import { useState, useEffect, useCallback } from "react";
import {
  Plus, Search, Pin, PinOff, Archive, ArchiveRestore,
  Trash2, MessageSquare, Clock, MoreVertical
} from "lucide-react";
import {
  fetchSessions, createSession, updateSession, deleteSession,
  type ChatSession
} from "../../lib/api";

/**
 * 格式化时间为简短显示
 *
 * @param dateStr - ISO 时间字符串
 * @returns 简短时间字符串（如"刚刚"、"3分钟前"、"昨天"、"2026-01-15"）
 */
function formatTime(dateStr: string | null): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMs / 3600000);
  const diffDay = Math.floor(diffMs / 86400000);

  if (diffMin < 1) return "刚刚";
  if (diffMin < 60) return `${diffMin}分钟前`;
  if (diffHour < 24) return `${diffHour}小时前`;
  if (diffDay === 1) return "昨天";
  if (diffDay < 7) return `${diffDay}天前`;
  return date.toLocaleDateString("zh-CN");
}

/**
 * SessionSidebar 组件的属性
 */
interface SessionSidebarProps {
  /** 当前选中的会话 ID */
  currentSessionId: string | null;
  /** 切换会话时的回调函数 */
  onSelectSession: (session: ChatSession) => void;
  /** 新建会话后的回调函数 */
  onCreateSession: (session: ChatSession) => void;
}

/**
 * 会话侧边栏主组件
 *
 * 显示会话列表，支持新建、切换、置顶、归档、删除
 */
export default function SessionSidebar({ currentSessionId, onSelectSession, onCreateSession }: SessionSidebarProps) {
  // 会话列表
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  // 加载状态
  const [loading, setLoading] = useState(true);
  // 搜索关键词
  const [searchQuery, setSearchQuery] = useState("");
  // 当前查看的标签页：active / archived
  const [activeTab, setActiveTab] = useState<"active" | "archived">("active");
  // 展开操作菜单的会话 ID
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);

  /**
   * 加载会话列表
   *
   * 根据当前标签页和搜索关键词从后端获取会话列表
   */
  const loadSessions = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchSessions(activeTab, searchQuery || undefined);
      if (result.success) {
        setSessions(result.sessions);
      }
    } catch (err) {
      console.error("加载会话列表失败:", err);
    } finally {
      setLoading(false);
    }
  }, [activeTab, searchQuery]);

  // 初始化和标签页/搜索变化时加载
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // 搜索时延迟加载（防抖）
  useEffect(() => {
    const timer = setTimeout(() => {
      loadSessions();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * 新建会话
   *
   * 创建一个新会话并自动切换到该会话
   */
  async function handleCreate() {
    try {
      const result = await createSession();
      if (result.success && result.session) {
        onCreateSession(result.session);
        await loadSessions();
      }
    } catch (err) {
      console.error("创建会话失败:", err);
    }
  }

  /**
   * 切换置顶状态
   *
   * @param session - 要操作的会话
   */
  async function handleTogglePin(session: ChatSession) {
    try {
      await updateSession(session.id, { isPinned: !session.is_pinned });
      setMenuOpenId(null);
      await loadSessions();
    } catch (err) {
      console.error("置顶失败:", err);
    }
  }

  /**
   * 归档/取消归档
   *
   * @param session - 要操作的会话
   */
  async function handleToggleArchive(session: ChatSession) {
    try {
      await updateSession(session.id, { isArchived: session.status !== "archived" });
      setMenuOpenId(null);
      await loadSessions();
    } catch (err) {
      console.error("归档失败:", err);
    }
  }

  /**
   * 删除会话
   *
   * @param session - 要删除的会话
   */
  async function handleDelete(session: ChatSession) {
    if (!window.confirm(`确定要删除会话"${session.title}"吗？\n此操作不可恢复，所有消息将永久丢失。`)) return;
    try {
      await deleteSession(session.id);
      setMenuOpenId(null);
      await loadSessions();
    } catch (err) {
      console.error("删除失败:", err);
    }
  }

  return (
    <div className="session-sidebar" style={{
      width: "260px",
      minWidth: "260px",
      height: "100%",
      display: "flex",
      flexDirection: "column",
      borderRight: "1px solid #e5e7eb",
      background: "#fafafa",
    }}>
      {/* 顶部：新建按钮 + 搜索框 */}
      <div style={{ padding: "12px", borderBottom: "1px solid #e5e7eb" }}>
        <button
          onClick={handleCreate}
          style={{
            width: "100%",
            padding: "10px 12px",
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            color: "white",
            border: "none",
            borderRadius: "8px",
            fontSize: "14px",
            fontWeight: 500,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "6px",
            marginBottom: "10px",
          }}
        >
          <Plus size={16} />
          新建对话
        </button>

        {/* 搜索框 */}
        <div style={{ position: "relative" }}>
          <Search size={14} style={{
            position: "absolute",
            left: "10px",
            top: "50%",
            transform: "translateY(-50%)",
            color: "#9ca3af",
          }} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索对话..."
            style={{
              width: "100%",
              padding: "8px 10px 8px 32px",
              border: "1px solid #e5e7eb",
              borderRadius: "6px",
              fontSize: "13px",
              outline: "none",
              background: "white",
            }}
          />
        </div>
      </div>

      {/* 标签页切换：活跃 / 归档 */}
      <div style={{ display: "flex", borderBottom: "1px solid #e5e7eb" }}>
        <button
          onClick={() => setActiveTab("active")}
          style={{
            flex: 1,
            padding: "8px",
            border: "none",
            background: activeTab === "active" ? "white" : "transparent",
            color: activeTab === "active" ? "#6366f1" : "#6b7280",
            fontSize: "13px",
            fontWeight: activeTab === "active" ? 600 : 400,
            cursor: "pointer",
            borderBottom: activeTab === "active" ? "2px solid #6366f1" : "2px solid transparent",
          }}
        >
          对话
        </button>
        <button
          onClick={() => setActiveTab("archived")}
          style={{
            flex: 1,
            padding: "8px",
            border: "none",
            background: activeTab === "archived" ? "white" : "transparent",
            color: activeTab === "archived" ? "#6366f1" : "#6b7280",
            fontSize: "13px",
            fontWeight: activeTab === "archived" ? 600 : 400,
            cursor: "pointer",
            borderBottom: activeTab === "archived" ? "2px solid #6366f1" : "2px solid transparent",
          }}
        >
          归档
        </button>
      </div>

      {/* 会话列表 */}
      <div style={{
        flex: 1,
        overflowY: "auto",
        padding: "4px",
      }}>
        {loading ? (
          <div style={{ textAlign: "center", padding: "20px", color: "#9ca3af", fontSize: "13px" }}>
            加载中...
          </div>
        ) : sessions.length === 0 ? (
          <div style={{ textAlign: "center", padding: "30px 20px", color: "#9ca3af", fontSize: "13px" }}>
            <MessageSquare size={32} style={{ margin: "0 auto 8px", opacity: 0.3 }} />
            <div>{activeTab === "active" ? "暂无对话" : "暂无归档对话"}</div>
            {activeTab === "active" && <div style={{ marginTop: "4px", fontSize: "12px" }}>点击上方"新建对话"开始</div>}
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => onSelectSession(session)}
              style={{
                padding: "10px 12px",
                marginBottom: "2px",
                borderRadius: "8px",
                cursor: "pointer",
                background: currentSessionId === session.id ? "#ede9fe" : "transparent",
                border: currentSessionId === session.id ? "1px solid #c4b5fd" : "1px solid transparent",
                position: "relative",
                transition: "background 0.15s",
              }}
              onMouseEnter={(e) => {
                if (currentSessionId !== session.id) e.currentTarget.style.background = "#f3f4f6";
              }}
              onMouseLeave={(e) => {
                if (currentSessionId !== session.id) e.currentTarget.style.background = "transparent";
              }}
            >
              {/* 置顶图标 */}
              {session.is_pinned === 1 && (
                <Pin size={12} style={{
                  position: "absolute",
                  top: "8px",
                  right: "32px",
                  color: "#8b5cf6",
                  fill: "#8b5cf6",
                }} />
              )}

              {/* 操作菜单按钮 */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setMenuOpenId(menuOpenId === session.id ? null : session.id);
                }}
                style={{
                  position: "absolute",
                  top: "6px",
                  right: "6px",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: "2px",
                  color: "#9ca3af",
                  display: "flex",
                }}
              >
                <MoreVertical size={14} />
              </button>

              {/* 操作菜单 */}
              {menuOpenId === session.id && (
                <div style={{
                  position: "absolute",
                  top: "28px",
                  right: "6px",
                  background: "white",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                  zIndex: 10,
                  overflow: "hidden",
                }} onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => handleTogglePin(session)}
                    style={menuItemStyle}
                  >
                    {session.is_pinned === 1 ? <PinOff size={14} /> : <Pin size={14} />}
                    {session.is_pinned === 1 ? "取消置顶" : "置顶"}
                  </button>
                  <button
                    onClick={() => handleToggleArchive(session)}
                    style={menuItemStyle}
                  >
                    {session.status === "archived" ? <ArchiveRestore size={14} /> : <Archive size={14} />}
                    {session.status === "archived" ? "取消归档" : "归档"}
                  </button>
                  <button
                    onClick={() => handleDelete(session)}
                    style={{ ...menuItemStyle, color: "#ef4444" }}
                  >
                    <Trash2 size={14} />
                    删除
                  </button>
                </div>
              )}

              {/* 会话标题 */}
              <div style={{
                fontSize: "13px",
                fontWeight: 500,
                color: "#1f2937",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                paddingRight: "60px",
                marginBottom: "4px",
              }}>
                {session.title}
              </div>

              {/* 会话元信息 */}
              <div style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                fontSize: "11px",
                color: "#9ca3af",
              }}>
                <span style={{ display: "flex", alignItems: "center", gap: "3px" }}>
                  <Clock size={10} />
                  {formatTime(session.last_message_at || session.created_at)}
                </span>
                <span>·</span>
                <span>{session.message_count} 条消息</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

/**
 * 操作菜单项的样式
 */
const menuItemStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "8px",
  padding: "8px 12px",
  width: "120px",
  background: "none",
  border: "none",
  fontSize: "13px",
  color: "#374151",
  cursor: "pointer",
  textAlign: "left",
};
