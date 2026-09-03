# RescueAI 产品升级方案 — WorkBuddy 接力

> 基于 6 条产品愿景，将 Qwen 演示版的智能逻辑回流到 FastAPI 标准架构，构建完整的 AI 地震救援决策平台。

---

## 一、背景

当前项目存在两套代码：

| | 标准平台 | 演示版 |
|---|---|---|
| 位置 | `backend/app/` + `frontend/` | `backend/Qwen 初版/` |
| AI 能力 | 空壳（模拟数据） | 真实 Qwen 调用 |
| 数据流 | SQLite CRUD | 内嵌 JSON + 实时 API |

**目标**：将演示版的 AI 智能逻辑回流到标准平台架构，实现 6 条产品愿景。

---

## 二、6 条产品愿景与技术映射

| # | 产品愿景 | 实现文件 |
|---|---|---|
| 1 | 两套代码合一 | `backend/services/ai_client.py` — DashScope 客户端从演示版回流 |
| 2 | 实时数据管道 | `backend/services/weibo_pipeline.py` + `nlp_service.py` + `models/weibo_post.py` |
| 3 | 地图聚合+优先级 | `backend/services/hotspot_service.py` + `priority_engine.py` + `models/disaster_hotspot.py` |
| 4 | 多维分析仪表盘 | `backend/services/analytics_service.py` + `frontend/views/SocialDashboard.vue` |
| 5 | AI 灾情简报 | `backend/services/brief_generator.py` + `prompts/brief_prompt.md` |
| 6 | AI 决策助手 | `backend/services/decision_assistant.py` + `case_matcher.py` + `data/rescue_cases.json` |
| 7 | 无人机空中救援 | `backend/services/drone_service.py` + `supply_service.py` + `recon_service.py` |

---

## 三、文件结构

```
work buddy接力/
├── README.md                              # 本文件
├── 架构设计.md                             # 整体架构 + 数据流设计
├── 集成指南.md                             # 如何接入现有项目
│
├── backend/
│   ├── models/
│   │   ├── weibo_post.py                  # 微博数据模型
│   │   ├── disaster_hotspot.py            # 灾情热点模型
│   │   ├── rescue_case.py                 # 救援案例模型
│   │   ├── drone.py                       # 无人机 + 任务模型
│   │   ├── supply_delivery.py             # 物资投送记录模型
│   │   └── aerial_recon.py                # 空中侦察记录模型
│   ├── schemas/
│   │   ├── weibo.py                       # 微博 Schema
│   │   ├── analytics.py                   # 分析 Schema
│   │   └── drone.py                       # 无人机模块 Schema
│   ├── services/
│   │   ├── ai_client.py                   # DashScope AI 客户端（从演示版回流）
│   │   ├── weibo_pipeline.py              # 微博数据管道（采集→过滤→入库）
│   │   ├── nlp_service.py                 # NER + 情感分析 + 损毁标签
│   │   ├── hotspot_service.py             # 地图聚合 + 灾情热点生成
│   │   ├── priority_engine.py             # 动态优先级引擎
│   │   ├── analytics_service.py           # 多维分析仪表盘
│   │   ├── brief_generator.py             # AI 灾情简报生成
│   │   ├── case_matcher.py                # 历史案例匹配引擎
│   │   ├── decision_assistant.py          # AI 决策助手
│   │   ├── drone_service.py               # 无人机机队/遥测/巡逻仿真
│   │   ├── supply_service.py              # 物资运输规划/投送
│   │   └── recon_service.py               # 空中侦察/AI路线分析
│   └── api/
│       ├── weibo.py                       # 微博数据 API
│       ├── analytics.py                   # 分析仪表盘 API
│       ├── brief.py                       # 灾情简报 API
│       ├── decision.py                    # AI 决策 API
│       ├── drone.py                       # 无人机机队/遥测/任务 API
│       ├── supply.py                      # 物资投送 API
│       └── recon.py                       # 空中侦察 API
│
├── frontend/
│   ├── api/
│   │   ├── weibo.js                       # 微博 API 封装
│   │   ├── analytics.js                   # 分析 API 封装
│   │   ├── brief.js                       # 简报 API 封装
│   │   ├── decision.js                    # 决策 API 封装
│   │   └── drone.js                       # 无人机模块 API 封装
│   ├── stores/
│   │   └── disaster.js                    # 灾情全局 Store
│   └── views/
│       ├── SocialDashboard.vue            # 社媒感知仪表盘
│       ├── DisasterHeatmap.vue            # 灾情热力图
│       ├── BriefCenter.vue                # 灾情简报中心
│       ├── DecisionAssistant.vue          # AI 决策助手
│       ├── DroneCommand.vue               # 无人机指挥中心（含巡逻动画）
│       ├── SupplyDelivery.vue             # 物资投送管理
│       └── AerialRecon.vue               # 空中侦察/路线研判
│
├── data/
│   └── rescue_cases.json                  # 救援案例知识库（结构化）
│
└── prompts/
    ├── brief_prompt.md                    # 灾情简报提示词
    ├── decision_prompt.md                 # 决策助手提示词
    ├── nlp_prompt.md                      # NLP 打标提示词
    ├── priority_prompt.md                 # 优先级排序提示词
    ├── recon_route_prompt.md              # 无人机路线分析提示词
    └── supply_plan_prompt.md              # 物资投送规划提示词
```

---

## 四、数据流总览

```
ICL 地震预警触发
    │
    ▼
微博 API 监测关键词 ──→ 噪声过滤（去重/辟谣/机器人/地理围栏）
    │
    ▼
NLP 处理 ──→ NER 地名提取 + 情感分析 + 损毁类型标签
    │
    ├──→ 地图聚合 ──→ 频次 × 严重度 → 灾情热力图
    │                    │
    │                    ▼
    │              动态优先级引擎 ──→ P0-P3 排序
    │                    │           （叠加：呼救信号 + 资源约束 + 72h 窗口）
    │                    │
    │                    ▼
    │              AI 决策助手 ──→ 预测 + 案例匹配 + 行动方案
    │
    ├──→ 多维分析仪表盘 ──→ 损毁分布 / 关键词排行 / 情感时间线
    │
    └──→ AI 灾情简报 ──→ Qwen3.8-Max 生成应急管理部风格通报

                         ┌──→ 无人机空中救援模块 ──┐
                         │     ① 巡逻搜索（保留演示动画）│
                         │     ② 物资投送（载重约束+航线规划）│
                         │     ③ 空中侦察（AI路线研判）│
                         └──────────────────────────┘
```

---

## 五、与现有代码的集成方式

### 后端集成

1. 将 `backend/models/*.py` 中的模型注册到 `backend/app/database.py` 的 `Base`
2. 将 `backend/api/*.py` 中的路由挂载到 `backend/app/api/v1/router.py`
3. 将 `backend/services/ai_client.py` 替换 `ai_service.py` 和 `ai_assistant_service.py` 中的模拟逻辑
4. 在 `backend/app/config.py` 中新增微博 API 和 DashScope 配置项

### 前端集成

1. 将 `frontend/api/*.js` 中的 API 函数挂载到现有 Axios 实例
2. 将 `frontend/views/*.vue` 注册到 `frontend/src/router/index.js`
3. 在 `frontend/src/layouts/MainLayout.vue` 侧边栏新增菜单项

---

## 六、技术栈

- **后端**：FastAPI + SQLAlchemy + SQLite（与现有架构一致）
- **AI**：DashScope API（Qwen3.8-Max 文本 / Qwen3.7-Plus 视觉）
- **NLP**：Qwen LLM + 自建地名词典 + 规则引擎
- **前端**：Vue 3 + Element Plus + ECharts（与现有架构一致）
- **数据源**：企业微博 API + ICL 地震预警 API + USGS 地震目录
