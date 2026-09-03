# RescueAI 统一部署说明

> 本文档覆盖本仓库四条可运行链路：**主演示载体（真 AI）→ 实时层 → 标准平台 → Vercel 在线版**。
> 定位声明：RescueAI 为地震救援**辅助决策**系统，不替代专业救援判断。

---

## ① 主演示载体：`backend/Qwen 初版`（评委演示主入口）

**零依赖**：仅使用 Python 标准库，无需安装任何第三方包。

```bash
cd "backend/Qwen 初版"
python3 ai_proxy.py
# 启动后访问 http://localhost:8010/
```

- 代理默认监听 `127.0.0.1:8010`（避开标准平台 FastAPI 的 8000 端口）；
  如需投屏设备访问：`RESCUE_AI_PROXY_HOST=0.0.0.0 python3 ai_proxy.py`。
- 停止进程只用 `pkill -f ai_proxy.py`。

### 三种演示模式

| 模式 | URL | 说明 | 前置条件 |
|---|---|---|---|
| 真 AI 模式 | `http://localhost:8010/` | Qwen3.8-Max 文本 + Qwen3.7-Plus 视觉 | `backend/.env` 中配置 `DASHSCOPE_API_KEY`（自备，见根目录 `.env.example`） |
| 保险丝模式 | `http://localhost:8010/?sim=1` | 零 AI 请求、零网络依赖，全流程可演示 | **无**（断网/无密钥可用） |
| 历史回测剧场 | `http://localhost:8010/?replay=1` | 真实时间轴 ×90 压缩回放 2025-03-28 缅甸地震四段叙事 | 建议配合真 AI；可与 sim 叠加：`?replay=1&sim=1` |

无密钥时真 AI 模式的 `/ai/proxy` 请求会自动回落预录兜底文案，页面不崩；详细演示流程见 `backend/Qwen 初版/演示须知.md`。

---

## ② 实时层：`live_feed.py`（社情实时接入）

```bash
cd "backend/Qwen 初版"
python3 live_feed.py --mode mock    # 离线模拟数据流（无外部依赖）
python3 live_feed.py --mode weibo   # 微博官方通道（需 weibo-cli 认证，申请中）
```

- 端口：**8012**。
- `mock` 模式：本地模拟社情数据流，开箱即用，用于联调与演示。
- `weibo` 模式：走微博官方实时通道（weibo-cli），**认证申请中，暂不可用**；在获批前请一律使用 `mock` 模式。禁止使用爬虫方式抓取微博数据。
- 更多用法详见 `backend/Qwen 初版/演示须知.md`。

---

## ③ 标准平台：`backend/app` + `frontend`（平台化框架，建设中）

> ⚠️ 平台化框架，建设中。当前仅为架构框架，功能持续合入中；评委演示请使用①主演示载体。

### 后端（FastAPI，端口 8000）

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example .env    # 填入 SECRET_KEY / DATABASE_URL 等
uvicorn app.main:app --reload --port 8000
```

### 前端（Vue 3 + Vite + Element Plus）

```bash
cd frontend
npm install
npm run dev
```

> 注意：主演示代理（8010）与 FastAPI 后端（8000）**互斥使用**，不要在同一演示中混启。

---

## ④ Vercel 在线版：`deploy/`

> **在线版已具备真实 AI 链路**：在 Vercel 控制台配置 `DASHSCOPE_API_KEY` 后，`/ai/proxy` 走真实 DashScope 调用；未配置时自动降级为离线演示（接口返回 `fallback:true`，页面渲染预录兜底文案，页面不崩）。
>
> 当前生产地址：**https://deploy-eight-mocha-43.vercel.app**

`deploy/` 为 Vercel 部署目录，内容与主演示载体同源：

- `deploy/index.html`：演示页面本体；
- `deploy/assets/`：卫星底图与建筑图片，**必须齐备**——缺失会导致地图画布空白；
- `deploy/vendor/tailwind.js`：本地化 Tailwind 运行时，**必须齐备**——缺失会导致整页样式丢失；
- `deploy/api/`：三个 Vercel Functions（Node ≥18 原生 fetch，零依赖）：
  - `ai-proxy.js` → `POST /ai/proxy`：透传 DashScope 兼容模式，与 `ai_proxy.py` 契约一致（白名单参数、`enable_thinking:false` 默认、无 Key/上游失败/超时均返回 `{fallback:true,reason}`）；上游调用 8s 超时，函数 `maxDuration:10`（Hobby 限制内）；
  - `icl-warnings.js` → `GET /icl/warnings`：返回 `deploy/data/icl_warnings_snapshot.json` 快照 + `offline:true`（前端标签切「离线快照数据」）；
  - `seismic-feed.js` → `GET /seismic/feed`：实时拉 USGS（7s 超时），失败回落与 `ai_proxy.py` 一致的 `OFFLINE_QUAKE` 样例（带 `offline:true`）；
- `deploy/data/icl_warnings_snapshot.json`：与后端同源的 ICL 预警快照（函数打包时内联）；
- `deploy/vercel.json`：rewrites 将 `/ai/proxy`、`/icl/warnings`、`/seismic/feed` 映射到上述函数，静态文件路由不受影响；
- `deploy/.vercel/`：Vercel 项目绑定信息（已被该目录 `.gitignore` 排除）。

### 环境变量（在 Vercel 控制台配置，代码中不保存任何密钥）

| 变量 | 必需 | 说明 |
|---|---|---|
| `DASHSCOPE_API_KEY` | 是（真 AI） | 缺失时 `/ai/proxy` 自动返回 FALLBACK，页面降级为离线演示 |
| `DASHSCOPE_TEXT_MODEL` | 否 | 文本模型覆盖，缺省 `qwen3.8-max` |
| `DASHSCOPE_VL_MODEL` | 否 | 视觉模型覆盖，缺省 `qwen3.7-plus` |

### 发布流程（启用真 AI）

```bash
cd deploy
vercel env add production          # 添加 DASHSCOPE_API_KEY（用户操作，勿写入代码）
vercel --prod                      # 配置环境变量后需重新部署才生效
```

未配置密钥时直接 `vercel --prod` 也可发布：页面全流程可演示，AI 部分走预录兜底（等效离线演示模式）。实时层（`127.0.0.1:8012`）线上不可达，页面已静默降级，不影响演示。

---

## ⑤ 常见故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| 8010 端口被占用 | 旧代理未退出 | `pkill -f ai_proxy.py` 后重启；**切勿** `lsof -ti:8000 \| xargs kill`（会误杀标准平台后端） |
| 页面 AI 响应为空/回退预录文案 | `.env` 缺失或无 `DASHSCOPE_API_KEY` | 检查 `backend/.env`（参照 `.env.example`）；或直接用 `?sim=1` |
| AI 调用超时 | 网络波动 / 模型限流 | 代理已内置视觉 20s / 文本 5s 超时自动兜底，刷新即可；持续失败切 `?sim=1` |
| 断网演示 | 无外网 | `?sim=1`（可叠加 `&replay=1`），零请求全流程可演示 |
| Vercel 在线版样式丢失 | `deploy/vendor/tailwind.js` 缺失 | 补齐 `vendor/tailwind.js` 后重新部署 |
| Vercel 在线版地图画布空白 | `deploy/assets/` 图片缺失 | 补齐 `assets/` 全部图片后重新部署 |
| Vercel 在线版 AI 不出结果 | 未在 Vercel 控制台配置 `DASHSCOPE_API_KEY` | 属自动降级（预录兜底）；在控制台添加该环境变量后重新 `vercel --prod` 即启用真 AI |
| 标准平台 8000 端口冲突 | 已有进程占用 | 换端口：`uvicorn app.main:app --port 8001` |
| `live_feed.py --mode weibo` 报认证错误 | weibo-cli 认证申请中 | 改用 `--mode mock` |
