# v3.0 — 新规划（文档定稿未实施）

> v3.0 规划在 2026-08-29 完成三份定稿文档（架构/视觉/实施），但受 v3.5 复赛冲刺优先级影响，尚未进入实施。

## 版本元信息

| 字段 | 值 |
|------|-----|
| 版本号 | v3.0 |
| 状态 | 📋 文档定稿未实施 |
| 定稿时间 | 2026-08-29 |
| 预计实施 | 决赛后（v3.5 冲刺完成后启动） |

## 规划要点（来自三份定稿文档）

1. **导航精简**: 11 视图 → 5 模块（应急指挥/态势地图/资源中心/人员管理/AI 助手）
2. **上报提速**: 7 步 → 3 步（效率 +57%）
3. **视觉升级**: Element Plus → Tailwind，品牌色 Primary Blue `#2563EB` / Teal `#0D9488` / Accent Purple `#7C3AED`
4. **AI 调度**: 加权评分算法（距离/库存/风险）+ 人工干预点
5. **实时推送**: WebSocket 支持，自动刷新
6. **数据模型**: 7 个 TypeScript 实体（Disaster/Resource/Volunteer/TrappedPerson/RescueTeam/DispatchTask/AIRecommendation）
7. **API 规范**: 20+ RESTful 端点
8. **深色主题**: Mobile First + WCAG AA

## 本目录内容

```
v3.0-新规划未实施/
├── README.md                          ← 本文件
└── plans/                             三份定稿文档（来自 documents/v3.0-new/）
    ├── README.md
    ├── CHANGELOG.md
    ├── new-architecture-plan.md       新架构与功能设计
    ├── new-visual-design.md           新视觉设计规范
    └── implementation-guide.md        实施路线图与技术栈
```

## 实施状态

| 文档 | 状态 | 位置 |
|------|------|------|
| 新架构设计 | ✅ 定稿 | `plans/new-architecture-plan.md` |
| 新视觉设计 | ✅ 定稿 | `plans/new-visual-design.md` |
| 实施指南 | ✅ 定稿 | `plans/implementation-guide.md` |
| 代码实施 | ❌ 未启动 | 被 v3.5 冲刺阻断 |

## 归档决策

v3.0 作为"规划已就绪，等待实施窗口"的版本，三份定稿文档保留在此，待 v3.5 冲刺完成后按 5 阶段推进。
v3.0 规划内容已被 v4.0 产品规划吸收整合。

---

*归档时间: 2026-08-30*
