# UI Components Library

## 基础组件

### Button
按钮组件，支持多种变体和尺寸。

**Props:**
- `variant`: 'primary' | 'secondary' | 'danger' | 'ghost' | 'icon'
- `size`: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
- `icon`: 图标组件
- `loading`: Boolean
- `disabled`: Boolean

**使用示例:**
```vue
<Button variant="primary" size="md">主要按钮</Button>
<Button variant="secondary" icon="Search">搜索</Button>
<Button variant="danger" loading>删除中...</Button>
```

### Card
卡片容器组件，支持三种类型。

**Props:**
- `type`: 'default' | 'stat' | 'ai'
- `title`: String
- `icon`: 图标组件
- `borderColor`: 'primary' | 'secondary' | 'accent' | 'critical' | 'high' | 'medium' | 'low' | 'minimal'
- `hover`: Boolean (默认true)

**Slots:**
- `default`: 卡片内容
- `header`: 自定义头部
- `actions`: 操作区域
- `footer`: 底部区域

**使用示例:**
```vue
<Card type="stat" title="总灾情数" icon="Warning" border-color="critical">
  <div class="text-3xl font-bold">1,234</div>
</Card>

<Card type="ai" title="AI分析建议">
  <p>根据当前数据分析...</p>
</Card>
```

### Tag
标签组件，用于状态标记。

**Props:**
- `variant`: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'critical' | 'high' | 'medium' | 'low' | 'minimal'
- `icon`: 图标组件
- `closable`: Boolean

**Events:**
- `close`: 关闭时触发

**使用示例:**
```vue
<Tag variant="critical">P0 危急</Tag>
<Tag variant="success" closable @close="handleClose">已完成</Tag>
```

### Badge
徽章组件，用于数字或状态点。

**Props:**
- `variant`: 'primary' | 'success' | 'warning' | 'danger' | 'info'
- `dot`: Boolean (显示为小圆点)

**使用示例:**
```vue
<Badge variant="danger">5</Badge>
<Badge variant="success" dot></Badge>
```

## 设计原则

### 颜色系统
- **Primary**: #2563EB (主要操作)
- **Secondary**: #0D9488 (次要操作、医疗相关)
- **Accent**: #7C3AED (AI功能专属)
- **Severity**: 按严重程度分级配色

### 间距规范
- xs: 4px
- sm: 8px
- md: 12px
- lg: 16px
- xl: 20px
- 2xl: 24px

### 圆角规范
- sm: 4px (标签、输入框)
- md: 8px (按钮、下拉菜单)
- lg: 12px (卡片、聊天气泡)
- full: 9999px (头像、圆形按钮)

### 阴影规范
- card: 0 1px 3px rgba(0, 0, 0, 0.1)
- card-hover: 0 4px 12px rgba(0, 0, 0, 0.15)
- modal: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24)

### 过渡动画
- fast: 0.15s (微交互)
- base: 0.2s (按钮、输入框)
- slow: 0.3s (卡片、弹窗)

## 无障碍支持

所有组件均支持：
- 键盘导航 (Tab/Shift+Tab)
- ARIA属性标注
- 焦点状态可见
- 屏幕阅读器友好

## 深色模式

组件自动适配深色模式，通过CSS变量切换主题色。

---

*最后更新: 2026-08-29*  
*版本: v3.0*
