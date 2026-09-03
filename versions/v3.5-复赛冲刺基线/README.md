# v3.5 — 复赛冲刺基线

> 当前工作版本。目标: 在 2026-09-04 体验包到期前稳定交付，演示线 + 最小平台化 + Vercel 在线版 三线并进。

## 版本元信息

| 字段 | 值 |
|------|-----|
| 版本号 | v3.5 |
| 状态 | 🚧 冲刺中 |
| 起止时间 | 2026-08-29 → 2026-09-04 |
| 核心目标 | 复赛交付 + 平台化最小合入 |

## 三条产品线

| 产品线 | 载体 | 职责 |
|--------|------|------|
| 演示线 | `backend/Qwen 初版/` (8010 + 8012) | 核心 AI 能力演示 |
| 平台线 | `frontend/` + `backend/app/` | 最小社情合入，承载"平台化架构"叙事 |
| 在线线 | `deploy/` (Vercel) | 评委/公众在线访问 |

## 冲刺范围（DoD）

### 必做（P0）
- [ ] 平台线最小社情合入验收:
  - `app/services/social/PlatformAdapter` 抽象基类
  - `weibo_adapter` 移植已验证解析逻辑
  - 抖音/小红书占位适配器
  - `SocialPost` 模型
  - `/api/v1/social` 四端点（ingest/batch-ingest/posts/heatmap）
  - 52 条种子离线回填
- [ ] `/ingest` 端点鉴权补齐（已知技术债）
- [ ] 演示排演通过
- [ ] Vercel 在线版三模式 E2E 通过（已完成）
- [ ] 口径规范终审（CENC 7.9 / USGS Mw7.7 双口径；伤亡数据时点标注）

### 不做（明确排除）
- ❌ `work buddy接力/` 补丁包整包合入（推迟到 v4.0）
- ❌ v3.0 视觉重构（推迟到 v4.0）
- ❌ WebSocket 实时推送（推迟到 v4.0）

## 本目录内容

```
v3.5-复赛冲刺基线/
├── README.md                           ← 本文件
├── deliverables/                       交付物
│   ├── RescueAI产品说明.md
│   ├── RescueAI商业计划书.docx / .html
│   ├── RescueAI路演讲稿.md
│   ├── 评测指标.md
│   ├── 评委建议优化方案.md
│   ├── 演示排演报告.md
│   ├── 演示视频脚本.md
│   ├── weibo-cli实测清单.md
│   ├── 数据来源与合规说明.md
│   └── DEPLOYMENT.md
└── pitch/                              路演/复赛 PPT
    ├── Pitching Deck Template_Physical AI Hackathon.pptx
    ├── RescueAI - Physical AI for Earthquake Rescue.pptx
    ├── RescueAI_20260719.pdf
    ├── RescueAI_答辩PPT.pptx
    ├── RescueAI复赛方案.pptx
    ├── RescueAI路演PPT.pptx
    ├── DESIGN.md
    └── STORY.md
```

## 关键风险

1. **weibo-cli 体验包 2026-09-04 到期**: 外部依赖，不可控
2. **`/ingest` 未加鉴权**: 上线前必补
3. **多载体维护成本**: 演示线/平台线/在线线三线并进，需要明确优先级

## 验收方式

- Playwright E2E (`pw-test/`)
- 演示排演通过
- Vercel 在线版三模式（live/replay/sim）可用
- 答辩材料口径终审通过

---

*基线时间: 2026-08-30*
