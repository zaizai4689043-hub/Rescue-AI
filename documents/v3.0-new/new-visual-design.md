# AI地震救援平台 - 新视觉设计规范

## 1. 设计哲学

### 1.1 核心原则

**"冷静 · 清晰 · 可信"**

在紧急救援场景中，界面设计必须:
1. **降低认知负荷**: 信息层级明确，一眼找到关键内容
2. **减少操作焦虑**: 明确的反馈、可撤销的操作、进度可视化
3. **建立信任感**: 专业稳重的视觉语言，AI辅助但不喧宾夺主

### 1.2 情感化设计策略

| 场景 | 情绪目标 | 设计手段 |
|------|----------|----------|
| 灾情监控 | 警觉但不恐慌 | 冷色调为主，红色仅用于真正紧急 |
| 资源调度 | 有序可控 | 清晰的列表、进度条、状态标签 |
| 人员救援 | 温暖关怀 | 圆润的卡片、柔和的阴影、人性化文案 |
| AI交互 | 智能可靠 | 渐变色、微动效、拟人化头像 |

---

## 2. 色彩系统重构

### 2.1 品牌色升级

#### 主色板

**Primary Blue**
- **色值**: `#2563EB` (更深的科技蓝)
- **用途**: 主要按钮、链接、激活状态
- **情感**: 专业、稳定、可信赖

**Secondary Teal**
- **色值**: `#0D9488` (青绿色)
- **用途**: 次要操作、成功状态、医疗相关
- **情感**: 生命、希望、治愈

**Accent Purple**
- **色值**: `#7C3AED` (紫色)
- **用途**: AI功能、智能推荐、高级特性
- **情感**: 智慧、创新、未来感

#### 功能色板

**严重程度配色 **(优化对比度)
| 等级 | 标签 | 颜色 | 背景色 | 用途 |
|------|------|------|--------|------|
| P0 | 危急 | `#DC2626` | `#FEF2F2` | 立即行动，最高优先级 |
| P1 | 严重 | `#EA580C` | `#FFF7ED` | 紧急处理 |
| P2 | 中等 | `#CA8A04` | `#FEFCE8` | 需要关注 |
| P3 | 一般 | `#2563EB` | `#EFF6FF` | 正常流程 |
| P4 | 轻微 | `#059669` | `#ECFDF5` | 低优先级 |

**状态色板**:
```javascript
{
  success: {
    bg: '#ECFDF5',
    border: '#059669',
    text: '#065F46'
  },
  warning: {
    bg: '#FEF3C7',
    border: '#D97706',
    text: '#92400E'
  },
  error: {
    bg: '#FEE2E2',
    border: '#DC2626',
    text: '#991B1B'
  },
  info: {
    bg: '#DBEAFE',
    border: '#2563EB',
    text: '#1E40AF'
  },
  neutral: {
    bg: '#F3F4F6',
    border: '#6B7280',
    text: '#374151'
  }
}
```

### 2.2 中性色系统

**浅色主题**:
```css
:root {
  /* 文字色 */
  --text-primary: #111827;      /* 标题、重要文本 */
  --text-secondary: #374151;    /* 正文 */
  --text-tertiary: #6B7280;     /* 次要信息、时间戳 */
  --text-disabled: #9CA3AF;     /* 禁用状态 */
  
  /* 背景色 */
  --bg-primary: #FFFFFF;        /* 卡片、弹窗 */
  --bg-secondary: #F9FAFB;      /* 页面背景 */
  --bg-tertiary: #F3F4F6;       /* 输入框、分隔线背景 */
  
  /* 边框色 */
  --border-light: #E5E7EB;      /* 细边框 */
  --border-medium: #D1D5DB;     /* 标准边框 */
  --border-dark: #9CA3AF;       /* 强调边框 */
  
  /* 阴影 */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}
```

**深色主题**:
```css
@media (prefers-color-scheme: dark) {
  :root {
    --text-primary: #F9FAFB;
    --text-secondary: #E5E7EB;
    --text-tertiary: #9CA3AF;
    --text-disabled: #6B7280;
    
    --bg-primary: #1F2937;
    --bg-secondary: #111827;
    --bg-tertiary: #374151;
    
    --border-light: #374151;
    --border-medium: #4B5563;
    --border-dark: #6B7280;
    
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
  }
}
```

### 2.3 渐变系统

**AI功能专属渐变**:
```css
.ai-gradient {
  background: linear-gradient(135deg, #7C3AED 0%, #2563EB 100%);
}

.ai-gradient-subtle {
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(37, 99, 235, 0.1) 100%);
}

.status-gradient-critical {
  background: linear-gradient(90deg, #DC2626 0%, #EA580C 100%);
}
```

---

## 3. 字体与排版系统

### 3.1 字体家族

**中文优先**:
```css
:root {
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 
               'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  --font-mono: 'SF Mono', Monaco, 'Cascadia Code', Consolas, monospace;
}
```

### 3.2 字号阶梯 (基于 1.25 比例)

| 级别 | 名称 | 字号 | 行高 | 字重 | 用途 |
|------|------|------|------|------|------|
| Display | 展示 | 48px | 1.1 | 700 | 大屏数字、倒计时 |
| H1 | 一级标题 | 32px | 1.2 | 700 | 页面主标题 |
| H2 | 二级标题 | 24px | 1.3 | 600 | 模块标题 |
| H3 | 三级标题 | 20px | 1.4 | 600 | 卡片标题 |
| Body-L | 大正文 | 16px | 1.6 | 400 | 重要段落 |
| Body | 正文 | 14px | 1.6 | 400 | 常规内容 |
| Body-S | 小正文 | 13px | 1.5 | 400 | 辅助说明 |
| Caption | 说明文字 | 12px | 1.4 | 400 | 标签、时间戳 |
| Overline | 超小字 | 11px | 1.3 | 500 | 图表标注 |

### 3.3 字重规范

```css
/* 仅使用 400, 500, 600, 700 四种字重 */
.font-regular { font-weight: 400; }  /* 正文 */
.font-medium { font-weight: 500; }   /* 强调、按钮 */
.font-semibold { font-weight: 600; } /* 标题 */
.font-bold { font-weight: 700; }     /* 数字、关键信息 */
```

### 3.4 排版最佳实践

**标题层级**:
```html
<!-- ✅ 正确 -->
<h1 class="text-3xl font-bold">灾情总览</h1>
<h2 class="text-2xl font-semibold">最新灾情</h2>
<h3 class="text-lg font-semibold">建筑倒塌</h3>

<!-- ❌ 错误: 跳过层级或使用不当字重 -->
<h1 class="text-xl font-normal">灾情总览</h1>
```

**段落间距**:
```css
.prose p {
  margin-bottom: 1em;  /* 段落间留白 */
}
.prose h2 + p {
  margin-top: 0.5em;   /* 标题后第一段稍紧凑 */
}
```

---

## 4. 间距与布局系统

### 4.1 间距标尺 (8px网格)

```
0px   - 无间距 (图标内部)
4px   - xs   (紧密元素，如标签内边距)
8px   - sm   (相关元素，如图标与文字)
12px  - md   (组件内元素，如表单字段)
16px  - lg   (组件间距，如卡片之间)
24px  - xl   (模块间距，如章节之间)
32px  - 2xl  (大块留白，如Hero区域)
48px  - 3xl  (页面级留白)
64px+ - 4xl+ (特殊场景)
```

### 4.2 容器宽度

```css
.container-xs { max-width: 480px; }   /* 移动端、侧边栏 */
.container-sm { max-width: 640px; }   /* 对话框 */
.container-md { max-width: 768px; }   /* 表单页 */
.container-lg { max-width: 1024px; }  /* 内容页 */
.container-xl { max-width: 1280px; }  /* 数据表格 */
.container-2xl { max-width: 1536px; } /* 大屏Dashboard */
```

### 4.3 布局模式

**响应式断点**:
```css
/* Mobile First */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
@media (min-width: 1536px) { /* 2xl */ }
```

**常用布局**:
```css
/* 两列布局 (左图右文) */
.grid-2-col {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 24px;
}

/* 三列统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

/* 瀑布流卡片 */
.masonry-grid {
  column-count: 3;
  column-gap: 16px;
}
```

---

## 5. 组件设计规范

### 5.1 按钮系统

#### 按钮变体

**Primary Button **(主要操作)
```css
.btn-primary {
  background: #2563EB;
  color: #FFFFFF;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.2s ease;
}
.btn-primary:hover {
  background: #1D4ED8;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}
.btn-primary:active {
  transform: scale(0.98);
}
```

**Secondary Button **(次要操作)
```css
.btn-secondary {
  background: #FFFFFF;
  color: #374151;
  border: 1px solid #D1D5DB;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 500;
}
.btn-secondary:hover {
  background: #F9FAFB;
  border-color: #9CA3AF;
}
```

**Danger Button **(危险操作)
```css
.btn-danger {
  background: #DC2626;
  color: #FFFFFF;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 500;
}
.btn-danger:hover {
  background: #B91C1C;
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}
```

**Ghost Button **(幽灵按钮)
```css
.btn-ghost {
  background: transparent;
  color: #2563EB;
  padding: 10px 16px;
  border-radius: 8px;
}
.btn-ghost:hover {
  background: rgba(37, 99, 235, 0.1);
}
```

**Icon Button **(图标按钮)
```css
.btn-icon {
  width: 40px;
  height: 40px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}
```

#### 按钮尺寸

```css
.btn-xs { padding: 4px 8px; font-size: 12px; }
.btn-sm { padding: 8px 12px; font-size: 13px; }
.btn-md { padding: 10px 20px; font-size: 14px; }  /* 默认 */
.btn-lg { padding: 12px 24px; font-size: 16px; }
.btn-xl { padding: 16px 32px; font-size: 18px; }
```

### 5.2 卡片系统

**基础卡片**:
```css
.card {
  background: #FFFFFF;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #E5E7EB;
  overflow: hidden;
}
.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #E5E7EB;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-body {
  padding: 20px;
}
.card-footer {
  padding: 16px 20px;
  border-top: 1px solid #E5E7EB;
  background: #F9FAFB;
}
```

**统计卡片 **(StatCard)
```css
.stat-card {
  background: #FFFFFF;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-left: 4px solid var(--accent-color);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.stat-card .icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-bg);
  color: var(--accent-color);
}
.stat-card .value {
  font-size: 32px;
  font-weight: 700;
  color: #111827;
}
.stat-card .label {
  font-size: 14px;
  color: #6B7280;
  margin-top: 4px;
}
```

**AI建议卡片**:
```css
.ai-card {
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.05) 0%, rgba(37, 99, 235, 0.05) 100%);
  border: 1px solid rgba(124, 58, 237, 0.2);
  border-radius: 12px;
  padding: 20px;
  position: relative;
  overflow: hidden;
}
.ai-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #7C3AED 0%, #2563EB 100%);
}
.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: linear-gradient(135deg, #7C3AED 0%, #2563EB 100%);
  color: #FFFFFF;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
```

### 5.3 表单系统

**输入框**:
```css
.input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #D1D5DB;
  border-radius: 8px;
  font-size: 14px;
  color: #111827;
  background: #FFFFFF;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.input:focus {
  outline: none;
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
.input::placeholder {
  color: #9CA3AF;
}
.input-error {
  border-color: #DC2626;
}
.input-error:focus {
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1);
}
```

**选择器**:
```css
.select {
  appearance: none;
  background-image: url("data:image/svg+xml,...");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 40px;
}
```

**表单布局**:
```css
.form-group {
  margin-bottom: 20px;
}
.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}
.form-label-required::after {
  content: '*';
  color: #DC2626;
  margin-left: 4px;
}
.form-hint {
  font-size: 12px;
  color: #6B7280;
  margin-top: 6px;
}
.form-error {
  font-size: 12px;
  color: #DC2626;
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}
```

### 5.4 标签系统

**状态标签**:
```css
.tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.4;
}
.tag-success {
  background: #ECFDF5;
  color: #065F46;
  border: 1px solid #A7F3D0;
}
.tag-warning {
  background: #FEF3C7;
  color: #92400E;
  border: 1px solid #FDE68A;
}
.tag-error {
  background: #FEE2E2;
  color: #991B1B;
  border: 1px solid #FECACA;
}
.tag-info {
  background: #DBEAFE;
  color: #1E40AF;
  border: 1px solid #BFDBFE;
}
.tag-neutral {
  background: #F3F4F6;
  color: #374151;
  border: 1px solid #E5E7EB;
}
```

**带图标标签**:
```css
.tag-with-icon {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.tag-dot::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
```

### 5.5 聊天气泡 (AI助手)

**AI消息**:
```css
.message-ai {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.message-ai .avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #7C3AED 0%, #2563EB 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFFFFF;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}
.message-ai .bubble {
  max-width: 70%;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px 12px 12px 4px;
  padding: 12px 16px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}
.message-ai .bubble p {
  margin: 0 0 8px 0;
}
.message-ai .bubble p:last-child {
  margin-bottom: 0;
}
.message-ai .time {
  font-size: 11px;
  color: #9CA3AF;
  margin-top: 6px;
}
```

**用户消息**:
```css
.message-user {
  display: flex;
  flex-direction: row-reverse;
  gap: 12px;
  margin-bottom: 16px;
}
.message-user .avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #6B7280;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFFFFF;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}
.message-user .bubble {
  max-width: 70%;
  background: #2563EB;
  color: #FFFFFF;
  border-radius: 12px 12px 4px 12px;
  padding: 12px 16px;
}
.message-user .time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 6px;
  text-align: right;
}
```

**快捷问题**:
```css
.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
  background: #F9FAFB;
  border-top: 1px solid #E5E7EB;
}
.quick-action-btn {
  padding: 6px 12px;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 16px;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s ease;
}
.quick-action-btn:hover {
  background: #EFF6FF;
  border-color: #2563EB;
  color: #2563EB;
}
```

---

## 6. 图标系统

### 6.1 图标库选择

**推荐使用**: Lucide Icons (轻量、现代、一致)

**备选**: Heroicons (Tailwind官方推荐)

### 6.2 图标使用规范

**尺寸**:
```css
.icon-xs { width: 12px; height: 12px; }
.icon-sm { width: 16px; height: 16px; }
.icon-md { width: 20px; height: 20px; }  /* 默认 */
.icon-lg { width: 24px; height: 24px; }
.icon-xl { width: 32px; height: 32px; }
.icon-2xl { width: 48px; height: 48px; }
```

**颜色**:
```css
/* 继承父元素颜色 */
.icon-inherit { color: currentColor; }

/* 功能色 */
.icon-success { color: #059669; }
.icon-warning { color: #D97706; }
.icon-error { color: #DC2626; }
.icon-info { color: #2563EB; }
.icon-neutral { color: #6B7280; }
```

**常见图标映射**:
```javascript
{
  // 导航
  dashboard: 'LayoutDashboard',
  map: 'MapPin',
  resources: 'Package',
  people: 'Users',
  ai: 'Sparkles',
  settings: 'Settings',
  
  // 操作
  add: 'Plus',
  edit: 'Pencil',
  delete: 'Trash2',
  search: 'Search',
  filter: 'Filter',
  refresh: 'RefreshCw',
  download: 'Download',
  upload: 'Upload',
  
  // 状态
  success: 'CheckCircle',
  warning: 'AlertTriangle',
  error: 'XCircle',
  info: 'Info',
  loading: 'Loader2',
  
  // 灾情类型
  earthquake: 'Activity',
  building: 'Building2',
  road: 'Route',
  medical: 'HeartPulse',
  rescue: 'LifeBuoy',
}
```

---

## 7. 动效系统

### 7.1 过渡动画

**全局过渡**:
```css
.transition-fast {
  transition: all 0.15s ease;
}
.transition-base {
  transition: all 0.2s ease;
}
.transition-slow {
  transition: all 0.3s ease;
}
```

**常用属性过渡**:
```css
/* 按钮悬停 */
.btn {
  transition: background-color 0.2s ease, 
              transform 0.1s ease,
              box-shadow 0.2s ease;
}

/* 卡片悬停 */
.card {
  transition: transform 0.2s ease,
              box-shadow 0.2s ease;
}

/* 输入框聚焦 */
.input {
  transition: border-color 0.2s ease,
              box-shadow 0.2s ease;
}
```

### 7.2 关键帧动画

**淡入**:
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.fade-in {
  animation: fadeIn 0.3s ease forwards;
}
```

**滑入**:
```css
@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
.slide-in-right {
  animation: slideInRight 0.3s ease forwards;
}
```

**脉冲 **(用于紧急提示)
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
```

**加载旋转**:
```css
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.spin {
  animation: spin 1s linear infinite;
}
```

### 7.3 微交互

**按钮点击反馈**:
```css
.btn:active {
  transform: scale(0.98);
}
```

**开关切换**:
```css
.toggle {
  position: relative;
  width: 44px;
  height: 24px;
  background: #D1D5DB;
  border-radius: 12px;
  transition: background 0.2s ease;
}
.toggle.active {
  background: #2563EB;
}
.toggle-knob {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: #FFFFFF;
  border-radius: 50%;
  transition: transform 0.2s ease;
}
.toggle.active .toggle-knob {
  transform: translateX(20px);
}
```

**进度条**:
```css
.progress-bar {
  height: 8px;
  background: #E5E7EB;
  border-radius: 4px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #2563EB 0%, #7C3AED 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}
```

---

## 8. 响应式设计

### 8.1 断点定义

```css
/* Mobile First 策略 */
:root {
  --breakpoint-sm: 640px;   /* 小屏手机 */
  --breakpoint-md: 768px;   /* 平板 */
  --breakpoint-lg: 1024px;  /* 小屏电脑 */
  --breakpoint-xl: 1280px;  /* 大屏电脑 */
  --breakpoint-2xl: 1536px; /* 超大屏 */
}
```

### 8.2 组件响应式适配

**侧边栏**:
```css
/* 桌面端: 固定宽度 */
.sidebar {
  width: 240px;
  position: fixed;
}

/* 平板: 可折叠 */
@media (max-width: 1024px) {
  .sidebar.collapsed {
    width: 64px;
  }
  .sidebar .logo-text,
  .sidebar .menu-text {
    display: none;
  }
}

/* 移动端: 抽屉式 */
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  .sidebar.open {
    transform: translateX(0);
  }
}
```

**统计卡片**:
```css
/* 桌面: 4列 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

/* 平板: 2列 */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 手机: 1列 */
@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
```

**表格**:
```css
/* 桌面: 完整表格 */
.table-desktop {
  display: table;
}

/* 移动端: 卡片式 */
@media (max-width: 768px) {
  .table-mobile {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .table-row {
    display: flex;
    flex-direction: column;
    padding: 16px;
    background: #FFFFFF;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
}
```

### 8.3 触摸优化

**最小点击区域**: 44x44px (Apple Human Interface Guidelines)

```css
.touch-target {
  min-width: 44px;
  min-height: 44px;
}

/* 移动端增加按钮内边距 */
@media (max-width: 768px) {
  .btn {
    padding: 12px 20px;
  }
}
```

---

## 9. 无障碍设计

### 9.1 色彩对比度

**WCAG AA标准**:
- 普通文字: 对比度 ≥ 4.5:1
- 大号文字 (≥18px): 对比度 ≥ 3:1

**已验证组合**:
```
#111827 on #FFFFFF → 16.1:1 ✅
#374151 on #FFFFFF → 10.3:1 ✅
#6B7280 on #FFFFFF → 5.7:1 ✅
#2563EB on #FFFFFF → 4.5:1 ✅ (临界值)
#FFFFFF on #2563EB → 4.5:1 ✅
```

### 9.2 ARIA标签

```html
<!-- 按钮 -->
<button aria-label="关闭对话框" aria-describedby="close-desc">
  <X />
</button>

<!-- 表单 -->
<label for="email">邮箱地址</label>
<input id="email" type="email" aria-required="true" aria-invalid="false" />
<span id="email-error" role="alert" aria-live="polite">请输入有效的邮箱地址</span>

<!-- 导航 -->
<nav aria-label="主导航">
  <ul role="menubar">
    <li role="none"><a role="menuitem" href="/dashboard">仪表盘</a></li>
  </ul>
</nav>

<!-- 加载状态 -->
<div role="status" aria-live="polite" aria-busy="true">
  <Loader2 class="spin" />
  <span>加载中...</span>
</div>
```

### 9.3 键盘导航

**Tab顺序**: 逻辑顺序，从左到右、从上到下

**焦点样式**:
```css
:focus-visible {
  outline: 2px solid #2563EB;
  outline-offset: 2px;
}
```

**快捷键**:
```javascript
// 全局快捷键
const shortcuts = {
  'r': () => openQuickReport(),      // 快速上报
  'm': () => openMap(),               // 打开地图
  '/': () => focusSearch(),           // 搜索
  'Escape': () => closeDialog(),      // 关闭弹窗
  '?': () => showHelp(),              // 帮助
}
```

---

## 10. 暗色主题

### 10.1 实现策略

**CSS变量切换**:
```css
:root {
  /* 浅色主题变量 */
  --bg-primary: #FFFFFF;
  --text-primary: #111827;
}

@media (prefers-color-scheme: dark) {
  :root {
    /* 深色主题变量 */
    --bg-primary: #1F2937;
    --text-primary: #F9FAFB;
  }
}

/* 手动切换类 */
.dark {
  --bg-primary: #1F2937;
  --text-primary: #F9FAFB;
}
```

### 10.2 深色主题调色板

```css
.dark {
  /* 背景 */
  --bg-primary: #1F2937;      /* 卡片 */
  --bg-secondary: #111827;    /* 页面 */
  --bg-tertiary: #374151;     /* 输入框 */
  
  /* 文字 */
  --text-primary: #F9FAFB;
  --text-secondary: #E5E7EB;
  --text-tertiary: #9CA3AF;
  
  /* 边框 */
  --border-light: #374151;
  --border-medium: #4B5563;
  
  /* 阴影 (更深) */
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
  
  /* 功能色 (降低饱和度) */
  --color-success: #059669;   /* 保持 */
  --color-warning: #D97706;   /* 保持 */
  --color-error: #EF4444;     /* 稍亮 */
  --color-info: #3B82F6;      /* 稍亮 */
}
```

### 10.3 图片与图标适配

```css
/* 深色模式下反转图标颜色 */
.dark .icon-invert {
  filter: invert(1) hue-rotate(180deg);
}

/* 图片降低亮度 */
.dark img {
  filter: brightness(0.9) contrast(1.1);
}
```

---

## 11. 设计令牌 (Design Tokens)

### 11.1 Token定义

```json
{
  "color": {
    "primary": {
      "default": { "value": "#2563EB" },
      "hover": { "value": "#1D4ED8" },
      "active": { "value": "#1E40AF" },
      "light": { "value": "#EFF6FF" }
    },
    "severity": {
      "critical": { "value": "#DC2626" },
      "high": { "value": "#EA580C" },
      "medium": { "value": "#CA8A04" },
      "low": { "value": "#2563EB" },
      "minimal": { "value": "#059669" }
    }
  },
  "spacing": {
    "xs": { "value": "4px" },
    "sm": { "value": "8px" },
    "md": { "value": "12px" },
    "lg": { "value": "16px" },
    "xl": { "value": "24px" },
    "2xl": { "value": "32px" }
  },
  "typography": {
    "fontFamily": {
      "sans": { "value": "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" },
      "mono": { "value": "'SF Mono', Monaco, monospace" }
    },
    "fontSize": {
      "display": { "value": "48px" },
      "h1": { "value": "32px" },
      "h2": { "value": "24px" },
      "body": { "value": "14px" },
      "caption": { "value": "12px" }
    }
  },
  "borderRadius": {
    "sm": { "value": "4px" },
    "md": { "value": "8px" },
    "lg": { "value": "12px" },
    "full": { "value": "9999px" }
  },
  "shadow": {
    "sm": { "value": "0 1px 2px rgba(0, 0, 0, 0.05)" },
    "md": { "value": "0 4px 6px -1px rgba(0, 0, 0, 0.1)" },
    "lg": { "value": "0 10px 15px -3px rgba(0, 0, 0, 0.1)" }
  }
}
```

### 11.2 Token使用示例

**Tailwind配置**:
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'var(--color-primary-default)',
          hover: 'var(--color-primary-hover)',
        },
        severity: {
          critical: 'var(--color-severity-critical)',
          high: 'var(--color-severity-high)',
        }
      },
      spacing: {
        'xs': 'var(--spacing-xs)',
        'sm': 'var(--spacing-sm)',
      },
      borderRadius: {
        'sm': 'var(--border-radius-sm)',
        'md': 'var(--border-radius-md)',
      }
    }
  }
}
```

---

## 12. 实施指南

### 12.1 迁移步骤

**阶段一: 基础准备 **(Week 1-2)
1. 建立Design Tokens文件
2. 配置Tailwind主题
3. 创建全局CSS变量
4. 搭建组件库基础结构

**阶段二: 核心组件重构 **(Week 3-4)
1. 按钮系统
2. 卡片系统
3. 表单组件
4. 标签与徽章

**阶段三: 页面级应用 **(Week 5-6)
1. Dashboard改造
2. 地图页优化
3. 资源中心更新
4. AI助手界面升级

**阶段四: 测试与优化 **(Week 7-8)
1. 跨浏览器测试
2. 无障碍审查
3. 性能优化
4. 用户反馈收集

### 12.2 技术栈建议

**CSS框架**: Tailwind CSS v3+ (实用优先)

**组件库**: 
- 选项A: Headless UI + 自定义样式 (完全可控)
- 选项B: Element Plus + 主题定制 (快速迁移)

**图标**: Lucide React/Vue (轻量、现代)

**动画**: Framer Motion (React) / VueUse Motion (Vue)

**Design Tokens管理**: Style Dictionary 或 Theo

### 12.3 代码规范

**命名约定**:
```css
/* BEM命名法 */
.block {}
.block__element {}
.block--modifier {}

/* 示例 */
.card {}
.card__header {}
.card__body {}
.card--elevated {}
```

**文件组织**:
```
src/styles/
├── tokens/
│   ├── colors.css
│   ├── spacing.css
│   ── typography.css
├── base/
│   ├── reset.css
│   ── variables.css
├── components/
│   ├── button.css
│   ├── card.css
│   └── form.css
├── utilities/
│   ├── animations.css
│   └── helpers.css
└── themes/
    ├── light.css
    └── dark.css
```

---

*文档版本: v1.0*  
*最后更新: 2026-08-29*  
*维护者: Design System Team*
