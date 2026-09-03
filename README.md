# RescueAI —— 地震黄金 72 小时 AI 辅助决策系统

> **定位声明：RescueAI 是辅助决策系统，为救援指挥提供信息聚合与研判参考，不替代专业救援判断。**

基于 2025-03-28 缅甸 M7.7 地震真实数据的数字孪生推演系统：双源感知抢回信息时差，AI 把「看清灾情 → 排出优先级 → 调度救援」的决策链压缩到分钟级。

---

## 核心能力概览

| 能力 | 说明 |
|---|---|
| 双源感知 | ICL 地震预警（成都高新减灾研究所，含离线快照降级）× 微博社情瀑布流，仪器台网与社交媒体互为补充 |
| AI 灾情简报 | 官方通报空窗期，基于社情样本实时生成 ≤200 字灾情简报（Qwen3.8-Max） |
| P0–P3 救援优先级 | 按倒塌形态、失联规模与跨境影响排序，每档附社情证据链与依据 |
| 社情热力图 | 帖量累计曲线、损毁类型分布、关键词与情感时间线可视化 |
| 空中搜索 | 无人机全域扫描、被困人员点亮；遥测协议已预留真机接入接口（`POST /drone/telemetry`） |
| 余震联动 | 弱余震不打断作业；强余震（mag≥5）自动暂停破拆支护后恢复 |
| 历史事件回测 | `?replay=1` 真实时间轴 ×90 压缩回放，四段叙事全程可复现 |
| 三级降级保险丝 | 真 AI → 预录兜底 → `?sim=1` 纯仿真，断网/断密钥全流程可演示 |

---

## 仓库结构

```
├── backend/
│   ├── Qwen 初版/          ★ 主演示载体（真 AI）：ai_proxy.py + 代码1.2-ai.html，零依赖
│   ├── app/                标准平台后端（FastAPI，建设中）
│   └── requirements.txt
├── frontend/               标准平台前端（Vue3 + Vite + Element Plus，建设中）
├── work buddy接力/          平台化路线图补丁包（未合并，含架构设计与集成指南）
├── GOAI复赛/               复赛交付：单文件指挥大屏 rescueai-dashboard.html + 提交附件
├── deploy/                 Vercel 在线版（配置 Key 后真 AI，未配置自动降级离线演示）
├── pw-test/                Playwright 验收测试脚本
├── outputs/                参赛文档：产品说明/商业计划书/路演讲稿等
├── screenshots/            运行证据（各任务验收截图）
├── DEPLOYMENT.md           统一部署说明
└── 数据来源与合规说明.md     数据来源与合规声明
```

各块之间的关系：

- **`backend/Qwen 初版`** —— 主演示载体，评委演示唯一入口，真 AI 全流程可跑（见下「快速开始」）。
- **`backend/app` + `frontend`** —— 标准平台框架（建设中），把主演示能力逐步平台化。
- **`work buddy接力`** —— 平台化路线图的补丁包（**未合并**），包含架构设计、集成指南与分工 prompt，供后续合入参考。
- **`GOAI复赛`** —— 复赛交付载体：单文件指挥大屏 `rescueai-dashboard.html`（社媒线索核实闭环抽屉 + 属地公益救援队推送追踪），已同步部署为在线版 `/semifinal.html`。
- **`deploy`** —— Vercel 在线版，与主演示同源：在 Vercel 控制台配置 `DASHSCOPE_API_KEY` 后具备真实 AI 链路，未配置时自动降级为离线演示（预录兜底）。当前地址：https://deploy-eight-mocha-43.vercel.app（复赛大屏：https://deploy-eight-mocha-43.vercel.app/semifinal.html）

---

## 快速开始

### 主演示载体（三模式）

```bash
cd "backend/Qwen 初版"
python3 ai_proxy.py        # 零依赖，仅 Python 标准库
```

| 模式 | URL | 条件 |
|---|---|---|
| 真 AI | http://localhost:8010/ | `backend/.env` 配置 `DASHSCOPE_API_KEY` |
| 零密钥离线演示 | http://localhost:8010/?sim=1 | 无（断网可用） |
| 历史回测剧场 | http://localhost:8010/?replay=1 | 可叠加 `&sim=1` |

### 实时层（社情接入，端口 8012）

```bash
python3 live_feed.py --mode mock    # 离线模拟数据流，开箱即用
python3 live_feed.py --mode weibo   # 微博官方通道（weibo-cli 认证，申请中）
```

### 标准平台（建设中）

```bash
# 后端：FastAPI 8000
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端：Vue3 + Vite
cd frontend && npm install && npm run dev
```

> 端口互斥说明与完整部署/排障见 [DEPLOYMENT.md](./DEPLOYMENT.md)。

---

## 配置说明

- 环境变量模板：根目录 [`.env.example`](./.env.example)，复制为 `backend/.env` 后填入。
- **DashScope Key 需自备**（阿里云百炼平台申请），用于真 AI 模式。
- **无密钥也可演示**：`?sim=1` 零 AI 请求、零网络依赖，全流程可跑。
- `.env` 已被 `.gitignore` 排除，密钥绝不入库。

---

## 测试与运行证据

验收测试基于 Playwright，位于 `pw-test/`：

```bash
cd pw-test
npm i && npx playwright install
node verify-ai.mjs         # 逐个运行，或按脚本名执行
```

脚本覆盖：AI 调用链路（`verify-ai.mjs`）、多模态兜底链路（`t13-acceptance.mjs`）、余震联动与救援流程（`t15-acceptance.mjs`）、沙盘画布渲染（`t17-canvas-shot.mjs`）、回测剧场（`verify-replay.mjs`）、实时社情层冒烟（`verify-live.mjs`）、空中搜索/投放（`t26-acceptance.mjs`、`t27-acceptance.mjs`）、复赛大屏核实闭环（`verify-drawer.mjs`、`verify-semifinal.mjs`、`verify-live-semifinal.mjs`）及多轮对齐回归（`verify-*`）。

**[`screenshots/`](./screenshots/) 目录为各任务的运行证据截图**，与脚本一一对应。

---

## 部署

四条部署链路（主演示 / 实时层 / 标准平台 / Vercel 在线版）与故障排查，统一见 **[DEPLOYMENT.md](./DEPLOYMENT.md)**。

---

## 数据与合规

详见根目录 **《[数据来源与合规说明.md](./数据来源与合规说明.md)》**。

一句话摘要：学术公开数据集脱敏使用、官方实时通道（weibo-cli）申请中、禁止爬虫方式获取数据。

---

## 数据口径附录（答辩引用）

| 口径 | 表述 |
|---|---|
| 震级双口径 | CENC 7.9（深 30km）/ USGS Mw 7.7（深 10km），页面以并排刻度卡呈现 |
| 首条涉震微博 | 早于主震发震时刻 **1 分 46 秒** |
| 社媒伤亡数字 | 约震后 **5 分钟**开始流传（官方首报为 03-28 19:15，沉默约 5 小时） |
| 死亡数字 | **截至 3/29 晚通报 1,644 人**，持续更新中 |
| 内嵌社情样本 | **52 条**精选微博（数据集全库 53,340 条，已匿名化） |

---

## 开源与复用

本项目以 **[MIT License](./LICENSE)** 开源，Copyright (c) 2026 RescueAI Team。

### 路线图

1. **微博官方实时接入**：weibo-cli 认证获批后，`live_feed.py --mode weibo` 切换真实时社情流；
2. **商业数据 API**：舆情服务直签，扩展多平台社情感知；
3. **无人机真机遥测**：遥测协议（`DRONE_TELEMETRY_SCHEMA`）已预留，经大疆 Cloud API / MAVLink 转发即可替换仿真；
4. **可穿戴设备接入**：救援人员与被困者生命体征数据回传；
5. **平台化合入**：`work buddy接力` 补丁包合入 `backend/app` + `frontend`，完成标准平台建设。

---

*AI 不替代救援者，它做的只是把时间抢回来。*
