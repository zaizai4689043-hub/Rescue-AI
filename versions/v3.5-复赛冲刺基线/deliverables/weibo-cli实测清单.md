# weibo-cli 个人认证通道实测清单

> 任务 #23 第一阶段交付物 · 产出时间：2026-08-28 ｜ 最终实测更新：2026-08-28 晚（A 情形达成，见「五、最终实测结论」）
> 范围：只读探测 + 用户侧操作清单。本文档不含任何登录操作（登录须用户本人浏览器授权），未改动任何产品代码。

> **【最终实测结论 · 2026-08-28 晚】✅ 对照表 A 情形（全通→直接联调）已达成**：开发者认证当日 13:56 通过，`doctor` 三闸门全绿；7 天免费体验包已领取（`trial_active`，有效至 2026-09-04，期间 search 零积分消耗）；实调 `search statuses/limited --q 地震 --type 1` 成功（顶层键 `statuses`、20 条、`id/text/created_at` 齐全，与 `_parse_weibo` 假设完全匹配，无需改代码）；`live_feed.py --mode weibo` 联调通过，`/live/social` 返回 `source:"weibo"` 的真实微博文本与话题标签；weibo→cache→mock 三级降级链验证有效，体验期到期后自动降级、服务不挂。7 步清单全部完成，见下方各步 ✅ 标注。

> **【第二轮实测 · 2026-08-28】执行状态**：① 安装 + `weibo --version` + `weibo --help` 已由助手完成（**本地安装** `weibo-cli/` 文件夹，非全局 `-g`）；②~⑦ 由用户本人登录后可执行。未登录态 `weibo doctor` 曾揭示 3 道闸门（登录账号 / 完成开发者认证 / 开通服务）构成的不确定性，已在最终实测中全部解除（见「五」）。

---

## 〇、本机探测结论摘要

| 探测项 | 结果 |
| --- | --- |
| `which weibo`（全局） | **未安装全局包**（按上一轮要求改为本地安装）：`weibo-cli/` 下 `npm install @weibo-ai/weibo-cli@0.9.1` 成功，`node_modules/.bin/` 提供 `weibo`/`wb`/`weibo-cli` 三别名，均指向 `dist/index.js` |
| `npm ls -g` 全局包 | 无 weibo 相关全局包；本机 Node v25.5.0 / npm 11.8.0（满足 CLI 要求 Node ≥ 18） |
| npm 最新版 | `@weibo-ai/weibo-cli@0.9.1`（18 个版本，约 2 周前发布，MIT，唯一依赖 undici） |
| bin 命令名 | `weibo`、`weibo-cli`、`wb` 三个别名，均指向 `dist/index.js` |
| README 核实 | 命令模式 `weibo <group> <action> [flags]`；action 可含 `/`（如 `search statuses/limited`）；全局 flag `--output json\|table\|yaml\|raw`、`--token`、`-h/--help`；认证走浏览器 / 设备码（`auth login` / `auth login --device`），token 存 OS keychain |
| `weibo --help` 实测 | **已执行**（本地 `./node_modules/.bin/weibo --help`）：命令模式 `weibo <group> <action> [flags]`；内置 commands = `me / doctor / auth / commands / version / check_update / upgrade`；**平台命令（statuses/comments/search/users…）仅在登录后可见**（help 末尾明示 `Log in ... to see platform commands`） |

**live_feed.py 版本敏感点核查**（`backend/Qwen 初版/live_feed.py`）：

- CLI 调用字符串：`['weibo', 'search', 'statuses/limited', '--q', q, '--output', 'json']` —— 与 README 示例 `weibo search statuses/limited --q keyword` + `--output json` **完全一致**，命令名与参数名无版本漂移风险（0.9.1 口径）。
- `_parse_weibo` 顶层容器尝试 `data / statuses / items / list / cards / result`，并支持再嵌套一层 `{statuses:[...]}`；本身为 list 直接用。
- 单帖取值：`id | idstr | mid` + `text | raw_text | long_text | content`，缺任一即跳过该条；`created_at` 容忍 epoch 秒/毫秒、ISO、微博原生英文格式，失败回落原文。
- 唯一敏感点：**若 0.9.1 实际返回的顶层键不在上述 6 个之内**（如 `data` 内再套未覆盖的键名），会抛 `未识别的 weibo-cli 顶层结构`，此时按「对照表」改一处映射即可——这正是步骤⑥要求回传原始 JSON 的原因。
- 超时 25s（`WEIBO_TIMEOUT`）；stderr 含 auth/login/token 字样时归因为未认证，上层自动降级，不会阻塞 HTTP。

**未登录态实测（第二轮 · 2026-08-28，本地安装后助手执行，未登录、无令牌）：**

| 命令 | 输出（节选） | 含义 |
| --- | --- | --- |
| `weibo auth whoami` | `缺少登录令牌。请运行 weibo-cli auth login…` | 无令牌即拒绝，符合预期 |
| `weibo doctor` | `× 登录账号` / `× 完成开发者认证` / `× 开通服务` → `下一步: weibo-cli auth login` | **关键**：未登录即提示 3 道闸门，其中「完成开发者认证」「开通服务」与个人开发者身份强相关 |
| `weibo commands list` | `缺少登录令牌…` | 登录前无法列出平台命令，步骤⑤须登录后补跑 |
| `weibo commands show search statuses/limited` | `缺少登录令牌…` | 同上，步骤⑤参数签名核对须登录后补跑 |

> 以上 4 条命令均**不含任何写操作、不触发授权跳转**，属安全只读探测；完整输出见 `outputs/weibo_probe/03_whoami.txt` ~ `06_commands_show.txt`。

---

## 一、用户侧 7 步操作清单【✅ 已全部完成，2026-08-28】

> 请在**用户本人终端**逐步执行。全部命令均为一次性前台命令，无常驻服务。

### ① 安装 weibo-cli ✅

> ✅ **助手已执行（第二轮）**：本地安装成功（`weibo-cli/` 文件夹内 `npm install @weibo-ai/weibo-cli`），`weibo --version` = **0.9.1**，`weibo --help` 全文已捕获（见 `outputs/weibo_probe/02_help.txt`）。注意：安装为**本地**而非文档示例的全局 `-g`；若要让 `live_feed.py` 通过 PATH 直接命中 `weibo`，需 `export PATH="/Users/zaizai/Downloads/AI地震救援/weibo-cli/node_modules/.bin:$PATH"`，或改全局安装——请确认偏好。

```bash
npm install -g @weibo-ai/weibo-cli
weibo --version
weibo --help
```

- **预期输出**：版本号 `0.9.1`（或更新）；`--help` 列出 groups：`statuses / comments / friendships / search / users / attitudes / tags / short_url / wbindex` 及内置 `auth / me / commands / config / version / upgrade`。
- **失败怎么办**：
  - `EACCES` 权限错误 → 改用 `npm config set prefix ~/.npm-global` 并把 `~/.npm-global/bin` 加进 PATH，或用 `npx @weibo-ai/weibo-cli`（注意：npx 方式下后续所有 `weibo` 命令都要换成 `npx @weibo-ai/weibo-cli`，live_feed.py 的 PATH 依赖会不满足，**建议仍走全局安装**）。
  - 镜像源问题 → `npm install -g @weibo-ai/weibo-cli --registry=https://registry.npmjs.org`。

> ⚠️ **步骤②~⑦ 须用户本人执行**：涉及浏览器/设备码授权登录、领积分、实调检索，均触碰个人账号凭据与可能产生费用，助手不代登、不代付。以下仅保留操作指引，待你登录后照跑，并把第二节「需回传信息清单」发回即可。

### ② 登录（浏览器/设备码授权）✅

> **实测结果**：用户本人浏览器授权登录成功，token 存入 macOS 钥匙串；网页端开发者认证于 **2026-08-28 13:56 通过**，CLI 网关身份快照同日同步。

```bash
weibo auth login
# 若终端提示设备码流程或处于 SSH/无图形环境：
weibo auth login --device
```

- **预期输出**：桌面终端自动拉起浏览器授权页；`--device` 时终端打印设备码与确认网址，需**本人在浏览器中确认**。成功后终端提示登录完成，token 存入 OS keychain（macOS 为钥匙串）。
- **失败怎么办**：
  - 浏览器未弹出 → 手动复制终端给出的 URL 到浏览器；仍失败用 `--device` 强制设备码。
  - 提示权限不足/未认证开发者 → 记录**完整报错原文**回传；这直接关系到下文「影响评估」。
  - 登录成功与否都请继续：成功走③~⑦；失败则把报错原文作为回传信息，通道评估直接落到对照表第 4 行。

### ③ 会话与就绪状态 ✅

> **实测结果**：`weibo auth whoami` 返回账号身份（用户 7890910050）；`weibo doctor` **三道闸门全绿**（登录账号 / 完成开发者认证 / 开通服务），第二轮实测的不确定性全部解除。

```bash
weibo auth whoami
weibo doctor
```

- **预期输出**：`whoami` 返回当前账号身份（uid/昵称等，**回传时请自行打码敏感字段**）；`doctor`（README 提到其为人类可读的就绪报告）给出网关连通性、凭据有效性等状态。
- **失败怎么办**：
  - `doctor` 若提示 `unknown command` → 改跑 `weibo commands list` 查看内置命令全集，找到等价的健康检查命令名回传。
  - `whoami` 报 401 → 回到②重新登录；连续失败记录报错。

### ④ 领取体验包 / 购积分（若需要）✅

> **实测结果**：已领取 **7 天免费体验包**，服务状态 `trial_active`，**有效期至 2026-09-04**；体验期内 search 调用**零积分消耗**（余额恒为 0），未产生任何费用。


> CLI 走积分（Credits）计量的检索能力。先探一次再决定是否充值。

- **操作**：先直接跳到⑥跑一次 `weibo search statuses/limited --q 地震 --output json`；
  - 若报「无积分 / 额度不足 / 需开通」类错误 → 按终端报错给出的指引领取**免费体验包**或购买最小档积分（具体入口以报错信息 / doctor 输出为准）。
- **预期输出**：领取/购买成功后⑥不再报额度错误。
- **失败怎么办**：把「报错原文 + 提示的开通入口」完整回传；若个人身份连体验包都无法领取，直接落到对照表第 3/4 行评估。

### ⑤ 全量命令目录（核心回传物之一）✅

> **实测结果**：`weibo commands list` 返回当前账号 **69 条命令面**，`search` 组在列（含 `statuses/limited` 等 4 条），个人开发者身份未被收窄；全文存档 `outputs/weibo_probe/05_commands_list.txt`。

```bash
weibo commands list > ~/weibo_commands.txt
weibo commands show search statuses/limited
```

- **预期输出**：`commands list` 给出当前账号可用的完整命令目录（README 称其「与平台同步」，即会反映该账号的实际权限范围）；`commands show` 给出 search 命令的参数签名。
- **失败怎么办**：若 `commands list` 为空或报权限错误，记录报错原文——这是「个人身份能用什么」的直接证据，务必回传。

### ⑥ 实调检索（核心实测）✅

```bash
weibo search statuses/limited --q 地震 --output json > "backend/Qwen 初版/data/_weibo_probe.json" 2> "backend/Qwen 初版/data/_weibo_probe.stderr.txt"
echo "exit=$?"
```

- **预期输出**：退出码 0；`_weibo_probe.json` 为合法 JSON，含多条微博帖（含 `id`/`text`/`created_at` 类字段）。
- **实测结果**：`weibo search statuses/limited --q 地震 --type 1 --count 20 --output json` 成功，原始响应存档 `backend/Qwen 初版/data/_weibo_probe.json`：**顶层键 `statuses`、20 条、帖级字段 `id/text/created_at` 齐全**，与 `_parse_weibo` 假设完全匹配（**对照表 A 情形**，无需改代码）。注意事项：`--type` 为必填参数；**服务端强制 `--count ≤ 20`**（传 50 会报 `COUNT_EXCEEDS_MAX`）；条目无独立 `topics` 键，话题词需从 `text` 中以 `#…#` 正则提取（`live_feed.py` 已按此实现）。
- **失败怎么办**：
  - 401 → 未登录/会话过期，回②。
  - 积分/套餐类报错 → 记录**报错原文**（通常含套餐名与档位提示），回④。
  - 其他错误 → stderr 已落盘，连同退出码一并回传。**不要反复重试**（未登录请求 401 属预期，积分接口可能有频控）。

### ⑦ 查 Credits 消耗 ✅

> **实测结果**：体验期内多次调用后余额恒为 **0**——体验期（`trial_active`，至 2026-09-04）内 search 调用**零积分消耗**；到期后若未转正，weibo 模式自动降级至缓存/回放。


- **操作**：在⑥成功后，再次执行⑥同一命令（共 2 次调用），并查看积分余额——入口以 `weibo doctor`、`weibo auth whoami` 输出或平台控制台「我的积分」页为准。
- **预期输出**：得到「单次 `search statuses/limited` 消耗 N 积分」的实测值。
- **失败怎么办**：找不到余额查询命令 → 登录 open.weibo.com 控制台截图/记录积分余额与消耗流水，换算单次消耗。

---

## 二、需回传信息清单

| # | 回传物 | 来源步骤 | 备注 |
| --- | --- | --- | --- |
| 1 | `weibo --version` 与 `weibo --help` 全文 | ① | 版本核对 |
| 2 | `weibo commands list` **全文**（~/weibo_commands.txt） | ⑤ | 判断个人身份可用命令面 |
| 3 | `weibo commands show search statuses/limited` 输出 | ⑤ | 参数签名核对 |
| 4 | 搜索原始 JSON：`backend/Qwen 初版/data/_weibo_probe.json` | ⑥ | **勿裁剪**，字段映射以它为准；stderr 文件一并回传 |
| 5 | 实际开通档位（体验包/付费档名称与额度） | ④⑦ | 若未花钱注明「免费体验包」 |
| 6 | 单次积分消耗数值 | ⑦ | 含余额查询方式 |
| 7 | 任一步失败的**完整报错原文** | 各步 | 尤其 401/权限/套餐类报错 |
| 8 | （若②失败）授权页截图或报错 | ② | 影响评估的关键证据 |

---

## 三、「个人开发者不能创建应用」影响评估

**结论（最终实测已定论，2026-08-28 晚）：个人开发者身份完全走通——网页端开发者认证于 2026-08-28 13:56 通过，`doctor` 三闸门全绿，69 条命令面含 search 组，体验包可正常领取，实调与联调均成功，命中对照表 A 情形。第二轮发现的「开发者认证/开通服务」两道闸门对个人身份开放，不构成障碍。**

依据（本机探测 + 已知事实）：

1. **独立网关**：weibo-cli 走 `open.weibo.com/cli/api` 独立网关，而非传统 `api.weibo.com` 的 AppKey/AppSecret 应用鉴权体系；「微连接/微服务应用」是后者的注册模型，与 CLI 网关不直接挂钩。
2. **设备码授权内建**：0.9.1 README 明示 `OAuth built-in — Browser or device-code login; tokens in OS keychain`，登录全程由 CLI 自带的客户端身份完成，**无需用户提供自建应用的 appkey**。
3. **命令目录与平台同步**：`weibo commands list` 按账号实际权限返回可用命令面，意味着个人身份即使有功能收窄，也会显式体现在目录里，而不是直接拒绝登录。
4. **手册前提吻合**：该 CLI 面向「人类与 AI Agent」，设计目标即绕过传统应用创建流程。
5. **（第二轮修正 → 最终实测解除）`doctor` 三闸门**：未登录态曾列出 `登录账号 / 完成开发者认证 / 开通服务` 三项；登录后实测（2026-08-28）三道闸门全部通过——开发者认证对个人身份开放（网页端 13:56 通过），开通服务以免费体验包形式完成，对照表 D 情形**未触发**。

**风险点（已实测排除）**：个人身份可能遇到的 ①登录成功但 `search` 组命令不在可用目录、②可用但被积分/套餐拦截、③个别 `/biz` 级接口不开放——均未发生：69 条命令面含 search 组，体验期零积分消耗，联调直接走通。

---

## 四、实测结果 → 开发动作对照表

| 实测情形 | 判定信号 | 开发动作 |
| --- | --- | --- |
| **A. 全通**：⑥返回合法 JSON，字段结构与 `_parse_weibo` 假设一致（顶层键 ∈ {data, statuses, items, list, cards, result}，帖级含 id+text+created_at）🎯 **实际命中（2026-08-28）** | 退出码 0，`_weibo_probe.json` 可被现有解析器吃下（可本地用 `python3 -c` 灌一次 `_parse_weibo` 验证） | **直接联调**：`python3 "backend/Qwen 初版/live_feed.py" --mode weibo`，验证 `/live/social` 返回 `source:"weibo"` 的真实帖；不改代码 ✅ 已完成，未改任何解析代码 |
| **B. 结构微差**：JSON 合法，但顶层键或帖级字段名不在现有假设内（如套 `result.data.records` 之类） | 解析器抛 `未识别的 weibo-cli 顶层结构` 或吃出 0 条 | **改一处映射**：在 `_parse_weibo` 顶层键候选列表（或帖级字段候选）中补上实测键名；其余防御逻辑复用，改动 ≤ 5 行 |
| **C. 被套餐拦截**：登录成功、命令存在，但检索报积分/档位错误 | 报错含额度/积分/开通字样 | **升档**：按报错指引领取体验包或购最小档积分；若预算不允许长期调用，把 `--interval` 调大（降低轮询频率）并保留缓存兜底，核算单次消耗 × 演示时长的总成本 |
| **D. 完全不可用**：登录即被拒，或 search 组对个人身份不开放 | ②或⑤直接失败 | **维持数据集回放口径**：`--mode mock` 照常，演示话术统一为：「实时层架构已就绪：PlatformAdapter 之上 weibo-cli 通道已完成接口对齐与降级演练，因开放平台个人身份配额限制，本次演示采用经真实采集清洗后的数据集回放，接入开关即开即用」——强调**通道已验证、数据为回放**，不做无法兑现的实时承诺 |

---

## 五、最终实测结论（2026-08-28 晚）

**🎯 结论：对照表 A 情形（全通 → 直接联调）达成，零代码改动走通全链路。**

| 项 | 实测结果 |
| --- | --- |
| 开发者认证 | 网页端于 **2026-08-28 13:56 通过**；CLI 网关身份快照同日同步，`weibo doctor` 三闸门（登录账号 / 完成开发者认证 / 开通服务）**全绿** |
| 服务状态 | 7 天免费体验包已领取，`service_status = trial_active`，**到期日 2026-09-04**；体验期内 search 调用**零积分消耗**（余额恒 0，未产生费用） |
| 权限面 | `weibo commands list` 返回 **69 条命令**，`search` 组在列（`statuses/limited` 等 4 条），个人身份未被收窄 |
| 实调检索 | `search statuses/limited --q 地震 --type 1` 成功：顶层键 **`statuses`、20 条、`id/text/created_at` 齐全**；`--type` 必填；服务端强制 **`--count ≤ 20`**（超限报 `COUNT_EXCEEDS_MAX`）；话题词经 `#…#` 正则从 `text` 提取 |
| 联调 | `live_feed.py --mode weibo` 通过：`/live/social` 返回 `source:"weibo"` 的真实微博文本与话题标签；`_parse_weibo` 零改动兼容 |
| 降级链 | **weibo → cache → mock 三级降级验证有效**；体验期到期后自动降级，服务不挂 |

关键数据与存档：原始响应 `backend/Qwen 初版/data/_weibo_probe.json`；命令面全文 `outputs/weibo_probe/05_commands_list.txt`。

**后续注意**：体验期于 **2026-09-04** 到期；到期未转正则 weibo 模式自动降级至缓存/回放，无需人工干预；如需长期实时接入，以正式订阅/合同授权为前提。

---

*本清单为任务 #23 第一阶段交付文件（最终实测更新：2026-08-28）；未启动任何常驻服务，未执行 git 提交。*

