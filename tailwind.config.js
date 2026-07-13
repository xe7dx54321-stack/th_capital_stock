/** @type {import('tailwindcss').Config} */

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    container: {
      center: true,
    },
    extend: {
      gridTemplateColumns: {
        // --- 新增：13 列栅格，用于 ValueScoreList 更复杂的表格布局
        "13": "repeat(13, minmax(0, 1fr))",
      },
      colors: {
        // Anthropic 风格配色
        surface: "#0f0f0f",        // 主背景（深炭灰）
        "surface-2": "#1a1a1a",     // 卡片背景
        "surface-3": "#252525",     // hover/内层
        "surface-4": "#2f2f2f",     // 边框/分隔

        text: "#f5f1ea",            // 主文字（米白）
        "text-muted": "#8a8a8a",    // 次要文字
        "text-dim": "#5a5a5a",      // 更次要

        accent: "#d4a373",          // 强调色（柔和珊瑚）
        "accent-2": "#e9c9a8",      // 次要强调色

        // 评分颜色
        "score-good": "#7cb342",
        "score-mid": "#d4a373",
        "score-bad": "#b74a2c",
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(0,0,0,0.2), 0 1px 3px rgba(0,0,0,0.1)",
        card: "0 2px 8px rgba(0,0,0,0.3)",
        hover: "0 4px 16px rgba(0,0,0,0.4)",
      },
    },
  },
  plugins: [],
};
