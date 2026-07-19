# UI 设计规范 / UI Design Specification

> **风格 / Style:** Claude 温暖奶油编辑风 / Warm Cream Editorial
> **配色 / Palette:** 奶油画布 + 珊瑚主色 + 深色技术面板 / Cream canvas + Coral accent + Dark navy technical surfaces

---

## 颜色系统 / Color System

| Token | Hex | 用途 / Usage |
|-------|-----|-------------|
| `--canvas` | `#faf9f5` | 页面主背景，温暖奶油色 / Main background |
| `--surface-soft` | `#f5f0e8` | 参数分组背景 / Parameter group bg |
| `--surface-card` | `#efe9de` | 卡片背景 / Card bg |
| `--surface-dark` | `#181715` | 技术面板（预览/对比/日志）/ Tech panels |
| `--surface-dark-elevated` | `#252320` | 深色面板标题栏 / Dark panel header |
| `--primary` | `#cc785c` | 珊瑚主色 — 按钮、激活态 / Coral CTAs |
| `--primary-active` | `#a9583e` | 珊瑚按压态 / Coral press state |
| `--ink` | `#141413` | 主文字（暖黑色）/ Primary text |
| `--body` | `#3d3d3a` | 正文 / Body text |
| `--muted` | `#6c6a64` | 次要文字 / Secondary text |
| `--muted-soft` | `#8e8b82` | 提示文字 / Captions |
| `--hairline` | `#e6dfd8` | 边框分割线 / Borders, dividers |
| `--on-primary` | `#ffffff` | 珊瑚按钮上的文字 / Text on coral |
| `--on-dark` | `#faf9f5` | 深色面板上的文字 / Text on dark |
| `--success` | `#5db872` | 成功状态 / Success |
| `--error` | `#c64545` | 错误状态 / Error |

---

## 排版 / Typography

| 级别 / Level | 字体 / Font | 字号 / Size | 字重 / Weight | 用途 / Use |
|-------------|------------|------------|--------------|-----------|
| 按钮 / Buttons | Inter | 11px | 500 | 工具栏按钮 |
| 面板标题 / Panel header | Inter | 11px | 500 | 区域标题 (CARRIER, PREVIEW...) |
| 参数值 / Values | JetBrains Mono | 15-18px | 500 | 滑块数值、指标读数 |
| 日志 / Log | JetBrains Mono | 12px | 400 | 底部终端日志 |
| 正文 / Body | Inter | 12-14px | 400 | 文件信息、描述文字 |

---

## 布局 / Layout

```
┌────────────────────────────────────────────────────────┐
│  状态栏: [● ONLINE] EMBED | EXTRACT      ZH | EN | RU  │
├────────────────────────────────────────────────────────┤
│  ┌─ 左列 / Left (奶油色画布) ──┐ ┌─ 右列 / Right ──┐ │
│  │  CARRIER 载体               │ │  PARAMETERS 参数  │ │
│  │  ┌─ 拖拽上传区 ──────────┐  │ │  ┌─ 水印列表 ──┐ │ │
│  │  │  + Drop image or click│  │ │  │ ＋ ADD     │ │ │
│  │  └───────────────────────┘  │ │  │ DEL ▲ ▼   │ │ │
│  │  文件名 | 尺寸 | 大小       │ │  └────────────┘ │ │
│  │                             │ │  ┌─ 位置参数 ─┐ │ │
│  │  PREVIEW 预览               │ │  │ X Y 旋转   │ │ │
│  │  ┌─ 深色面板 ───────────┐  │ │  │ 字号 透明度 │ │ │
│  │  │  canvas / 提取结果   │  │ │  └────────────┘ │ │
│  │  └──────────────────────┘  │ │  ┌─ 算法参数 ─┐ │ │
│  └────────────────────────────┘ │  │ Alpha Delta│ │ │
│                                 │  │ Level      │ │ │
│  COMPARISON 对比 (深色面板)      │  │ SYNC BCH  │ │ │
│  ┌──────────────────────────┐  │  │ 容量显示   │ │ │
│  │  FOUND 4/4               │  │  └────────────┘ │ │
│  │  [TYPE] text             │  │  ┌────────────┐ │ │
│  │  PSNR SSIM BITS STATUS   │  │  │ ⟫ EMBED ⟪ │ │ │
│  └──────────────────────────┘  │  └────────────┘ │ │
│                                 └────────────────┘│
│  LOG 日志 (深色面板)                              │
│  ┌──────────────────────────────────────────────┐│
│  │  [HH:MM:SS] >>> message                     ││
│  └──────────────────────────────────────────────┘│
└────────────────────────────────────────────────────┘
```

---

## 组件 / Components

| 组件 | 样式 / Style |
|------|-------------|
| **状态栏 / Status Bar** | 56px 高，奶油色背景，珊瑚色分割 `\|` |
| **上传区 / Drop Zone** | 2px 虚线边框 `--hairline`，12px 圆角，hover 变珊瑚色 |
| **预览面板** | `--surface-dark` 背景，12px 圆角 |
| **参数分组** | `--surface-soft` 背景，8px 圆角，1px `--hairline` 边框 |
| **滑块 / Sliders** | 3px 轨，14px 珊瑚色圆形拖块 |
| **按钮 / Buttons** | Inter 11px/500，8px 圆角，珊瑚色激活态 |
| **执行按钮 / Execute** | 珊瑚色填充 `--primary`，白色文字，hover 变深 |
| **复选框/切换** | 珊瑚色激活 `--primary` |
| **日志面板 / Log** | 深色背景，JetBrains Mono 12px，时间戳灰色 |
| **模态框 / Modal** | 居中，`backdrop-filter: blur(4px)`，16px 圆角 |


## 状态颜色 / Status Colors

| 状态 | 圆点 | 含义 |
|------|------|------|
| IDLE | 🟢 `--success` | 空闲，等待操作 |
| BUSY | 🔴 `--error` | 处理中，按钮禁用 |
| ERROR | 🔴 `--error` | 处理失败，日志显示错误 |
| DONE | 🟢 `--success` | 完成，显示结果指标 |

---

## 响应式 / Responsive

- **> 768px:** 两列网格 / Two-column grid (1fr 1.2fr)
- **< 768px:** 单列堆叠 / Single column stacked
- **< 480px:** 状态栏紧凑排列 / Compact status bar
