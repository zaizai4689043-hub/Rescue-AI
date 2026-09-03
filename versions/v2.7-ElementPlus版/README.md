# v2.7 — Element Plus 版（已归档）

> 首个上线标准平台版本，基于 Vue3 + Element Plus，11 个一级视图，为 v3.0 重构提供基线。

## 版本元信息

| 字段 | 值 |
|------|-----|
| 版本号 | v2.7 |
| 状态 | ✅ 已归档（不再新增功能） |
| 基线时间 | 2026-08-29 |
| 技术栈 | Vue 3 + Element Plus + Vite + ECharts |
| 代码位置 | `frontend/`（11 个 views）、`backend/app/` |

## 核心能力

- 11 个视图: Dashboard / DisasterMap / DisasterReport / DisasterList / ResourceCenter / VolunteerManage / TrackedPersons / AssessmentReport / AIAssistant / UserManage / Login
- Element Plus 原生组件风格
- 色彩: Primary `#409EFF`，严重程度 5 级（绿→深蓝→橙→红→深红）
- 七步灾情上报表单

## 本目录内容

```
v2.7-ElementPlus版/
├── README.md                       ← 本文件
├── archived/
│   ├── AI灾害救援平台PRD.pdf      初始 PRD（产品需求文档 v1）
│   ├── README.md                   v2.7-legacy 归档说明
│   ├── existing-design-system.md   v2.7 设计系统分析
│   └── 演示须知.md                 演示版使用说明（副本）
└── screenshots/                    10 张 Element Plus 版 UI 快照
    ├── 01-dashboard.png
    ├── 02-ai-assistant.png
    ├── 03-situation-map.png
    └── ...（共 10 张）
```

## 归档决策

v2.7 在 v3.0 重构启动后作为"现状基线"留存：
- 其设计系统文档（`existing-design-system.md`）为 v3.0 迁移提供对照
- Element Plus 版的 UI 截图为视觉回归测试的参考标准
- 后续所有视觉/架构变更必须能在 v2.7 截图上对照说明"为什么改"

## 与后续版本的关系

- v2.7 → v3.0: 视觉系统重构（Element Plus → Tailwind），导航从 11 视图精简为 5 模块
- v2.7 → v4.0: 演示线 9 项 AI 能力全量迁入此标准平台

---

*归档时间: 2026-08-30*
